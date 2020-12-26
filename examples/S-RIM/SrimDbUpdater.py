from threading import Timer

import pandas as pd
import requests
from bs4 import BeautifulSoup
import urllib, pymysql, calendar, time, json
from urllib.request import urlopen
from datetime import datetime
import math


class SrimDbUpdater:
    def __init__(self):
        """생성자: MariaDB 연결 및 종목코드 딕셔너리 생성"""
        self.conn = pymysql.connect(host='localhost', user='root',
                                    password='1234', db='INVESTAR', charset='utf8')
        with self.conn.cursor() as curs:
            sql = """
                  CREATE TABLE IF NOT EXISTS my_srim_result (
                      code VARCHAR(20),
                      name varchar(100),
                      cur_price bigint(20),
                      est_level bigint(20),
                      est_price0 bigint(20),
                      est_price1 bigint(20),
                      est_price2 bigint(20),
                      disparity0 bigint(10),
                      disparity1 bigint(10),
                      disparity2 bigint(10),
                      rep_roe float(10),
                      is_cheap_per boolean,
                      eps bigint(10),
                      eps_expect_ratio float(10),
                      market_cap bigint(20),
                      trading_cnt bigint(20),
                      last_update DATE,
                      PRIMARY KEY (code,last_update))
                  """
            curs.execute(sql)
        self.conn.commit()
        self.codes = dict()

    def __del__(self):
        """소멸자: MariaDB 연결 해제"""
        self.conn.close()

    def is_nan_check(self, value, retval=0):
        if math.isnan(value):
            ret = retval
        else:
            ret = value
        return ret

    def update_srim_db(self, hopedate=None):
        if hopedate is not None:
            curdate = hopedate
            dateformat = hopedate
        else:
            curdate = datetime.now().strftime('%Y%m%d')
            dateformat = "DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i:%s')"

        df = pd.read_excel('./srim_my_daily/srim_hh_'+curdate+'.xlsx')

        with self.conn.cursor() as curs:
            for r in df.itertuples():
                eps_expect_this_year_ratio = self.is_nan_check(r.eps, 0.0)
                eps = self.is_nan_check(r.eps)
                est_price = self.is_nan_check(r.est_price)
                est_price1 = self.is_nan_check(r.est_price1)
                est_price2 = self.is_nan_check(r.est_price2)
                disparity = self.is_nan_check(r.disparity)
                disparity1 = self.is_nan_check(r.disparity1)
                disparity2 = self.is_nan_check(r.disparity2)
                market_cap = self.is_nan_check(r.market_cap)
                trading_cnt = self.is_nan_check(r.trading_cnt)

                sql = f"REPLACE INTO my_srim_result VALUES ('{r.code}','{r.name}', {r.price}," \
                      f"{r.est_level},{est_price},{est_price1},{est_price2}," \
                      f"{disparity},{disparity1},{disparity2},{r.rep_roe},{r.is_cheap_comp_per}," \
                      f"{eps},'{eps_expect_this_year_ratio}',{market_cap}, {trading_cnt}," \
                      f"{dateformat})"
                print(sql)
                curs.execute(sql)
                self.conn.commit()

if __name__ == '__main__':
    dbu = SrimDbUpdater()
    dbu.update_srim_db()