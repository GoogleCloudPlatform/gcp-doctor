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

# Lint as: python3
"""GCE nodes have good disk performance.

Verify that the persistent disks used by the GCE instances provide a "good"
performance, where good is defined to be less than 100ms IO queue time. If it's
more than that, it probably means that the instance would benefit from a faster
disk (changing the type or making it larger).
"""

import operator as op
from typing import Dict

from gcpdiag import config, lint, models
from gcpdiag.queries import gce, monitoring

SLO_LATENCY_MS = 100
# SLO: at least 99.5% of minutes are good (7 minutes in a day)
SLO_BAD_MINUTES_RATIO = 0.005
# If we have less than this minutes measured, skip
SLO_VALID_MINUTES_PER_DAY = 12 * 60

_query_results_per_project_id: Dict[str, monitoring.TimeSeriesCollection] = {}


def prefetch_rule(context: models.Context):
  # Fetch the metrics for all instances.
  instances = gce.get_instances(context)
  if not instances:
    return

  within_str = 'within %dd, d\'%s\'' % (config.WITHIN_DAYS,
                                        monitoring.period_aligned_now(60))
  _query_results_per_project_id[context.project_id] = \
      monitoring.query(
          context.project_id, f"""
fetch gce_instance
| {{ metric 'agent.googleapis.com/disk/operation_time'
     | align rate(1m) ;
     metric 'agent.googleapis.com/disk/operation_count'
     | align delta(1m) }}
| {within_str}
| filter metric.device !~ '.*\\\\d'
| join
| value [val(0)*val(1), val(1)]
| group_by [resource.instance_id], [sum(val(0)), sum(val(1))]
| value [val(0)/val(1)]
| every 1m
| value(val() > cast_units({SLO_LATENCY_MS}, "ms/s"))
| group_by 1d, [ .count_true, .count ]
  """)


def run_rule(context: models.Context, report: lint.LintReportRuleInterface):
  instances = gce.get_instances(context)
  if not instances:
    report.add_skipped(None, 'no instances found')
    return

  for i in sorted(instances.values(), key=op.attrgetter('project_id', 'name')):
    ts_key = frozenset({f'resource.instance_id:{i.id}'})
    try:
      ts = _query_results_per_project_id[context.project_id][ts_key]
    except KeyError:
      report.add_skipped(i, 'no data')
      continue

    # Did we miss the SLO on any day?
    # note: we don't calculate the SLO for the whole "WITHIN_DAYS" period
    # because otherwise you would get different results depending on how that
    # period is defined.
    total_minutes_bad = 0
    total_minutes = 0
    slo_missed = 0
    slo_valid = 0
    for day_value in ts['values']:
      total_minutes_bad += day_value[0]
      total_minutes += day_value[1]
      if day_value[1] >= SLO_VALID_MINUTES_PER_DAY:
        slo_valid = 1
        if day_value[0] / day_value[1] > SLO_BAD_MINUTES_RATIO:
          slo_missed = 1
    if slo_missed:
      report.add_failed(
          i, f'disk latency >{SLO_LATENCY_MS}ms during {total_minutes_bad} ' +
          f'out of {total_minutes} minutes')
    elif not slo_valid:
      report.add_skipped(i, 'not enough data')
    else:
      report.add_ok(i)
