"""Test list, dict, etc."""

from pytype import utils
from pytype.pytd import pytd
from pytype.tests import test_inference


class ContainerTest(test_inference.InferenceTest):
  """Tests for containers."""

  def testTuplePassThrough(self):
    ty = self.Infer("""
      def f(x):
        return x
      f((3, "str"))
    """, deep=False, solve_unknowns=False, show_library_calls=True)
    self.assertHasOnlySignatures(
        ty.Lookup("f"),
        ((pytd.TupleType(self.tuple, (self.int, self.str)),),
         pytd.TupleType(self.tuple, (self.int, self.str))))

  def testTuple(self):
    ty = self.Infer("""
      def f(x):
        return x[0]
      f((3, "str"))
    """, deep=False, solve_unknowns=False, show_library_calls=True)
    self.assertHasOnlySignatures(
        ty.Lookup("f"),
        ((pytd.TupleType(self.tuple, (self.int, self.str)),),
         self.int))

  def testTupleSwap(self):
    ty = self.Infer("""
      def f(x):
        return (x[1], x[0])
      f((3, "str"))
    """, deep=False, solve_unknowns=False, show_library_calls=True)
    self.assertHasOnlySignatures(
        ty.Lookup("f"),
        ((pytd.TupleType(self.tuple, (self.int, self.str)),),
         pytd.TupleType(self.tuple, (self.str, self.int))))

  def testEmptyTuple(self):
    ty = self.Infer("""
      def f():
        return ()
      f()
    """, deep=False, solve_unknowns=False, show_library_calls=True)
    self.assertHasOnlySignatures(
        ty.Lookup("f"),
        ((), pytd.HomogeneousContainerType(self.tuple, (pytd.NothingType(),))))

  def testSetsSanity(self):
    ty = self.Infer("""
      def f():
        x = set([1])
        x.add(10)
        return x
      f()
    """, deep=False, solve_unknowns=False, show_library_calls=True)
    self.assertHasOnlySignatures(
        ty.Lookup("f"),
        ((), pytd.HomogeneousContainerType(self.set, (self.int,))))

  def testSetsAdd(self):
    ty = self.Infer("""
      def f():
        x = set([])
        x.add(1)
        x.add(10)
        return x
      f()
    """, deep=False, solve_unknowns=False, show_library_calls=True)
    self.assertHasOnlySignatures(
        ty.Lookup("f"),
        ((), pytd.HomogeneousContainerType(self.set, (self.int,))))

  def testSets(self):
    ty = self.Infer("""
      def f():
        x = set([1,2,3])
        if x:
          x = x | set()
          y = x
          return x
        else:
          x.add(10)
          return x
      f()
    """, deep=False, solve_unknowns=False, show_library_calls=True)
    self.assertHasOnlySignatures(
        ty.Lookup("f"),
        ((), pytd.HomogeneousContainerType(self.set, (self.int,))))

  def testListLiteral(self):
    ty = self.Infer("""
      def f():
        return [1, 2, 3]
      f()
    """, deep=False, solve_unknowns=False, show_library_calls=True)
    self.assertHasOnlySignatures(
        ty.Lookup("f"),
        ((), pytd.HomogeneousContainerType(self.list, (self.int,))))

  def testListAppend(self):
    ty = self.Infer("""
      def f():
        x = []
        x.append(1)
        x.append(2)
        x.append(3)
        return x
      f()
    """, deep=False, solve_unknowns=False, show_library_calls=True)
    self.assertHasOnlySignatures(
        ty.Lookup("f"),
        ((), pytd.HomogeneousContainerType(self.list, (self.int,))))

  def testListConcat(self):
    ty = self.Infer("""
      def f():
        x = []
        x.append(1)
        x.append(2)
        x.append(3)
        return [0] + x
      f()
    """, deep=False, solve_unknowns=False, show_library_calls=True)
    self.assertHasOnlySignatures(
        ty.Lookup("f"),
        ((), pytd.HomogeneousContainerType(self.list, (self.int,))))

  def testListConcatMultiType(self):
    ty = self.Infer("""
      def f():
        x = []
        x.append(1)
        x.append("str")
        return x + [1.3] + x
      f()
    """, deep=False, solve_unknowns=False, show_library_calls=True)
    self.assertHasOnlySignatures(
        ty.Lookup("f"),
        ((),
         pytd.HomogeneousContainerType(
             self.list,
             (pytd.UnionType((self.int, self.float, self.str)),))))

  def testUnionIntoTypeParam(self):
    ty = self.Infer("""
      y = __any_object__
      if y:
        x = 3
      else:
        x = 3.1
      l = []
      l.append(x)
    """, deep=False, solve_unknowns=False)
    self.assertTypesMatchPytd(ty, """
      from typing import List
      x = ...  # type: int or float
      y = ...  # type: ?
      l = ...  # type: List[int or float, ...]
    """)

  def testListConcatUnlike(self):
    ty = self.Infer("""
      def f():
        x = []
        x.append(1)
        x.append(2)
        x.append(3)
        return ["str"] + x
      f()
    """, deep=False, solve_unknowns=False, show_library_calls=True)
    self.assertHasOnlySignatures(
        ty.Lookup("f"),
        ((), pytd.HomogeneousContainerType(self.list, (self.intorstr,))))

  def testAnyObject(self):
    ty = self.Infer("""
      def f():
        return __any_object__
      def g():
        return __any_object__()
      def h():
        return __any_object__("name")
      f(); g(); h()
    """, deep=False, solve_unknowns=False)
    self.assertHasOnlySignatures(ty.Lookup("f"), ((), self.anything))
    self.assertHasOnlySignatures(ty.Lookup("g"), ((), self.anything))
    self.assertHasOnlySignatures(ty.Lookup("h"), ((), self.anything))

  def testDictLiteral(self):
    ty = self.Infer("""
      def f():
        return {"test": 1, "arg": 42}
      f()
    """, deep=False, solve_unknowns=False, show_library_calls=True)
    self.assertHasOnlySignatures(
        ty.Lookup("f"),
        ((), self.str_int_dict))

  def testDictEmptyConstructor(self):
    ty = self.Infer("""
      def f():
        return dict()
      f()
    """, deep=False, solve_unknowns=False, show_library_calls=True)
    self.assertHasOnlySignatures(
        ty.Lookup("f"),
        ((), self.nothing_nothing_dict))

  def testDictConstructor(self):
    ty = self.Infer("""
      def f():
        return dict([(1, 2), (3, 4)])
      f()
    """, deep=False, solve_unknowns=False, show_library_calls=True)
    self.assertHasOnlySignatures(
        ty.Lookup("f"),
        ((), self.int_int_dict))

  def testDictConstructor2(self):
    ty = self.Infer("""
      def f():
        return dict([(1, "bar"), (2, "foo")])
      f()
    """, deep=False, solve_unknowns=False, show_library_calls=True)
    self.assertHasOnlySignatures(
        ty.Lookup("f"),
        ((), self.int_str_dict))

  def testDictUpdate(self):
    ty = self.Infer("""
      def f():
        d = {}
        d["test"] = 1
        d["arg"] = 42
        return d
      f()
    """, deep=False, solve_unknowns=False, show_library_calls=True)
    self.assertHasOnlySignatures(
        ty.Lookup("f"),
        ((), self.str_int_dict))

  def testForIter(self):
    ty = self.Infer("""
      class A(object):
        def __init__(self):
          self.parent = "foo"

      def set_parent(l):
        for e in l:
          e.parent = 1

      def f():
        a = A()
        b = A()
        set_parent([a, b])
        return a.parent

      f()
    """, deep=False, solve_unknowns=False, show_library_calls=True)
    self.assertHasOnlySignatures(ty.Lookup("f"),
                                 ((),
                                  self.intorstr))

  def testOverloading(self):
    ty = self.Infer("""
      class Base(object):
        parent = None
        children = ()
        def bar(self, new):
            for ch in self.parent.children:
                ch.foobar = 3

      class Node(Base):
        def __init__(self, children):
          self.children = list(children)
          for ch in self.children:
            ch.parent = self

      class Leaf(Base):
        def __init__(self):
          pass

      def f():
        l1 = Leaf()
        l2 = Leaf()
        n1 = Node([l1, l2])
        l2.bar(None)
        return l2.foobar

      f()
    """, deep=False, solve_unknowns=False, show_library_calls=True)
    self.assertHasOnlySignatures(ty.Lookup("f"),
                                 ((),
                                  self.int))

  def testClassAttr(self):
    ty = self.Infer("""
      class Node(object):
        children = ()

      def f():
        n1 = Node()
        n1.children = [n1]
        for ch in n1.children:
          ch.foobar = 3
        return n1.foobar

      f()
    """, deep=False, solve_unknowns=False, show_library_calls=True)
    self.assertHasOnlySignatures(ty.Lookup("f"),
                                 ((),
                                  self.int))

  def testHeterogeneous(self):
    ty = self.Infer("""
      def f():
        x = list()
        x.append(3)
        x.append("str")
        return x[0]
      f()
    """, deep=False, solve_unknowns=False, show_library_calls=True)
    self.assertHasOnlySignatures(ty.Lookup("f"),
                                 ((),
                                  self.intorstr))

  def testListComprehension(self):
    # uses byte_LIST_APPEND
    ty = self.Infer("""
      def f():
        return [i for i in (1,2,3)]
      f()
    """, deep=False, solve_unknowns=False, show_library_calls=True)
    self.assertHasOnlySignatures(ty.Lookup("f"),
                                 ((),
                                  self.int_list))

  def testSetComprehension(self):
    # uses byte_SET_ADD
    ty = self.Infer("""
      def f():
        return {i for i in [1,2,3]}
      f()
    """, deep=False, solve_unknowns=False, show_library_calls=True)
    self.assertHasOnlySignatures(ty.Lookup("f"),
                                 ((),
                                  self.int_set))

  def testDictComprehension(self):
    # uses byte_MAP_ADD
    ty = self.Infer("""
      def f():
        return {i: i for i in xrange(3)}
      f()
    """, deep=False, solve_unknowns=False, show_library_calls=True)
    self.assertHasOnlySignatures(ty.Lookup("f"),
                                 ((),
                                  self.int_int_dict))

  def testLeakingType(self):
    ty = self.Infer("""
      import sys
      a = [str(ty) for ty in (float, int, bool)[:len(sys.argv)]]
    """, deep=True, solve_unknowns=False)
    self.assertTypesMatchPytd(ty, """
      from typing import List, Type
      sys = ...  # type: module
      a = ...  # type: List[str, ...]
      ty = ...  # type: Type[float or int]
    """)

  def testEmptyOrString(self):
    ty = self.Infer("""
      d = dict()
      d["a"] = "queen"
      entry = d["a"]
      open('%s' % entry, 'w')
    """, deep=False, solve_unknowns=False)
    self.assertTypesMatchPytd(ty, """
      from typing import Dict
      d = ...  # type: Dict[str, str]
      entry = ...  # type: str
    """)

  def testDictInit(self):
    ty = self.Infer("""
      def f():
        return dict([])
    """, deep=True, solve_unknowns=False)
    self.assertTypesMatchPytd(ty, """
      from typing import Dict
      def f() -> Dict[nothing, nothing]
    """)

  def testDictTupleInit(self):
    ty = self.Infer("""
      def f():
        return dict([("foo", "foo")])
    """, deep=True, solve_unknowns=False)
    self.assertTypesMatchPytd(ty, """
      from typing import Dict
      def f() -> Dict[str, str]
    """)

  def testEmptyTupleAsArg(self):
    ty = self.Infer("""
      def f(x):
        if x:
          return isinstance(1, ())
        else:
          return 3j
    """, deep=True, solve_unknowns=False)
    self.assertTypesMatchPytd(ty, """
      def f(x) -> bool or complex
    """)

  def testEmptyTypeParamAsArg(self):
    ty = self.Infer("""
      def f():
        return u"".join(map(unicode, ()))
    """, deep=True, solve_unknowns=False)
    self.assertTypesMatchPytd(ty, """
      def f() -> unicode
    """)

  def testAccessEmptyDictInIf(self):
    ty = self.Infer("""
      class Foo(object):
        pass

      def f(key):
        d = {}
        if key is None:
          e = Foo()
        else:
          e = d[key]
        e.next = None
        return e
    """, deep=True, solve_unknowns=False, report_errors=False)
    self.assertTypesMatchPytd(ty, """
      class Foo(object):
        next = ...  # type: NoneType

      def f(key) -> Foo
    """)

  def testCascade(self):
    ty = self.Infer("""
      if __any_object__:
        x = 3
      else:
        x = 3.14
      y = divmod(x, x)
    """, deep=True, solve_unknowns=False)
    self.assertTypesMatchPytd(ty, """
      from typing import Tuple
      x = ...  # type: float or int
      y = ...  # type: Tuple[float or int, float or int]
    """)

  def testMaybeAny(self):
    ty = self.Infer("""
      x = __any_object__
      x.as_integer_ratio()
      if x:
        x = 1
      y = divmod(x, 3.14)
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      from typing import Tuple
      x = ...  # type: float or int
      y = ...  # type: Tuple[complex or float, ...]
    """)

  def testIndex(self):
    ty = self.Infer("""
      def f():
        l = [__any_object__]
        if __random__:
          pos = None
        else:
          pos = 0
        l[pos] += 1
        return l
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      # The element types aren't more precise since the solver doesn't know
      # which element of the list gets modified.
      def f() -> list
    """)

  def testCircularReferenceList(self):
    ty = self.Infer("""
      def f():
        lst = []
        lst.append(lst)
        return lst
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      from typing import List
      def f() -> List[list]: ...
    """)

  def testCircularReferenceDictionary(self):
    ty = self.Infer("""
      def f():
        g = __any_object__
        s = {}
        if g:
          s1 = {}
          s[__any_object__] = s1
          s = s1
        g = s.get('$end', None)
        s['$end'] = g
        return s1
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      from typing import Dict, Union
      def f() -> Dict[str, Union[None, dict]]: ...
    """)

  def testEqOperatorOnItemFromEmptyDict(self):
    self.Infer("""
      d = {}
      d[1] == d[1]
    """)

  def testIterateEmptyList(self):
    ty = self.Infer("""
      lst1 = []
      lst2 = [x for x in lst1]
      x.some_attribute = 42
      y = x.some_attribute
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      from typing import Any, List
      lst1 = ...  # type: List[nothing]
      lst2 = ...  # type: List[nothing]
      x = ...  # type: Any
      y = ...  # type: Any
    """)

  def testIteratePyiList(self):
    with utils.Tempdir() as d:
      d.create_file("a.pyi", """
        lst1 = ...  # type: list
      """)
      ty = self.Infer("""
        import a
        lst2 = [x for x in a.lst1]
        x.some_attribute = 42
        y = x.some_attribute
      """, pythonpath=[d.path], deep=True, solve_unknowns=True)
      self.assertTypesMatchPytd(ty, """
        from typing import Any
        a = ...  # type: module
        lst2 = ...  # type: list
        x = ...  # type: Any
        y = ...  # type: Any
      """)

  def testIteratePyiListAny(self):
    with utils.Tempdir() as d:
      d.create_file("a.pyi", """
        from typing import Any, List
        lst1 = ...  # type: List[Any]
      """)
      ty = self.Infer("""
        import a
        lst2 = [x for x in a.lst1]
        x.some_attribute = 42
        y = x.some_attribute
      """, pythonpath=[d.path], deep=True, solve_unknowns=True)
      self.assertTypesMatchPytd(ty, """
        from typing import Any
        a = ...  # type: module
        lst2 = ...  # type: list
        x = ...  # type: Any
        y = ...  # type: Any
      """)

  def testIteratePyiListInt(self):
    with utils.Tempdir() as d:
      d.create_file("a.pyi", """
        from typing import List
        lst1 = ...  # type: List[int]
      """)
      ty = self.Infer("""
        import a
        lst2 = [x for x in a.lst1]
      """, pythonpath=[d.path], deep=True, solve_unknowns=True)
      self.assertTypesMatchPytd(ty, """
        from typing import List
        a = ...  # type: module
        lst2 = ...  # type: List[int]
        x = ...  # type: int
      """)

  def testIteratePyiListNothing(self):
    with utils.Tempdir() as d:
      d.create_file("a.pyi", """
        from typing import List
        lst1 = ...  # type: List[nothing]
      """)
      ty = self.Infer("""
        import a
        lst2 = [x for x in a.lst1]
        x.some_attribute = 42
        y = x.some_attribute
      """, pythonpath=[d.path], deep=True, solve_unknowns=True)
      self.assertTypesMatchPytd(ty, """
        from typing import Any, List
        a = ...  # type: module
        lst2 = ...  # type: List[nothing]
        x = ...  # type: Any
        y = ...  # type: Any
      """)

  def testDict(self):
    ty, errors = self.InferAndCheck("""
      mymap = {'a': 3.14, 'b':1}
      a = mymap['a']
      b1 = mymap['b']
      c = mymap['foobar']
      mymap[str()] = 3j
      b2 = mymap['b']
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      from typing import Dict, Union
      mymap = ...  # type: Dict[str, Union[int, float, complex]]
      a = ...  # type: float
      b1 = ...  # type: int
      c = ...  # type: Union[int, float]
      b2 = ...  # type: Union[int, float, complex]
    """)
    self.assertErrorLogIs(errors, [
        (5, "key-error", "foobar")
    ])

  def testIteratePyiListUnion(self):
    with utils.Tempdir() as d:
      d.create_file("a.pyi", """
        from typing import List, Set
        lst1 = ...  # type: List[nothing] or Set[int]
      """)
      ty = self.Infer("""
        import a
        lst2 = [x for x in a.lst1]
      """, pythonpath=[d.path], deep=True, solve_unknowns=True)
      self.assertTypesMatchPytd(ty, """
        from typing import List
        a = ...  # type: module
        lst2 = ...  # type: List[int]
        x = ...  # type: int
      """)

  def testCallEmpty(self):
    ty = self.Infer("""
      empty = []
      y = [x() for x in empty]
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      from typing import Any, List
      empty = ...  # type: List[nothing]
      y = ...  # type: list
      x = ...  # type: Any
    """)

  def testBranchEmpty(self):
    ty = self.Infer("""
      empty = []
      def f(x):
        if x:
          return 3
        else:
          return "foo"
      y = [f(x) for x in empty]
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      from typing import Any, List
      empty = ...  # type: List[nothing]
      def f(x) -> int or str
      y = ...  # type: List[int or str]
      x = ...  # type: Any
    """)

  def testConstructorEmpty(self):
    ty = self.Infer("""
      empty = []
      y = [list(x) for x in empty]
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      from typing import Any, List
      empty = ...  # type: List[nothing]
      y = ...  # type: List[list]
      x = ...  # type: Any
    """)

  def testIsInstanceEmpty(self):
    ty = self.Infer("""
      empty = []
      y = [isinstance(x, int) for x in empty]
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      from typing import Any, List
      empty = ...  # type: List[nothing]
      y = ...  # type: List[bool]
      x = ...  # type: Any
    """)

  def testInnerClassEmpty(self):
    ty = self.Infer("""
      empty = []
      def f(x):
        class X(x):
          pass
        return {X: X()}
      y = [f(x) for x in empty]
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      from typing import Any, Dict, List
      empty = ...  # type: List[nothing]
      def f(x) -> Dict[type, Any]
      y = ...  # type: List[Dict[type, Any]]
      x = ...  # type: Any
    """)

  def testEmptyList(self):
    ty = self.Infer("""
      cache = {
        "data": {},
        "lru": [],
      }
      def read(path):
        if path:
          cache["lru"].append(path)
        else:
          oldest = cache["lru"].pop(0)
          return oldest
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      from typing import Any, Dict
      cache = ...  # type: Dict[str, Dict[nothing, nothing] or list]
      def read(path) -> Any
    """)


if __name__ == "__main__":
  test_inference.main()
