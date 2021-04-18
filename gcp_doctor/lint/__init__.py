# Lint as: python3
"""lint command: find potential issues in GCP projects."""

import abc
import dataclasses
import enum
import importlib
import inspect
import logging
import pkgutil
import re
from collections.abc import Callable
from typing import List, Optional

from gcp_doctor import models
from gcp_doctor.utils import GcpApiError


class LintTestClass(enum.Enum):
  ERR = 'ERR'
  BP = 'BP'
  SEC = 'SEC'
  WARN = 'WARN'

  def __str__(self):
    return str(self.value)


@dataclasses.dataclass
class LintTest:
  """Identifies a lint test."""
  product: str
  test_class: LintTestClass
  test_id: str
  short_desc: str
  long_desc: str
  run_test_f: Callable

  def __hash__(self):
    return str(self.product + self.test_class.value + self.test_id).__hash__()

  def __str__(self):
    return self.product + '/' + self.test_class.value + '/' + self.test_id


class LintReport:
  """Used by the test modules to report test results to the user."""

  def test_start(self, test: LintTest, context: models.Context):
    """Called when a test run is started on a context."""
    return LintReportTestInterface(self, test, context)

  def test_end(self, test: LintTest, context: models.Context):
    """Called when the test is finished running."""
    pass

  @abc.abstractmethod
  def add_skipped(self,
                  test: LintTest,
                  context: models.Context,
                  resource: Optional[models.Resource],
                  reason: str,
                  short_info: str = None):
    pass

  @abc.abstractmethod
  def add_ok(self,
             test: LintTest,
             context: models.Context,
             resource: models.Resource,
             short_info: str = None):
    pass

  @abc.abstractmethod
  def add_failed(self,
                 test: LintTest,
                 context: models.Context,
                 resource: models.Resource,
                 reason: str,
                 short_info: str = None):
    pass


class LintReportTestInterface:
  """LintTest objects use this interface to report their results."""

  def __init__(self, report: LintReport, test: LintTest,
               context: models.Context):
    self.report = report
    self.test = test
    self.context = context

  def add_skipped(self,
                  resource: Optional[models.Resource],
                  reason: str,
                  short_info: str = None):
    self.report.add_skipped(self.test, self.context, resource, reason,
                            short_info)

  def add_ok(self, resource: models.Resource, short_info: str = ''):
    self.report.add_ok(self.test, self.context, resource, short_info)

  def add_failed(self,
                 resource: models.Resource,
                 reason: str,
                 short_info: str = None):
    self.report.add_failed(self.test, self.context, resource, reason,
                           short_info)


class LintTestRepository:
  """Repository of Lint tests which is also used to run the tests."""
  tests: List[LintTest]

  def __init__(self):
    self.tests = []

  def register_test(self, test: LintTest):
    self.tests.append(test)

  @staticmethod
  def _iter_namespace(ns_pkg):
    """Workaround for https://github.com/pyinstaller/pyinstaller/issues/1905."""
    prefix = ns_pkg.__name__ + '.'
    for p in pkgutil.iter_modules(ns_pkg.__path__, prefix):
      yield p[1]
    toc = set()
    for importer in pkgutil.iter_importers(ns_pkg.__name__.partition('.')[0]):
      if hasattr(importer, 'toc'):
        toc |= importer.toc
    for name in toc:
      if name.startswith(prefix):
        yield name

  def load_tests(self, pkg):
    for name in LintTestRepository._iter_namespace(pkg):
      # Skip code tests
      if name.endswith('_test'):
        continue

      # Determine Lint Test parameters based on the module name.
      m = re.search(
          r"""
           \.([^\.]+)\. # product path, e.g.: .gke.
           ([a-z]+)_    # class prefix, e.g.: 'err_'
           (\d+_\d+)    # id: 2020_001
        """, name, re.VERBOSE)
      if not m:
        logging.warning('can\'t determine test parameters from module name: %s',
                        name)
        continue
      product, test_class, test_id = m.group(1, 2, 3)

      # Import the module.
      module = importlib.import_module(name)

      # Get a reference to the run_test() function.
      run_test_f = None
      for f_name, f in inspect.getmembers(module, inspect.isfunction):
        if f_name == 'run_test':
          run_test_f = f
          break
      if not run_test_f:
        raise RuntimeError(f'module {module} doesn\'t have a run_test function')

      # Get module docstring.
      doc = inspect.getdoc(module)
      if not doc:
        raise RuntimeError(
            f'module {module} doesn\'t provide a module docstring')
      # The first line is the short "good state description"
      doc_lines = doc.splitlines()
      short_desc = doc_lines[0]
      long_desc = None
      if len(doc_lines) >= 3:
        if doc_lines[1]:
          raise RuntimeError(
              f'module {module} has a non-empty second line in the module docstring'
          )
        long_desc = '\n'.join(doc_lines[2:])

      # Instantiate the LintTest object and register it
      test = LintTest(product=product,
                      test_class=LintTestClass(test_class.upper()),
                      test_id=test_id,
                      run_test_f=run_test_f,
                      short_desc=short_desc,
                      long_desc=long_desc)

      self.register_test(test)

  def run_tests(self, context: models.Context, report: LintReport):
    self.tests.sort(key=str)
    for test in self.tests:
      test_report = report.test_start(test, context)
      try:
        test.run_test_f(context, test_report)
      except (ValueError) as e:
        report.add_skipped(test, context, None, str(e))
      except (GcpApiError) as api_error:
        report.add_skipped(test, context, None, str(api_error))
      report.test_end(test, context)
