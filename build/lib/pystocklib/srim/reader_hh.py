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
    #TODO eps 증가율 가져오기
    url.append(
        "https://comp.fnguide.com/SVO2/ASP/SVD_FinanceRatio.asp?pGB=1&gicode=" + code + "&cID=&MenuYn=Y&ReportGB=&NewMenuID=104&stkGb=701")
    url.append(
        "https://comp.fnguide.com/SVO2/ASP/SVD_Invest.asp?pGB=1&gicode=" + code + "&cID=&MenuYn=Y&ReportGB=&NewMenuID=105&stkGb=701")
    url.append(
        "https://comp.fnguide.com/SVO2/ASP/SVD_Consensus.asp?pGB=1&gicode=" + code + "&cID=&MenuYn=Y&ReportGB=&NewMenuID=108&stkGb=701")

    if gb > 4:
        return None

    url = url[gb]
    try:
        resp = requests.get(url)
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

def get_financial_highlight(value, ret_cnt=3):
    i = 0
    output = []
    for x in value:
        if i == 0:
            i = i + 1
            continue
        try:
            output.append(float(x))
            i = i + 1
            if i > ret_cnt + 1:
                break
        except:
            output.append(0)
    return output


def get_roe_average(roes):
    roes0 = 0
    roes1 = 0
    roes2 = 0

    if roes[0] is not None and roes[0] > 0:
        roes0 = float(roes[0])
    if roes[1] is not None and roes[1] > 0:
        roes1 = float(roes[1])
    if roes[2] is not None and roes[2] > 0:
        roes2 = float(roes[2])

    # uptrend or downtrend
    if roes0 <= roes1 <= roes2 or roes0 >= roes1 >= roes2:
        roe = roes2
    else:
        roe = (roes0 + roes1 * 2 + roes2 * 3) / 6  # weighting average
        # print(f'{roe}:{roes0}:{roes1}:{roes2}')
    return roe


def is_capital_up(capitalValue, wantValue):
    comflag = False
    try:
        if capitalValue is not None and wantValue is not None:
            if float(capitalValue) > float(wantValue):
                comflag = True
    except:
        return False
    return comflag


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
