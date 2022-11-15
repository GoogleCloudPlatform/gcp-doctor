# Copyright 2021 Google LLC
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
"""GCE VM service account is valid

Disabling or deleting the service account used by a GCE VM will results in
authentication issues for gcloud components and dependant apps.
Restore/enable the service account use by the VM.
"""

from gcpdiag import lint, models
from gcpdiag.queries import gce, iam


def run_rule(context: models.Context, report: lint.LintReportRuleInterface):
  # Find all instances.
  instances = gce.get_instances(context).values()
  if not instances:
    report.add_skipped(None, 'no instances found')

  for instance in sorted(instances, key=lambda i: i.name):
    # Verify instance has a service account as it may be created without one.
    sa = instance.service_account
    if sa:
      # Verify service account exists for VM
      if not iam.is_service_account_existing(sa, context.project_id):
        report.add_failed(instance,
                          f'attached service account is deleted: {sa}')
      elif not iam.is_service_account_enabled(sa, context.project_id):
        report.add_failed(instance,
                          f'attached service account is disabled: {sa}')
      else:
        report.add_ok(instance)
    else:
      report.add_skipped(instance, 'instance does not have a service account')
