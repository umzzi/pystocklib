import numbers
import time
from datetime import datetime
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

    try:
        resp = requests.get(url, verify=False, timeout=15)
        return resp.text
    except requests.exceptions.RequestException as error:
        print("Error:", error)
        time.sleep(1)
        resp = requests.get(url, verify=False, timeout=15)
        return resp.text
    except AttributeError as e:
        return None


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
