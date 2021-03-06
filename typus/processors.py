# coding: utf-8

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from builtins import *  # noqa
from functools import update_wrapper, wraps
from itertools import count, cycle

from .chars import DLQUO, LAQUO, LDQUO, LSQUO, RAQUO, RDQUO, RSQUO
from .utils import re_compile

__all__ = ('EscapePhrases', 'EscapeHtml', 'Quotes', 'Expressions')


def tail_processor(text, *args, **kwargs):
    return text


class BaseProcessor(object):
    """
    Processors are the core of Typus. See subclasses for examples.
    """

    def __init__(self, typus):
        # Makes possible to decorate processor
        update_wrapper(self, self.__class__, updated=())

        # Stores Typus to access it's configuration
        self.typus = typus

    def __call__(self, typus):
        raise NotImplementedError

    def __radd__(self, other):
        return self(other or tail_processor)


class EscapePhrases(BaseProcessor):
    """
    Escapes phrases which should never be processed.

    >>> en_typus('Typus turns `(c)` into "(c)"', escape_phrases=['`(c)`'])
    'Typus turns `(c)` into “©”'

    Also there is a little helper :func:`typus.utils.splinter` which should
    help you to split string into the phrases.
    """

    placeholder = '{{#phrase{0}#}}'

    def __call__(self, func):
        @wraps(self, updated=())
        def inner(text, *args, **kwargs):
            storage = []
            counter = count()
            escaped = self._save_values(text, storage, counter, **kwargs)

            # Runs typus
            processed = func(escaped, *args, **kwargs)
            if not storage:
                return processed

            restored = self._restore_values(processed, storage, **kwargs)
            return restored
        return inner

    def _save_values(self, text, storage, counter, escape_phrases=(), **kwargs):
        for phrase in escape_phrases:
            if not phrase.strip():
                continue
            key = self.placeholder.format(next(counter))
            text = text.replace(phrase, key)
            storage.append((key, phrase))
        return text

    def _restore_values(self, text, storage, **kwargs):
        """
        Puts data into the text in reversed order.
        It's important to loop over and restore text step by step
        because some 'stored' chunks may contain keys to other ones.
        """
        for key, value in reversed(storage):
            text = text.replace(key, value)
        return text


class EscapeHtml(EscapePhrases):
    """
    Extracts html tags and puts them back after.

    >>> en_typus('Typus turns <code>(c)</code> into "(c)"')
    'Typus turns <code>(c)</code> into “©”'

    .. caution::
        Doesn't support nested ``<code>`` tags.
    """

    placeholder = '{{#html{0}#}}'
    skiptags = 'head|iframe|pre|code|script|style|video|audio|canvas'
    patterns = (
        re_compile(r'(<)({0})(.*?>.*?</\2>)'.format(skiptags)),
        # Doctype, xml, closing tag, any tag
        re_compile(r'(<[\!\?/]?[a-z]+.*?>)'),
        # Comments
        re_compile(r'(<\!\-\-.*?\-\->)'),
    )

    def _save_values(self, text, storage, counter, **kwargs):
        for pattern in self.patterns:
            text = pattern.sub(self._replace(storage, counter), text)
        return text

    def _replace(self, storage, counter):
        def inner(match):
            key = self.placeholder.format(next(counter))
            html = ''.join(match.groups())
            storage.append((key, html))
            return key
        return inner


class Quotes(BaseProcessor):
    """
    Replaces regular quotes with typographic ones.
    Supports any level nesting, but doesn't work well with minutes ``1'``
    and inches ``1"`` within the quotes, that kind of cases are ignored.
    Use it with :class:`typus.mixins.RuQuotes` or
    :class:`typus.mixins.EnQuotes` or provide Typus attributes
    ``loq, roq, leq, req`` with custom quotes.

    >>> en_typus('Say "what" again!')
    'Say “what” again!'
    """

    def __init__(self, *args, **kwargs):
        super(Quotes, self).__init__(*args, **kwargs)

        # Odd and even levels: left, right
        self.loq, self.roq = self.typus.loq, self.typus.roq
        self.leq, self.req = self.typus.leq, self.typus.req

        # Pairs of odd and even quotes. Already *switched* in one dimension.
        # See :meth:`_switch_nested` for more help.
        self.switch = (self.loq + self.req, self.leq + self.roq)

        # Replaces all quotes with `'`
        quotes = ''.join((LSQUO, RSQUO, LDQUO, RDQUO, DLQUO, LAQUO, RAQUO))
        self.re_normalize = re_compile(r'[{0}]'.format(quotes))

        # Matches nested quotes (with no quotes within)
        # and replaces with odd level quotes
        self.re_normal = re_compile(
            # No words before
            r'(?<!\w)'
            # Starts with quote
            r'(["\'])'
            r'(?!\s)'
            # Everything but quote inside
            r'((?!\1).+?)'
            r'(?!\s)'
            # Ends with same quote from the beginning
            r'\1'
            # No words afterwards
            r'(?!\w)'
        )
        self.re_normal_replace = r'{0}\2{1}'.format(self.loq, self.roq)

        # Matches with typo quotes
        self.re_nested = re_compile(r'({0}|{1})'.format(self.loq, self.roq))

    def __call__(self, func):
        @wraps(self, updated=())
        def inner(text, *args, **kwargs):
            # Normalizes editor's quotes to double one
            normalized = self.re_normalize.sub('\'', text)

            # Replaces normalized quotes with first level ones, starting
            # from inner pairs, moves to sides
            nested = 0
            while True:
                normalized, replaced = self.re_normal.subn(
                    self.re_normal_replace, normalized)
                if not replaced:
                    break
                nested += 1

            # Saves some cpu :)
            # Most cases are about just one level quoting
            if nested < 2:
                return func(normalized, *args, **kwargs)

            # At this point all quotes are of odd type, have to fix it
            switched = self._switch_nested(normalized)
            return func(switched, *args, **kwargs)
        return inner

    def _switch_nested(self, text):
        """
        Switches nested quotes to another type.
        This function stored in a separate method to make possible to mock it
        in tests to make sure it doesn't called without special need.
        """

        # Stores a cycled pairs of possible quotes. Every other loop it's
        # switched to provide *next* type of a given quote
        quotes = cycle(self.switch)

        def replace(match):
            # Since only odd quotes are matched, comparison is the way to
            # choose whether it's left or right one of type should be returned.
            # As the first quote is the left one, makes negative equal which
            # return false, i.e. zero index
            return next(quotes)[match.group() != self.loq]
        return self.re_nested.sub(replace, text)


class Expressions(BaseProcessor):
    r"""
    Provides regular expressions support. Looks for ``expressions`` list
    attribute in Typus with expressions name, compiles and runs them on every
    Typus call.

    >>> from typus.core import TypusCore
    >>> from typus.processors import Expressions
    ...
    >>> class MyExpressionsMixin:
    ...     def expr_bold_price(self):
    ...         expr = (
    ...             (r'(\$\d+)', r'<b>\1</b>'),
    ...         )
    ...         return expr
    ...
    >>> class MyTypus(MyExpressionsMixin, TypusCore):
    ...     expressions = ('bold_price', )  # no prefix `expr_`!
    ...     processors = (Expressions, )
    ...
    >>> my_typus = MyTypus()  # `expr_bold_price` is compiled and stored
    >>> my_typus('Get now just for $1000!')
    'Get now just for <b>$1000</b>!'

    .. note::
        *Expression* is a pair of regex and replace strings. Regex strings are
        compiled with :func:`typus.utils.re_compile` with a bunch of flags:
        unicode, case-insensitive, etc. If that doesn't suit for you pass your
        own flags as a third member of the tuple: ``(regex, replace, re.I)``.
    """

    def __init__(self, *args, **kwargs):
        super(Expressions, self).__init__(*args, **kwargs)

        # Compiles expressions
        self.compiled_exprs = [
            (re_compile(*group[::2]), group[1])
            for name in self.typus.expressions
            for group in getattr(self.typus, 'expr_' + name)()
        ]

    def __call__(self, func):
        @wraps(self, updated=())
        def inner(text, *args, **kwargs):
            # Applies expressions
            for expr, repl in self.compiled_exprs:
                text = expr.sub(repl, text)
            text = func(text, *args, **kwargs)
            return text
        return inner
