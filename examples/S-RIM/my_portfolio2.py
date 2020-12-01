from pystocklib.common import *
import pystocklib.srim as srim
import pystocklib.srim.reader as srim_reader
import time
import pandas as pd
from datetime import date, datetime

code_list = [
#     ["357780" ,"솔브레인"],
#     ["011170", "롯데케미칼"],
#              ["097950","CJ제일제당"],
#             ["069960","현대백화점"],
#              ["017670","SK텔레콤"],
#              ["009150","삼성전기"],
#              ["012630", "HDC"],
# ["078340","컴투스"],
# ["035900", "JYP Ent."],
# ["001680","대상"],
# ["009810",""],
# ["238490","힘스"],
["005930", "삼성전자"],
["078340", "컴투스"],
["004170", "신세계"],
["000660", "SK하이닉스"]
]
# k
k = srim_reader.get_5years_earning_rate()

'''
roe > k
현재가격이 20%이익 감소시 가격보다 싼거.
지배주주지분이 증가하는 거
시총이 2000억 이상인거
'''
data = []
for acode in code_list:
    disparity, *others = srim.get_disparity(acode[0], k, w=0)
    if disparity is None:
        continue
    else:
        roe = others[5]
        curPrice = others[0]
        estPrice = others[1]
        estPrice1 = others[7]
        estPrice2 = others[8]
        print(roe)
        print(curPrice)
        print(estPrice)

    compFlag = False
    if curPrice is not None :
        compFlag = float(curPrice) < float(estPrice)
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
            # 시총이 total_capital 억 이상?
            #if srim_reader.get_is_aggreagate_up(acode[0],total_capital):
                data.append({'code': acode[0], 'name': acode[1], 'curPrice': others[0], 'estPrice20%': estPrice2,
                             'disparity20': disparity20, 'roe': roe, 'capital': isCr[1]})

# filtering the company (ROE > k)
df = pd.DataFrame(data=data)
df = df.set_index('code')
'''
cond = df['roe'] > k
df = df[cond]
'''
# sorting
df2 = df.sort_values(by='disparity20', ascending=False)

today = date.today()
df2.to_excel("srim_hh2_"+ today.strftime("%Y%m%d") + ".xlsx")

print(df2)
