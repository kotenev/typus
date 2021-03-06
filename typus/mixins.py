# coding: utf-8

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import re
from builtins import *  # noqa

from .chars import *  # noqa
from .utils import map_choices

__all__ = ('EnQuotes', 'RuQuotes', 'EnRuExpressions')


class EnQuotes(object):
    r"""
    Provides English quotes configutation for :class:`typus.processors.Quotes`
    processor.

    >>> en_typus('He said "\'Winnie-the-Pooh\' is my favorite book!".')
    'He said “‘Winnie-the-Pooh’ is my favorite book!”.'
    """

    # Left odd, right odd, left even, right even
    loq, roq, leq, req = LDQUO, RDQUO, LSQUO, RSQUO


class RuQuotes(object):
    r"""
    Provides Russian quotes configutation for :class:`typus.processors.Quotes`
    processor.

    >>> ru_typus('Он сказал: "\'Винни-Пух\' -- моя любимая книга!".')
    'Он сказал: «„Винни-Пух“ — моя любимая книга!».'
    """

    # Left odd, right odd, left even, right even
    loq, roq, leq, req = LAQUO, RAQUO, DLQUO, LDQUO


class EnRuExpressions(object):
    """
    This class holds most of Typus functionality for English and Russian
    languages. It works with :class:`typus.processors.Expressions`.
    """

    expressions = (
        'spaces linebreaks apostrophe complex_symbols mdash primes phones '
        'digit_spaces pairs units ranges vulgar_fractions math ruble abbrs '
        'rep_positional_spaces del_positional_spaces'
    ).split()

    # Any unicode word
    words = r'[^\W\d_]'

    complex_symbols = {
        '...': '…',
        '<-': '←',
        '->': '→',
        '+-': '±',
        '+' + MINUS: '±',
        '<=': '≤',
        '>=': '≥',
        '/=': '≠',
        '==': '≡',
        '(r)': '®',
        '(c)': '©',
        '(p)': '℗',
        '(tm)': '™',
        '(sm)': '℠',
        # cyrillic
        '(с)': '©',
        '(р)': '℗',
        '(тм)': '™',

    }

    vulgar_fractions = {
        '1/2': '½',
        '1/3': '⅓',
        '1/5': '⅕',
        '1/6': '⅙',
        '1/8': '⅛',
        '2/3': '⅔',
        '2/5': '⅖',
        '3/4': '¾',
        '3/5': '⅗',
        '3/8': '⅜',
        '4/5': '⅘',
        '5/6': '⅚',
        '5/8': '⅝',
        '7/8': '⅞',
    }

    math = {
        '-': MINUS,
        '*xх': TIMES,
    }

    # Not need to put >=, +-, etc, after expr_complex_symbols
    math_operators = r'[\-{0}\*xх{1}\+\=±≤≥≠÷\/]'.format(MINUS, TIMES)

    rep_positional_spaces = {
        # No need to put vulgar fractions in here because of expr_digit_spaces
        # which joins digits and words afterward
        'after': '←$€£%±{0}{1}©§¶№'.format(MINUS, TIMES),
        'both': '&≡≤≥≠',
        'before': '₽→' + MDASH,
    }

    del_positional_spaces = {
        'before': '®℗™℠:,.?!…',
    }

    # Replace this if you don't need nbsp before ruble
    ruble = NBSP + '₽'

    def expr_spaces(self):
        """
        Trims spaces at the beginning and end of the line and remove extra
        spaces within.

        >>> en_typus('   foo bar  ')
        'foo bar'

        .. caution::
            Doesn't work correctly with nbsp (replaces with whitespace).
        """

        expr = (
            (r'{0}{{2,}}'.format(ANYSP), WHSP),
            (r'(?:^{0}+|{0}+$)'.format(ANYSP), ''),
        )
        return expr

    def expr_linebreaks(self):
        r"""
        Converts line breaks to unix-style and removes extra breaks
        if found more than two in a row.

        >>> en_typus('foo\r\nbar\n\n\nbaz')
        'foo\nbar\n\nbaz'
        """

        expr = (
            (r'\r\n', '\n'),
            (r'\n{2,}', '\n' * 2),
        )
        return expr

    def expr_apostrophe(self):
        """
        Replaces single quote with apostrophe.

        >>> en_typus("She'd, I'm, it's, don't, you're, he'll, 90's")
        'She’d, I’m, it’s, don’t, you’re, he’ll, 90’s'

        .. note::
            By the way it works with any omitted word. But then again, why not?
        """

        expr = (
            (r'(?<={0}|[0-9])\'(?={0})'.format(self.words), RSQUO),
        )
        return expr

    def expr_complex_symbols(self):
        """
        Replaces complex symbols with Unicode characters. Doesn't care
        about case-sensitivity and handles Cyrillic-Latin twins
        like ``c`` and ``с``.

        >>> en_typus('(c)(с)(C)(r)(R)...')
        '©©©®®…'

        .. csv-table:: Character map
            :header: …, ←, →, ±, ≤, ≥, ≠, ≡, ®, ©, ℗, ™, ℠

            ..., <-, ->, +- or +−, <=, >=, /=, ==, (r), (c), (p), (tm), (sm)
        """

        expr = (
            map_choices(self.complex_symbols),
        )
        return expr

    def expr_mdash(self):
        """
        Replaces dash with mdash.

        >>> en_typus('foo -- bar')  # adds non-breakable space after `foo`
        'foo\u00A0— bar'
        """

        expr = (
            # Double dash guarantees to be replaced with mdash
            (r'{0}--{0}'.format(WHSP), MDASH_PAIR),

            # Dash can be between anything except digits
            # because in that case it's not obvious
            (r'{0}+[\-|{1}]{0}+(?!\d\b)'.format(ANYSP, NDASH), MDASH_PAIR),

            # Same but backwards
            # It joins non-digit with digit or word
            (r'(\b\D+){0}+[\-|{1}]{0}+'.format(ANYSP, NDASH),
             r'\1{0}'.format(MDASH_PAIR)),

            # Line beginning adds nbsp after dash
            (r'^\-{{1,2}}{0}+'.format(ANYSP),
             r'{0}{1}'.format(MDASH, NBSP)),

            # Also mdash can be at the end of the line in poems
            (r'{0}+\-{{1,2}}{0}*(?=$|<br/?>)'.format(ANYSP),
             r'{0}{1}'.format(NBSP, MDASH)),
        )
        return expr

    def expr_primes(self):
        r"""
        Replaces quotes with prime after digits.

        >>> en_typus('3\' 5" long')
        '3′ 5″ long'

        .. caution::
            Won't break "4", but fails with " 4".
        """

        expr = (
            (r'(^|{0})(\d+)\''.format(ANYSP), r'\1\2' + SPRIME),
            (r'(^|{0})(\d+)"'.format(ANYSP), r'\1\2' + DPRIME),
        )
        return expr

    def expr_phones(self):
        """
        Replaces dash with ndash in phone numbers which should be a trio of
        2-4 length digits.

        >>> en_typus('111-00-00'), en_typus('00-111-00'), en_typus('00-00-111')
        ('111–00–00', '00–111–00', '00–00–111')
        """

        expr = (
            (r'([0-9]{2,4})\-([0-9]{2,4})\-([0-9]{2,4})',
             r'\1{0}\2{0}\3'.format(NDASH)),
        )
        return expr

    def expr_digit_spaces(self):
        """
        Replaces whitespace with non-breakable space after 4 (and less)
        length digits if word or digit without comma or math operators
        found afterwards:
        3 apples
        40 000 bucks
        400 + 3
        Skips:
        4000 bucks
        40 000,00 bucks
        """

        expr = (
            (r'\b(\d{{1,3}}){0}(?=[0-9]+\b|{1}|{2})'
             .format(WHSP, self.words, self.math_operators), r'\1' + NBSP),
        )
        return expr

    def expr_pairs(self):
        """
        Replaces whitespace with non-breakable space after 1-2 length words.
        """

        expr = (
            # Unions, units and all that small staff
            (r'\b({1}{{1,2}}){0}+'.format(WHSP, self.words), r'\1' + NBSP),
            # Fixes previous with leading dash, ellipsis or apostrophe
            (r'([-…’]{1}{{1,2}}){0}'.format(NBSP, self.words), r'\1' + WHSP),
        )
        return expr

    def expr_units(self):
        """
        Puts non-breakable space between digits and units.

        >>> en_typus('1mm', debug=True), en_typus('1mm')
        ('1_mm', '1 mm')
        """

        expr = (
            (r'\b(\d+){0}*(?!(?:nd|rd|th|d|g|px)\b)({1}{{1,3}})\b'
             .format(WHSP, self.words),
             r'\1{0}\2'.format(NBSP)),
        )
        return expr

    def expr_ranges(self):
        """
        Replaces dash with mdash in ranges.
        Supports float and negative values.
        Tries to not mess with minus: skips if any math operator or word
        was found after dash: 3-2=1, 24-pin.
        **NOTE**: _range_ should not have spaces between dash: `2-3` and
        left side should be less than right side.
        """

        def ufloat(string):
            return float(string.replace(',', '.'))

        def replace(match):
            left, dash, right = match.groups()
            if ufloat(left) < ufloat(right):
                dash = MDASH
            return '{0}{1}{2}'.format(left, dash, right)

        expr = (
            (r'(-?(?:[0-9]+[\.,][0-9]+|[0-9]+))(-)'
             r'([0-9]+[\.,][0-9]+|[0-9]+)'
             r'(?!{0}+{1}|{2})'
             .format(ANYSP, self.math_operators, self.words),
             replace),
        )
        return expr

    def expr_vulgar_fractions(self):
        """
        Replaces vulgar fractions with appropriate unicode characters.

        >>> en_typus('1/2')
        '½'
        """

        expr = (
            # \b to excludes digits which are not on map, like `11/22`
            map_choices(self.vulgar_fractions, r'\b({0})\b'),
        )
        return expr

    def expr_math(self):
        """
        Puts minus and multiplication symbols between pair and before
        single digits.

        >>> en_typus('3 - 3 = 0')
        '3 − 3 = 0'
        >>> en_typus('-3 degrees')
        '−3 degrees'
        >>> en_typus('3 x 3 = 9')
        '3 × 3 = 9'
        >>> en_typus('x3 better!')
        '×3 better!'

        .. important::

            Should run after `mdash` and `phones` expressions.
        """

        expr = (
            (r'(^|{0}|\d)[{1}]({0}*\d)'.format(ANYSP, re.escape(x)),
             r'\1{0}\2'.format(y)) for x, y in self.math.items()
        )
        return expr

    def expr_abbrs(self):
        """
        Adds narrow non-breakable space and replaces whitespaces between
        shorten words.
        """

        expr = (
            (r'\b({1}\.){0}*({1}\.)'.format(ANYSP, self.words),
             r'\1{0}\2'.format(NNBSP)),
            (r'\b({1}\.){0}*(?={1})'.format(WHSP, self.words),
             r'\1{0}'.format(NBSP)),
        )
        return expr

    def expr_ruble(self):
        """
        Replaces `руб` and `р` (with or without dot) after digits
        with ruble symbol.

        >>> en_typus('1000 р.')
        '1000 ₽'

        .. caution::

            Drops the dot at the end of sentence if match found in there.
        """

        expr = (
            (r'(\d){0}*(?:руб|р)\b\.?'.format(ANYSP),
             r'\1{0}'.format(self.ruble)),
        )
        return expr

    def _positional_spaces(self, data, find, replace):
        """
        Helper method for `rep_positional_spaces` and `del_positional_spaces`
        expressions.
        """

        both = data.get('both', '')
        before = re.escape(data.get('before', '') + both)
        after = re.escape(data.get('after', '') + both)
        expr = []
        if before:
            expr.append((r'{0}+(?=[{1}])'.format(find, before), replace))
        if after:
            expr.append((r'(?<=[{1}]){0}+'.format(find, after), replace))
        return expr

    def expr_rep_positional_spaces(self):
        """
        Replaces whitespaces after and before certain symbols
        with non-breakable space.
        """

        expr = self._positional_spaces(self.rep_positional_spaces, WHSP, NBSP)
        return expr

    def expr_del_positional_spaces(self):
        """
        Removes spaces before and after certain symbols.
        """

        expr = self._positional_spaces(self.del_positional_spaces, ANYSP, '')
        return expr
