from unittest import TestCase
from pystocklib.srim import srim_calculator
from pystocklib.srim import reader_hh


class Test(TestCase):
    def test_self_shares_count(self):
        # 발행주식 - 자기주식
        self.assertEqual(srim_calculator.self_shares_count(100, 30), 70.0)
        # 자기주식이 None/NaN이면 0으로 간주 → 발행주식 그대로
        self.assertEqual(srim_calculator.self_shares_count(100, None), 100.0)
        self.assertEqual(srim_calculator.self_shares_count(100, float("nan")), 100.0)

    def test_get_roe_average_uses_five_year_weighted_average(self):
        roes = [10, 20, 30, 40, 50]
        expected = (10 * 1 + 20 * 2 + 30 * 3 + 40 * 4 + 50 * 5) / 15
        self.assertAlmostEqual(reader_hh.get_roe_average(roes), expected)

    def test_get_roe_average_counts_negative_years_as_zero(self):
        roes = [10, -20, 30, None, 50]
        expected = (10 * 1 + 0 * 2 + 30 * 3 + 0 * 4 + 50 * 5) / 15
        self.assertAlmostEqual(reader_hh.get_roe_average(roes), expected)

    def test_get_srim_disparity_is_positive_when_est_price_is_above_current_price(self):
        disparity, _, _, est_price, _, _ = srim_calculator.get_srim_disparity(
            cur_price=100,
            net_worth=1000,
            roe=20,
            k=10,
            total_shares=10,
            self_hold_shares=0,
            w=1,
        )
        self.assertEqual(est_price, 200)
        self.assertEqual(disparity, 100.0)
