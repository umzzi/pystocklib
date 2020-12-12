import numbers
import sys

import pystocklib.srim.reader_hh as hh_reader
import pandas as pd

# ret = srim_reader.get_shares("014440")
# print(ret)

# pegr 구하기
from pystocklib.srim import srim_calculator
from pystocklib.srim.reader import get_5years_earning_rate
from pystocklib.srim.srim_calculator import cal_geometric_avg, get_pegr_value

code = "A005930"
df = pd.read_html(hh_reader.get_html_fnguide(code, gb=2))
eps_incr_ratio = df[0].values

df2 = pd.read_html(hh_reader.get_html_fnguide(code, gb=0))
stock = df2[8].values
cur_per = stock[4][1]
print(df2[7].values)

eps = hh_reader.get_financial_highlight(eps_incr_ratio[13], 4)

# print(isinstance(5, numbers.Number))

# eps = [24.5,98.2,11.1, -47.5, 20.7]
# print(eps)
pegr, epsavg = srim_calculator.get_pegr_value(eps, cur_per)
# print(cur_per)
# print("pegr:",pegr)
# print(epsavg)

price = ""
if price is not None and bool(price):
    print(int(float(price)))

# cf = pd.read_html(hh_reader.get_html_fnguide(code, gb=4))
# print(cf)

print(sys.argv[1])
print(sys.argv[2])
print(sys.argv[3])

# eps2 = [3479.0, 2088.0, 2643.0, 3364.0]
eps2 = [5421.0, 6024.0, 3166.0, 4067.0]

eps_incr_percent, eps_geo_avg, eps_incre_level = hh_reader.calculate_eps(eps2)
print(srim_calculator.calculate_pegr(eps_geo_avg, 1.0))
print(eps_incr_percent)

k = get_5years_earning_rate()
print(k)