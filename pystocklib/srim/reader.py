from pystocklib.common import *


def make_acode(code):
    '''
    generate acode such as A005930, A000020
    :param code:
    :return: acode
    '''
    acode = None
    if len(code) == 6:
        acode = 'A' + code
    elif len(code) == 7:
        acode = 'A' + code[1:]
    return acode


def get_5years_earning_rate():
    url = "https://www.kisrating.com/ratingsStatistics/statics_spread.do"
    selector = "#con_tab1 > div.table_ty1 > table > tbody > tr:nth-child(11) > td:nth-child(9)"
    ret = get_element_by_css_selector(url, selector)
    return ret


def get_net_worth(code):
    acode = make_acode(code)
    url = f"http://comp.fnguide.com/SVO2/ASP/SVD_main.asp?pGB=1&gicode={acode}"
    selector = "#highlight_D_A > table > tbody > tr:nth-child(10) > td:nth-child(4)"
    ret = get_element_by_css_selector(url, selector)
    try:
        return ret * 100000000
    except:
        return 0


def get_roe(code):
    acode = make_acode(code)
    url = f"http://comp.fnguide.com/SVO2/ASP/SVD_main.asp?pGB=1&gicode={acode}"
    selector = "#highlight_D_A > table > tbody > tr:nth-child(18) > td"
    try:
        tags = get_elements_by_css_selector(url, selector)

        vals = [tag.text for tag in tags]

        roes = []
        for x in vals:
            try:
                x = x.replace(',', '')
                roes.append(float(x))
            except:
                roes.append(0)
        roe3 = roes[:3]

        # uptrend or downtrend 계속 늘어나는 방향, 감소하는 방향이면 제일 최근값을 쓴다.
        if roe3[0] <= roe3[1] <= roe3[2] or roe3[0] >= roe3[1] >= roe3[2]:
            roe = roe3[2]
        else:
           roe = (roe3[0] + roe3[1] * 2 + roe3[2] * 3) / 6  # weighting average
    except:
        roe = 0
    return roe


def get_shares(code):
    acode = make_acode(code)
    url = f"http://comp.fnguide.com/SVO2/ASP/SVD_main.asp?pGB=1&gicode={acode}"
    selector = "#svdMainGrid1 > table > tbody > tr:nth-child(7) > td:nth-child(2)"
    total_shares = get_element_by_css_selector(url, selector, rawdata=True)
    try:
        total_shares = total_shares.split("/")[0]
        total_shares = total_shares.replace(",", "")
        total_shares = float(total_shares)
    except:
        print(f'{url}:could not get_shares')
        total_shares = 0

    selector = "#svdMainGrid5 > table > tbody > tr:nth-child(5) > td:nth-child(3)"
    self_hold_shares = get_element_by_css_selector(url, selector)
    if self_hold_shares is None:
        self_hold_shares = 0

    return total_shares - self_hold_shares


def get_current_price(code):
    acode = make_acode(code)
    url = f"http://comp.fnguide.com/SVO2/ASP/SVD_main.asp?pGB=1&gicode={acode}"
    selector = "#svdMainChartTxt11"
    return get_element_by_css_selector(url, selector)


# 시가총액
def get_aggregate_value(code):
    acode = make_acode(code)
    url = f"http://comp.fnguide.com/SVO2/ASP/SVD_main.asp?pGB=1&gicode={acode}"
    selector = "#svdMainGrid1 > table > tbody > tr:nth-child(5) > td:nth-child(2)"
    return get_element_by_css_selector(url, selector, rawdata=True)



def get_is_aggreagate_up(code, wantValue):
    try:
        val = get_aggregate_value(code)
        val = float(val.replace(',', ''))
        if val > wantValue:
            return True
    except:
        return False




def get_capital_value(code):
    acode = make_acode(code)
    url = f"http://comp.fnguide.com/SVO2/ASP/SVD_main.asp?pGB=1&gicode={acode}"
    selector = "#highlight_D_A > table > tbody > tr:nth-child(10) > td"
    ic_flag = False
    capital3 = ""
    try:
        tags = get_elements_by_css_selector(url, selector)
        vals = [tag.text for tag in tags]
        capital = []
        for x in vals:
            try:
                x = x.replace(',', '')
                capital.append(float(x))
            except:
                capital.append(0)

        capital3 = capital[:3]
        if capital3[0] < capital3[1] or capital3[0] < capital3[2]:
            if capital3[1] < capital3[2]:
                ic_flag = True
        else:
            ic_flag = False
    except:
        ic_flag = False
    return ic_flag, capital3


def compare_price(curprice, price2):
    try:
        diff = round((1 - (curprice / price2)) * 100, 2)

        if curprice < price2:
            cheap = "싸다"
        else:
            cheap = "비싸다"
    except:
        cheap = "값없음"
        diff = ""
    return cheap, diff



if __name__ == "__main__":
    # print(get_5years_earning_rate())
    # print(get_net_worth("005930"))
    # print(get_roe("005930"))
    # print(get_shares("005930"))
    # print(get_current_price("005930"))
    print(get_roe("023460"))
