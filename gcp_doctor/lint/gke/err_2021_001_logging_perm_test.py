# Lint as: python3
"""Test code in err_2020_001_sa_perm.py."""

import io
from unittest import mock

from gcp_doctor import lint, models
from gcp_doctor.lint import report_terminal
from gcp_doctor.lint.gke import err_2021_001_logging_perm
from gcp_doctor.queries import gke_stub, iam_stub

DUMMY_PROJECT_NAME = 'gcpd-gke-1-9b90'


def get_api_stub(service_name: str, version: str):
  if service_name == 'container':
    return gke_stub.get_api_stub(service_name, version)
  elif service_name in ['cloudresourcemanager', 'iam']:
    return iam_stub.get_api_stub(service_name, version)
  else:
    raise ValueError(f"I don't know how to mock {service_name}")


@mock.patch('gcp_doctor.queries.apis.get_api', new=get_api_stub)
class Test:

  def test_run_rule(self):
    context = models.Context(projects=[DUMMY_PROJECT_NAME])
    output = io.StringIO()
    report = report_terminal.LintReportTerminal(file=output)
    rule = lint.LintRule(product='test',
                         rule_class=lint.LintRuleClass.ERR,
                         rule_id='9999_999',
                         short_desc='short description',
                         long_desc='long description',
                         run_rule_f=err_2021_001_logging_perm.run_rule)
    lint_report = report.rule_start(rule, context)
    rule.run_rule_f(context, lint_report)
    report.rule_end(rule, context)
    # yapf: disable
    assert (output.getvalue() == (
        '*  test/ERR/9999_999: short description\n'
        '   - gcpd-gke-1-9b90/europe-west1/gke2/default-pool                       [ OK ]\n'
        '   - gcpd-gke-1-9b90/europe-west1/gke3/default-pool                       [FAIL]\n'
        '     service account: gke3sa@gcpd-gke-1-9b90.iam.gserviceaccount.com\n'
        '     missing role: roles/logging.logWriter\n'
        '   - gcpd-gke-1-9b90/europe-west4-a/gke1                                  [SKIP]\n'
        '     logging disabled\n\n'
        '   long description\n\n'
    ))
