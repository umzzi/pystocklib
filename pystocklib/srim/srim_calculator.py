import pystocklib.srim.reader as reader


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
    if total_shares is not None and self_hold_shares is not None:
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

    if value is not None and shares is not None:
        price = value / shares

    if value1 is not None:
        price1 = value / shares

    if value2 is not None:
        price2 = value / shares

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
        disparity = round((cur_price / est_price) * 100,2)
        disparity10 = round((cur_price / est_price1) * 100,2)
        disparity20 = round((cur_price / est_price2) * 100,2)
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
