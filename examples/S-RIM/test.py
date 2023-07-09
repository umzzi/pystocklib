import numbers
import sys

import requests
from bs4 import BeautifulSoup
import pystocklib.srim.reader_hh as hh_reader

company_code = "000660"
now_price = hh_reader.get_naver_price(company_code)
print(now_price)


df = hh_reader.read_naver(company_code, "SK하이닉스", 1)
print(df)