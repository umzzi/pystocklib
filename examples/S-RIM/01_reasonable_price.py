import csv

import pystocklib.srim as srim
import pystocklib.srim.reader as srim_reader
from pystocklib.common import *
import pandas as pd
from datetime import date, datetime

# KOSPI code list
kospi = get_code_list_by_market(market=2)
kospi.to_csv("KOSPI.csv")

# KOSDAQ code list
kosdaq = get_code_list_by_market(market=3)
kosdaq.to_csv("KOSDAQ.csv")

# KOSPI+KOSDAQ
codes = pd.concat([kospi, kosdaq])

k = srim_reader.get_5years_earning_rate()

# error cases
# print(srim.estimate_price("344820", k))

code_list = list(codes.index)
# index = code_list.index("A318410")
# code_list = code_list[index: ]

now = datetime.now()
print("S_RIM calculate START :", now.strftime("%d/%m/%Y %H:%M:%S"))

today = date.today()
with open('./S-RIM_전종목_' + today.strftime("%Y%m%d") + '.txt',
          mode='w+', encoding='utf-8') as f:
    f.write("code, codeName, curPrice, 싼가?, 20%이익감소가대비, 적정주가, 10%이익 감소가, 20%이\익 감소가, ROE, 요구수익률(BBB-5년 회사채)\n")
    for i, code in enumerate(code_list):
        # print(f"{i}/{len(code_list)} {code[0]} {code[1]}", end="\t")
        # price, shares, value, net_worth, roe, excess_earning, price1, price2
        price = srim.estimate_price(code[0], k, w=0)
        roe = round(price[4], 2)
        v = ""
        if roe < k:
            # v = "ROE가 요구수익률보다 낮다. 현재만 보면 투자하면 안된다!"
            continue
        else:
            curPrice = srim_reader.get_current_price(code[0])
            cheapflag = srim_reader.compare_price(curPrice, price[7])
            if round(cheapflag[1]) > 10:
                # pp = f'{code[0]}, {code[1]}, {round(curPrice)}, {cheapflag[0]}, {cheapflag[1]}, {v}, {round(price[0],2)}, {round(price[6],2)}, {round(price[7],2)},{roe}, {k}'
                pp = f'{code[0]}, {code[1]}, {round(curPrice)}, {cheapflag[0]}, {cheapflag[1]}, {round(price[0], 2)}, {round(price[6], 2)}, {round(price[7], 2)}, {roe}, {k}'
                if (i % 10 == 0):
                    print(f'{i}/{len(code_list)},{pp}\n')
                f.write(pp)
                f.write("\n")
                f.flush()
    f.close()

now2 = datetime.now()
print("S_RIM calculate END :", now2.strftime("%d/%m/%Y %H:%M:%S"))
