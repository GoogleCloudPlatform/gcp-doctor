#
# Copyright 2022 Google LLC
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# Lint as: python3
"""BigQuery copy job does not exceed the daily copy quota

This rule verifies that there are no log entries reporting that the number of copy jobs
running in a project exceeded the daily limit

"""
from boltons.iterutils import get_path

from gcpdiag import lint, models
from gcpdiag.queries import apis, crm, logs

MATCH_STR = 'Quota exceeded: Your project exceeded quota for copies per project.'

COPY_QUOTA_EXCEEDED = [
    'severity=ERROR',
    'protoPayload.@type="type.googleapis.com/google.cloud.audit.AuditLog"',
    f'protoPayload.status.message:("{MATCH_STR}")',
]
logs_by_project = {}


def prepare_rule(context: models.Context):
  logs_by_project[context.project_id] = logs.query(
      project_id=context.project_id,
      resource_type='bigquery_resource',
      log_name='log_id("cloudaudit.googleapis.com/data_access")',
      filter_str=' AND '.join(COPY_QUOTA_EXCEEDED))


def run_rule(context: models.Context, report: lint.LintReportRuleInterface):
  project = crm.get_project(context.project_id)
  # skip entire rule if logging is disabled
  if not apis.is_enabled(context.project_id, 'logging'):
    report.add_skipped(project, 'Logging api is disabled')
    return
  # skip entire rule if the BigQuery API is disabled
  if not apis.is_enabled(context.project_id, 'bigquery'):
    report.add_skipped(project, 'BigQuery api is disabled')
    return
  if logs_by_project.get(context.project_id) and \
     logs_by_project[context.project_id].entries:
    for log_entry in logs_by_project[context.project_id].entries:
      project_ok_flag = True
      logging_check_path = get_path(log_entry,
                                    ('protoPayload', 'status', 'message'),
                                    default='')
      if MATCH_STR not in logging_check_path:
        continue
      else:
        report.add_failed(
            project,
            'Quota exceeded: Your project exceeded quota for copies per project.'
        )
        project_ok_flag = False
        break
    if project_ok_flag:
      report.add_ok(project)
  else:
    report.add_ok(project)
