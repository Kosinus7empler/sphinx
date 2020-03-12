"""
    test_domain_c
    ~~~~~~~~~~~~~

    Tests the C Domain

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

import pytest

from docutils import nodes
import sphinx.domains.c as cDomain
from sphinx import addnodes
from sphinx.addnodes import (
    desc, desc_addname, desc_annotation, desc_content, desc_name, desc_optional,
    desc_parameter, desc_parameterlist, desc_returns, desc_signature, desc_type,
    pending_xref
)
from sphinx.domains.c import DefinitionParser, DefinitionError
from sphinx.domains.c import _max_id, _id_prefix, Symbol
from sphinx.testing import restructuredtext
from sphinx.testing.util import assert_node
from sphinx.util import docutils


def parse(name, string):
    parser = DefinitionParser(string, None)
    parser.allowFallbackExpressionParsing = False
    ast = parser.parse_declaration(name, name)
    parser.assert_end()
    return ast


def check(name, input, idDict, output=None):
    # first a simple check of the AST
    if output is None:
        output = input
    ast = parse(name, input)
    res = str(ast)
    if res != output:
        print("")
        print("Input:    ", input)
        print("Result:   ", res)
        print("Expected: ", output)
        raise DefinitionError("")
    rootSymbol = Symbol(None, None, None, None)
    symbol = rootSymbol.add_declaration(ast, docname="TestDoc")
    parentNode = addnodes.desc()
    signode = addnodes.desc_signature(input, '')
    parentNode += signode
    ast.describe_signature(signode, 'lastIsName', symbol, options={})

    idExpected = [None]
    for i in range(1, _max_id + 1):
        if i in idDict:
            idExpected.append(idDict[i])
        else:
            idExpected.append(idExpected[i - 1])
    idActual = [None]
    for i in range(1, _max_id + 1):
        #try:
        id = ast.get_id(version=i)
        assert id is not None
        idActual.append(id[len(_id_prefix[i]):])
        #except NoOldIdError:
        #    idActual.append(None)

    res = [True]
    for i in range(1, _max_id + 1):
        res.append(idExpected[i] == idActual[i])

    if not all(res):
        print("input:    %s" % input.rjust(20))
        for i in range(1, _max_id + 1):
            if res[i]:
                continue
            print("Error in id version %d." % i)
            print("result:   %s" % idActual[i])
            print("expected: %s" % idExpected[i])
        #print(rootSymbol.dump(0))
        raise DefinitionError("")


def test_expressions():
    return  # TODO
    def exprCheck(expr, id, id4=None):
        ids = 'IE1CIA%s_1aE'
        idDict = {2: ids % expr, 3: ids % id}
        if id4 is not None:
            idDict[4] = ids % id4
        check('class', 'template<> C<a[%s]>' % expr, idDict)
    # primary
    exprCheck('nullptr', 'LDnE')
    exprCheck('true', 'L1E')
    exprCheck('false', 'L0E')
    ints = ['5', '0', '075', '0x0123456789ABCDEF', '0XF', '0b1', '0B1']
    unsignedSuffix = ['', 'u', 'U']
    longSuffix = ['', 'l', 'L', 'll', 'LL']
    for i in ints:
        for u in unsignedSuffix:
            for l in longSuffix:
                expr = i + u + l
                exprCheck(expr, 'L' + expr + 'E')
                expr = i + l + u
                exprCheck(expr, 'L' + expr + 'E')
    for suffix in ['', 'f', 'F', 'l', 'L']:
        for e in [
                '5e42', '5e+42', '5e-42',
                '5.', '5.e42', '5.e+42', '5.e-42',
                '.5', '.5e42', '.5e+42', '.5e-42',
                '5.0', '5.0e42', '5.0e+42', '5.0e-42']:
            expr = e + suffix
            exprCheck(expr, 'L' + expr + 'E')
        for e in [
                'ApF', 'Ap+F', 'Ap-F',
                'A.', 'A.pF', 'A.p+F', 'A.p-F',
                '.A', '.ApF', '.Ap+F', '.Ap-F',
                'A.B', 'A.BpF', 'A.Bp+F', 'A.Bp-F']:
            expr = "0x" + e + suffix
            exprCheck(expr, 'L' + expr + 'E')
    exprCheck('"abc\\"cba"', 'LA8_KcE')  # string
    exprCheck('this', 'fpT')
    # character literals
    for p, t in [('', 'c'), ('u8', 'c'), ('u', 'Ds'), ('U', 'Di'), ('L', 'w')]:
        exprCheck(p + "'a'", t + "97")
        exprCheck(p + "'\\n'", t + "10")
        exprCheck(p + "'\\012'", t + "10")
        exprCheck(p + "'\\0'", t + "0")
        exprCheck(p + "'\\x0a'", t + "10")
        exprCheck(p + "'\\x0A'", t + "10")
        exprCheck(p + "'\\u0a42'", t + "2626")
        exprCheck(p + "'\\u0A42'", t + "2626")
        exprCheck(p + "'\\U0001f34c'", t + "127820")
        exprCheck(p + "'\\U0001F34C'", t + "127820")

    # TODO: user-defined lit
    exprCheck('(... + Ns)', '(... + Ns)', id4='flpl2Ns')
    exprCheck('(Ns + ...)', '(Ns + ...)', id4='frpl2Ns')
    exprCheck('(Ns + ... + 0)', '(Ns + ... + 0)', id4='fLpl2NsL0E')
    exprCheck('(5)', 'L5E')
    exprCheck('C', '1C')
    # postfix
    exprCheck('A(2)', 'cl1AL2EE')
    exprCheck('A[2]', 'ix1AL2E')
    exprCheck('a.b.c', 'dtdt1a1b1c')
    exprCheck('a->b->c', 'ptpt1a1b1c')
    exprCheck('i++', 'pp1i')
    exprCheck('i--', 'mm1i')
    exprCheck('dynamic_cast<T&>(i)++', 'ppdcR1T1i')
    exprCheck('static_cast<T&>(i)++', 'ppscR1T1i')
    exprCheck('reinterpret_cast<T&>(i)++', 'pprcR1T1i')
    exprCheck('const_cast<T&>(i)++', 'ppccR1T1i')
    exprCheck('typeid(T).name', 'dtti1T4name')
    exprCheck('typeid(a + b).name', 'dttepl1a1b4name')
    # unary
    exprCheck('++5', 'pp_L5E')
    exprCheck('--5', 'mm_L5E')
    exprCheck('*5', 'deL5E')
    exprCheck('&5', 'adL5E')
    exprCheck('+5', 'psL5E')
    exprCheck('-5', 'ngL5E')
    exprCheck('!5', 'ntL5E')
    exprCheck('~5', 'coL5E')
    exprCheck('sizeof...(a)', 'sZ1a')
    exprCheck('sizeof(T)', 'st1T')
    exprCheck('sizeof -42', 'szngL42E')
    exprCheck('alignof(T)', 'at1T')
    exprCheck('noexcept(-42)', 'nxngL42E')
    # new-expression
    exprCheck('new int', 'nw_iE')
    exprCheck('new volatile int', 'nw_ViE')
    exprCheck('new int[42]', 'nw_AL42E_iE')
    exprCheck('new int()', 'nw_ipiE')
    exprCheck('new int(5, 42)', 'nw_ipiL5EL42EE')
    exprCheck('::new int', 'nw_iE')
    exprCheck('new int{}', 'nw_iilE')
    exprCheck('new int{5, 42}', 'nw_iilL5EL42EE')
    # delete-expression
    exprCheck('delete p', 'dl1p')
    exprCheck('delete [] p', 'da1p')
    exprCheck('::delete p', 'dl1p')
    exprCheck('::delete [] p', 'da1p')
    # cast
    exprCheck('(int)2', 'cviL2E')
    # binary op
    exprCheck('5 || 42', 'ooL5EL42E')
    exprCheck('5 && 42', 'aaL5EL42E')
    exprCheck('5 | 42', 'orL5EL42E')
    exprCheck('5 ^ 42', 'eoL5EL42E')
    exprCheck('5 & 42', 'anL5EL42E')
    # ['==', '!=']
    exprCheck('5 == 42', 'eqL5EL42E')
    exprCheck('5 != 42', 'neL5EL42E')
    # ['<=', '>=', '<', '>']
    exprCheck('5 <= 42', 'leL5EL42E')
    exprCheck('5 >= 42', 'geL5EL42E')
    exprCheck('5 < 42', 'ltL5EL42E')
    exprCheck('5 > 42', 'gtL5EL42E')
    # ['<<', '>>']
    exprCheck('5 << 42', 'lsL5EL42E')
    exprCheck('5 >> 42', 'rsL5EL42E')
    # ['+', '-']
    exprCheck('5 + 42', 'plL5EL42E')
    exprCheck('5 - 42', 'miL5EL42E')
    # ['*', '/', '%']
    exprCheck('5 * 42', 'mlL5EL42E')
    exprCheck('5 / 42', 'dvL5EL42E')
    exprCheck('5 % 42', 'rmL5EL42E')
    # ['.*', '->*']
    exprCheck('5 .* 42', 'dsL5EL42E')
    exprCheck('5 ->* 42', 'pmL5EL42E')
    # conditional
    # TODO
    # assignment
    exprCheck('a = 5', 'aS1aL5E')
    exprCheck('a *= 5', 'mL1aL5E')
    exprCheck('a /= 5', 'dV1aL5E')
    exprCheck('a %= 5', 'rM1aL5E')
    exprCheck('a += 5', 'pL1aL5E')
    exprCheck('a -= 5', 'mI1aL5E')
    exprCheck('a >>= 5', 'rS1aL5E')
    exprCheck('a <<= 5', 'lS1aL5E')
    exprCheck('a &= 5', 'aN1aL5E')
    exprCheck('a ^= 5', 'eO1aL5E')
    exprCheck('a |= 5', 'oR1aL5E')

    # Additional tests
    # a < expression that starts with something that could be a template
    exprCheck('A < 42', 'lt1AL42E')
    check('function', 'template<> void f(A<B, 2> &v)',
          {2: "IE1fR1AI1BX2EE", 3: "IE1fR1AI1BXL2EEE", 4: "IE1fvR1AI1BXL2EEE"})
    exprCheck('A<1>::value', 'N1AIXL1EEE5valueE')
    check('class', "template<int T = 42> A", {2: "I_iE1A"})
    check('enumerator', 'A = std::numeric_limits<unsigned long>::max()', {2: "1A"})

    exprCheck('operator()()', 'clclE')
    exprCheck('operator()<int>()', 'clclIiEE')

    # pack expansion
    exprCheck('a(b(c, 1 + d...)..., e(f..., g))', 'cl1aspcl1b1cspplL1E1dEcl1esp1f1gEE')


def test_type_definitions():
    check('type', "T", {1: "T"})
    check('type', "struct T", {1: 'T'})
    check('type', "enum T", {1: 'T'})
    check('type', "union T", {1: 'T'})

    check('type', "bool *b", {1: 'b'})
    check('type', "bool *const b", {1: 'b'})
    check('type', "bool *volatile const b", {1: 'b'})
    check('type', "bool *volatile const b", {1: 'b'})
    check('type', "bool *volatile const *b", {1: 'b'})
    check('type', "bool b[]", {1: 'b'})
    check('type', "long long int foo", {1: 'foo'})
    # test decl specs on right
    check('type', "bool const b", {1: 'b'})

    # from breathe#267 (named function parameters for function pointers
    check('type', 'void (*gpio_callback_t)(struct device *port, uint32_t pin)',
          {1: 'gpio_callback_t'})


def test_macro_definitions():
    check('macro', 'M', {1: 'M'})
    check('macro', 'M()', {1: 'M'})
    check('macro', 'M(arg)', {1: 'M'})
    check('macro', 'M(arg1, arg2)', {1: 'M'})
    check('macro', 'M(arg1, arg2, arg3)', {1: 'M'})
    check('macro', 'M(...)', {1: 'M'})
    check('macro', 'M(arg, ...)', {1: 'M'})
    check('macro', 'M(arg1, arg2, ...)', {1: 'M'})
    check('macro', 'M(arg1, arg2, arg3, ...)', {1: 'M'})


def test_member_definitions():
    check('member', 'void a', {1: 'a'})
    check('member', '_Bool a', {1: 'a'})
    check('member', 'bool a', {1: 'a'})
    check('member', 'char a', {1: 'a'})
    check('member', 'int a', {1: 'a'})
    check('member', 'float a', {1: 'a'})
    check('member', 'double a', {1: 'a'})

    check('member', 'unsigned long a', {1: 'a'})

    check('member', 'int .a', {1: 'a'})

    check('member', 'int *a', {1: 'a'})
    check('member', 'int **a', {1: 'a'})
    check('member', 'const int a', {1: 'a'})
    check('member', 'volatile int a', {1: 'a'})
    check('member', 'restrict int a', {1: 'a'})
    check('member', 'volatile const int a', {1: 'a'})
    check('member', 'restrict const int a', {1: 'a'})
    check('member', 'restrict volatile int a', {1: 'a'})
    check('member', 'restrict volatile const int a', {1: 'a'})

    check('member', 'T t', {1: 't'})
    check('member', 'struct T t', {1: 't'})
    check('member', 'enum T t', {1: 't'})
    check('member', 'union T t', {1: 't'})

    check('member', 'int a[]', {1: 'a'})

    check('member', 'int (*p)[]', {1: 'p'})

    check('member', 'int a[42]', {1: 'a'})
    check('member', 'int a = 42', {1: 'a'})
    check('member', 'T a = {}', {1: 'a'})
    check('member', 'T a = {1}', {1: 'a'})
    check('member', 'T a = {1, 2}', {1: 'a'})
    check('member', 'T a = {1, 2, 3}', {1: 'a'})

    # test from issue #1539
    check('member', 'CK_UTF8CHAR model[16]', {1: 'model'})

    check('member', 'auto int a', {1: 'a'})
    check('member', 'register int a', {1: 'a'})
    check('member', 'extern int a', {1: 'a'})
    check('member', 'static int a', {1: 'a'})

    check('member', 'thread_local int a', {1: 'a'})
    check('member', '_Thread_local int a', {1: 'a'})
    check('member', 'extern thread_local int a', {1: 'a'})
    check('member', 'thread_local extern int a', {1: 'a'},
          'extern thread_local int a')
    check('member', 'static thread_local int a', {1: 'a'})
    check('member', 'thread_local static int a', {1: 'a'},
          'static thread_local int a')

    check('member', 'int b : 3', {1: 'b'})


def test_function_definitions():
    check('function', 'void f()', {1: 'f'})
    check('function', 'void f(int)', {1: 'f'})
    check('function', 'void f(int i)', {1: 'f'})
    check('function', 'void f(int i, int j)', {1: 'f'})
    check('function', 'void f(...)', {1: 'f'})
    check('function', 'void f(int i, ...)', {1: 'f'})
    check('function', 'void f(struct T)', {1: 'f'})
    check('function', 'void f(struct T t)', {1: 'f'})
    check('function', 'void f(union T)', {1: 'f'})
    check('function', 'void f(union T t)', {1: 'f'})
    check('function', 'void f(enum T)', {1: 'f'})
    check('function', 'void f(enum T t)', {1: 'f'})

    # test from issue #1539
    check('function', 'void f(A x[])', {1: 'f'})

    # test from issue #2377
    check('function', 'void (*signal(int sig, void (*func)(int)))(int)', {1: 'signal'})

    check('function', 'extern void f()', {1: 'f'})
    check('function', 'static void f()', {1: 'f'})
    check('function', 'inline void f()', {1: 'f'})

    # tests derived from issue #1753 (skip to keep sanity)
    check('function', "void f(float *q(double))", {1: 'f'})
    check('function', "void f(float *(*q)(double))", {1: 'f'})
    check('function', "void f(float (*q)(double))", {1: 'f'})
    check('function', "int (*f(double d))(float)", {1: 'f'})
    check('function', "int (*f(bool b))[5]", {1: 'f'})
    check('function', "void f(int *const p)", {1: 'f'})
    check('function', "void f(int *volatile const p)", {1: 'f'})

    # from breathe#223
    check('function', 'void f(struct E e)', {1: 'f'})
    check('function', 'void f(enum E e)', {1: 'f'})
    check('function', 'void f(union E e)', {1: 'f'})


def test_union_definitions():
    return  # TODO
    check('union', 'A', {2: "1A"})


def test_enum_definitions():
    return  # TODO
    check('enum', 'A', {2: "1A"})
    check('enum', 'A : std::underlying_type<B>::type', {2: "1A"})
    check('enum', 'A : unsigned int', {2: "1A"})
    check('enum', 'public A', {2: "1A"}, output='A')
    check('enum', 'private A', {2: "1A"})

    check('enumerator', 'A', {2: "1A"})
    check('enumerator', 'A = std::numeric_limits<unsigned long>::max()', {2: "1A"})


def test_anon_definitions():
    return  # TODO
    check('class', '@a', {3: "Ut1_a"})
    check('union', '@a', {3: "Ut1_a"})
    check('enum', '@a', {3: "Ut1_a"})
    check('class', '@1', {3: "Ut1_1"})
    check('class', '@a::A', {3: "NUt1_a1AE"})


def test_initializers():
    return  # TODO
    idsMember = {1: 'v__T', 2: '1v'}
    idsFunction = {1: 'f__T', 2: '1f1T'}
    idsTemplate = {2: 'I_1TE1fv', 4: 'I_1TE1fvv'}
    # no init
    check('member', 'T v', idsMember)
    check('function', 'void f(T v)', idsFunction)
    check('function', 'template<T v> void f()', idsTemplate)
    # with '=', assignment-expression
    check('member', 'T v = 42', idsMember)
    check('function', 'void f(T v = 42)', idsFunction)
    check('function', 'template<T v = 42> void f()', idsTemplate)
    # with '=', braced-init
    check('member', 'T v = {}', idsMember)
    check('function', 'void f(T v = {})', idsFunction)
    check('function', 'template<T v = {}> void f()', idsTemplate)
    check('member', 'T v = {42, 42, 42}', idsMember)
    check('function', 'void f(T v = {42, 42, 42})', idsFunction)
    check('function', 'template<T v = {42, 42, 42}> void f()', idsTemplate)
    check('member', 'T v = {42, 42, 42,}', idsMember)
    check('function', 'void f(T v = {42, 42, 42,})', idsFunction)
    check('function', 'template<T v = {42, 42, 42,}> void f()', idsTemplate)
    check('member', 'T v = {42, 42, args...}', idsMember)
    check('function', 'void f(T v = {42, 42, args...})', idsFunction)
    check('function', 'template<T v = {42, 42, args...}> void f()', idsTemplate)
    # without '=', braced-init
    check('member', 'T v{}', idsMember)
    check('member', 'T v{42, 42, 42}', idsMember)
    check('member', 'T v{42, 42, 42,}', idsMember)
    check('member', 'T v{42, 42, args...}', idsMember)
    # other
    check('member', 'T v = T{}', idsMember)


def test_attributes():
    return  # TODO
    # style: C++
    check('member', '[[]] int f', {1: 'f__i', 2: '1f'})
    check('member', '[ [ ] ] int f', {1: 'f__i', 2: '1f'},
          # this will fail when the proper grammar is implemented
          output='[[ ]] int f')
    check('member', '[[a]] int f', {1: 'f__i', 2: '1f'})
    # style: GNU
    check('member', '__attribute__(()) int f', {1: 'f__i', 2: '1f'})
    check('member', '__attribute__((a)) int f', {1: 'f__i', 2: '1f'})
    check('member', '__attribute__((a, b)) int f', {1: 'f__i', 2: '1f'})
    # style: user-defined id
    check('member', 'id_attr int f', {1: 'f__i', 2: '1f'})
    # style: user-defined paren
    check('member', 'paren_attr() int f', {1: 'f__i', 2: '1f'})
    check('member', 'paren_attr(a) int f', {1: 'f__i', 2: '1f'})
    check('member', 'paren_attr("") int f', {1: 'f__i', 2: '1f'})
    check('member', 'paren_attr(()[{}][]{}) int f', {1: 'f__i', 2: '1f'})
    with pytest.raises(DefinitionError):
        parse('member', 'paren_attr(() int f')
    with pytest.raises(DefinitionError):
        parse('member', 'paren_attr([) int f')
    with pytest.raises(DefinitionError):
        parse('member', 'paren_attr({) int f')
    with pytest.raises(DefinitionError):
        parse('member', 'paren_attr([)]) int f')
    with pytest.raises(DefinitionError):
        parse('member', 'paren_attr((])) int f')
    with pytest.raises(DefinitionError):
        parse('member', 'paren_attr({]}) int f')

    # position: decl specs
    check('function', 'static inline __attribute__(()) void f()',
          {1: 'f', 2: '1fv'},
          output='__attribute__(()) static inline void f()')
    check('function', '[[attr1]] [[attr2]] void f()',
          {1: 'f', 2: '1fv'},
          output='[[attr1]] [[attr2]] void f()')
    # position: declarator
    check('member', 'int *[[attr]] i', {1: 'i__iP', 2: '1i'})
    check('member', 'int *const [[attr]] volatile i', {1: 'i__iPVC', 2: '1i'},
          output='int *[[attr]] volatile const i')
    check('member', 'int &[[attr]] i', {1: 'i__iR', 2: '1i'})
    check('member', 'int *[[attr]] *i', {1: 'i__iPP', 2: '1i'})


def test_xref_parsing():
    return  # TODO
    def check(target):
        class Config:
            cpp_id_attributes = ["id_attr"]
            cpp_paren_attributes = ["paren_attr"]
        parser = DefinitionParser(target, None, Config())
        ast, isShorthand = parser.parse_xref_object()
        parser.assert_end()
    check('f')
    check('f()')
    check('void f()')
    check('T f()')


# def test_print():
#     # used for getting all the ids out for checking
#     for a in ids:
#         print(a)
#     raise DefinitionError("")


def filter_warnings(warning, file):
    lines = warning.getvalue().split("\n");
    res = [l for l in lines if "domain-c" in l and "{}.rst".format(file) in l and
           "WARNING: document isn't included in any toctree" not in l]
    print("Filtered warnings for file '{}':".format(file))
    for w in res:
        print(w)
    return res


@pytest.mark.sphinx(testroot='domain-c', confoverrides={'nitpicky': True})
def test_build_domain_c(app, status, warning):
    app.builder.build_all()
    ws = filter_warnings(warning, "index")
    assert len(ws) == 0


def test_cfunction(app):
    text = (".. c:function:: PyObject* "
            "PyType_GenericAlloc(PyTypeObject *type, Py_ssize_t nitems)")
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree[1], addnodes.desc, desctype="function",
                domain="c", objtype="function", noindex=False)

    domain = app.env.get_domain('c')
    entry = domain.objects.get('PyType_GenericAlloc')
    assert entry == ('index', 'c.PyType_GenericAlloc', 'function')


def test_cmember(app):
    text = ".. c:member:: PyObject* PyTypeObject.tp_bases"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree[1], addnodes.desc, desctype="member",
                domain="c", objtype="member", noindex=False)

    domain = app.env.get_domain('c')
    entry = domain.objects.get('PyTypeObject.tp_bases')
    assert entry == ('index', 'c.PyTypeObject.tp_bases', 'member')


def test_cvar(app):
    text = ".. c:var:: PyObject* PyClass_Type"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree[1], addnodes.desc, desctype="var",
                domain="c", objtype="var", noindex=False)

    domain = app.env.get_domain('c')
    entry = domain.objects.get('PyClass_Type')
    assert entry == ('index', 'c.PyClass_Type', 'var')
