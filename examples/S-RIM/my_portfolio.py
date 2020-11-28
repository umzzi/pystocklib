from datetime import date

import pandas as pd

import pystocklib.srim as srim
import pystocklib.srim.reader as srim_reader
from pystocklib.common import *

# KOSPI code list
kospi = get_code_list_by_market(market=2)
kospi.to_excel("KOSPI.xlsx")

# KOSDAQ code list
kosdaq = get_code_list_by_market(market=3)
kosdaq.to_excel("KOSDAQ.xlsx")

# KOSPI+KOSDAQ
df = pd.concat([kospi, kosdaq])

# k
k = srim_reader.get_5years_earning_rate()

'''
roe > k
현재가격이 20%이익 감소시 가격보다 싼거.
지배주주지분이 증가하는 거
시총 기준?
'''
data = []
index = 0
for acode in df.index:
    disparity, *others = srim.get_disparity(acode[0], k, w=0)
    roe = others[5]
    curPrice = others[0]
    estPrice = others[1]
    estPrice1 = others[7]
    estPrice2 = others[8]
    net_worth = others[4]
    index = index + 1

    comPrice = estPrice1

    compFlag = False
    if curPrice is not None and comPrice is not None:
        compFlag = float(curPrice) < float(comPrice)
        if estPrice1 is not None:
            estPrice1 = round(estPrice1)
        if estPrice2 is not None:
            estPrice2 = round(estPrice2)
        if others[9] is not None:
            disparity20 = round(others[9], 2)
        else:
            disparity20 = others[9]
        diff = estPrice2 - curPrice

    total_capital = 1000
    if roe > k and compFlag:
        isCr = srim_reader.get_capital_value(acode[0])
        # 지배주주지분이 증가하나?
        if isCr[0]:
            # 시총이 total_capital억 이상
            #if srim_reader.get_is_aggreagate_up(acode[0], total_capital):
                data.append(
                    {'code': acode[0], 'name': acode[1], 'curPrice': others[0], 'curPrice1': estPrice1,
                     'estPrice20%': round(estPrice2, 2),
                     'disparity20': disparity20, 'estprice2-curprice': diff,
                     'roe': roe, 'capital': isCr[1],
                     '시가총액':net_worth})
                print(index, "/", len(df.index), acode[1])

# filtering the company (ROE > k)
df = pd.DataFrame(data=data)
df = df.set_index('code')
'''
cond = df['roe'] > k
df = df[cond]
'''
# sorting
df2 = df.sort_values(by='disparity20', ascending=True)

today = date.today()
df2.to_excel("srim_hh_" + today.strftime("%Y%m%d") + ".xlsx")
