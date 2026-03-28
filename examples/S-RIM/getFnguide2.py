import sys
from io import StringIO

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
import os
os.makedirs("./srim_my_daily", exist_ok=True)
kospi.to_excel("./srim_my_daily/KOSPI.xlsx")

# KOSDAQ code list
kosdaq = get_code_list_by_market(market=3)
kosdaq.to_excel("./srim_my_daily/KOSDAQ.xlsx")

# KOSPI+KOSDAQ
if inputCheck == "TRUE":
    mdf = pd.concat([inframe])
else:
    mdf = pd.concat([kospi, kosdaq])

# k
k = srim_reader.get_5years_earning_rate()
if k is None or k == 0:
    k = 8.0  # 기본값: BBB- 5년 평균 회사채 수익률
    print(f'kisrating.com에서 k값을 가져오지 못해 기본값 {k}%를 사용합니다.')
else:
    print(f'요구수익률 k = {k}%')

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
         df = pd.read_html(StringIO(hh_reader.get_html_fnguide(code, gb=0)))
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

    # 시가총액
    market_capital = stock[0][1]

    # 수정주가PER
    cur_per = stock[4][1]
    is_cheaper_per = srim_calculator.is_per_compare_sector(cur_per, stock[4][2])

    # 4년 ROE
    roes = reader_hh.get_financial_highlight(jemu[17])
    rep_roe = reader_hh.get_roe_average(roes)

    # 4년 EPS
    epslist = reader_hh.get_financial_highlight(jemu[18])
    # eps 증가율 구하기

    # 4년 PER
    pers = reader_hh.get_financial_highlight(jemu[21])

    # 4년 PBR
    pbrs = reader_hh.get_financial_highlight(jemu[22])
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
    capital = reader_hh.get_financial_highlight(jemu[9])
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

    prices = [others[2], others[3], others[4]]
    price_level = srim_calculator.get_price_level(cur_price, prices)

    # fnguide 재무비율 페이지의 EPS증가율 가져오기
    gf = pd.read_html(StringIO(hh_reader.get_html_fnguide(code, gb=2)))
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

    naver_url = "https://finance.naver.com/item/coinfo.nhn?code=" + code.replace("A", "")
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
                '시가총액(억)': stock[0][1],  # 시가총액(억원)
                '거래량': trading_cnt,  # 거래량
                '지배주주자본': capital,  # 지배주주지분
                "최대주주지분율": jasa[0][3],  # 최대주주지분율
                jemu[17][0]: roes,
                jemu[21][0]: pers,
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
                    '시가총액(억)': stock[0][1],  # 시가총액(억원)
                    '거래량': trading_cnt,  # 거래량
                    '지배주주자본': capital,  # 지배주주지분
                    "최대주주지분율": jasa[0][3],  # 최대주주지분율
                    jemu[17][0]: roes,
                    jemu[21][0]: pers,
                    stock[1][0]: stock[1][1],  # 매출익
                    stock[2][0]: stock[2][1],  # 영업이익
                    "자기주식수": self_hold_shares,  # 자사주수
                    stock[7][0]: stock[7][1],  # 배당수익
                    isCr: isCr  # 자기자본이 계속 늘고있나.
                }
            )

if index > 0:
    df = pd.DataFrame(data=data)
    df = df.set_index(['code', 'name'])

    # sorting
    df2 = df.sort_values(by='est_level', ascending=False)

    has_dividend = False
    if dividend is not None and len(dividend) > 0:
        dd = pd.DataFrame(data=dividend)
        dd = dd.set_index(['code', 'name'])
        dd2 = dd.sort_values(by='배당수익률', ascending=False)
        has_dividend = True

    today = date.today()
    import os
    from datetime import datetime
    os.makedirs("./srim_my_daily", exist_ok=True)
    filename = "./srim_my_daily/srim_hh_v2_" + today.strftime("%Y%m%d") + ".xlsx"
    # 파일이 이미 존재하고 쓰기 불가능하면 시간 붙여서 생성
    if os.path.exists(filename):
        try:
            open(filename, 'a').close()
        except (PermissionError, OSError):
            filename = "./srim_my_daily/srim_hh_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".xlsx"
            print(f'기존 파일 잠김. 새 파일명: {filename}')

    # ============================================================
    # xlsxwriter로 Excel 저장 + 조건부 색상 서식 적용
    # ============================================================
    with pd.ExcelWriter(filename, engine="xlsxwriter") as writer:
        df2.to_excel(writer, sheet_name="rim")

        workbook = writer.book
        worksheet = writer.sheets['rim']

        if has_dividend:
            dd2.to_excel(writer, sheet_name="dividend")
            worksheet2 = writer.sheets['dividend']

        # --- 서식 정의 ---
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1})

        # est_level 색상
        fmt_level3 = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100', 'bold': True})
        fmt_level2 = workbook.add_format({'bg_color': '#FFEB9C', 'font_color': '#9C6500', 'bold': True})
        fmt_level1 = workbook.add_format({'bg_color': '#FCD5B4', 'font_color': '#974706', 'bold': True})

        # est_price 색상: 적정가 >= 현재가 (저평가, 녹색)
        fmt_price_green = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100', 'bold': True, 'num_format': '#,##0'})
        # est_price 색상: 적정가 80~100% of 현재가 (관망, 노란색)
        fmt_price_yellow = workbook.add_format({'bg_color': '#FFEB9C', 'font_color': '#9C6500', 'num_format': '#,##0'})
        # est_price 색상: 적정가 < 80% of 현재가 (고평가, 빨간색)
        fmt_price_red = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006', 'num_format': '#,##0'})

        # 컬럼 인덱스 찾기 (code, name이 index이므로 +2 오프셋)
        cols = list(df2.columns)
        col_est_level = cols.index('est_level') + 2
        col_price = cols.index('price') + 2
        col_est_price = cols.index('est_price') + 2
        col_est_price1 = cols.index('est_price1') + 2
        col_est_price2 = cols.index('est_price2') + 2

        # Write the column headers with the defined format.
        for col_num, value in enumerate(df2.columns.values):
            worksheet.write(0, col_num + 2, value, header_format)
            if has_dividend:
                worksheet2.write(0, col_num + 2, value, header_format)

        # --- 데이터 행별 조건부 서식 적용 ---
        for row_idx in range(len(df2)):
            excel_row = row_idx + 1  # 헤더가 0행

            est_level = df2.iloc[row_idx]['est_level']
            cur_price_val = df2.iloc[row_idx]['price']

            # est_level 색상
            if est_level == 3:
                worksheet.write(excel_row, col_est_level, est_level, fmt_level3)
            elif est_level == 2:
                worksheet.write(excel_row, col_est_level, est_level, fmt_level2)
            elif est_level == 1:
                worksheet.write(excel_row, col_est_level, est_level, fmt_level1)

            # est_price, est_price1, est_price2 색상
            for col_idx, price_col in enumerate(['est_price', 'est_price1', 'est_price2']):
                est_val = df2.iloc[row_idx][price_col]
                excel_col = [col_est_price, col_est_price1, col_est_price2][col_idx]

                try:
                    est_val = float(est_val)
                    if cur_price_val > 0:
                        ratio = est_val / cur_price_val
                        if ratio >= 1.0:
                            worksheet.write(excel_row, excel_col, est_val, fmt_price_green)
                        elif ratio >= 0.8:
                            worksheet.write(excel_row, excel_col, est_val, fmt_price_yellow)
                        else:
                            worksheet.write(excel_row, excel_col, est_val, fmt_price_red)
                except (ValueError, TypeError):
                    pass

        # 배당주 시트에도 동일 서식 적용
        if has_dividend:
            cols_dd = list(dd2.columns)
            dd_col_est_level = cols_dd.index('est_level') + 2
            dd_col_price = cols_dd.index('price') + 2
            dd_col_est_price = cols_dd.index('est_price') + 2
            dd_col_est_price1 = cols_dd.index('est_price1') + 2
            dd_col_est_price2 = cols_dd.index('est_price2') + 2

            for row_idx in range(len(dd2)):
                excel_row = row_idx + 1

                est_level = dd2.iloc[row_idx]['est_level']
                cur_price_val = dd2.iloc[row_idx]['price']

                if est_level == 3:
                    worksheet2.write(excel_row, dd_col_est_level, est_level, fmt_level3)
                elif est_level == 2:
                    worksheet2.write(excel_row, dd_col_est_level, est_level, fmt_level2)
                elif est_level == 1:
                    worksheet2.write(excel_row, dd_col_est_level, est_level, fmt_level1)

                for col_idx, price_col in enumerate(['est_price', 'est_price1', 'est_price2']):
                    est_val = dd2.iloc[row_idx][price_col]
                    excel_col = [dd_col_est_price, dd_col_est_price1, dd_col_est_price2][col_idx]

                    try:
                        est_val = float(est_val)
                        if cur_price_val > 0:
                            ratio = est_val / cur_price_val
                            if ratio >= 1.0:
                                worksheet2.write(excel_row, excel_col, est_val, fmt_price_green)
                            elif ratio >= 0.8:
                                worksheet2.write(excel_row, excel_col, est_val, fmt_price_yellow)
                            else:
                                worksheet2.write(excel_row, excel_col, est_val, fmt_price_red)
                    except (ValueError, TypeError):
                        pass

        # ============================================================
        # 추가 시트: 수치항목 설명, 시기별 비교, 주요종목 시계열, S-RIM 공식
        # ============================================================

        # --- 공통 서식 ---
        fmt_sheet_header = workbook.add_format({
            'bold': True, 'font_size': 11, 'font_color': '#FFFFFF',
            'bg_color': '#2F5496', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        fmt_cat = workbook.add_format({
            'bold': True, 'font_size': 11, 'font_color': '#1F3864',
            'bg_color': '#D6E4F0', 'border': 1})
        fmt_cell = workbook.add_format({
            'font_size': 10, 'text_wrap': True, 'valign': 'top', 'border': 1})
        fmt_cell_bold = workbook.add_format({
            'font_size': 10, 'bold': True, 'text_wrap': True, 'valign': 'top', 'border': 1})

        # ========== 시트: 수치항목 설명 ==========
        ws_desc = workbook.add_worksheet("수치항목 설명")
        ws_desc.set_column('A:A', 22)
        ws_desc.set_column('B:B', 45)
        ws_desc.set_column('C:C', 45)
        ws_desc.set_column('D:D', 35)

        desc_headers = ["항목명", "설명", "해석 방법", "필터 기준"]
        for c, h in enumerate(desc_headers):
            ws_desc.write(0, c, h, fmt_sheet_header)

        desc_data = [
            ["[핵심 밸류에이션]", "", "", ""],
            ["est_level", "S-RIM 적정가 대비 현재가의 위치 등급", "3=적정가80%이하(매수적극), 2=적정가90%이하(매수고려), 1=적정가100%이하(관망), 0=적정가초과(비싸다)", "est_level > 0인 종목만 결과에 포함"],
            ["price", "현재 주가 (원)", "FnGuide에서 가져온 최신 종가", "-"],
            ["est_price", "S-RIM 적정주가 (w=1.0, 정상 시나리오)", "순자산 + 초과이익의 현재가치. ROE가 k보다 높을수록 적정가 상승", "-"],
            ["est_price1", "S-RIM 적정주가 (w=0.9, 초과이익 10% 감소)", "초과이익이 매년 10%씩 줄어드는 보수적 시나리오", "-"],
            ["est_price2", "S-RIM 적정주가 (w=0.8, 초과이익 20% 감소)", "가장 보수적 시나리오. 이 가격보다 싸면 매우 저평가", "-"],
            ["disparity", "괴리율 (%). (1 - est_price/현재가) × 100", "음수(-)일수록 저평가. -100%면 적정가가 현재가의 2배", "값이 클수록 결과 상위 정렬"],
            ["disparity1 / disparity2", "90%/80% 시나리오별 괴리율", "disparity와 동일한 해석. 보수적 관점의 저평가 정도", "-"],
            ["[수익성 지표]", "", "", ""],
            ["rep_roe", "가중평균 ROE (%). 3년치 가중평균 (1:2:3 비중)", "높을수록 자기자본 대비 수익 창출력 우수", "roeCheck=TRUE일 때 rep_roe > k 필터"],
            ["k (요구수익률)", "BBB- 5년 회사채 수익률 (KIS Rating)", "투자자가 기대하는 최소 수익률", "ROE가 이보다 높은 종목만 통과"],
            ["cur_per", "현재 PER (주가수익비율)", "낮을수록 이익 대비 저평가", "-"],
            ["is_cheap_comp_per", "동종업계 PER 대비 저렴 여부 (True/False)", "True면 같은 업종 평균보다 PER이 낮음", "-"],
            ["[EPS 성장 분석]", "", "", ""],
            ["eps", "주당순이익 (원). 최근 연도 기준", "높을수록 주당 벌어들이는 이익이 큼", "-"],
            ["eps_level", "EPS 증가 추세 등급 (0~3)", "3=4년연속증가, 2=3년연속, 1=2년연속, 0=감소", "-"],
            ["eps증가율기하평균", "EPS 증가율의 기하평균 (%)", "복리 기준 연평균 EPS 성장률", "-"],
            ["pegr", "PEG Ratio (PER / EPS증가율기하평균)", "1이하면 성장성 대비 저평가, 2이상이면 고평가", "-"],
            ["[기업 건전성]", "", "", ""],
            ["지배주주자본", "지배주주지분 (억원). 3~4년치 배열", "순자산 규모. S-RIM 계산의 핵심 입력값", "capitalCheck=TRUE일 때 증가 추세 필터"],
            ["최대주주지분율", "최대주주 + 특수관계인 지분율 (%)", "높을수록 경영 안정성. 50%이상+배당 시 배당주", "배당주 필터: 50% 이상"],
            ["시가총액(억)", "시가총액 (억원)", "기업 규모 판단", "-"],
            ["거래량", "당일 거래량", "유동성 판단", "-"],
            ["[배당 분석]", "", "", ""],
            ["배당수익률", "배당수익률 (%)", "높을수록 배당 매력 우수", "배당주 시트: 배당>0 & 최대주주지분율>50%"],
        ]

        for r, row_data in enumerate(desc_data):
            is_cat = row_data[1] == "" and row_data[2] == "" and row_data[3] == ""
            for c, val in enumerate(row_data):
                if is_cat:
                    ws_desc.write(r + 1, c, val, fmt_cat)
                elif c == 0:
                    ws_desc.write(r + 1, c, val, fmt_cell_bold)
                else:
                    ws_desc.write(r + 1, c, val, fmt_cell)

        # ========== 시트: 시기별 비교 ==========
        past_files = [
            ('2020-12', './srim_my_daily/srim_hh_20201207.xlsx'),
            ('2021-06', './srim_my_daily/srim_hh_20210608.xlsx'),
            ('2021-12', './srim_my_daily/srim_hh_20211228.xlsx'),
            ('2022-06', './srim_my_daily/srim_hh_20220612.xlsx'),
            ('2022-12', './srim_my_daily/srim_hh_20221228.xlsx'),
            ('2023-03', './srim_my_daily/srim_hh_20230317.xlsx'),
            ('2023-07', './srim_my_daily/srim_hh_20230709.xlsx'),
        ]

        ws_comp = workbook.add_worksheet("시기별 비교")
        comp_headers = ["시기", "통과 종목수", "평균 est_level", "평균 괴리율(%)", "평균 ROE(%)", "평균 PER", "Level3 비율(%)"]
        for c, h in enumerate(comp_headers):
            ws_comp.write(0, c, h, fmt_sheet_header)
            ws_comp.set_column(c, c, 16)

        fmt_comp_cell = workbook.add_format({'font_size': 10, 'align': 'center', 'border': 1})
        comp_row = 1
        for period, fpath in past_files:
            try:
                pdf = pd.read_excel(fpath)
                cnt = len(pdf)
                avg_level = round(pdf['est_level'].mean(), 2)
                avg_disp = round(pdf['disparity'].mean(), 2)
                avg_roe = round(pdf['rep_roe'].mean(), 2)
                avg_per = round(pd.to_numeric(pdf['cur_per'], errors='coerce').mean(), 2)
                lv3_pct = round((pdf['est_level'] == 3).sum() / cnt * 100, 1)
                for c, v in enumerate([period, cnt, avg_level, avg_disp, avg_roe, avg_per, lv3_pct]):
                    ws_comp.write(comp_row, c, v, fmt_comp_cell)
                comp_row += 1
            except:
                pass

        # 현재 데이터 행 추가
        fmt_comp_cur = workbook.add_format({
            'font_size': 10, 'align': 'center', 'border': 1,
            'bold': True, 'font_color': '#0000FF'})
        cur_cnt = len(df2)
        if cur_cnt > 0:
            cur_avg_level = round(df2['est_level'].mean(), 2)
            cur_avg_disp = round(df2['disparity'].mean(), 2)
            cur_avg_roe = round(df2['rep_roe'].mean(), 2)
            cur_avg_per = round(pd.to_numeric(df2['cur_per'], errors='coerce').mean(), 2)
            cur_lv3_pct = round((df2['est_level'] == 3).sum() / cur_cnt * 100, 1)
            for c, v in enumerate([today.strftime("%Y-%m") + "(현재)", cur_cnt, cur_avg_level,
                                   cur_avg_disp, cur_avg_roe, cur_avg_per, cur_lv3_pct]):
                ws_comp.write(comp_row, c, v, fmt_comp_cur)

        # ========== 시트: 주요종목 시계열 ==========
        ws_ts = workbook.add_worksheet("주요종목 시계열")
        ts_headers = ["종목", "시기", "주가", "적정가(w=1)", "적정가(w=0.9)", "적정가(w=0.8)", "괴리율(%)", "Level", "ROE(%)"]
        for c, h in enumerate(ts_headers):
            ws_ts.write(0, c, h, fmt_sheet_header)
            ws_ts.set_column(c, c, 14)
        ws_ts.set_column(0, 0, 12)

        fmt_ts_cell = workbook.add_format({'font_size': 10, 'align': 'center', 'border': 1})
        fmt_ts_bold = workbook.add_format({'font_size': 10, 'align': 'center', 'border': 1, 'bold': True})
        fmt_ts_cur = workbook.add_format({
            'font_size': 10, 'align': 'center', 'border': 1,
            'bold': True, 'font_color': '#0000FF'})

        track_codes = {
            'A005930': '삼성전자', 'A005380': '현대차', 'A000270': '기아',
            'A035420': '네이버', 'A012330': '현대모비스'
        }

        ts_row = 1
        for scode, sname in track_codes.items():
            for period, fpath in past_files:
                try:
                    pdf = pd.read_excel(fpath)
                    match = pdf[pdf['code'] == scode]
                    if len(match) > 0:
                        r = match.iloc[0]
                        vals = [sname, period, r['price'], r['est_price'], r['est_price1'],
                                r['est_price2'], r['disparity'], r['est_level'], r['rep_roe']]
                        for c, v in enumerate(vals):
                            fmt = fmt_ts_bold if c == 0 else fmt_ts_cell
                            ws_ts.write(ts_row, c, v, fmt)
                        ts_row += 1
                except:
                    pass

            # 현재 데이터에서 해당 종목 찾기
            if scode in df2.index.get_level_values(0):
                cur_row = df2.loc[scode].iloc[0] if isinstance(df2.loc[scode], pd.DataFrame) else df2.loc[scode]
                vals = [sname, today.strftime("%Y-%m") + "(현재)", cur_row['price'],
                        cur_row['est_price'], cur_row['est_price1'], cur_row['est_price2'],
                        cur_row['disparity'], cur_row['est_level'], cur_row['rep_roe']]
                for c, v in enumerate(vals):
                    ws_ts.write(ts_row, c, v, fmt_ts_cur)
                ts_row += 1

            ts_row += 1  # 종목간 빈 행

        # ========== 시트: S-RIM 공식 ==========
        ws_formula = workbook.add_worksheet("S-RIM 공식")
        ws_formula.set_column('A:A', 25)
        ws_formula.set_column('B:B', 70)

        formula_data = [
            ("S-RIM 핵심 공식", ""),
            ("적정가치 (w=1)", "V = 순자산 + (순자산 × (ROE - k)) / k"),
            ("적정가치 (w<1)", "V = 순자산 + 초과이익 × w / (1 + k% - w)"),
            ("초과이익", "순자산 × (ROE - k) × 0.01"),
            ("적정주가", "적정가치 / (총주식수 - 자기주식수)"),
            ("괴리율", "(1 - 적정주가/현재가) × 100"),
            ("", ""),
            ("시나리오별 의미", ""),
            ("w = 1.0 (est_price)", "초과이익이 영구 지속. 낙관적 시나리오"),
            ("w = 0.9 (est_price1)", "초과이익이 매년 10%씩 감소. 중립 시나리오"),
            ("w = 0.8 (est_price2)", "초과이익이 매년 20%씩 감소. 보수적 시나리오"),
            ("", ""),
            ("Price Level 결정", ""),
            ("Level 3 (매수적극)", "현재가 < est_price2 (가장 보수적 적정가보다도 쌈)"),
            ("Level 2 (매수고려)", "est_price2 ≤ 현재가 < est_price1"),
            ("Level 1 (관망)", "est_price1 ≤ 현재가 < est_price"),
            ("Level 0 (비싸다)", "현재가 ≥ est_price (적정가를 초과)"),
            ("", ""),
            ("필터링 조건 (getFnguide2.py)", ""),
            ("argv[1] roeCheck", "TRUE면 rep_roe > k인 종목만 통과 (ROE가 요구수익률 이상)"),
            ("argv[2] capitalCheck", "TRUE면 지배주주자본이 증가 추세인 종목만 통과"),
            ("argv[3] inputCheck", "TRUE면 코드에 직접 입력한 종목만, FALSE면 코스피+코스닥 전체"),
            ("", ""),
            ("배당주 필터링", ""),
            ("배당주 조건", "최대주주지분율 > 50% AND 배당수익률 > 0"),
            ("", ""),
            ("현재 요구수익률", f"k = {k}% (KIS Rating BBB- 5년 회사채 수익률)"),
            ("분석일자", today.strftime("%Y-%m-%d")),
        ]

        f_row = 0
        for label, val in formula_data:
            if val == "" and label != "":
                ws_formula.write(f_row, 0, label, fmt_cat)
                ws_formula.write(f_row, 1, "", fmt_cat)
            elif label == "" and val == "":
                f_row += 1
                continue
            else:
                ws_formula.write(f_row, 0, label, fmt_cell_bold)
                ws_formula.write(f_row, 1, val, fmt_cell)
            f_row += 1

    print(f'\n결과 저장: {filename}')
    print(f'총 {len(data)}개 종목 (배당주: {len(dividend)}개)')
    div_str = "dividend, " if has_dividend else ""
    print(f'포함 시트: rim, {div_str}수치항목 설명, 시기별 비교, 주요종목 시계열, S-RIM 공식')