import numbers

import numpy

import pystocklib.srim.reader as reader


def won_convert_to_float(value):
    price = 0
    if value is not None and bool(value):
        if not isinstance(value, float):
            price = value.replace(",", "")
        if not price or price != "":
            price = int(price)
    return price


def parsing_string_sep(value, sep, order):
    if value is not None:
        ret_value = value.split(sep)[order]
    return ret_value

def get_pegr_value(eps_rtos, cur_per):
    # return pegr(cur_per/geovalue), geovalue(esp 증가율 기하평균)
    pegr = 0
    epsmulti = 1
    cnt = 0
    geoValue = 0
    for item in eps_rtos:
        if isinstance(item, numbers.Number) and item != 0 and item != "적전":
            item = float(item)
            epsmulti *= 1 + (item * 0.01)
            # print(1 + (item * 0.01))
            cnt = cnt + 1

    if cnt > 0 and epsmulti > 0:
        geoValue = ((epsmulti ** (1 / cnt)) - 1) * 100

    if cur_per is not None and geoValue != 0:
        pegr = cur_per / geoValue

    pegr = round(float(null_check(pegr)), 2)

    return pegr, geoValue


def estimate_rim(net_worth, roe, k, w=1):
    """
    :param net_worth 지배주주자
    :param k: expected earning rate
    :param w:  1:적정주가 0.9:적정주-10%
    :return: value:회사적정가치, 초과이익(Excess Earning)
    """
    excess_earning = net_worth * (roe - k) * 0.01
    value1 = 0
    value2 = 0

    if w == 1:
        value = net_worth + (net_worth * (roe - k)) / k
    elif w == 0:
        excess_earning = net_worth * (roe - k) * 0.01
        value = net_worth + (net_worth * (roe - k)) / k

        w1 = 0.9
        mul1 = w1 / (1.0 + k * 0.01 - w1)
        value1 = net_worth + excess_earning * mul1

        w2 = 0.8
        mul2 = w2 / (1.0 + k * 0.01 - w2)
        value2 = net_worth + excess_earning * mul2
    else:
        excess_earning = net_worth * (roe - k) * 0.01
        mul = w / (1.0 + k * 0.01 - w)
        value = net_worth + excess_earning * mul

    return value, value1, value2, excess_earning


def self_shares_count(total_shares, self_hold_shares):
    if total_shares is None and bool(total_shares) == False:
        total_shares = 0
    if self_hold_shares is None or numpy.isnan(self_hold_shares):
        self_hold_shares = 0
    return float(total_shares) - float(self_hold_shares)


def estimate_rim_price(net_worth, roe, k, total_shares, self_hold_shares, w=1):
    """
    calculate reasonable price
    :param code:
    :param k:
    :param w:
    :return: Reasonable Price, Shares, Value, NetWorth, ROE, Excess Earning
    """
    # 회사 적정 가치 계산
    value, value1, value2, excess_earning = estimate_rim(net_worth, roe, k, w)
    # 회사 주식수
    shares = self_shares_count(total_shares, self_hold_shares)
    price = 0
    price1 = 0
    price2 = 0

    if shares > 0:
        if value is not None:
            price = value / shares

        if value1 is not None:
            price1 = value1 / shares

        if value2 is not None:
            price2 = value2 / shares

    return price, price1, price2, excess_earning


def get_srim_disparity(cur_price, net_worth, roe, k, total_shares, self_hold_shares, w=1):
    """
    get disparity that is calculated by (cur_price / est_price ) * 100
    :param code:
    :param k:
    :param w:
    :return:
    """
    est_price, est_price1, est_price2, excess_earning = estimate_rim_price(net_worth, roe, k, total_shares,
                                                                           self_hold_shares, w)

    try:
        # disparity = round((cur_price / est_price) * 100, 2)
        # disparity10 = round((cur_price / est_price1) * 100, 2)
        # disparity20 = round((cur_price / est_price2) * 100, 2)

        #    1 - (est_price/cur_price) , 현재가가 목표가보다 얼마나 저렴한지, 목표가일때 얻을 예상 수익
        disparity = round((1 - (est_price / cur_price)) * 100, 2)
        disparity10 = round((1 - (est_price1 / cur_price)) * 100, 2)
        disparity20 = round((1 - (est_price2 / cur_price)) * 100, 2)
    except:
        disparity = None
        disparity10 = None
        disparity20 = None
    # print(f'{cur_price}:{disparity};{disparity10}:{disparity20}')

    if est_price is not None and est_price > 0:
        est_price = round(est_price)

    if est_price1 is not None and est_price1 > 0:
        est_price1 = round(est_price1)

    if est_price2 is not None and est_price2 > 0:
        est_price2 = round(est_price2)

    return disparity, disparity10, disparity20, est_price, est_price1, est_price2


def get_price_level(cur_price, prices):
    if cur_price < prices[2]:
        level = 3
    elif cur_price < prices[1]:
        level = 2
    elif cur_price < prices[0]:
        level = 1
    else:
        level = 0
    return level


if __name__ == "__main__":
    k = reader.get_5years_earning_rate()


def printf(format, *values):
    print(format % values)


def null_check(value):
    if value is not None:
        return value
    else:
        return 0


def is_per_compare_sector(cur_per, sector_per):
    return float(null_check(cur_per)) < float(null_check(sector_per))


def make_dividend_stock(capitalrto, dividend):
    return float(null_check(capitalrto)) > 50 and float(null_check(dividend)) > 0
