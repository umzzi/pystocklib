import sys

from pystocklib.common import *
from datetime import date
import time

import pandas as pd
import pystocklib.srim.reader as srim_reader
import pystocklib.srim.reader_hh as hh_reader
import pystocklib.srim.srim_calculator as srim_calculator

# KOSPI code list
from pystocklib.srim import reader_hh

input_data = [
    {'cd': srim_reader.make_acode("035420"), 'nm': 'naver'},
    {'cd': srim_reader.make_acode("005930"), 'nm': '삼성전자'},
    {'cd': srim_reader.make_acode("272210"), 'nm': '한화시스'},
    {'cd': srim_reader.make_acode("288620"), 'nm': '에스퓨얼'},
    {'cd': srim_reader.make_acode("112610"), 'nm': '씨에스윈'},
    {'cd': srim_reader.make_acode("298050"), 'nm': '효성첨단소'},
    {'cd': srim_reader.make_acode("089980"), 'nm': '상아프론테'},
    {'cd': srim_reader.make_acode("003670"), 'nm': '포스코케미칼'},
    {'cd': srim_reader.make_acode("078600"), 'nm': '대주전자재료'},
    {'cd': srim_reader.make_acode("278280"), 'nm': '천보'},
    {'cd': srim_reader.make_acode("247540"), 'nm': '에코프로비엠'},
    {'cd': srim_reader.make_acode("122990"), 'nm': '와이솔'},
    {'cd': srim_reader.make_acode("009150"), 'nm': '삼성전기'},
    {'cd': srim_reader.make_acode("232140"), 'nm': '와이아이케이'},
    {'cd': srim_reader.make_acode("078600"), 'nm': '대주전자재료'},
    {'cd': srim_reader.make_acode("222800"), 'nm': '심텍'},
    {'cd': srim_reader.make_acode("319660"), 'nm': '피에스케이'},
    {'cd': srim_reader.make_acode("012330"), 'nm': '현대모비스'},
    {'cd': srim_reader.make_acode("005380"), 'nm': '현대차'},
    {'cd': srim_reader.make_acode("000270"), 'nm': '기아차'},
    {'cd': srim_reader.make_acode("204320"), 'nm': '만도'},
    {'cd': srim_reader.make_acode("060250"), 'nm': '엔에치엔사이버결제'},
    {'cd': srim_reader.make_acode("035720"), 'nm': '카카오'},
    {'cd': srim_reader.make_acode("012510"), 'nm': '더존비즈온'},
    {'cd': srim_reader.make_acode("272210"), 'nm': '한화시스템'},
    {'cd': srim_reader.make_acode("022100"), 'nm': '포스코아이씨'},
    {'cd': srim_reader.make_acode("018260"), 'nm': '삼성에스디에스'},
    {'cd': srim_reader.make_acode("243070"), 'nm': '휴온스'},
    {'cd': srim_reader.make_acode("216080"), 'nm': '제테마'},
    {'cd': srim_reader.make_acode("214150"), 'nm': '클래시스'},
    {'cd': srim_reader.make_acode("214450"), 'nm': '파마리서치프로덕트'},
    {'cd': srim_reader.make_acode("194700"), 'nm': '노바렉스'},
    {'cd': srim_reader.make_acode("008490"), 'nm': '서흥'},
    {'cd': srim_reader.make_acode("020760"), 'nm': '일진디스플'},
    {'cd': srim_reader.make_acode("046890"), 'nm': '서울반도체'},
    {'cd': srim_reader.make_acode("363280"), 'nm': '티와이홀딩스'},
    {'cd': srim_reader.make_acode("010780"), 'nm': '아이에스동서'},
    {'cd': srim_reader.make_acode("067900"), 'nm': '와이엔텍'},
    {'cd': srim_reader.make_acode("017810"), 'nm': '풀무원'},
    {'cd': srim_reader.make_acode("035900"), 'nm': '제이와이피'},
    {'cd': srim_reader.make_acode("053030"), 'nm': '바이넥스'},
    {'cd': srim_reader.make_acode("237690"), 'nm': '에스티팜'},
]
inframe = pd.DataFrame(input_data)
inframe = inframe.set_index(['cd', 'nm'])

# execute option
# defalt: TRUE TRUE FALSE
# argv[1] ROE > K
# argv[2] isCaptial increase
# argv[3] 원하는 리스트만 체크할 것인지

roeCheck = sys.argv[1]
capitalCheck = sys.argv[2]
inputCheck = sys.argv[3]

# KOSPI code list
kospi = get_code_list_by_market(market=2)
kospi.to_excel("KOSPI.xlsx")

# KOSDAQ code list
kosdaq = get_code_list_by_market(market=3)
kosdaq.to_excel("KOSDAQ.xlsx")

# KOSPI+KOSDAQ
if inputCheck == "TRUE":
    mdf = pd.concat([inframe])
else:
    mdf = pd.concat([kospi, kosdaq])

# k
k = srim_reader.get_5years_earning_rate()

index = 0
data = []
dividend = []
for acode in mdf.index:
    # if index == 100: break
    code = acode[0]
    ticker = acode[1]
    index = index + 1
    if index % 100 == 0:
        print(f'{index}/{len(mdf.index)}:{code}:{ticker}')
        time.sleep(1)

    try :
         df = pd.read_html(hh_reader.get_html_fnguide(code, gb=0))
    except:
        print(f'{index}/{len(mdf.index)}:{code}:{ticker}')
        continue

    # 현재종가
    price = srim_calculator.parsing_string_sep(df[0][1][0], "/", 0)
    cur_price = srim_calculator.won_convert_to_float(price)

    # 발행주수
    shares = srim_calculator.parsing_string_sep(df[0][1][6], "/", 0)
    total_shares = srim_calculator.won_convert_to_float(shares)

    # 거래량
    trading_cnt = srim_calculator.won_convert_to_float(df[0][3][0])

    if df.__sizeof__() < 200:
        print(f'{ticker}:{df.__sizeof__()} : 정보가 충분하지 않다.')
        continue

    stock = df[8].values
    jasa = df[4].values
    self_hold_shares = jasa[4][2]
    jemu = df[10].values

    # Financial Highlight 표의 행을 '라벨'로 찾는다(위치 인덱스 밀림에 강건).
    # 못 찾으면 기존 위치 인덱스로 폴백하여 동작을 보존한다.
    roe_row = reader_hh.get_row_by_label(jemu, 'ROE', 17)
    eps_row = reader_hh.get_row_by_label(jemu, 'EPS(원)', 18)
    per_row = reader_hh.get_row_by_label(jemu, 'PER', 21)
    pbr_row = reader_hh.get_row_by_label(jemu, 'PBR', 22)
    capital_row = reader_hh.get_row_by_label(jemu, '지배주주지분', 9)

    # 자본잠식 종목은 ROE가 비정상값으로 튀어 적정주가가 왜곡 → S-RIM 제외
    if not reader_hh.is_roe_reliable(roe_row):
        # print(f'{index}:{ticker} : 자본잠식 → S-RIM 제외')
        continue

    # 시가총액
    market_capital = stock[0][1]

    # 수정주가PER
    cur_per = stock[4][1]
    is_cheaper_per = srim_calculator.is_per_compare_sector(cur_per, stock[4][2])

    # 5년 ROE 가중평균. FnGuide가 제공하는 값이 5개보다 적으면 가능한 범위만 사용한다.
    roes = reader_hh.get_financial_highlight(roe_row, reader_hh.DEFAULT_ROE_YEARS)
    rep_roe = reader_hh.get_roe_average(roes)

    # 가장 최근 해가 적자(음수 ROE)면 S-RIM 전제(안정적 초과수익)가 깨짐 → 제외
    if roeCheck == "TRUE" and reader_hh.has_recent_loss(roes):
        # print(f'{index}:{ticker} : 최근 해 적자 → S-RIM 제외')
        continue

    # 4년 EPS
    epslist = reader_hh.get_financial_highlight(eps_row)
    # eps 증가율 구하기

    # 4년 PER
    pers = reader_hh.get_financial_highlight(per_row)

    # 4년 PBR
    pbrs = reader_hh.get_financial_highlight(pbr_row)
    if roeCheck == "TRUE" and rep_roe < k:
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
    capital = reader_hh.get_financial_highlight(capital_row)
    # 지배주주지분이 최근 어느 해라도 (-)/0 이면 자본잠식 이력 → S-RIM 적용 불가
    if not reader_hh.is_equity_positive(capital):
        # print(f'{index}:{ticker} : 자본잠식 이력 → S-RIM 제외')
        continue
    isCr = reader_hh.is_capital_increment(capital)
    if capitalCheck == "TRUE" and not isCr:
        # print(f'{index}:{ticker} : 자기자본이 늘고 있지 않다.')
        continue

    # 영업 이익률이 증가하나?

    net_worth = capital[2]
    if net_worth is not None:
        net_worth = net_worth * 100000000
    else:
        net_worth = 0

    # cur_price, net_worth, roe, k, total_shares, self_total_shares, w=1
    disparity, *others = srim_calculator.get_srim_disparity(cur_price, net_worth, rep_roe, k,
                                                            total_shares, self_hold_shares, w=0)

    # 상승여력이 비현실적으로 크면 단년 ROE 왜곡 등으로 적정가 과대추정 → 제외
    try:
        if float(disparity) > reader_hh.DISPARITY_MAX:
            # print(f'{index}:{ticker} : 상승여력 {disparity}% > {reader_hh.DISPARITY_MAX} → 과대추정 제외')
            continue
    except (TypeError, ValueError):
        pass

    prices = [others[2], others[3], others[4]]
    price_level = srim_calculator.get_price_level(cur_price, prices)

    # fnguide 재무비율 페이지의 EPS증가율 가져오기
    try:
        gf = pd.read_html(hh_reader.get_html_fnguide(code, gb=2))
    except:
        print(f'{index}/{len(mdf.index)}:{code}:{ticker} (gb=2 skip)')
        continue
    eps_incr_ratio = gf[0].values
    pegr = 0
    eps = []
    recent_eps = ""
    if eps_incr_ratio is not None and len(eps_incr_ratio) > 13:
        eps = hh_reader.get_financial_highlight(eps_incr_ratio[13], 5)
        pegr, epsavg = srim_calculator.get_pegr_value(eps, cur_per)
        recent_eps = eps[-1]

    # eps값으로 계산
    eps_incr_percent, eps_geo_avg, eps_incre_level = hh_reader.calculate_eps(epslist)
    pegr = srim_calculator.calculate_pegr(eps_geo_avg, cur_per)

    naver_url = "https://stock.naver.com/domestic/stock/" + code.replace("A", "")
    link = '=HYPERLINK("' + naver_url + '", "' + code + '")'
    consen_url = "http://comp.fnguide.com/SVO2/ASP/SVD_Consensus.asp?pGB=1&gicode=" + code + "&cID=&MenuYn=Y&ReportGB=&NewMenuID=108&stkGb=701"
    consen_link = '=HYPERLINK("' + consen_url + '", "' + ticker + '")'

    # TODO
    # code, est_price, est_price1, est_price2, last_date db에 업데이트 하기.
    if price_level > 0:
        data.append(
            {
                'code': code,
                'name': ticker,
                'naverlink': link,
                'fnlink': consen_link,
                'est_level': price_level,
                'price': cur_price,
                'pegr': pegr,
                'cur_per': cur_per,
                'est_price': prices[0],
                'est_price1': prices[1],
                'est_price2': prices[2],
                'disparity': disparity,
                'disparity1': others[0],
                'disparity2': others[1],
                'rep_roe': round(rep_roe, 2),
                'is_cheap_comp_per': is_cheaper_per,  # 동종업계 per보다 싼가
                'eps_level': eps_incre_level,  # eps 증가추세에 따른 레벨 부여
                'eps': stock[3][1],  # EPS,
                'eps_expect': epslist[-1],
                'eps_expect_this_year_ratio': eps_incr_percent[-1],  # eps올해예상증가
                'eps_list': epslist,
                'eps증가율': eps_incr_percent,
                'eps증가율기하평균': eps_geo_avg,
                'EPS최근증가율': recent_eps,
                'EPS증가율_ORG': eps,
                'EPS증가율_AVG': epsavg,
                'market_cap': stock[0][1],  # 시가총액
                'trading_cnt': trading_cnt,  # 거래량
                '지배주주자본': capital,  # 지배주주지분
                "최대주주지분율": jasa[0][3],  # 최대주주지분율
                roe_row[0]: roes,
                per_row[0]: pers,
                stock[1][0]: stock[1][1],  # 매출익
                stock[2][0]: stock[2][1],  # 영업이익
                "자기주식수": self_hold_shares,  # 자사주수
                stock[7][0]: stock[7][1],  # 배당수익
                isCr: isCr  # 자기자본이 계속 늘고있나.
            }
        )

        # 배당주 찾기
        # 최대주주지분이 50%이상 이고 배당이 있는 주식.
        is_dividend = srim_calculator.make_dividend_stock(jasa[0][3], stock[7][1])
        if is_dividend:
            dividend.append(
                {
                    'code': code,
                    'name': ticker,
                    'naverlink': link,
                    'fnlink': consen_link,
                    'est_level': price_level,
                    'price': cur_price,
                    'pegr': pegr,
                    'cur_per': cur_per,
                    'est_price': prices[0],
                    'est_price1': prices[1],
                    'est_price2': prices[2],
                    'disparity': disparity,
                    'disparity1': others[0],
                    'disparity2': others[1],
                    'rep_roe': round(rep_roe, 2),
                    'is_cheap_comp_per': is_cheaper_per,  # 동종업계 per보다 싼가
                    'eps_level': eps_incre_level,  # eps 증가추세에 따른 레벨 부여
                    'eps': stock[3][1],  # EPS,
                    'eps_expect': epslist[-1],
                    'eps_expect_this_year_ratio': eps_incr_percent[-1],  # eps올해예상증가
                    'eps_list': epslist,
                    'eps증가율': eps_incr_percent,
                    'eps증가율기하평균': eps_geo_avg,
                    'EPS최근증가율': recent_eps,
                    'EPS증가율_ORG': eps,
                    'EPS증가율_AVG': epsavg,
                    'market_cap': stock[0][1],  # 시가총액(억)
                    'trading_cnt': trading_cnt,  # 거래량
                    '지배주주자본': capital,  # 지배주주지분
                    "최대주주지분율": jasa[0][3],  # 최대주주지분율
                    roe_row[0]: roes,
                    per_row[0]: pers,
                    stock[1][0]: stock[1][1],  # 매출익
                    stock[2][0]: stock[2][1],  # 영업이익
                    "자기주식수": self_hold_shares,  # 자사주수
                    stock[7][0]: stock[7][1],  # 배당수익
                    isCr: isCr  # 자기자본이 계속 늘고있나.
                }
            )

if index > 0:
    df = pd.DataFrame(data=data)
    df = df.set_index('code')

    # sorting: 시가총액 높은 순 (문자/콤마 대비 숫자로 변환해 정렬)
    df['_mcap_sort'] = pd.to_numeric(df['market_cap'].astype(str).str.replace(',', ''), errors='coerce')
    df2 = df.sort_values(by='_mcap_sort', ascending=False).drop(columns='_mcap_sort')

    has_dividend = False
    if dividend is not None and len(dividend) > 0:
        dd = pd.DataFrame(data=dividend)
        dd = dd.set_index('code')
        dd2 = dd.sort_values(by='배당수익률', ascending=False)
        has_dividend = True

    today = date.today()
    # 결과 파일은 CSV (Excel 한글 호환 위해 utf-8-sig). code는 인덱스로 첫 컬럼에 기록됨.
    filename = "./srim_my_daily/srim_hh_" + today.strftime("%Y%m%d") + ".csv"
    df2.to_csv(filename, encoding="utf-8-sig")
    print(f"결과 저장: {filename} ({len(df2)} 종목)")

    if has_dividend:
        div_filename = "./srim_my_daily/srim_hh_" + today.strftime("%Y%m%d") + "_dividend.csv"
        dd2.to_csv(div_filename, encoding="utf-8-sig")
        print(f"배당 저장: {div_filename} ({len(dd2)} 종목)")
