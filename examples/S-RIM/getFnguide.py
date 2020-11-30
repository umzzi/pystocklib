from pystocklib.common import *
from datetime import date
import time

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
dividend = []
for acode in mdf.index:
    if i == 10: break
    code = acode[0]
    ticker = acode[1]
    i = i + 1
    if i % 100 == 0 :
        print(f'{i}/{len(mdf.index)}:{code}:{ticker}')
        time.sleep(0.5)

    df = pd.read_html(reader_hh.get_html_fnguide(code, gb=0))


    #현재종가
    price = srim_calculator.parsing_string_sep(df[0][1][0], "/", 0)
    cur_price = srim_calculator.won_convert_to_float(price)

    #발행주수
    shares = srim_calculator.parsing_string_sep(df[0][1][6], "/", 0)
    total_shares = srim_calculator.won_convert_to_float(shares)

    #거래량
    trading_cnt = srim_calculator.won_convert_to_float(df[0][3][0])

    stock = df[8].values
    jasa = df[4].values
    self_hold_shares = jasa[4][2]
    jemu = df[10].values

    # 시가총액
    market_capital = stock[0][1]

    # 수정주가PER
    is_cheaper_per = srim_calculator.is_per_compare_sector(stock[4][1], stock[4][2])

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

    #영업 이익률이 증가하나?

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

    naver_url = "https://finance.naver.com/item/coinfo.nhn?code="+code.replace("A","")
    link = '=HYPERLINK("' + naver_url + '", "'+code+'")'
    consen_url = "http://comp.fnguide.com/SVO2/ASP/SVD_Consensus.asp?pGB=1&gicode="+code+"&cID=&MenuYn=Y&ReportGB=&NewMenuID=108&stkGb=701"
    consen_link = '=HYPERLINK("' + consen_url + '", "'+ticker+'")'
    if price_level > 0:
        data.append(
            {
                'code': link,
                'name': consen_link,
                'link': link,
                'est_level': price_level,
                'price': cur_price,
                'est_price': prices[0],
                'est_price1': prices[1],
                'est_price2': prices[2],
                'disparity2': others[1],
                'rep_roe': round(rep_roe, 2),
                ' < 동종업계per': is_cheaper_per,
                'disparity': disparity,
                'disparity1': others[0],
                stock[0][0]: stock[0][1],  # 시가총액
                '거래량': trading_cnt,
                '지배주주자본': capital,  # 지배주주지분
                "최대주주지분율": jasa[0][3],  # 최대주주지분율
                jemu[17][0]: roes,
                jemu[21][0]: pers,
                stock[1][0]: stock[1][1],  # 매출익
                stock[2][0]: stock[2][1],  # 영업이익
                stock[3][0]: stock[3][1],  # EPS
                "자기주식수": self_hold_shares,  # 자사주수
                stock[7][0]: stock[7][1],  # 배당수익
            }
        )

        #배당주 찾기
        #최대주주지분이 50%이상 이고 배당이 있는 주식.
        is_dividend = srim_calculator.make_dividend_stock(jasa[0][3], stock[7][1])
        if is_dividend :
            dividend.append(
                {
                    'code': code,
                    'name': ticker,
                    'link': link,
                    'est_level': price_level,
                    'price': cur_price,
                    'est_price': prices[0],
                    'est_price1': prices[1],
                    'est_price2': prices[2],
                    'disparity2': others[1],
                    'rep_roe': round(rep_roe, 2),
                    ' < 동종업계per': is_cheaper_per,
                    'disparity': disparity,
                    'disparity1': others[0],
                    '시가총액(억)': stock[0][1],  # 시가총액
                    '거래량': trading_cnt,
                    '지배주주자본': capital,  # 지배주주지분
                    "최대주주지분율": jasa[0][3],  # 최대주주지분율
                    jemu[17][0]: roes,
                    jemu[21][0]: pers,
                    stock[1][0]: stock[1][1],  # 매출익
                    stock[2][0]: stock[2][1],  # 영업이익
                    stock[3][0]: stock[3][1],  # EPS
                    "자기주식수": self_hold_shares,  # 자사주수
                    stock[7][0]: stock[7][1],  # 배당수익
                }
            )

if i > 0:
    df = pd.DataFrame(data=data)
    df = df.set_index('code','name')
    # sorting
    df2 = df.sort_values(by='est_level', ascending=False)

    dd = pd.DataFrame(data=dividend)
    dd = dd.set_index('code','name')
    dd2 = dd.sort_values(by='배당수익률', ascending=False)

    today = date.today()
    filename = "./srim_hh_" + today.strftime("%Y%m%d") + ".xlsx"

    with pd.ExcelWriter(filename ,engine="xlsxwriter") as writer:
        df2.to_excel(writer, sheet_name="rim", startrow=1, header=False)
        dd2.to_excel(writer, sheet_name="dividend")

        workbook  = writer.book
        worksheet = writer.sheets['rim']
        worksheet2 = writer.sheets['dividend']

        # Add a header format.
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1})

        # Write the column headers with the defined format.
        for col_num, value in enumerate(df2.columns.values):
            worksheet.write(0, col_num + 1, value, header_format)
            worksheet2.write(0, col_num + 1, value, header_format)

        # Close the Pandas Excel writer and output the Excel file.
        # writer.save()


