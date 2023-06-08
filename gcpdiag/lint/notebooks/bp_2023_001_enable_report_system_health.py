# Copyright 2022 Google LLC
#
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
"""Vertex AI Workbench instance enables system health report

User-managed notebooks instances can report the system health of the core
services like Docker service, Docker reverse proxy agent, Jupyter service and
Jupyter API.

"""
from gcpdiag import lint, models
from gcpdiag.queries import apis, notebooks

GUEST_ATTRIBUTES = {
    'enable-guest-attributes': 'true',
    'report-system-health': 'true'
}


def run_rule(context: models.Context, report: lint.LintReportRuleInterface):

  if not apis.is_enabled(context.project_id, 'notebooks'):
    report.add_skipped(None, 'Notebooks API is disabled')
    return

  instances = notebooks.get_instances(context)
  if not instances:
    report.add_skipped(None, 'No instances found')
    return

  for instance in instances.values():
    if all(
        instance.metadata.get(k, 'false').casefold() == v.casefold()
        for k, v in GUEST_ATTRIBUTES.items()):
      report.add_ok(instance)
    else:
      report.add_failed(instance)
