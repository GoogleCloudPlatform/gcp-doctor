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
"""Test code in logs.py."""

import concurrent.futures
import re
from unittest import mock

from gcpdiag.queries import apis_stub, logs, logs_stub

DUMMY_PROJECT_ID = 'gcpd-gke-1-9b90'
FIRST_INSERT_ID = '-hqnw82c9z6'
TOTAL_LOG_ENTRIES = 6


@mock.patch('gcpdiag.queries.apis.get_api', new=apis_stub.get_api_stub)
class TestLogs:
  """Test logs.py functions."""

  def test_single_query(self):
    query = logs.query(project_id=DUMMY_PROJECT_ID,
                       resource_type='gce_instance',
                       log_name='fake.log',
                       filter_str='filter1')

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
      logs.execute_queries(executor)
      # verify the number of entries
      all_entries = list(query.entries)
      assert len(all_entries) == TOTAL_LOG_ENTRIES
      # verify that the first log entry is correct (the earliest one)
      first = next(iter(query.entries))
      assert first['insertId'] == FIRST_INSERT_ID

  def test_aggregated_query(self):
    """Verify that multiple queries get aggregated into one."""
    logs.query(project_id=DUMMY_PROJECT_ID,
               resource_type='gce_instance',
               log_name='fake.log',
               filter_str='filter1')
    logs.query(project_id=DUMMY_PROJECT_ID,
               resource_type='gce_instance',
               log_name='fake.log',
               filter_str='filter2')
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
      logs.execute_queries(executor)
    # verify the filter that is used
    assert re.match(
        r'timestamp>"\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d\+00:00"\n'
        r'resource.type="gce_instance"\n'
        r'logName="fake.log"\n'
        r'\(\(filter1\) OR \(filter2\)\)', logs_stub.logging_body['filter'])
    # also verify other parameters of the job
    assert logs_stub.logging_body['orderBy'] == 'timestamp desc'
    assert logs_stub.logging_body['pageSize'] == 500
    assert logs_stub.logging_body['resourceNames'] == [
        'projects/gcpd-gke-1-9b90'
    ]
