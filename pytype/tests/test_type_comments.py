"""Tests for type comments."""


from pytype.tests import test_inference


class FunctionCommentTest(test_inference.InferenceTest):
  """Tests for type comments."""

  def testCommentOutTypeComment(self):
    ty = self.Infer("""
      def foo():
        # # type: () -> not a legal type spec
        return 1
    """, deep=True, filename="test.py")
    self.assertTypesMatchPytd(ty, """
      def foo() -> int
    """)

  def testFunctionUnspecifiedArgs(self):
    ty = self.Infer("""
      def foo(x):
        # type: (...) -> int
        return x
    """, filename="test.py")
    self.assertTypesMatchPytd(ty, """
      def foo(x) -> int
    """)

  def testFunctionReturnSpace(self):
    ty = self.Infer("""
      from typing import Dict
      def foo(x):
        # type: (...) -> Dict[int, int]
        return x
    """, filename="test.py")
    self.assertTypesMatchPytd(ty, """
      from typing import Dict
      def foo(x) -> Dict[int, int]
    """)

  def testFunctionZeroArgs(self):
    # Include some stray whitespace.
    ty = self.Infer("""
      def foo():
        # type: (  ) -> int
        return x
    """, filename="test.py")
    self.assertTypesMatchPytd(ty, """
      def foo() -> int
    """)

  def testFunctionOneArg(self):
    # Include some stray whitespace.
    ty = self.Infer("""
      def foo(x):
        # type: ( int ) -> int
        return x
    """, filename="test.py")
    self.assertTypesMatchPytd(ty, """
      def foo(x: int) -> int
    """)

  def testFunctionSeveralArgs(self):
    ty = self.Infer("""
      def foo(x, y, z):
        # type: (int, str, float) -> None
        return x
    """, filename="test.py")
    self.assertTypesMatchPytd(ty, """
      def foo(x: int, y: str, z: float) -> None
    """)

  def testFunctionSeveralLines(self):
    ty = self.Infer("""
      def foo(x,
              y,
              z):
        # type: (int, str, float) -> None
        return x
    """, filename="test.py")
    self.assertTypesMatchPytd(ty, """
      def foo(x: int, y: str, z: float) -> None
    """)

  def testFunctionNoneInArgs(self):
    ty = self.Infer("""
      def foo(x, y, z):
        # type: (int, str, None) -> None
        return x
    """, filename="test.py")
    self.assertTypesMatchPytd(ty, """
      def foo(x: int, y: str, z: None) -> None
    """)

  def testSelfIsOptional(self):
    ty = self.Infer("""
      class Foo(object):
        def f(self, x):
          # type: (int) -> None
          pass

        def g(self, x):
          # type: (Foo, int) -> None
          pass
    """, filename="test.py")
    self.assertTypesMatchPytd(ty, """
      class Foo(object):
        def f(self, x: int) -> None: ...
        def g(self, x: int) -> None: ...
    """)

  def testClsIsOptional(self):
    ty = self.Infer("""
      class Foo(object):
        @classmethod
        def f(cls, x):
          # type: (int) -> None
          pass

        @classmethod
        def g(cls, x):
          # type: (Foo, int) -> None
          pass
    """, filename="test.py")
    self.assertTypesMatchPytd(ty, """
      class Foo(object):
        f = ... # type: classmethod
        g = ... # type: classmethod
    """)

  def testFunctionStarArg(self):
    # TODO(dbaum): This test can be simplified once *args types appear in
    # the resulting pytd.
    ty = self.Infer("""
      class Foo(object):
        def __init__(self, *args):
          # type: (int) -> None
          self.value = args[0]
    """, filename="test.py", deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      class Foo(object):
        value = ...  # type: int
        def __init__(self, *args) -> None: ...
    """)

  def testFunctionStarStarArg(self):
    # TODO(dbaum): This test can be simplified once **kwargs types appear in
    # the resulting pytd.
    ty = self.Infer("""
      class Foo(object):
        def __init__(self, **kwargs):
          # type: (int) -> None
          self.value = kwargs['x']
    """, filename="test.py", deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      class Foo(object):
        value = ...  # type: int
        def __init__(self, **kwargs) -> None: ...
    """)

  def testFunctionNoReturn(self):
    _, errors = self.InferAndCheck("""
      def foo():
        # type: () ->
        pass
    """, filename="test.py")
    self.assertErrorLogContains(
        errors, r"test\.py.*line 3.*invalid-function-type-comment")

  def testFunctionTooManyArgs(self):
    _, errors = self.InferAndCheck("""
      def foo(x):
        # type: (int, str) -> None
        y = x
        return x
    """, filename="test.py")
    self.assertErrorLogContains(
        errors, (r"test\.py.*line 3.*invalid-function-type-comment"
                 r".*Expected 1 args, 2 given"))

  def testFunctionTooFewArgs(self):
    _, errors = self.InferAndCheck("""
      def foo(x, y, z):
        # type: (int, str) -> None
        y = x
        return x
    """, filename="test.py")
    self.assertErrorLogContains(
        errors, (r"test\.py.*line 3.*invalid-function-type-comment"
                 r".*Expected 3 args, 2 given"))

  def testFunctionTooFewArgsDoNotCountSelf(self):
    _, errors = self.InferAndCheck("""
      def foo(self, x, y, z):
        # type: (int, str) -> None
        y = x
        return x
    """, filename="test.py")
    self.assertErrorLogContains(
        errors, (r"test\.py.*line 3.*invalid-function-type-comment"
                 r".*Expected 3 args, 2 given"))

  def testFunctionMissingArgs(self):
    _, errors = self.InferAndCheck("""
      def foo(x):
        # type: () -> int
        return x
    """, filename="test.py")
    self.assertErrorLogContains(
        errors, r"test\.py.*line 3.*invalid-function-type-comment")

  def testInvalidFunctionTypeComment(self):
    _, errors = self.InferAndCheck("""
      def foo(x):
        # type: blah blah blah
        return x
    """, filename="test.py")
    self.assertErrorLogContains(
        errors,
        r"test\.py.*line 3.*blah blah blah.*invalid-function-type-comment")

  def testInvalidFunctionArgs(self):
    _, errors = self.InferAndCheck("""
      def foo(x):
        # type: (abc def) -> int
        return x
    """, filename="test.py")
    self.assertErrorLogContains(
        errors,
        (r"test\.py.*line 3.*abc def.*invalid-function-type-comment"
         r".*unexpected EOF"))


class FunctionCommentWithAnnotationsTest(test_inference.InferenceTest):
  """Tests for type comments that require annotations."""

  def testFunctionTypeCommentPlusAnnotations(self):
    _, errors = self.InferAndCheck("""
      from __future__ import google_type_annotations
      def foo(x: int) -> float:
        # type: (int) -> float
        return x
    """, filename="test.py")
    self.assertErrorLogContains(
        errors, r"test\.py.*line 4.*redundant-function-type-comment")


class AssignmentCommentTest(test_inference.InferenceTest):
  """Tests for type comments applied to assignments."""

  def testClassAttributeComment(self):
    ty = self.Infer("""
      class Foo(object):
        s = None  # type: str
    """, deep=True, filename="test.py")
    self.assertTypesMatchPytd(ty, """
      class Foo(object):
        s = ...  # type: str
    """)

  def testInstanceAttributeComment(self):
    ty = self.Infer("""
      class Foo(object):
        def __init__(self):
          self.s = None  # type: str
    """, deep=True, filename="test.py")
    self.assertTypesMatchPytd(ty, """
      class Foo(object):
        s = ...  # type: str
    """)

  def testGlobalComment(self):
    ty = self.Infer("""
      X = None  # type: str
    """, deep=True, filename="test.py")
    self.assertTypesMatchPytd(ty, """
      X = ...  # type: str
    """)

  def testLocalComment(self):
    ty = self.Infer("""
      X = None

      def foo():
        x = X  # type: str
        return x
    """, deep=True, filename="test.py")
    self.assertTypesMatchPytd(ty, """
      X = ...  # type: None
      def foo() -> str: ...
    """)

  def testBadComment(self):
    _, errors = self.InferAndCheck("""
      X = None  # type: abc def
    """, deep=True, filename="test.py")
    self.assertErrorLogContains(
        errors,
        (r"test\.py.*line 2.*abc def.*invalid-type-comment"
         r".*unexpected EOF"))

  def testConversionError(self):
    _, errors = self.InferAndCheck("""
      X = None  # type: 1 if x else 2
    """, deep=True, filename="test.py")
    self.assertErrorLogContains(
        errors,
        r"test\.py.*line 2.*1 if x else 2.*invalid-type-comment")

  def testNameErrorInsideComment(self):
    _, errors = self.InferAndCheck("""
      X = None  # type: Foo
    """, deep=True, filename="test.py")
    self.assertErrorLogContains(
        errors,
        r"test\.py.*line 2.*Foo.*invalid-type-comment")

  def testTypeCommentUsesFilename(self):
    # TODO(dbaum): This test will likely become unnecessary once we warn on
    # unhandled type comments and test those warnings.

    # This is a fragile test.  It depends on the fact that builtins has an
    # assignment on line 4, thus would process the tzinfo type comment and
    # trigger a name-error if filename was ignored.
    ty = self.Infer("""
      from datetime import tzinfo
      def foo():
        x = None  # type: tzinfo
        return x
    """, deep=True, filename="test.py")
    self.assertTypesMatchPytd(ty, """
      import datetime
      from typing import Type
      tzinfo = ...  # type: Type[datetime.tzinfo]
      def foo() -> datetime.tzinfo: ...
    """)

  def testWarnOnIgnoredTypeComment(self):
    _, errors = self.InferAndCheck("""
      X = []
      X[0] = None  # type: str
      # type: int
    """, deep=True, filename="test.py")
    self.assertErrorLogContains(
        errors,
        r"test\.py.*line 3.*str.*ignored-type-comment")
    self.assertErrorLogContains(
        errors,
        r"test\.py.*line 4.*int.*ignored-type-comment")


if __name__ == "__main__":
  test_inference.main()
