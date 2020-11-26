from pystocklib.common import *
import pystocklib.srim as srim
import pystocklib.srim.reader as srim_reader
import time
import pandas as pd

ret = srim_reader.get_shares("014440")
print(ret)