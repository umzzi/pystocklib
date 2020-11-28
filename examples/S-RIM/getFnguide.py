from pystocklib.common import *
from datetime import date

import pandas as pd
import pystocklib.srim.reader as srim_reader
import pystocklib.srim.reader_hh as hh_reader
import pystocklib.srim.srim_calculator as srim_calculator

# KOSPI code list
from pystocklib.srim import reader_hh

kospi = get_code_list_by_market(market=2)
kospi.to_excel("KOSPI.xlsx")

# KOSDAQ code list
kosdaq = get_code_list_by_market(market=3)
kosdaq.to_excel("KOSDAQ.xlsx")

# KOSPI+KOSDAQ
mdf = pd.concat([kospi, kosdaq])

# k
k = srim_reader.get_5years_earning_rate()

i = 0
data = []
for acode in mdf.index:
    # if i == 5: break
    code = acode[0]
    ticker = acode[1]
    i = i + 1
    print(f'{i}/{len(mdf.index)}:{code}:{ticker}')

    df = pd.read_html(reader_hh.get_html_fnguide(code, gb=0))

    price = df[0][1][0]
    if price is not None:
        cur_price = price.split("/")[0]
        cur_price = cur_price.replace(",", "")
        cur_price = float(cur_price)
    else:
        cur_price = 0

    shares = df[0][1][6]
    if shares is not None:
        total_shares = shares.split("/")[0]
        total_shares = total_shares.replace(",", "")
    else:
        total_shares = 0

    stock = df[8].values
    jasa = df[4].values
    self_hold_shares = jasa[4][2]
    jemu = df[10].values

    # 시가총액
    market_capital = stock[0][1]

    # 4년 ROE
    roes = reader_hh.get_financial_highlight(jemu[17])
    rep_roe = reader_hh.get_roe_average(roes)
    # 4년 PER
    pers = reader_hh.get_financial_highlight(jemu[21])
    # 4년 PBR
    pbrs = reader_hh.get_financial_highlight(jemu[22])

    if rep_roe < k:
        # print(f'{index}:{ticker} : 평균 roe가 요구 수익률보다 낮다')
        continue

    # 시가 총액이 얼마이상인가?
    '''
    std_capital = 1000
    isCapBigger = reader_hh.is_capital_up(market_capital, std_capital)
    if not isCapBigger:
        print(f'{index}:{ticker} : 시가총액이 {market_capital}, {std_capital}억보다 작다')
        continue
'''
    # 4년 지배주주자본
    capital = reader_hh.get_financial_highlight(jemu[9])
    isCr = reader_hh.is_capital_increment(capital)
    if not isCr:
        # print(f'{index}:{ticker} : 자기자본이 늘고 있지 않다.')
        continue

    net_worth = capital[2]
    if net_worth is not None:
        net_worth = net_worth * 100000000
    else:
        net_worth = 0

    # cur_price, net_worth, roe, k, total_shares, self_total_shares, w=1
    disparity, *others = srim_calculator.get_srim_disparity(cur_price, net_worth, rep_roe, k,
                                                            total_shares, self_hold_shares, w=0)

    prices = [others[2], others[3], others[4]]
    price_level = srim_calculator.get_price_level(cur_price, prices)

    data.append(
        {
            'code': code,
            'name': ticker,
            'price': cur_price,
            'rep_roe': round(rep_roe, 2),
            'est_level': price_level,
            'est_price': prices[0], 'disparity': disparity,
            'est_price1': prices[1], 'disparity1': others[0],
            'est_price2': prices[2], 'disparity2': others[1],
            stock[0][0]: stock[0][1],  # 시가총액
            stock[1][0]: stock[1][1],  # 매출익
            stock[2][0]: stock[2][1],  # 영업이익
            stock[3][0]: stock[3][1],  # EPS
            stock[7][0]: stock[7][1],  # 배당수익
            jasa[0][0]: jasa[0][3],  # 최대주주지분율
            jasa[4][0]: self_hold_shares,  # 자사주수
            jemu[9][0]: capital,  # 지배주주지분
            jemu[17][0]: roes,
            jemu[21][0]: pers
        }
    )




if i > 0:
    df = pd.DataFrame(data=data)
    df = df.set_index('code','name')
    # sorting
    df2 = df.sort_values(by='est_level', ascending=False)

    today = date.today()
    df2.to_excel("srim_hh_" + today.strftime("%Y%m%d") + ".xlsx")
    df2.to_csv("srim_hh_" + today.strftime("%Y%m%d") + ".csv")
