import pystocklib.srim as srim
import pystocklib.srim.reader as srim_reader
from build.lib.pystocklib.srim import printf

k = srim_reader.get_5years_earning_rate()

# todo 종목코드 , 명 입력받기

code_list = [
    ["357780" ,"솔브레인"],
    ["011170", "롯데케미칼"],
             ["097950","CJ제일제당"], ["069960","현대백화점"],
             ["017670","SK텔레콤"],
             ["009150","삼성전기"],
             ["011070","LG이노텍"],
             ["012630", "HDC"],
["078340","컴투스"],
             ["035900", "JYP Ent."],
["001680","대상"]]


print("code, codeName, curPrice, 싼가?, 적정주가, 10%이익 감소가, 20%이익 감소가, ROE, 요구수익률(BBB-5년 회사채)\n")
for i, code in enumerate(code_list):
    #print(f"{i}/{len(code_list)}", {code[0]}, {code[1]}, end="\t")
    # price, shares, value, net_worth, roe, excess_earning, price1, price2
    price = srim.estimate_price(code[0], k, w=0)
    curPrice = srim_reader.get_current_price(code[0])
    cheapflag = srim_reader.compare_price(curPrice, price[7])
    roe = price[4]
    v = ""
    if roe < k :
        v="ROE가 요구수익률보다 낮다. 현재만 보면 투자하면 안된다!"
    pp = f'{code[0]}, {code[1]}, {curPrice}, {cheapflag}, {v} {round(price[0],2)}, {round(price[6],2)}, {round(price[7],2)},{round(price[4],2)}, {k}'
    print(f'{i}:{pp}')
    #https://finance.naver.com/item/sise_time.nhn?code=272450&thistime=202011191406

