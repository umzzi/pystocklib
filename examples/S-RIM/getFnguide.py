import sys

from pystocklib.common import *
from datetime import date
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

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
# 출력 파일명 날짜(선택 argv[5], 기본 오늘=YYYYMMDD). 크롤은 항상 FnGuide/네이버의 현재
# 시점 데이터를 가져오므로 과거 날짜를 지정해도 과거 시세가 나오지는 않는다 — 자정을 걸친
# 실행이나 재적재(백필) 때 결과 파일명을 원하는 날짜로 맞추기 위한 용도.
output_date = sys.argv[5] if len(sys.argv) > 5 else date.today().strftime("%Y%m%d")
# 병렬 크롤링 스레드 수(선택 argv[4], 기본 6). 2026-06-29~07-10 사이 CSV가 0종목으로
# 계속 생성되던 사고는 스레드 수가 아니라 gb=0 재무하이라이트가 JS 렌더링으로 바뀌어
# read_html이 깨진 게 원인이었다(gb=3 기반으로 데이터 소스 교체함, process_stock 주석 참고).
# 워커 6개로 2627종목 전체 크롤 시 약 3분17초, 타임아웃 소수(3건) 수준으로 안정적.
MAX_WORKERS = int(sys.argv[4]) if len(sys.argv) > 4 else 6

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

data = []
dividend = []


def process_stock(acode):
    """한 종목을 크롤·계산해 적합하면 전역 data/dividend 리스트에 append 한다.
    종목 간 의존성이 없어 스레드 풀로 병렬 실행한다(네트워크 I/O 대기 단축).
    CPython의 list.append 는 GIL 하에서 원자적이라 락 없이 안전하다.
    부적합/실패 시 그냥 return.

    데이터 소스 (2026-06-22 FnGuide 개편 이후):
    - 현재가/거래량: 네이버 polling API. FnGuide Snapshot(gb=0)이 모든 종목에
      삼성전자 페이지를 반환하는 서버 캐시 버그로 무력화되어 이전함.
    - EPS/BPS/DPS/PER/PBR/시가총액: FnGuide gb=3(투자지표). gb=0 재무하이라이트가
      JS 렌더링으로 바뀌어 무력화된 이후 남은 유일한 서버렌더 종목별 지표 소스.
      은행/증권 등 금융업종도 gb=1과 달리 동일 구조라 별도 분기가 필요 없다.
    - ROE는 EPS/BPS로 직접 계산(대표ROE는 기존과 동일하게 5년 가중평균).
    - 지배주주자본 총액 대신 BPS(주당순자산)를 net_worth로 써서 1주 기준으로 RIM을
      계산한다(자사주 수량은 더 이상 구할 수 없어 조정 생략, 영향은 미미).
    - gb=2(재무비율)는 완전히 빈 페이지로 죽어 사용하지 않는다.
    - 최대주주지분율/자사주수/동종업계PER은 소스가 사라져 근사값으로 대체했다.
      자세한 내용은 CLAUDE.md 참고.
    """
    code = acode[0]
    ticker = acode[1]

    try:
        price, trading_cnt, _ = hh_reader.get_naver_snapshot(code)
    except Exception:
        return
    if not price:
        return

    inv = hh_reader.get_invest_tables(code)
    if inv is None:
        return
    eps_list, bps_list = inv['eps_list'], inv['bps_list']
    if len(eps_list) < 2 or bps_list[-1] is None or bps_list[-1] <= 0:
        return

    roes = [round(e / b * 100, 2) if e is not None and b else None
            for e, b in zip(eps_list, bps_list)]

    # 자본잠식/비정상 ROE 종목은 적정주가가 왜곡되므로 S-RIM 제외.
    # is_roe_reliable은 (라벨, 값...) 형태의 행을 기대하므로 더미 라벨을 앞에 붙인다.
    if not reader_hh.is_roe_reliable([None] + roes):
        return

    # 대표 ROE(5년 가중평균, 음수 반영/급등 완충은 get_roe_average에서 처리)
    rep_roe = reader_hh.get_roe_average(roes)

    # 가장 최근 해가 적자(음수 ROE)면 S-RIM 전제(안정적 초과수익)가 깨짐 → 제외
    if roeCheck == "TRUE" and reader_hh.has_recent_loss(roes):
        return
    if roeCheck == "TRUE" and rep_roe < k:
        return

    # BPS(주당순자산)가 최근 어느 해라도 0 이하면 자본잠식 이력 → S-RIM 적용 불가
    if not reader_hh.is_equity_positive(bps_list):
        return
    isCr = reader_hh.is_capital_increment(bps_list)
    if capitalCheck == "TRUE" and not isCr:
        return

    net_worth = bps_list[-1]  # 주당순자산 = RIM의 net_worth, total_shares=1로 1주 기준 계산
    disparity, *others = srim_calculator.get_srim_disparity(price, net_worth, rep_roe, k,
                                                             1, 0, w=0)

    # 상승여력이 비현실적으로 크면 단년 ROE 왜곡 등으로 적정가 과대추정 → 제외
    try:
        if float(disparity) > reader_hh.DISPARITY_MAX:
            return
    except (TypeError, ValueError):
        pass

    prices = [others[2], others[3], others[4]]
    price_level = srim_calculator.get_price_level(price, prices)
    if price_level <= 0:
        return

    eps_incr_percent, eps_geo_avg, eps_incre_level = hh_reader.calculate_eps(eps_list)
    cur_per = round(price / eps_list[-1], 2) if eps_list[-1] else None
    pegr = srim_calculator.calculate_pegr(eps_geo_avg, cur_per)

    dps = inv['dps_list'][-1] if inv['dps_list'] else None
    dividend_yield = round((dps or 0) / price * 100, 2) if price else 0.0

    naver_url = "https://stock.naver.com/domestic/stock/" + code.replace("A", "")
    link = '=HYPERLINK("' + naver_url + '", "' + code + '")'
    invest_url = "https://comp.fnguide.com/SVO2/ASP/SVD_Invest.asp?pGB=1&gicode=" + code + "&cID=&MenuYn=Y&ReportGB=&NewMenuID=105&stkGb=701"
    invest_link = '=HYPERLINK("' + invest_url + '", "' + ticker + '")'

    row = {
        'code': code,
        'name': ticker,
        'naverlink': link,
        'fnlink': invest_link,
        'est_level': price_level,
        'price': price,
        'pegr': pegr,
        'cur_per': cur_per,
        'est_price': prices[0],
        'est_price1': prices[1],
        'est_price2': prices[2],
        'disparity': disparity,
        'disparity1': others[0],
        'disparity2': others[1],
        'rep_roe': round(rep_roe, 2),
        'is_cheap_comp_per': True,  # 동종업계 PER 소스가 사라져 항상 통과(과거엔 stock[4][2] 비교)
        'eps_level': eps_incre_level,
        'eps': eps_list[-1],
        'eps_expect': eps_list[-1],
        'eps_expect_this_year_ratio': eps_incr_percent[-1],
        'eps_list': eps_list,
        'eps증가율': eps_incr_percent,
        'eps증가율기하평균': eps_geo_avg,
        'EPS최근증가율': eps_incr_percent[-1],
        'EPS증가율_ORG': eps_incr_percent,
        'EPS증가율_AVG': eps_geo_avg,
        'market_cap': inv['market_cap'],
        'trading_cnt': trading_cnt,
        '지배주주자본': bps_list,  # 총액이 아니라 BPS(주당순자산) 리스트 — 소스 변경으로 의미 변경됨
        '최대주주지분율': None,  # 소스 소실
        'ROE': roes,
        'PER': inv['per_list'],
        'PBR': inv['pbr_list'],
        'SPS': inv['sps_list'],
        '자기주식수': 0,  # 소스 소실, RIM 계산도 self_hold_shares=0으로 일치
        '배당수익률': dividend_yield,
        isCr: isCr,
    }
    data.append(row)

    # 배당주 찾기: 최대주주지분율 소스가 사라져 배당수익률 기준(1%+)으로 대체
    if dividend_yield > 1.0:
        dividend.append(row)

# ===== 병렬 크롤링 실행 (스레드 풀) =====
codes = list(mdf.index)
total = len(codes)
print(f'대상 {total}종목, {MAX_WORKERS} 스레드 병렬 크롤링 시작')
_done = 0
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as _ex:
    _futures = [_ex.submit(process_stock, ac) for ac in codes]
    for _f in as_completed(_futures):
        _done += 1
        if _done % 200 == 0:
            print(f'  {_done}/{total} ...')
        try:
            _f.result()
        except Exception:
            pass

print(f'적합 후보 {len(data)}종목 / 배당 {len(dividend)}종목')

if data:
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

    # 결과 파일은 CSV (Excel 한글 호환 위해 utf-8-sig). code는 인덱스로 첫 컬럼에 기록됨.
    filename = "./srim_my_daily/srim_hh_" + output_date + ".csv"
    df2.to_csv(filename, encoding="utf-8-sig")
    print(f"결과 저장: {filename} ({len(df2)} 종목)")

    if has_dividend:
        div_filename = "./srim_my_daily/srim_hh_" + output_date + "_dividend.csv"
        dd2.to_csv(div_filename, encoding="utf-8-sig")
        print(f"배당 저장: {div_filename} ({len(dd2)} 종목)")
