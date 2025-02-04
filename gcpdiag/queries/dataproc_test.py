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
"""Test code in dataproc.py."""

from unittest import mock

from gcpdiag import models
from gcpdiag.queries import apis_stub, dataproc

DUMMY_PROJECT_NAME = 'gcpdiag-dataproc1-aaaa'
DUMMY_SUCCESS_JOB_ID = '1234567890'
DUMMY_FAILED_JOB_ID = '1234567891'
NUMBER_OF_CLUSTERS_IN_DATAPROC_JSON_DUMP_FILE = 4
REGION = 'us-central1'
POLICY_ID = 'CDF_AUTOSCALING_POLICY_V1'


@mock.patch('gcpdiag.queries.apis.get_api', new=apis_stub.get_api_stub)
class TestDataproc:
  """Test Dataproc"""

  def test_get_clusters(self):
    context = models.Context(project_id=DUMMY_PROJECT_NAME)
    clusters = dataproc.get_clusters(context)
    assert len(clusters) == NUMBER_OF_CLUSTERS_IN_DATAPROC_JSON_DUMP_FILE

  def test_get_cluster(self):
    cluster = dataproc.get_cluster('good', 'us-central1', DUMMY_PROJECT_NAME)
    assert cluster.name == 'good'

  def test_is_running(self):
    context = models.Context(project_id=DUMMY_PROJECT_NAME)
    clusters = dataproc.get_clusters(context)
    assert ('good', True) in [(c.name, c.is_running()) for c in clusters]

  def test_stackdriver_logging_enabled(self):
    context = models.Context(project_id=DUMMY_PROJECT_NAME)
    clusters = dataproc.get_clusters(context)
    for c in clusters:
      # dataproc:dataproc.logging.stackdriver.enable is set
      # and equals "true"
      if c.name == 'test-best-practices-enabled':
        assert c.is_stackdriver_logging_enabled()

      # dataproc:dataproc.logging.stackdriver.enable is set
      # and equals "false"
      if c.name == 'test-best-practices-disabled':
        assert not c.is_stackdriver_logging_enabled()

  def test_monitoring_enabled(self):
    context = models.Context(project_id=DUMMY_PROJECT_NAME)
    clusters = dataproc.get_clusters(context)
    for cluster in clusters:
      if cluster.name == 'test-best-practices-enabled':
        assert cluster.is_stackdriver_monitoring_enabled()

      if cluster.name == 'test-best-practices-disabled':
        assert not cluster.is_stackdriver_monitoring_enabled()

  def test_zone(self):
    context = models.Context(project_id=DUMMY_PROJECT_NAME)
    clusters = dataproc.get_clusters(context)
    for cluster in clusters:
      if cluster.name == 'test-best-practices-enabled':
        assert cluster.zone == 'us-central1-b'

  def test_is_gce_cluster(self):
    context = models.Context(project_id=DUMMY_PROJECT_NAME)
    clusters = dataproc.get_clusters(context)
    for cluster in clusters:
      if cluster.name == 'test-best-practices-enabled':
        assert cluster.is_gce_cluster

  def test_gce_network_uri(self):
    context = models.Context(project_id=DUMMY_PROJECT_NAME)
    clusters = dataproc.get_clusters(context)
    uri = 'projects/gcpdiag-dataproc1-aaaa/global/networks/default'
    for cluster in clusters:
      if cluster.name == 'test-best-practices-enabled':
        assert uri in cluster.gce_network_uri

  def test_auto_scaling_policy(self):
    context = models.Context(project_id=DUMMY_PROJECT_NAME)
    policy = dataproc.get_auto_scaling_policy(context.project_id, REGION,
                                              POLICY_ID)
    policy_name = ('projects/gcpdiag-dataproc1-aaaa/regions/us-central1/'
                   'autoscalingPolicies/CDF_AUTOSCALING_POLICY_V1')
    assert policy.name == policy_name

  def test_get_job_by_jobid_(self):
    failed_job = dataproc.get_job_by_jobid(
        project_id=DUMMY_PROJECT_NAME,
        region='us-central1',
        job_id=DUMMY_FAILED_JOB_ID,
    )

    assert failed_job.state == 'ERROR'

    success_job = dataproc.get_job_by_jobid(
        project_id=DUMMY_PROJECT_NAME,
        region='us-central1',
        job_id=DUMMY_SUCCESS_JOB_ID,
    )

    assert success_job.state == 'DONE'
