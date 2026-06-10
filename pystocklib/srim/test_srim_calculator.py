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
        # 양수해 중앙값 30 × 2 = 60 상한, 어느 해도 안 걸림 → 그대로 가중평균
        expected = (10 * 1 + 20 * 2 + 30 * 3 + 40 * 4 + 50 * 5) / 15
        self.assertAlmostEqual(reader_hh.get_roe_average(roes), expected)

    def test_get_roe_average_reflects_negative_years_as_is(self):
        # 음수 해는 0으로 가리지 않고 그대로 반영, 결측(None)은 분자/분모에서 제외
        roes = [10, -20, 30, None, 50]
        vals = [10, -20, 30, 50]  # None 제외, 음수 유지 (스파이크 상한 60에 안 걸림)
        expected = (10 * 1 + -20 * 2 + 30 * 3 + 50 * 4) / (1 + 2 + 3 + 4)
        self.assertAlmostEqual(reader_hh.get_roe_average(roes), expected)

    def test_get_roe_average_dampens_one_off_spike(self):
        # 최근 단년 급등(100)은 양수해 중앙값(10)의 2배=20으로 완충
        roes = [10, 10, 10, 10, 100]
        expected = (10 * 1 + 10 * 2 + 10 * 3 + 10 * 4 + 20 * 5) / 15
        self.assertAlmostEqual(reader_hh.get_roe_average(roes), expected)

    def test_get_roe_average_skips_nan_in_denominator(self):
        roes = [20, float("nan"), 40]
        expected = (20 * 1 + 40 * 2) / (1 + 2)
        self.assertAlmostEqual(reader_hh.get_roe_average(roes), expected)

    def test_has_recent_loss(self):
        self.assertTrue(reader_hh.has_recent_loss([10, 20, -5]))        # 최근 적자
        self.assertFalse(reader_hh.has_recent_loss([10, -5, 20]))       # 과거만 적자
        self.assertFalse(reader_hh.has_recent_loss([10, 20, float("nan")]))  # 최근 유효값 20
        self.assertFalse(reader_hh.has_recent_loss([]))

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
