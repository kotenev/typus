# coding: utf-8

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from builtins import *  # noqa

import unittest2
from typus import en_typus, ru_typus
from typus.chars import *  # noqa
from typus.mixins import EnRuExpressions

from tests.test_mixins import EnRuExpressionsTestCommon


class SummaryTest(unittest2.TestCase, EnRuExpressionsTestCommon):
    maxDiff = None

    def typus(self, *args):
        def testcase(text, test, debug=False):
            return self.assertEqual(ru_typus(text, debug), test)
        return testcase

    def test_debug(self):
        test = self.typus()
        test('1m', '1_m', debug=True)

    def test_quotes(self):
        test = self.typus()
        test('00 "11" 00', '00 «11» 00')
        test('''00" "11 '22' 11"? "11 '22 "33 33?"' 11" 00 "11 '22' 11" 0"''',
             '00{1} «11 „22“ 11»? «11 „22 «33{0}33?»“ 11» 00 «11 „22“ 11» 0{1}'
             .format(NBSP, DPRIME))  # clashes with digit_spaces

    def test_mdash(self):
        test = super(SummaryTest, self).test_mdash()
        test('foo - "11" 00', 'foo{0}«11» 00'.format(MDASH_PAIR))
        test('2 - 2foo', '2{0}2{1}foo'.format(MDASH_PAIR, NBSP))  # + units
        test('2 - 2', '2{0}{1}{0}2'.format(NBSP, MINUS))  # + minus
        test('Winnie-the-Pooh', 'Winnie-the-Pooh')

    def test_primes(self):
        test = super(SummaryTest, self).test_primes()
        test('"4"', '«4»')

    def test_phones(self):
        test = super(SummaryTest, self).test_phones()
        test('55-555', '55{0}555'.format(MDASH))  # + range

    def test_ranges(self):
        test = super(SummaryTest, self).test_ranges()
        test('2-3 foo', '2{1}3{0}foo'.format(NBSP, MDASH))  # + ranges
        test('(15-20 items)', '(15{1}20{0}items)'.format(NBSP, MDASH))

        # Float
        test('0,5-3', '0,5{0}3'.format(MDASH))
        test('-0,5-3', '{1}0,5{0}3'.format(MDASH, MINUS))
        test('-5.5-3', '{1}5.5{0}3'.format(MDASH, MINUS))
        test('-5,5-3', '{1}5,5{0}3'.format(MDASH, MINUS))
        test('-5,5-3.5', '{1}5,5{0}3.5'.format(MDASH, MINUS))

        # Fails to math
        test('2 - 3', '2{0}{1}{0}3'.format(NBSP, MINUS))
        test('2-3 x 4', '2{1}3{0}{2}{0}4'.format(NBSP, MINUS, TIMES))
        test('2-3 * 4', '2{1}3{0}{2}{0}4'.format(NBSP, MINUS, TIMES))
        test('2-3 - 4', '2{1}3{0}{1}{0}4'.format(NBSP, MINUS))

    def test_math(self):
        test = self.typus()
        for options, result in EnRuExpressions.math.items():
            for option in options:
                # -3, 3-3, 3 - 3, x - 3
                if result == MINUS:
                    # This one clashes with range
                    test('2{0}3'.format(option), '2{0}3'.format(MDASH))
                    # This one clashes with mdash
                    test('x{0}{1}{0}3'.format(NBSP, option),
                         'x{0}{1} 3'.format(NBSP, MDASH))
                else:
                    test('2{0}3'.format(option), '2{0}3'.format(result))
                    test('x{0}{1}{0}3'.format(NBSP, option),
                         'x{0}{1}{0}3'.format(NBSP, result))

                test(option + '3', result + '3')
                test('3{0}{1}{0}2'.format(NBSP, option),
                     '3{0}{1}{0}2'.format(NBSP, result))

    def test_pairs(self):
        test = super(SummaryTest, self).test_pairs()
        test('aaa 2a', 'aaa 2{0}a'.format(NBSP))  # clashes with units

    def test_digit_spaces(self):
        test = super(SummaryTest, self).test_digit_spaces()
        test('4444444 foo', '4444444{0}foo'.format(NBSP))  # + untis
        test('444 -', '444{0}{1}'.format(NBSP, MDASH))

    def test_example(self):
        test = self.typus()
        text = (
            'Излучение, как следует из вышесказанного, концентрирует '
            'внутримолекулярный предмет - деятельности . "...ff \'Можно?\' '
            'предположить, что силовое - "поле "мент "d" ально" отклоняет" '
            'сенсибельный \'квазар !..\' cc", не учитывая мнения авторитетов. '
            'Искусство испускает данный электрон, учитывая опасность, '
            '<code> "d" test -- test(c)</code> которую    представляли '
            'собой писания Дюринга для не окрепшего еще немецкого рабочего '
            'движения. Смысл жизни -- амбивалентно (с) дискредитирует '
            'закон (r) исключённого(tm) третьего (тм)...      \n\n\n'
            '- Химическое соединение (p) ненаблюдаемо контролирует экран-ый '
            'квазар (р). Идеи 3/4  гедонизма занимают b & b центральное место '
            'в утилитаризме(sm) "Милля и Бентама", однако <- гравитирующая -> '
            'сфера масштабирует фотон, +-2мм изменяя привычную == реальность. '
            'Силовое *3 поле -3 реально 3 * 2 /= 6   3x3 восстанавливает '
            'трансцендентальный 3" 2\' принцип 1000р. восприятия.'
            '"...\'test\'" (c) m&m\'s\n\n\n'
        )
        result = (
            'Излучение, как следует из_вышесказанного, концентрирует '
            'внутримолекулярный предмет_— деятельности. «…ff „Можно?“ '
            'предположить, что силовое_— „поле «мент „d“ ально» отклоняет“ '
            'сенсибельный „квазар!..“ cc», не_учитывая мнения авторитетов. '
            'Искусство испускает данный электрон, учитывая опасность, '
            '<code> "d" test -- test(c)</code> которую представляли собой '
            'писания Дюринга для не_окрепшего еще немецкого рабочего '
            'движения. Смысл жизни_— амбивалентно ©_дискредитирует закон® '
            'исключённого™ третьего™…\n\n'
            '—_Химическое соединение℗ ненаблюдаемо контролирует экран-ый '
            'квазар℗. Идеи ¾_гедонизма занимают b_&_b_центральное место '
            'в_утилитаризме℠ «Милля и_Бентама», однако ←_гравитирующая_→ '
            'сфера масштабирует фотон, ±2_мм изменяя привычную_≡_реальность. '
            'Силовое ×3_поле −3_реально 3_×_2_≠_6 3×3 восстанавливает '
            'трансцендентальный 3″ 2′ принцип 1000_₽ восприятия.'
            '«…„test“» ©_m&m’s'
        ).replace('_', NBSP)
        test(text, result)


class SummaryTest2(SummaryTest):
    def typus(self, *args):
        def testcase(text, test, debug=False):
            test = (test.replace(ru_typus.leq, en_typus.leq)
                        .replace(ru_typus.req, en_typus.req)
                        .replace(ru_typus.loq, en_typus.loq)
                        .replace(ru_typus.roq, en_typus.roq))
            self.assertEqual(en_typus(text, debug), test)
        return testcase
