# -*- coding: utf-8 -*-
"""Misc unicode tests

Made for Jython.
"""
import itertools
import random
import re
import string
import sys
import unittest
from io import StringIO
from test import support
from java.lang import StringBuilder

class UnicodeTestCase(unittest.TestCase):

    def test_simplejson_plane_bug(self):
        # a bug exposed by simplejson: unicode __add__ was always
        # forcing the basic plane
        chunker = re.compile(r'(.*?)(["\\\x00-\x1f])', re.VERBOSE | re.MULTILINE | re.DOTALL)
        orig = 'z\U0001d120x'
        quoted1 = '"z\U0001d120x"'
        quoted2 = '"' + orig + '"'
        # chunker re gives different results depending on the plane
        self.assertEqual(chunker.match(quoted1, 1).groups(), (orig, '"'))
        self.assertEqual(chunker.match(quoted2, 1).groups(), (orig, '"'))

    def test_parse_unicode(self):
        foo = 'ą\n'
        self.assertEqual(len(foo), 2, repr(foo))
        self.assertEqual(repr(foo), "u'\\u0105\\n'")
        self.assertEqual(ord(foo[0]), 261)
        self.assertEqual(ord(foo[1]), 10)

        bar = foo.encode('utf-8')
        self.assertEqual(len(bar), 3)
        self.assertEqual(repr(bar), "'\\xc4\\x85\\n'")
        self.assertEqual(ord(bar[0]), 196)
        self.assertEqual(ord(bar[1]), 133)
        self.assertEqual(ord(bar[2]), 10)

    def test_parse_raw_unicode(self):
        foo = r'ą\n'
        self.assertEqual(len(foo), 3, repr(foo))
        self.assertEqual(repr(foo), "u'\\u0105\\\\n'")
        self.assertEqual(ord(foo[0]), 261)
        self.assertEqual(ord(foo[1]), 92)
        self.assertEqual(ord(foo[2]), 110)

        bar = foo.encode('utf-8')
        self.assertEqual(len(bar), 4)
        self.assertEqual(repr(bar), "'\\xc4\\x85\\\\n'")
        self.assertEqual(ord(bar[0]), 196)
        self.assertEqual(ord(bar[1]), 133)
        self.assertEqual(ord(bar[2]), 92)
        self.assertEqual(ord(bar[3]), 110)

        for baz in r'Hello\u0020World !', r'Hello\U00000020World !':
            self.assertEqual(len(baz), 13, repr(baz))
            self.assertEqual(repr(baz), "u'Hello World !'")
            self.assertEqual(ord(baz[5]), 32)

        quux = r'\U00100000'
        self.assertEqual(repr(quux), "u'\\U00100000'")
        if sys.maxunicode == 0xffff:
            self.assertEqual(len(quux), 2)
            self.assertEqual(ord(quux[0]), 56256)
            self.assertEqual(ord(quux[1]), 56320)
        else:
            self.assertEqual(len(quux), 1)
            self.assertEqual(ord(quux), 1048576)

    def test_raw_unicode_escape(self):
        foo = '\U00100000'
        self.assertEqual(foo.encode('raw_unicode_escape'), '\\U00100000')
        self.assertEqual(foo.encode('raw_unicode_escape').decode('raw_unicode_escape'),
                         foo)
        for bar in '\\u', '\\u000', '\\U00000':
            self.assertRaises(UnicodeDecodeError, bar.decode, 'raw_unicode_escape')

    def test_encode_decimal(self):
        self.assertEqual(int('\u0039\u0032'), 92)
        self.assertEqual(int('\u0660'), 0)
        self.assertEqual(int(' \u001F\u0966\u096F\u0039'), 99)
        self.assertEqual(int('\u0663'), 3)
        self.assertEqual(float('\u0663.\u0661'), 3.1)
        self.assertEqual(complex('\u0663.\u0661'), 3.1+0j)

    def test_unstateful_end_of_data(self):
        # http://bugs.jython.org/issue1368
        for encoding in 'utf-8', 'utf-16', 'utf-16-be', 'utf-16-le':
            self.assertRaises(UnicodeDecodeError, '\xe4'.decode, encoding)

    def test_formatchar(self):
        self.assertEqual('%c' % 255, '\xff')
        self.assertRaises(OverflowError, '%c'.__mod__, 256)

        result = '%c' % 256
        self.assertTrue(isinstance(result, str))
        self.assertEqual(result, '\u0100')
        if sys.maxunicode == 0xffff:
            self.assertEqual('%c' % sys.maxunicode, '\uffff')
        else:
            self.assertEqual('%c' % sys.maxunicode, '\U0010ffff')
        self.assertRaises(OverflowError, '%c'.__mod__, sys.maxunicode + 1)

    def test_repr(self):
        self.assertTrue(isinstance('%r' % 'foo', str))

    def test_unicode_lone_surrogate(self):
        # http://bugs.jython.org/issue2190
        self.assertRaises(ValueError, chr, 0xd800)
        self.assertRaises(ValueError, chr, 0xdfff)

    def test_concat(self):
        self.assertRaises(UnicodeDecodeError, lambda : '' + '毛泽东')
        self.assertRaises(UnicodeDecodeError, lambda : '毛泽东' + '')

    def test_join(self):
        self.assertRaises(UnicodeDecodeError, ''.join, ['foo', '毛泽东'])
        self.assertRaises(UnicodeDecodeError, '毛泽东'.join, ['foo', 'bar'])

    def test_file_encoding(self):
        '''Ensure file writing doesn't attempt to encode things by default and reading doesn't
        decode things by default.  This was jython's behavior prior to 2.2.1'''
        EURO_SIGN = "\u20ac"
        try:
            EURO_SIGN.encode()
        except UnicodeEncodeError:
            # This default encoding can't handle the encoding the Euro sign.  Skip the test
            return

        f = open(support.TESTFN, "w")
        self.assertRaises(UnicodeEncodeError, f, write, EURO_SIGN,
                "Shouldn't be able to write out a Euro sign without first encoding")
        f.close()

        f = open(support.TESTFN, "w")
        f.write(EURO_SIGN.encode('utf-8'))
        f.close()

        f = open(support.TESTFN, "r")
        encoded_euro = f.read()
        f.close()
        os.remove(support.TESTFN)
        self.assertEqual('\xe2\x82\xac', encoded_euro)
        self.assertEqual(EURO_SIGN, encoded_euro.decode('utf-8'))

    def test_translate(self):
        # http://bugs.jython.org/issue1483
        self.assertEqual(
            '\u0443\u043a\u0430\u0437\u0430\u0442\u044c'.translate({}),
            '\u0443\u043a\u0430\u0437\u0430\u0442\u044c')
        self.assertEqual('\u0443oo'.translate({0x443: 102}), 'foo')
        self.assertEqual(
            chr(sys.maxunicode).translate({sys.maxunicode: 102}),
            'f')


class UnicodeMaterial(object):
    ''' Object holding a list of single characters and a unicode string
        that is their concatenation. The sequence is created from a
        background sequence of basic plane characters and random
        replacement with supplementary plane characters (those with
        point code>0xffff).
    '''

    base = tuple('abcdefghijklmnopqrstuvwxyz')
    supp = tuple(map(chr, list(range(0x10000, 0x1000c))))
    used = sorted(set(base+supp))

    def __init__(self, size=20, pred=None, ran=None):
        ''' Create size chars choosing an SP char at i where
            pred(ran, i)==True where ran is an instance of
            random.Random supplied in the constructor or created
            locally (if ran==None).
        '''

        # Generators for the BMP and SP characters
        base = itertools.cycle(UnicodeMaterial.base)
        supp = itertools.cycle(UnicodeMaterial.supp)

        # Each instance gets a random generator
        if ran is None:
            ran = random.Random()
        self.random = ran

        if pred is None:
            pred = lambda ran, j : ran.random() < DEFAULT_RATE

        # Generate the list
        r = list()
        for i in range(size):
            if pred(self.random, i):
                c = next(supp)
            else:
                c = next(base)
            r.append(c)

        # The list and its concatenation are our material
        self.ref = r
        self.size = len(r)
        self.text = ''.join(r)
        self.target = ''

    def __len__(self):
        return self.size

    def insert(self, target, p=None):
        ''' Insert target string at position p (or middle), truncating if
            that would make the material any longer
        '''
        if p is None:
            p = max(0, (self.size-len(target)) // 2)

        n = 0
        for t in target:
            if p+n >= self.size:
                break;
            self.ref[p+n] = t
            n += 1

        self.target = target[:n]
        self.text = ''.join(self.ref)


class UnicodeIndexMixTest(unittest.TestCase):
    # Test indexing where there may be more than one code unit per code point.
    # See Jython Issue #2100.

    # Functions defining particular distributions of SP codes
    #
    def evenly(self, rate=0.2):
        'Evenly distributed at given rate'
        def f(ran, i):
            return ran.random() < rate
        return f

    def evenly_before(self, k, rate=0.2):
        'Evenly distributed on i<k at given rate'
        def f(ran, i):
            return i < k and ran.random() < rate
        return f

    def evenly_from(self, k, rate=0.2):
        'Evenly distributed on i>=k at given rate'
        def f(ran, i):
            return i >= k and ran.random() < rate
        return f

    def at(self, places):
        'Only at specified places'
        def f(ran, i):
            return i in places
        return f

    def setUp(self):
        ran = random.Random(1234)  # ensure repeatable
        mat = list()
        mat.append(UnicodeMaterial(10, self.at([2]), ran))
        mat.append(UnicodeMaterial(10, self.at([2, 5]), ran))
        mat.append(UnicodeMaterial(50, self.evenly(), ran))
        mat.append(UnicodeMaterial(200, self.evenly_before(70), ran))
        mat.append(UnicodeMaterial(200, self.evenly_from(130), ran))
        mat.append(UnicodeMaterial(1000, self.evenly(), ran))

        self.material = mat


    def test_getitem(self):
        # Test map from to code point index to internal representation
        # Fails in Jython 2.7b3

        def check_getitem(m):
            # Check indexing the string returns the expected point code
            for i in range(m.size):
                self.assertEqual(m.text[i], m.ref[i])

        for m in self.material:
            check_getitem(m)

    def test_slice(self):
        # Test indexing gets the slice ends correct.
        # Passes in Jython 2.7b3, but may be touched by #2100 changes.

        def check_slice(m):
            # Check a range of slices against slices of the reference.
            n = 1
            while n <= m.size:
                for i in range(m.size - n):
                    exp = ''.join(m.ref[i:i+n])
                    self.assertEqual(m.text[i:i+n], exp)
                n *= 3

        for m in self.material:
            check_slice(m)

    def test_find(self):
        # Test map from internal find result to code point index
        # Fails in Jython 2.7b3

        def check_find(ref):
            # Check find returns indexes for single point codes
            for c in set(m.used):
                start = 0
                u = m.text
                while start < m.size:
                    i = u.find(c, start)
                    if i < 0: break
                    self.assertEqual(u[i], c)
                    self.assertGreaterEqual(i, start)
                    start = i + 1

        def check_find_str(m, t):
            # Check find returns correct index for string target
            i = m.text.find(t)
            self.assertEqual(list(t), m.ref[i:i+len(t)])

        targets = [
            "this",
            "ab\U00010041de", 
            "\U00010041\U00010042\U00010042xx",
            "xx\U00010041\U00010042\U00010043yy",
        ]

        for m in self.material:
            check_find(m)
            for t in targets:
                # Insert in middle then try to find it
                m.insert(t)
                check_find_str(m, t)

    def test_rfind(self):
        # Test map from internal rfind result to code point index
        # Fails in Jython 2.7b3

        def check_rfind(ref):
            # Check rfind returns indexes for single point codes
            for c in set(m.used):
                end = m.size
                u = m.text
                while True:
                    i = u.rfind(c, 0, end)
                    if i < 0: break
                    self.assertLess(i, end)
                    self.assertEqual(u[i], c)
                    end = i

        def check_rfind_str(m, t):
            # Check rfind returns correct index for string target
            i = m.text.rfind(t)
            self.assertEqual(list(t), m.ref[i:i+len(t)])

        targets = [
            "this",
            "ab\U00010041de", 
            "\U00010041\U00010042\U00010042xx",
            "xx\U00010041\U00010042\U00010043yy",
        ]

        for m in self.material:
            check_rfind(m)
            for t in targets:
                # Insert in middle then try to find it
                m.insert(t)
                check_rfind_str(m, t)

    def test_surrogate_validation(self):

        def insert_sb(text, c1, c2):
            # Insert code points c1, c2 in the text, as a Java StringBuilder
            sb = StringBuilder()
            # c1 at the quarter point
            p1 = len(mat) // 4
            for c in mat.text[:p1]:
                sb.appendCodePoint(ord(c))
            sb.appendCodePoint(c1)
            # c2 at the three-quarter point
            p2 = 3 * p1
            for c in mat.text[p1:p2]:
                sb.appendCodePoint(ord(c))
            sb.appendCodePoint(c2)
            # Rest of text
            for c in mat.text[p2:]:
                sb.appendCodePoint(ord(c))
            return sb

        # Test that lone surrogates are rejected
        for surr in [0xdc81, 0xdc00, 0xdfff, 0xd800, 0xdbff]:
            for mat in self.material:

                # Java StringBuilder with two private-use characters:
                sb = insert_sb(mat.text, 0xe000, 0xf000)
                # Check this is acceptable
                #print repr(unicode(sb))
                self.assertEqual(len(str(sb)), len(mat)+2)

                # Java StringBuilder with private-use and lone surrogate:
                sb = insert_sb(mat.text, 0xe000, surr)
                # Check this is detected
                #print repr(unicode(sb))
                self.assertRaises(ValueError, str, sb)


class UnicodeFormatTestCase(unittest.TestCase):

    def test_unicode_mapping(self):
        assertTrue = self.assertTrue
        class EnsureUnicode(dict):
            def __missing__(self, key):
                assertTrue(isinstance(key, str))
                return key
        '%(foo)s' % EnsureUnicode()

    def test_non_ascii_unicode_mod_str(self):
        # Regression test for a problem on the formatting logic: when no unicode
        # args were found, Jython stored the resulting buffer on a PyString,
        # decoding it later to make a PyUnicode. That crashed when the left side
        # of % was a unicode containing non-ascii chars
        self.assertEqual("\u00e7%s" % "foo", "\u00e7foo")


class UnicodeStdIOTestCase(unittest.TestCase):

    def setUp(self):
        self.stdout = sys.stdout

    def tearDown(self):
        sys.stdout = self.stdout

    def test_intercepted_stdout(self):
        msg = 'Circle is 360\u00B0'
        sys.stdout = StringIO()
        print(msg, end=' ')
        self.assertEqual(sys.stdout.getvalue(), msg)


class UnicodeFormatStrTest(unittest.TestCase):
    # Adapted from test_str StrTest by liberally adding u-prefixes.

    def test__format__(self):
        def test(value, format, expected):
            r = value.__format__(format)
            self.assertEqual(r, expected)
            # note 'xyz'==u'xyz', so must check type separately
            self.assertIsInstance(r, str)
            # also test both with the trailing 's'
            r = value.__format__(format + 's')
            self.assertEqual(r, expected)
            self.assertIsInstance(r, str)

        test('', '', '')
        test('abc', '', 'abc')
        test('abc', '.3', 'abc')
        test('ab', '.3', 'ab')
        test('abcdef', '.3', 'abc')
        test('abcdef', '.0', '')
        test('abc', '3.3', 'abc')
        test('abc', '2.3', 'abc')
        test('abc', '2.2', 'ab')
        test('abc', '3.2', 'ab ')
        test('result', 'x<0', 'result')
        test('result', 'x<5', 'result')
        test('result', 'x<6', 'result')
        test('result', 'x<7', 'resultx')
        test('result', 'x<8', 'resultxx')
        test('result', ' <7', 'result ')
        test('result', '<7', 'result ')
        test('result', '>7', ' result')
        test('result', '>8', '  result')
        test('result', '^8', ' result ')
        test('result', '^9', ' result  ')
        test('result', '^10', '  result  ')
        test('a', '10000', 'a' + ' ' * 9999)
        test('', '10000', ' ' * 10000)
        test('', '10000000', ' ' * 10000000)

    def test_format(self):
        self.assertEqual(''.format(), '')
        self.assertEqual('a'.format(), 'a')
        self.assertEqual('ab'.format(), 'ab')
        self.assertEqual('a{{'.format(), 'a{')
        self.assertEqual('a}}'.format(), 'a}')
        self.assertEqual('{{b'.format(), '{b')
        self.assertEqual('}}b'.format(), '}b')
        self.assertEqual('a{{b'.format(), 'a{b')

        # examples from the PEP:
        import datetime
        self.assertEqual("My name is {0}".format('Fred'), "My name is Fred")
        self.assertIsInstance("My name is {0}".format('Fred'), str)
        self.assertEqual("My name is {0[name]}".format(dict(name='Fred')),
                         "My name is Fred")
        self.assertEqual("My name is {0} :-{{}}".format('Fred'),
                         "My name is Fred :-{}")

        d = datetime.date(2007, 8, 18)
        self.assertEqual("The year is {0.year}".format(d),
                         "The year is 2007")

        # classes we'll use for testing
        class C:
            def __init__(self, x=100):
                self._x = x
            def __format__(self, spec):
                return spec

        class D:
            def __init__(self, x):
                self.x = x
            def __format__(self, spec):
                return str(self.x)

        # class with __str__, but no __format__
        class E:
            def __init__(self, x):
                self.x = x
            def __str__(self):
                return 'E(' + self.x + ')'

        # class with __repr__, but no __format__ or __str__
        class F:
            def __init__(self, x):
                self.x = x
            def __repr__(self):
                return 'F(' + self.x + ')'

        # class with __format__ that forwards to string, for some format_spec's
        class G:
            def __init__(self, x):
                self.x = x
            def __str__(self):
                return "string is " + self.x
            def __format__(self, format_spec):
                if format_spec == 'd':
                    return 'G(' + self.x + ')'
                return object.__format__(self, format_spec)

        # class that returns a bad type from __format__
        class H:
            def __format__(self, format_spec):
                return 1.0

        class I(datetime.date):
            def __format__(self, format_spec):
                return self.strftime(format_spec)

        class J(int):
            def __format__(self, format_spec):
                return int.__format__(self * 2, format_spec)


        self.assertEqual(''.format(), '')
        self.assertEqual('abc'.format(), 'abc')
        self.assertEqual('{0}'.format('abc'), 'abc')
        self.assertEqual('{0:}'.format('abc'), 'abc')
        self.assertEqual('X{0}'.format('abc'), 'Xabc')
        self.assertEqual('{0}X'.format('abc'), 'abcX')
        self.assertEqual('X{0}Y'.format('abc'), 'XabcY')
        self.assertEqual('{1}'.format(1, 'abc'), 'abc')
        self.assertEqual('X{1}'.format(1, 'abc'), 'Xabc')
        self.assertEqual('{1}X'.format(1, 'abc'), 'abcX')
        self.assertEqual('X{1}Y'.format(1, 'abc'), 'XabcY')
        self.assertEqual('{0}'.format(-15), '-15')
        self.assertEqual('{0}{1}'.format(-15, 'abc'), '-15abc')
        self.assertEqual('{0}X{1}'.format(-15, 'abc'), '-15Xabc')
        self.assertEqual('{{'.format(), '{')
        self.assertEqual('}}'.format(), '}')
        self.assertEqual('{{}}'.format(), '{}')
        self.assertEqual('{{x}}'.format(), '{x}')
        self.assertEqual('{{{0}}}'.format(123), '{123}')
        self.assertEqual('{{{{0}}}}'.format(), '{{0}}')
        self.assertEqual('}}{{'.format(), '}{')
        self.assertEqual('}}x{{'.format(), '}x{')

        # weird field names
        self.assertEqual("{0[foo-bar]}".format({'foo-bar':'baz'}), 'baz')
        self.assertEqual("{0[foo bar]}".format({'foo bar':'baz'}), 'baz')
        self.assertEqual("{0[ ]}".format({' ':3}), '3')

        self.assertEqual('{foo._x}'.format(foo=C(20)), '20')
        self.assertEqual('{1}{0}'.format(D(10), D(20)), '2010')
        self.assertEqual('{0._x.x}'.format(C(D('abc'))), 'abc')
        self.assertEqual('{0[0]}'.format(['abc', 'def']), 'abc')
        self.assertEqual('{0[1]}'.format(['abc', 'def']), 'def')
        self.assertEqual('{0[1][0]}'.format(['abc', ['def']]), 'def')
        self.assertEqual('{0[1][0].x}'.format(['abc', [D('def')]]), 'def')

        self.assertIsInstance('{0[1][0].x}'.format(['abc', [D('def')]]), str)

        # strings
        self.assertEqual('{0:.3s}'.format('abc'), 'abc')
        self.assertEqual('{0:.3s}'.format('ab'), 'ab')
        self.assertEqual('{0:.3s}'.format('abcdef'), 'abc')
        self.assertEqual('{0:.0s}'.format('abcdef'), '')
        self.assertEqual('{0:3.3s}'.format('abc'), 'abc')
        self.assertEqual('{0:2.3s}'.format('abc'), 'abc')
        self.assertEqual('{0:2.2s}'.format('abc'), 'ab')
        self.assertEqual('{0:3.2s}'.format('abc'), 'ab ')
        self.assertEqual('{0:x<0s}'.format('result'), 'result')
        self.assertEqual('{0:x<5s}'.format('result'), 'result')
        self.assertEqual('{0:x<6s}'.format('result'), 'result')
        self.assertEqual('{0:x<7s}'.format('result'), 'resultx')
        self.assertEqual('{0:x<8s}'.format('result'), 'resultxx')
        self.assertEqual('{0: <7s}'.format('result'), 'result ')
        self.assertEqual('{0:<7s}'.format('result'), 'result ')
        self.assertEqual('{0:>7s}'.format('result'), ' result')
        self.assertEqual('{0:>8s}'.format('result'), '  result')
        self.assertEqual('{0:^8s}'.format('result'), ' result ')
        self.assertEqual('{0:^9s}'.format('result'), ' result  ')
        self.assertEqual('{0:^10s}'.format('result'), '  result  ')
        self.assertEqual('{0:10000}'.format('a'), 'a' + ' ' * 9999)
        self.assertEqual('{0:10000}'.format(''), ' ' * 10000)
        self.assertEqual('{0:10000000}'.format(''), ' ' * 10000000)

        # format specifiers for user defined type
        self.assertEqual('{0:abc}'.format(C()), 'abc')

        # !r and !s coercions
        self.assertEqual('{0!s}'.format('Hello'), 'Hello')
        self.assertEqual('{0!s:}'.format('Hello'), 'Hello')
        self.assertEqual('{0!s:15}'.format('Hello'), 'Hello          ')
        self.assertEqual('{0!s:15s}'.format('Hello'), 'Hello          ')
        self.assertEqual('{0!r}'.format('Hello'), "'Hello'")
        self.assertEqual('{0!r:}'.format('Hello'), "'Hello'")
        self.assertEqual('{0!r}'.format(F('Hello')), 'F(Hello)')

        # test fallback to object.__format__
        self.assertEqual('{0}'.format({}), '{}')
        self.assertEqual('{0}'.format([]), '[]')
        self.assertEqual('{0}'.format([1]), '[1]')
        self.assertEqual('{0}'.format(E('data')), 'E(data)')
        self.assertEqual('{0:d}'.format(G('data')), 'G(data)')
        self.assertEqual('{0!s}'.format(G('data')), 'string is data')

        msg = 'object.__format__ with a non-empty format string is deprecated'
        with support.check_warnings((msg, PendingDeprecationWarning)):
            self.assertEqual('{0:^10}'.format(E('data')), ' E(data)  ')
            self.assertEqual('{0:^10s}'.format(E('data')), ' E(data)  ')
            self.assertEqual('{0:>15s}'.format(G('data')), ' string is data')

        #FIXME: not supported in Jython yet:
        if not support.is_jython:
            self.assertEqual("{0:date: %Y-%m-%d}".format(I(year=2007,
                                                           month=8,
                                                           day=27)),
                             "date: 2007-08-27")

            # test deriving from a builtin type and overriding __format__
            self.assertEqual("{0}".format(J(10)), "20")


        # string format specifiers
        self.assertEqual('{0:}'.format('a'), 'a')

        # computed format specifiers
        self.assertEqual("{0:.{1}}".format('hello world', 5), 'hello')
        self.assertEqual("{0:.{1}s}".format('hello world', 5), 'hello')
        self.assertEqual("{0:.{precision}s}".format('hello world', precision=5), 'hello')
        self.assertEqual("{0:{width}.{precision}s}".format('hello world', width=10, precision=5), 'hello     ')
        self.assertEqual("{0:{width}.{precision}s}".format('hello world', width='10', precision='5'), 'hello     ')

        self.assertIsInstance("{0:{width}.{precision}s}".format('hello world', width='10', precision='5'), str)

        # test various errors
        self.assertRaises(ValueError, '{'.format)
        self.assertRaises(ValueError, '}'.format)
        self.assertRaises(ValueError, 'a{'.format)
        self.assertRaises(ValueError, 'a}'.format)
        self.assertRaises(ValueError, '{a'.format)
        self.assertRaises(ValueError, '}a'.format)
        self.assertRaises(IndexError, '{0}'.format)
        self.assertRaises(IndexError, '{1}'.format, 'abc')
        self.assertRaises(KeyError,   '{x}'.format)
        self.assertRaises(ValueError, "}{".format)
        self.assertRaises(ValueError, "{".format)
        self.assertRaises(ValueError, "}".format)
        self.assertRaises(ValueError, "abc{0:{}".format)
        self.assertRaises(ValueError, "{0".format)
        self.assertRaises(IndexError, "{0.}".format)
        self.assertRaises(ValueError, "{0.}".format, 0)
        self.assertRaises(IndexError, "{0[}".format)
        self.assertRaises(ValueError, "{0[}".format, [])
        self.assertRaises(KeyError,   "{0]}".format)
        self.assertRaises(ValueError, "{0.[]}".format, 0)
        self.assertRaises(ValueError, "{0..foo}".format, 0)
        self.assertRaises(ValueError, "{0[0}".format, 0)
        self.assertRaises(ValueError, "{0[0:foo}".format, 0)
        self.assertRaises(KeyError,   "{c]}".format)
        self.assertRaises(ValueError, "{{ {{{0}}".format, 0)
        self.assertRaises(ValueError, "{0}}".format, 0)
        self.assertRaises(KeyError,   "{foo}".format, bar=3)
        self.assertRaises(ValueError, "{0!x}".format, 3)
        self.assertRaises(ValueError, "{0!}".format, 0)
        self.assertRaises(ValueError, "{0!rs}".format, 0)
        self.assertRaises(ValueError, "{!}".format)
        self.assertRaises(IndexError, "{:}".format)
        self.assertRaises(IndexError, "{:s}".format)
        self.assertRaises(IndexError, "{}".format)

        # issue 6089
        self.assertRaises(ValueError, "{0[0]x}".format, [None])
        self.assertRaises(ValueError, "{0[0](10)}".format, [None])

        # can't have a replacement on the field name portion
        self.assertRaises(TypeError, '{0[{1}]}'.format, 'abcdefg', 4)

        # exceed maximum recursion depth
        self.assertRaises(ValueError, "{0:{1:{2}}}".format, 'abc', 's', '')
        self.assertRaises(ValueError, "{0:{1:{2:{3:{4:{5:{6}}}}}}}".format,
                          0, 1, 2, 3, 4, 5, 6, 7)

        # string format spec errors
        self.assertRaises(ValueError, "{0:-s}".format, '')
        self.assertRaises(ValueError, format, "", "-")
        self.assertRaises(ValueError, "{0:=s}".format, '')

    def test_format_auto_numbering(self):
        class C:
            def __init__(self, x=100):
                self._x = x
            def __format__(self, spec):
                return spec

        self.assertEqual('{}'.format(10), '10')
        self.assertEqual('{:5}'.format('s'), 's    ')
        self.assertEqual('{!r}'.format('s'), "'s'")
        self.assertEqual('{._x}'.format(C(10)), '10')
        self.assertEqual('{[1]}'.format([1, 2]), '2')
        self.assertEqual('{[a]}'.format({'a':4, 'b':2}), '4')
        self.assertEqual('a{}b{}c'.format(0, 1), 'a0b1c')

        self.assertEqual('a{:{}}b'.format('x', '^10'), 'a    x     b')
        self.assertEqual('a{:{}x}b'.format(20, '#'), 'a0x14b')

        # can't mix and match numbering and auto-numbering
        self.assertRaises(ValueError, '{}{1}'.format, 1, 2)
        self.assertRaises(ValueError, '{1}{}'.format, 1, 2)
        self.assertRaises(ValueError, '{:{1}}'.format, 1, 2)
        self.assertRaises(ValueError, '{0:{}}'.format, 1, 2)

        # can mix and match auto-numbering and named
        self.assertEqual('{f}{}'.format(4, f='test'), 'test4')
        self.assertEqual('{}{f}'.format(4, f='test'), '4test')
        self.assertEqual('{:{f}}{g}{}'.format(1, 3, g='g', f=2), ' 1g3')
        self.assertEqual('{f:{}}{}{g}'.format(2, 4, f=1, g='g'), ' 14g')


class StringModuleUnicodeTest(unittest.TestCase):
    # Taken from test_string ModuleTest and converted for unicode

    def test_formatter(self):

        def assertEqualAndUnicode(r, exp):
            self.assertEqual(r, exp)
            self.assertIsInstance(r, str)

        fmt = string.Formatter()
        assertEqualAndUnicode(fmt.format("foo"), "foo")
        assertEqualAndUnicode(fmt.format("foo{0}", "bar"), "foobar")
        assertEqualAndUnicode(fmt.format("foo{1}{0}-{1}", "bar", 6), "foo6bar-6")
        assertEqualAndUnicode(fmt.format("-{arg!r}-", arg='test'), "-'test'-")

        # override get_value ############################################
        class NamespaceFormatter(string.Formatter):
            def __init__(self, namespace={}):
                string.Formatter.__init__(self)
                self.namespace = namespace

            def get_value(self, key, args, kwds):
                if isinstance(key, str):
                    try:
                        # Check explicitly passed arguments first
                        return kwds[key]
                    except KeyError:
                        return self.namespace[key]
                else:
                    string.Formatter.get_value(key, args, kwds)

        fmt = NamespaceFormatter({'greeting':'hello'})
        assertEqualAndUnicode(fmt.format("{greeting}, world!"), 'hello, world!')


        # override format_field #########################################
        class CallFormatter(string.Formatter):
            def format_field(self, value, format_spec):
                return format(value(), format_spec)

        fmt = CallFormatter()
        assertEqualAndUnicode(fmt.format('*{0}*', lambda : 'result'), '*result*')


        # override convert_field ########################################
        class XFormatter(string.Formatter):
            def convert_field(self, value, conversion):
                if conversion == 'x':
                    return None
                return super(XFormatter, self).convert_field(value, conversion)

        fmt = XFormatter()
        assertEqualAndUnicode(fmt.format("{0!r}:{0!x}", 'foo', 'foo'), "'foo':None")


        # override parse ################################################
        class BarFormatter(string.Formatter):
            # returns an iterable that contains tuples of the form:
            # (literal_text, field_name, format_spec, conversion)
            def parse(self, format_string):
                for field in format_string.split('|'):
                    if field[0] == '+':
                        # it's markup
                        field_name, _, format_spec = field[1:].partition(':')
                        yield '', field_name, format_spec, None
                    else:
                        yield field, None, None, None

        fmt = BarFormatter()
        assertEqualAndUnicode(fmt.format('*|+0:^10s|*', 'foo'), '*   foo    *')

        # test all parameters used
        class CheckAllUsedFormatter(string.Formatter):
            def check_unused_args(self, used_args, args, kwargs):
                # Track which arguments actually got used
                unused_args = set(kwargs.keys())
                unused_args.update(list(range(0, len(args))))

                for arg in used_args:
                    unused_args.remove(arg)

                if unused_args:
                    raise ValueError("unused arguments")

        fmt = CheckAllUsedFormatter()
        # The next series should maybe also call assertEqualAndUnicode:
        #assertEqualAndUnicode(fmt.format(u"{0}", 10), "10")
        #assertEqualAndUnicode(fmt.format(u"{0}{i}", 10, i=100), "10100")
        #assertEqualAndUnicode(fmt.format(u"{0}{i}{1}", 10, 20, i=100), "1010020")
        # But string.Formatter.format returns bytes. See CPython Issue 15951.
        self.assertEqual(fmt.format("{0}", 10), "10")
        self.assertEqual(fmt.format("{0}{i}", 10, i=100), "10100")
        self.assertEqual(fmt.format("{0}{i}{1}", 10, 20, i=100), "1010020")
        self.assertRaises(ValueError, fmt.format, "{0}{i}{1}", 10, 20, i=100, j=0)
        self.assertRaises(ValueError, fmt.format, "{0}", 10, 20)
        self.assertRaises(ValueError, fmt.format, "{0}", 10, 20, i=100)
        self.assertRaises(ValueError, fmt.format, "{i}", 10, 20, i=100)


def test_main():
    support.run_unittest(
                UnicodeTestCase,
                UnicodeIndexMixTest,
                UnicodeFormatTestCase,
                UnicodeStdIOTestCase,
                UnicodeFormatStrTest,
                StringModuleUnicodeTest,
            )


if __name__ == "__main__":
    test_main()
