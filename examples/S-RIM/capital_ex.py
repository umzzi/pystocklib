from pystocklib.common import *
import pystocklib.srim as srim
import pystocklib.srim.reader as srim_reader
import time
import pandas as pd

ret = srim_reader.get_capital_value("001680")
if ret[0]:
    print("지배주주자본이 증가한다.")
    print(ret[1])
ret = srim_reader.get_aggregate_value("001680")
print(ret)
#code="032980"
code="001680"
aval_flag = srim_reader.get_is_aggreagate_up(code, 2000)
print(aval_flag)
if aval_flag:
    print("시총이 2000억 이상")
else:
    print("ㅜㅐ")