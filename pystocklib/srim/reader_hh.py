import json
import numbers
import re
import time
from datetime import datetime
from io import StringIO
from urllib.request import urlopen

from pystocklib.common import *


def get_html_fnguide(code, gb):
    """
    :param ticker: 종목코드
    :param gb: 데이터 종류 (0: snapshot 1 : 재무제표, 2 : 재무비율, 3: 투자지표, 4:컨센서스 )
    :return:
    """

    url = []

    url.append(
        "http://comp.fnguide.com/SVO2/ASP/SVD_main.asp?pGB=1&gicode=" + code + "&cID=&MenuYn=Y&ReportGB=&NewMenuID=101&stkGb=701")
    url.append(
        "https://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp?pGB=1&gicode=" + code + "&cID=&MenuYn=Y&ReportGB=&NewMenuID=103&stkGb=701")
    url.append(
        "https://comp.fnguide.com/SVO2/ASP/SVD_FinanceRatio.asp?pGB=1&gicode=" + code + "&cID=&MenuYn=Y&ReportGB=&NewMenuID=104&stkGb=701")
    url.append(
        "https://comp.fnguide.com/SVO2/ASP/SVD_Invest.asp?pGB=1&gicode=" + code + "&cID=&MenuYn=Y&ReportGB=&NewMenuID=105&stkGb=701")
    url.append(
        "https://comp.fnguide.com/SVO2/ASP/SVD_Consensus.asp?pGB=1&gicode=" + code + "&cID=&MenuYn=Y&ReportGB=&NewMenuID=108&stkGb=701")

    if gb > 4:
        return None

    url = url[gb]
    #print(url)

    for attempt, wait in enumerate([0, 3, 8]):
        if wait:
            time.sleep(wait)
        try:
            resp = requests.get(url, verify=False, timeout=15)
            return resp.text
        except requests.exceptions.RequestException as error:
            print(f"Error(재시도 {attempt+1}/3):", error)
        except AttributeError:
            return None
    return None


NAVER_UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                           '(KHTML, like Gecko) Chrome/120 Safari/537.36'}


def _to_float(s):
    if s is None:
        return None
    m = re.search(r'-?[\d,]+\.?\d*', str(s).replace('\xa0', ''))
    return float(m.group().replace(',', '')) if m else None


def get_naver_snapshot(code):
    """
    네이버 polling API에서 실시간 현재가/거래량/종목명을 가져온다.

    FnGuide Snapshot(gb=0)이 2026-06-22 개편 이후 모든 종목코드에 대해 삼성전자
    페이지를 반환하는 서버측 캐시 버그로 무력화되어(gicode 파라미터 무시), 현재가·
    거래량 소스를 네이버로 이전했다. gb=0은 더 이상 어떤 용도로도 신뢰할 수 없다.
    """
    ncode = code.replace("A", "")
    resp = requests.get(f"https://polling.finance.naver.com/api/realtime/domestic/stock/{ncode}",
                         headers=NAVER_UA, timeout=10)
    data = resp.json()['datas'][0]
    price = _to_float(data.get('closePrice'))
    volume = _to_float(data.get('accumulatedTradingVolume'))
    # 시가총액(억원)을 캐시: FnGuide 2026-11 개편 후 투자지표 페이지에 '현재' 시총이 없어
    # get_invest_tables가 이 값을 쓴다. (시그니처 유지를 위해 별도 캐시로 전달)
    mv = _to_float(data.get('marketValueFullRaw'))
    if mv:
        _NAVER_MCAP[code] = round(mv / 1e8)
    return price, volume, data.get('stockName')


_NAVER_MCAP = {}  # code -> 시가총액(억원). 스레드 병렬에서도 dict 대입은 GIL로 안전.


def _get_fnguide_invest_html(code):
    """새 FnGuide 투자지표 페이지 HTML(재시도 3회, 실패 시 None).

    ⚠️ 종목 지정은 반드시 `cmp_cd` 파라미터다. 구 사이트의 `gicode`는 새 사이트가 무시하고
    항상 삼성전자 페이지를 돌려준다(전 종목이 삼성전자 값이 되는 사고 방지)."""
    url = f"https://wcomp.fnguide.com/CompanyInfo/Invest?cmp_cd={code.replace('A', '')}"
    for attempt, wait in enumerate([0, 3, 8]):
        if wait:
            time.sleep(wait)
        try:
            resp = requests.get(url, headers=NAVER_UA, verify=False, timeout=15)
            if resp.status_code == 200:
                return resp.text
            print(f"Error(재시도 {attempt+1}/3): {code} HTTP {resp.status_code}")
        except requests.exceptions.RequestException as error:
            print(f"Error(재시도 {attempt+1}/3):", error)
    return None


def _extract_js_json(html, key):
    """`key: {...json...}` 형태의 인라인 JS 객체 값을 JSON으로 파싱해 돌려준다(없거나 깨지면 None)."""
    m = re.search(r'\b' + re.escape(key) + r'\s*:\s*', html)
    if not m:
        return None
    try:
        obj, _ = json.JSONDecoder().raw_decode(html[m.end():])
        return obj
    except ValueError:
        return None


def _clean_invest_label(s):
    """gb=3 표의 펼치기 버튼 텍스트('계산에 참여한 계정 펼치기')를 라벨에서 제거."""
    return str(s).replace('\xa0', '').replace(' ', '').replace('계산에참여한계정펼치기', '')


def get_invest_row(df, label):
    """gb=3(투자지표) 표에서 정규화된 라벨로 행을 찾는다. get_row_by_label과 별도인
    이유는 이 표 특유의 '펼치기' 잡음 제거가 필요해서다."""
    for i in range(len(df)):
        if _clean_invest_label(df.iloc[i, 0]).startswith(label):
            return df.iloc[i]
    return None


def get_invest_tables(code):
    """
    FnGuide gb=3(투자지표) 페이지에서 연도별 EPS/BPS/DPS/PER/PBR/SPS와 최근 시가총액을
    가져온다. gb=0(Snapshot)의 재무하이라이트가 JS 렌더링으로 바뀌어 무력화된 이후
    (2026-06-22~), 이 페이지가 남은 유일한 서버렌더 종목별 지표 소스다. 은행/증권 등
    금융업종도 gb=1(재무제표)과 달리 동일 구조로 제공되어 별도 분기 없이 처리된다.
    리스트는 오래된→최근 연도 순.
    """
    # 2026-11 FnGuide 개편: 구 /SVO2/ASP/SVD_Invest.asp는 404, 새 /CompanyInfo/Invest 페이지는
    # 표가 빈 껍데기이고 값은 페이지 안 invest.init({... invValueIndex: {...}}) 인라인 JSON에
    # 들어 있다(JS가 렌더링). 별도 API 호출 없이 그 JSON을 파싱한다.
    html = _get_fnguide_invest_html(code)
    if not html:
        return None
    # 안전장치: 응답 페이지의 종목코드(cmp_cd)가 요청과 다르면(서버가 파라미터를 무시하고
    # 기본 종목=삼성전자를 준 경우) 잘못된 종목의 데이터이므로 버린다.
    m = re.search(r"cmp_cd:\s*'([0-9A-Z]+)'", html)
    if not m or m.group(1) != code.replace('A', ''):
        return None
    vi = _extract_js_json(html, 'invValueIndex')
    if not vi:
        return None
    rows, header = vi.get('data') or [], vi.get('header') or []
    # header: [{'YYMM': '2022/12', 'CD': 'VAL1'}, ... {'YYMM': '2026/09', 'CD': 'VAL5'}]
    # 연도(12월 결산) 컬럼만 사용 — 마지막 '2026/09' 같은 누적 분기 컬럼은 기존과 같이 제외.
    cols = [(h['CD'], h['YYMM']) for h in header if re.match(r'20\d\d/12', str(h.get('YYMM')))]
    if not cols or not rows:
        return None
    years = [y for _, y in cols]

    def find(grp, label, lvl=None, prefix=False):
        for r in rows:
            nm = str(r.get('NM', '')).strip()
            ok = nm.startswith(label) if prefix else nm == label
            if r.get('GRP_CD') == grp and ok and (lvl is None or r.get('LVL') == lvl):
                return r
        return None

    def year_values(row):
        if row is None:
            return [None] * len(cols)
        return [_to_float(row.get(cd)) for cd, _ in cols]

    if code not in _NAVER_MCAP:   # 보통은 get_naver_snapshot이 먼저 호출되어 채워져 있다
        try:
            get_naver_snapshot(code)
        except Exception:
            pass

    return {
        'years': years,
        'eps_list': year_values(find(1, 'EPS', lvl=1)),                    # Per Share
        'bps_list': year_values(find(1, 'BPS', lvl=1)),
        'dps_list': year_values(find(2, 'DPS(보통주', prefix=True)),         # Dividends
        'sps_list': year_values(find(1, 'SPS', lvl=1)),
        'per_list': year_values(find(3, 'PER', lvl=1)),                    # Multiples
        'pbr_list': year_values(find(3, 'PBR', lvl=1)),
        'market_cap': _NAVER_MCAP.get(code),
    }


def ext_fin_fnguide_data(ticker, gb, item, n, freq="a"):
    """
    :param ticker: 종목코드
    :param gb: 데이터 종류 (0 : 재무제표, 1 : 재무비율, 2: 투자지표)
    :param item: html_text file에서 원하는 계정의 데이터를 가져온다.
    :param n: 최근 몇 개의 데이터를 가져 올것인지
    :param freq: Y : 연간재무, Q : 분기재무
    :return: item의 과거 데이터
    """

    html_text = get_html_fnguide(ticker, gb)

    soup = BeautifulSoup(html_text, 'lxml')

    d = soup.find_all(text=item)

    if (len(d) == 0):
        return None

    # 재무제표면 최근 3년을 가져오고 재무비율이면 최근 4년치를 가져온다.
    nlimit = 3 if gb == 0 else 4

    if n > nlimit:
        return None
    if freq == 'a':
        # 연간 데이터
        d_ = d[0].find_all_next(class_="r", limit=nlimit)
        # 분기 데이터
    elif freq == 'q':
        d_ = d[1].find_all_next(class_="r", limit=nlimit)
    else:
        d_ = None

    try:
        data = d_[(nlimit - n):nlimit]
        v = [v.text for v in data]

    except AttributeError as e:
        return None

    return (v)


DEFAULT_ROE_YEARS = 5
# 한 해 ROE가 같은 기업 '양수 해' 중앙값의 이 배수를 넘으면 일회성 급등으로 보고
# 상한 처리한다. 단년 ROE 급등이 적정가를 과도하게 밀어올리는 문제를 줄인다.
ROE_SPIKE_CAP_FACTOR = 2.0
# 상승여력(괴리율)이 이보다 크면 단년 ROE 왜곡 등에 의한 적정가 과대추정으로 보고
# S-RIM 후보에서 제외한다. (후보 분포상 중앙값 ~76%, 정상 고ROE주 보존을 위해 200%로 설정)
DISPARITY_MAX = 200.0


def get_financial_highlight(value, ret_cnt=4):
    output = []
    if value is None:
        return output

    for x in value[1:]:
        if len(output) >= ret_cnt:
            break
        try:
            output.append(float(str(x).replace(',', '')))
        except (TypeError, ValueError):
            output.append(0)
    return output


def _median(values):
    s = sorted(values)
    n = len(s)
    if n == 0:
        return 0
    mid = n // 2
    if n % 2:
        return s[mid]
    return (s[mid - 1] + s[mid]) / 2


def _dampen_roe_spikes(vals, factor=ROE_SPIKE_CAP_FACTOR):
    """
    같은 기업 '양수 해' ROE 중앙값의 factor 배를 상한으로, 위로 튄 일회성
    급등 ROE를 완충한다. 아래로는 건드리지 않으므로 적자 해는 그대로 남는다.
    양수 해가 없으면 완충하지 않는다.
    """
    positives = [v for v in vals if v > 0]
    if not positives:
        return list(vals)
    cap = _median(positives) * factor
    return [min(v, cap) for v in vals]


def get_roe_average(roes, years=DEFAULT_ROE_YEARS):
    """
    S-RIM 대표 ROE = 최근일수록 큰 가중치를 둔 가중 산술평균.

    - 음수 ROE(적자 해)는 0으로 가리지 않고 그대로 반영해 대표값을 정직하게
      끌어내린다. (적자 이력 기업을 과도하게 낙관하지 않기 위함)
    - 결측(NaN/파싱불가)은 분자/분모 모두에서 제외한다. (데이터 없음 ≠ 본전 0%)
    - 한 해가 같은 기업 양수해 중앙값의 ROE_SPIKE_CAP_FACTOR 배를 넘으면
      일회성 급등으로 보고 상한으로 완충한다.
    사용 가능한 값들에 대해 오래된→최근 순으로 1..n 가중치를 부여한다.
    """
    if not roes:
        return 0

    vals = []
    for roe in roes[:years]:
        try:
            roe = float(roe)
        except (TypeError, ValueError):
            continue  # 결측/파싱불가 → 제외
        if roe != roe:  # nan → 제외
            continue
        vals.append(roe)
    if not vals:
        return 0

    vals = _dampen_roe_spikes(vals)

    weighted_sum = 0
    weight_sum = 0
    for idx, roe in enumerate(vals, start=1):
        weighted_sum += roe * idx
        weight_sum += idx

    if weight_sum == 0:
        return 0
    return weighted_sum / weight_sum


def has_recent_loss(roes):
    """
    가장 최근 연도 ROE가 음수(현재 적자)면 S-RIM 대표값의 전제(안정적 초과수익)가
    깨지므로 후보에서 제외하기 위한 게이트. roes 는 오래된→최근 순서이며 마지막
    유효값이 가장 최근 해다. 유효값이 없으면 False.
    """
    recent = None
    for roe in roes:
        try:
            v = float(roe)
        except (TypeError, ValueError):
            continue
        if v != v:  # nan
            continue
        recent = v
    return recent is not None and recent < 0


def get_row_by_label(values, label, fallback_index=None):
    """
    Financial Highlight 등 표(values=ndarray)에서 첫 컬럼 라벨이 label인 행을 반환한다.
    FnGuide가 행 순서/개수를 바꿔도 '라벨'로 찾으므로 위치 인덱스 밀림에 강건하다.
    공백 무시 후 정확일치 → 접두일치 순으로 탐색하고, 못 찾으면 fallback_index
    (이전 위치 기반 동작 보존)를, 그것도 없으면 None을 반환한다.
    """
    if values is None:
        return None
    target = str(label).replace(" ", "")
    candidate = None
    for row in values:
        cell = str(row[0]).replace(" ", "")
        if cell == target:
            return row
        if candidate is None and cell.startswith(target):
            candidate = row
    if candidate is not None:
        return candidate
    if fallback_index is not None and fallback_index < len(values):
        return values[fallback_index]
    return None


ROE_PLAUSIBLE_MAX = 100.0  # %. 이보다 큰 ROE는 자본잠식/일회성이익에 의한 왜곡으로 본다.


def is_roe_reliable(roe_row):
    """
    ROE 행이 S-RIM에 쓸 만한지 검사한다. 다음이면 부적합(False):
    - '완전잠식'/'자본잠식' 마커가 있다.
    - |ROE| 가 비정상적으로 큰(>100%) 값이 있다. 자본이 0에 수렴했던 해
      (자본잠식 직후 회복기)나 일회성 이익으로 ROE가 1270% 처럼 튄 경우로,
      이런 종목은 S-RIM 적정주가가 왜곡되므로 제외한다.
    정상 종목의 한 자리~수십% ROE는 통과한다.
    """
    if roe_row is None:
        return False
    for cell in roe_row[1:]:
        if isinstance(cell, str):
            if '잠식' in cell:
                return False
            continue
        try:
            v = float(cell)
        except (TypeError, ValueError):
            continue
        if v != v:  # nan
            continue
        if abs(v) > ROE_PLAUSIBLE_MAX:
            return False
    return True


def is_equity_positive(capital):
    """
    지배주주지분(억) 리스트에 0 이하 값이 있으면 최근 자본잠식 이력으로 보고
    S-RIM 부적합(False)으로 판단한다. nan/None 은 건너뛴다.
    """
    if not capital:
        return False
    for v in capital:
        if v is None:
            continue
        try:
            v = float(v)
        except (TypeError, ValueError):
            continue
        if v != v:  # nan
            continue
        if v <= 0:
            return False
    return True


def is_capital_up(capitalValue, wantValue):
    comflag = False
    try:
        if capitalValue is not None and wantValue is not None:
            if float(capitalValue) > float(wantValue):
                comflag = True
    except:
        return False
    return comflag

'''
    지배주주자본이 계속 증가하는가?
'''
def is_capital_increment(capital):
    ic_flag = False
    try:
        if capital[0] < capital[1] or capital[0] < capital[2]:
            if capital[1] < capital[2]:
                ic_flag = True
            else:
                ic_flag = False
    except:
        ic_flag = False
    return ic_flag


def calculate_esp_percent(eps):
    pre_val = 0
    eps_incr_percent = []
    try:
        for item in eps:
            if pre_val == 0:
                pre_val = item
            else:
                rto = ((item / pre_val) - 1) * 100
                pre_val = item
                eps_incr_percent.append(round(rto, 1))
    except AttributeError as e:
        print(e)
    return eps_incr_percent


def calculate_esp_incr_levl(eps):
    eps_incre_level = 0
    try:
        if eps[0] < eps[1] < eps[2] < eps[3]:
            eps_incre_level = 3
        elif eps[1] < eps[2] < eps[3]:
            eps_incre_level = 2
        elif eps[2] < eps[3]:
            eps_incre_level = 1
    except AttributeError as e:
        print(e)
    return eps_incre_level


def calculate_esp_geo_avg(eps_incr_percent):
    epsmulti = 1
    geoAvg = 0
    cnt = 0
    for item in eps_incr_percent:
        if isinstance(item, numbers.Number) and item != 0 and item != "적전":
            item = float(item)
            epsmulti *= 1 + (item * 0.01)
            # print(1 + (item * 0.01))
            cnt = cnt + 1

    if cnt > 0 and epsmulti > 0:
        geoAvg = ((epsmulti ** (1 / cnt)) - 1) * 100

    return geoAvg


def calculate_eps(eps):
    eps_incr_percent = calculate_esp_percent(eps)
    eps_geo_avg = calculate_esp_geo_avg(eps_incr_percent)
    eps_incre_level = calculate_esp_incr_levl(eps)

    return eps_incr_percent, eps_geo_avg, eps_incre_level

def get_naver_code(company_code):
    company_code = company_code.replace("A", "")
    url = "http://finance.naver.com/item/main.nhn?code="+company_code
    bs_obj = BeautifulSoup(requests.get(url,
                                      headers={'User-agent': 'Mozilla/5.0'}, timeout=15).text, "html.parser")
    return bs_obj


def get_naver_price(company_code):
    bs_obj = get_naver_code(company_code)
    no_today = bs_obj.find("p", {"class":"no_today"})
    blind = no_today.find("span", {"class":"blind"})
    now_price = blind.text
    return now_price

def read_naver(code, company, pages_to_fetch):
        """네이버에서 주식 시세를 읽어서 데이터프레임으로 반환"""
        try:
            code = code.replace("A", "")
            url = f"http://finance.naver.com/item/sise_day.nhn?code={code}"
            print(url)
            html = BeautifulSoup(requests.get(url,
                                              headers={'User-agent': 'Mozilla/5.0'}, timeout=15).text, "lxml")
            pgrr = html.find("td", class_="pgRR")
            if pgrr is None:
                return None
            s = str(pgrr.a["href"]).split('=')
            lastpage = s[-1]
            df = pd.DataFrame()
            pages = min(int(lastpage), pages_to_fetch)
            for page in range(1, pages + 1):
                pg_url = '{}&page={}'.format(url, page)
                df = df.append(pd.read_html(requests.get(pg_url,
                                                         headers={'User-agent': 'Mozilla/5.0'}, timeout=15).text)[0])
                tmnow = datetime.now().strftime('%Y-%m-%d %H:%M')
                print('[{}] {} ({}) : {:04d}/{:04d} pages are downloading...'.
                      format(tmnow, company, code, page, pages), end="\r")
            df = df.rename(columns={'날짜': 'date', '종가': 'close', '전일비': 'diff'
                , '시가': 'open', '고가': 'high', '저가': 'low', '거래량': 'volume'})
            df['date'] = df['date'].replace('.', '-')
            df = df.dropna()
            df[['close', 'diff', 'open', 'high', 'low', 'volume']] = df[['close',
                                                                         'diff', 'open', 'high', 'low',
                                                                         'volume']].astype(int)
            df = df[['date', 'open', 'high', 'low', 'close', 'diff', 'volume']]
        except Exception as e:
            print('Exception occured :', str(e))
            return None
        return df
