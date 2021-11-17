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
"""Test code in gke.py."""

import ipaddress
from unittest import mock

import pytest
from packaging.version import LegacyVersion

from gcpdiag import models
from gcpdiag.queries import apis_stub, gce, gke
from gcpdiag.queries.gke import Version

DUMMY_PROJECT_NAME = 'gcpd-gke-1-9b90'
DUMMY_CLUSTER1_NAME = f'projects/{DUMMY_PROJECT_NAME}/zones/europe-west4-a/clusters/gke1'
DUMMY_CLUSTER1_LABELS = {'foo': 'bar'}
DUMMY_CLUSTER2_NAME = f'projects/{DUMMY_PROJECT_NAME}/locations/europe-west1/clusters/gke2'
DUMMY_CLUSTER2_SHORT_NAME = f'{DUMMY_PROJECT_NAME}/europe-west1/gke2'
DUMMY_CLUSTER1_SERVICE_ACCOUNT = '18404348413-compute@developer.gserviceaccount.com'
DUMMY_CLUSTER2_SERVICE_ACCOUNT = 'gke2sa@gcpd-gke-1-9b90.iam.gserviceaccount.com'

# pylint: disable=consider-iterating-dictionary


@mock.patch('gcpdiag.queries.apis.get_api', new=apis_stub.get_api_stub)
class TestCluster:
  """Test gke.Cluster."""

  def test_get_clusters_by_label(self):
    """get_clusters returns the right cluster matched by label."""
    context = models.Context(project_id=DUMMY_PROJECT_NAME,
                             labels=[DUMMY_CLUSTER1_LABELS])
    clusters = gke.get_clusters(context)
    assert DUMMY_CLUSTER1_NAME in clusters and len(clusters) == 1

  def test_get_clusters_by_region(self):
    """get_clusters returns the right cluster matched by region."""
    context = models.Context(project_id=DUMMY_PROJECT_NAME,
                             regions=['europe-west4'])
    clusters = gke.get_clusters(context)
    assert DUMMY_CLUSTER1_NAME in clusters and len(clusters) == 1

  def test_cluster_properties(self):
    """verify cluster property methods."""
    context = models.Context(project_id=DUMMY_PROJECT_NAME)
    clusters = gke.get_clusters(context)
    c = clusters[DUMMY_CLUSTER1_NAME]
    assert c.name == 'gke1'
    assert c.master_version == '1.20.10-gke.1600'
    assert c.release_channel == 'REGULAR'

  def test_get_path_regional(self):
    """full_path and short_path should return correct results with regional clusters."""
    context = models.Context(project_id=DUMMY_PROJECT_NAME)
    clusters = gke.get_clusters(context)
    assert DUMMY_CLUSTER2_NAME in clusters.keys()
    c = clusters[DUMMY_CLUSTER2_NAME]
    assert c.full_path == DUMMY_CLUSTER2_NAME
    assert str(c) == DUMMY_CLUSTER2_NAME
    assert c.short_path == DUMMY_CLUSTER2_SHORT_NAME

  def test_has_logging_enabled_false(self):
    """has_logging_enabled should return false for GKE cluster with logging disabled."""
    context = models.Context(project_id=DUMMY_PROJECT_NAME)
    clusters = gke.get_clusters(context)
    assert DUMMY_CLUSTER1_NAME in clusters.keys()
    c = clusters[DUMMY_CLUSTER1_NAME]
    assert not c.has_logging_enabled()

  def test_has_logging_enabled_true(self):
    """has_logging_enabled should return true for GKE cluster with logging enabled."""
    context = models.Context(project_id=DUMMY_PROJECT_NAME)
    clusters = gke.get_clusters(context)
    assert DUMMY_CLUSTER2_NAME in clusters.keys()
    c = clusters[DUMMY_CLUSTER2_NAME]
    assert c.has_logging_enabled()

  def test_has_default_service_account(self):
    """has_default_service_account should return true for GKE node-pools with
    the default GCE SA."""
    context = models.Context(project_id=DUMMY_PROJECT_NAME)
    clusters = gke.get_clusters(context)
    # 'default-pool' has the default SA
    c = clusters[DUMMY_CLUSTER1_NAME]
    assert c.nodepools[0].has_default_service_account()
    # 'default-pool' doesn't have the default SA
    c = clusters[DUMMY_CLUSTER2_NAME]
    assert not c.nodepools[0].has_default_service_account()

  def test_pod_ipv4_cidr(self):
    """returns correct pod CIDR"""
    context = models.Context(project_id=DUMMY_PROJECT_NAME)
    clusters = gke.get_clusters(context)
    # cluster 1
    c = clusters[DUMMY_CLUSTER1_NAME]
    assert c.pod_ipv4_cidr.compare_networks(
        ipaddress.ip_network('192.168.1.0/24')) == 0
    # cluster 2
    c = clusters[DUMMY_CLUSTER2_NAME]
    assert c.pod_ipv4_cidr.compare_networks(
        ipaddress.ip_network('10.112.0.0/14')) == 0

  def test_current_node_count(self):
    """returns correct number of nodes running"""
    context = models.Context(project_id=DUMMY_PROJECT_NAME)
    clusters = gke.get_clusters(context)
    # cluster 1
    c = clusters[DUMMY_CLUSTER1_NAME]
    assert c.current_node_count == 1
    # cluster 2
    c = clusters[DUMMY_CLUSTER2_NAME]
    assert c.current_node_count == 3

  def test_np_pod_ipv4_cidr_size(self):
    """resturn correct pod CIDR size per allocated to node pool."""
    context = models.Context(project_id=DUMMY_PROJECT_NAME)
    clusters = gke.get_clusters(context)
    # cluster 1
    c = clusters[DUMMY_CLUSTER1_NAME]
    assert c.nodepools[0].pod_ipv4_cidr_size == 24

  def test_has_workload_identity_enabled(self):
    context = models.Context(project_id=DUMMY_PROJECT_NAME)
    clusters = gke.get_clusters(context)
    c = clusters[DUMMY_CLUSTER1_NAME]
    assert not c.nodepools[0].has_workload_identity_enabled()

  def test_nodepool_instance_groups(self):
    context = models.Context(project_id=DUMMY_PROJECT_NAME)
    clusters = gke.get_clusters(context)
    c = clusters[DUMMY_CLUSTER1_NAME]
    migs = c.nodepools[0].instance_groups
    assert len(migs) == 1
    m = next(iter(migs))
    assert m.is_gke()

  def test_get_node_by_instance_id(self):
    context = models.Context(project_id=DUMMY_PROJECT_NAME)
    clusters = gke.get_clusters(context)
    c = clusters[DUMMY_CLUSTER1_NAME]
    migs = c.nodepools[0].instance_groups
    assert len(migs) == 1
    m = next(iter(migs))
    found_nodes = 0
    for i in gce.get_instances(context).values():
      if m.is_instance_member(m.project_id, m.region, i.name):
        node = gke.get_node_by_instance_id(context, i.id)
        assert node.mig == m
        found_nodes += 1
    assert found_nodes == 1

  def test_service_account_property(self):
    context = models.Context(project_id=DUMMY_PROJECT_NAME)
    clusters = gke.get_clusters(context)
    # 'default-pool' has the default SA
    c = clusters[DUMMY_CLUSTER1_NAME]
    assert c.nodepools[0].service_account == DUMMY_CLUSTER1_SERVICE_ACCOUNT
    # cluster2 has a custom SA
    c = clusters[DUMMY_CLUSTER2_NAME]
    assert c.nodepools[0].service_account == DUMMY_CLUSTER2_SERVICE_ACCOUNT


class TestVersion:
  """ Test GKE Version class """

  def test_init(self):
    Version('1.19.13-gke.701')
    self.raises('x.19.13-gke.701')
    self.raises('.19.13-gke.701')
    self.raises('1.x.13-gke.701')
    self.raises('1..13-gke.701')
    self.raises('x')

  def test_same_major(self):
    assert Version('1.19.13-gke.701').same_major(Version('1.23.45-six.7'))
    assert not Version('1.19.13-gke.701').same_major(Version('9.23.45-six.7'))

  def test_diff_minor(self):
    assert Version('1.19.13-gke.701').diff_minor(Version('1.23.45-six.7')) == 4
    assert Version('1.19.13-gke.701').diff_minor(Version('1.19.45-six.7')) == 0

  def test_eq_str(self):
    assert Version('1.19.13-gke.701') == '1.19.13-gke.701'
    assert Version('1.19.13-gke.701') != '1.19.13-gke.702'

  def test_add_str(self):
    assert 'the version is: ' + Version('1.19.13-gke.701') == \
      'the version is: 1.19.13-gke.701'
    assert Version('1.19.13-gke.701') + '!' == '1.19.13-gke.701!'
    with pytest.raises(TypeError):
      assert Version('1.19.13-gke.701') + 42
    with pytest.raises(TypeError):
      assert 42 + Version('1.19.13-gke.701')
    with pytest.raises(TypeError):
      assert Version('1.19.13-gke.701') + Version('1.19.13-gke.701')

  def test_eq_version(self):
    assert Version('1.19.13-gke.701') == Version('1.19.13-gke.701')
    assert Version('1.19.13-gke.701') != Version('1.19.13-gke.702')

  def test_compatible_with_legacy_version(self):
    l1 = LegacyVersion(Version('1.19.13-gke.701'))
    l2 = LegacyVersion(Version('1.19.14-something.else'))
    assert l1 < l2

  def test_compare_lt_gt(self):
    assert Version('1.19.13-gke.701') < Version('2.19.13-gke.701')
    assert Version('1.19.13-gke.701') < Version('1.20.13-gke.701')
    assert Version('1.19.13-gke.701') < Version('1.19.14-gke.701')

    assert Version('1.19') < Version('1.19.13-gke.701')
    assert Version('1.19.13-gke.701') < Version('1.20')
    assert Version('1') < Version('1.19.13-gke.701')
    assert Version('1.19.13-gke.701') < Version('2')
    assert Version('1') < Version('2')

  def raises(self, v):
    with pytest.raises(Exception):
      Version(v)
