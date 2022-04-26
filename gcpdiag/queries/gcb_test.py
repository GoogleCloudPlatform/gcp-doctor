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
"""Test code in gcb.py."""

from unittest import mock

from gcpdiag import models
from gcpdiag.queries import apis_stub, gcb

DUMMY_PROJECT_NAME = 'gcpdiag-gcb1-aaaa'
BUILD_ID_FAILED_STEP = '01ff384c-d7f2-4295-ad68-5c32529d8b85'
BUIDL_ID_FAILED_LOGGING = '58c22070-5629-480e-b822-cd8eff7befb8'
BUILD_ID_FAILED_IMAGE_UPLOAD = 'db540598-5a45-46f3-a716-39d834e884c6'
CUSTOM1_SERVICE_ACCOUNT = \
  'projects/gcpdiag-gcb1-aaaa/serviceAccounts/gcb-custom1@gcpdiag-gcb1-aaaa.iam.gserviceaccount.com'
BUILD_IMAGE = 'us-central1-docker.pkg.dev/gcpdiag-gcb1-aaaa/gcb1-repository/image'


@mock.patch('gcpdiag.queries.apis.get_api', new=apis_stub.get_api_stub)
class TestCloudBuild:
  """Test Cloud Build"""

  def test_get_builds(self):
    context = models.Context(project_id=DUMMY_PROJECT_NAME)
    builds = gcb.get_builds(context=context)
    assert len(builds) == 3
    assert BUILD_ID_FAILED_STEP in builds
    assert BUIDL_ID_FAILED_LOGGING in builds
    assert BUILD_ID_FAILED_IMAGE_UPLOAD in builds

  def test_build_service_account(self):
    context = models.Context(project_id=DUMMY_PROJECT_NAME)
    builds = gcb.get_builds(context=context)
    assert (builds[BUILD_ID_FAILED_IMAGE_UPLOAD].service_account ==
            CUSTOM1_SERVICE_ACCOUNT)
    assert builds[BUILD_ID_FAILED_STEP].service_account is None

  def test_build_images(self):
    context = models.Context(project_id=DUMMY_PROJECT_NAME)
    builds = gcb.get_builds(context=context)
    assert builds[BUILD_ID_FAILED_IMAGE_UPLOAD].images == [BUILD_IMAGE]
    assert builds[BUILD_ID_FAILED_STEP].images == []
