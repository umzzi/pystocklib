from unittest import TestCase
from pystocklib.srim import srim_calculator


class Test(TestCase):
    def test_self_shares_count(self):
        # 발행주식 - 자기주식
        self.assertEqual(srim_calculator.self_shares_count(100, 30), 70.0)
        # 자기주식이 None/NaN이면 0으로 간주 → 발행주식 그대로
        self.assertEqual(srim_calculator.self_shares_count(100, None), 100.0)
        self.assertEqual(srim_calculator.self_shares_count(100, float("nan")), 100.0)
