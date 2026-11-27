import requests
import time
from bs4 import BeautifulSoup
import pandas as pd
from urllib3.exceptions import InsecureRequestWarning

def get_element_by_css_selector(url, selector, rawdata=False):
    try:
        requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
        resp = requests.get(url, verify=False, timeout=15)
        print(url)
        html = resp.text
        soup = BeautifulSoup(html, "html5lib")
        tags = soup.select(selector)
        if not tags:
            print(f"get_element_by_css_selector: 셀렉터 매치 없음 (사이트 레이아웃 변경 의심): {selector}")
            return None
        tag = tags[0]

        if rawdata:
            return tag.text
        else:
            if tag.text is not None:
                return float(tag.text.replace(",", ""))
            else:
                return 0
    except (AttributeError, ValueError) as e:
        print(e)
        return None


def get_elements_by_css_selector(url, selector):
    try:
        requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
        resp = requests.get(url, timeout=15)
        html = resp.text
        soup = BeautifulSoup(html, "html5lib")
        tags = soup.select(selector)
        return tags
    except:
        return None


def get_code_list_by_market(market=1):
    """
    get listed company information such as code and name
    :param market: 1: all, 2: kospi, 3: kosdaq
    :return: DataFrame
    """
    # FnGuide lookup_data.asp는 2026-11 사이트 개편으로 404가 되어 네이버 증권
    # 시가총액 순위 API로 대체했다. 기존 목록과 동일하게 '보통주'만(우선주/ETF/ETN 제외)
    # 돌려주고, 코드는 FnGuide 형식(A+6자리), 컬럼은 기존(gb, mkt_gb, stk_gb)을 유지한다.
    markets = {2: [('KOSPI', '유가증권시장', 1)],
               3: [('KOSDAQ', '코스닥', 2)],
               1: [('KOSPI', '유가증권시장', 1), ('KOSDAQ', '코스닥', 2)]}[market]
    ua = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                        '(KHTML, like Gecko) Chrome/120 Safari/537.36'}
    rows = []
    for naver_mkt, gb, mkt_gb in markets:
        page, total, got = 1, None, 0
        while total is None or got < total:
            data = None
            for attempt, wait in enumerate([0, 3, 8]):
                if wait:
                    time.sleep(wait)
                try:
                    resp = requests.get(
                        f"https://m.stock.naver.com/api/stocks/marketValue/{naver_mkt}",
                        params={'page': page, 'pageSize': 100}, headers=ua, timeout=15)
                    resp.raise_for_status()
                    data = resp.json()
                    break
                except (requests.exceptions.RequestException, ValueError) as e:
                    print(f"get_code_list_by_market({naver_mkt} p{page}) 재시도 {attempt+1}/3 실패: {e}")
            if data is None:
                raise RuntimeError(f"get_code_list_by_market: {naver_mkt} page {page} 조회 3회 모두 실패")
            stocks = data.get('stocks') or []
            total = data.get('totalCount', 0)
            if not stocks:
                break
            got += len(stocks)
            for s in stocks:
                code = str(s.get('itemCode', ''))
                # 보통주만: 일반 주식이면서 코드 끝자리가 0 (우선주는 5/7/K 등)
                if s.get('stockEndType') == 'stock' and len(code) == 6 and code.endswith('0'):
                    rows.append({'cd': 'A' + code, 'nm': s.get('stockName'),
                                 'gb': gb, 'mkt_gb': mkt_gb, 'stk_gb': 701})
            page += 1
    if not rows:
        raise RuntimeError(f"get_code_list_by_market: market={market} 종목 리스트가 비어 있음")
    df = pd.DataFrame(rows).drop_duplicates('cd')
    df = df.set_index(['cd', 'nm'])
    return df







if __name__ == "__main__":
    df = get_code_list_by_market(market=3)
    print(df.head())
