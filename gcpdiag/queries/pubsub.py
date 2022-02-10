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
"""Queries related to GCP PubSub

"""

import logging
import re
from typing import Dict, Mapping

import googleapiclient.errors

from gcpdiag import caching, config, models, utils
from gcpdiag.queries import apis, iam


class Topic(models.Resource):
  """Represent a Topic"""
  _resource_data: dict

  def __init__(self, project_id, resource_data):
    super().__init__(project_id=project_id)
    self._resource_data = resource_data
    self._metadata_dict = None

  @property
  def name(self) -> str:
    m = re.search(r'/topics/([^/]+)$', self._resource_data['name'])
    if not m:
      raise RuntimeError('can\'t determine name of topic %s' %
                         (self._resource_data['name']))
    return m.group(1)

  @property
  def full_path(self) -> str:
    return self._resource_data['name']

  @property
  def short_path(self) -> str:
    path = self.project_id + '/' + self.name
    return path


@caching.cached_api_call
def get_topics(context: models.Context) -> Mapping[str, Topic]:
  topics: Dict[str, Topic] = {}
  if not apis.is_enabled(context.project_id, 'pubsub'):
    return topics
  pubsub_api = apis.get_api('pubsub', 'v1', context.project_id)
  logging.info('fetching list of PubSub topics in project %s',
               context.project_id)
  query = pubsub_api.projects().topics().list(
      project=f'projects/{context.project_id}')
  try:
    resp = query.execute(num_retries=config.API_RETRIES)
    if 'topics' not in resp:
      return topics
    for resp_b in resp['topics']:
      # verify that we have some minimal data that we expect
      if 'name' not in resp_b:
        raise RuntimeError('missing data in topics response')
      f = Topic(project_id=context.project_id, resource_data=resp_b)
      topics[f.full_path] = f
  except googleapiclient.errors.HttpError as err:
    raise utils.GcpApiError(err) from err
  return topics


class TopicIAMPolicy(iam.BaseIAMPolicy):

  def _is_resource_permission(self, permission):
    return True


@caching.cached_api_call(in_memory=True)
def get_topic_iam_policy(name: str) -> TopicIAMPolicy:
  project_id = utils.get_project_by_res_name(name)

  pubsub_api = apis.get_api('pubsub', 'v1', project_id)
  request = pubsub_api.projects().topics().getIamPolicy(resource=name)

  return iam.fetch_iam_policy(request, TopicIAMPolicy, project_id, name)


class Subscription(models.Resource):
  """Represent a Subscription"""
  _resource_data: dict

  def __init__(self, project_id, resource_data):
    super().__init__(project_id=project_id)
    self._resource_data = resource_data
    self._metadata_dict = None

  @property
  def name(self) -> str:
    m = re.search(r'/subscriptions/([^/]+)$', self._resource_data['name'])
    if not m:
      raise RuntimeError('can\'t determine name of subscription %s' %
                         (self._resource_data['name']))
    return m.group(1)

  @property
  def full_path(self) -> str:
    return self._resource_data['name']

  @property
  def short_path(self) -> str:
    path = self.project_id + '/' + self.name
    return path

  @property
  def topic(self) -> Topic:
    if 'topic' not in self._resource_data:
      raise RuntimeError('topic not set for subscription {self.name}')
    m = re.match(r'projects/([^/]+)/topics/([^/]+)',
                 self._resource_data['topic'])
    if not m:
      raise RuntimeError("can't parse topic: %s" % self._resource_data['topic'])
    (project_id, topic_name) = (m.group(1), self._resource_data['topic'])
    topics = get_topics(models.Context(project_id))
    if topic_name not in topics:
      raise RuntimeError(
          f'Topic {topic_name} for Subscription {self.name} not found')
    return topics[topic_name]


@caching.cached_api_call
def get_subscription(context: models.Context) -> Mapping[str, Subscription]:
  subscription: Dict[str, Subscription] = {}
  if not apis.is_enabled(context.project_id, 'pubsub'):
    return subscription
  pubsub_api = apis.get_api('pubsub', 'v1', context.project_id)
  logging.info('fetching list of PubSub subscriptions in project %s',
               context.project_id)
  query = pubsub_api.projects().subscriptions().list(
      project=f'projects/{context.project_id}')
  try:
    resp = query.execute(num_retries=config.API_RETRIES)
    if 'subscriptions' not in resp:
      return subscription
    for resp_b in resp['subscriptions']:
      # verify that we have some minimal data that we expect
      if 'name' not in resp_b:
        raise RuntimeError('missing data in topics response')
      f = Subscription(project_id=context.project_id, resource_data=resp_b)
      subscription[f.full_path] = f
  except googleapiclient.errors.HttpError as err:
    raise utils.GcpApiError(err) from err
  return subscription


class SubscriptionIAMPolicy(iam.BaseIAMPolicy):

  def _is_resource_permission(self, permission):
    return True


@caching.cached_api_call(in_memory=True)
def get_subscription_iam_policy(name: str) -> SubscriptionIAMPolicy:
  project_id = utils.get_project_by_res_name(name)

  pubsub_api = apis.get_api('pubsub', 'v1', project_id)
  request = pubsub_api.projects().subscriptions().getIamPolicy(resource=name)

  return iam.fetch_iam_policy(request, SubscriptionIAMPolicy, project_id, name)
