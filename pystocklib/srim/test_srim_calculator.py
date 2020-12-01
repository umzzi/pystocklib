from unittest import TestCase
import pystocklib.srim.reader as reader
from pystocklib.srim import srim_calculator


class Test(TestCase):
    def test_self_shares_count(self):
        srim_calculator.self_shares_count(111)
        self.fail()


