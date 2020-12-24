from threading import Timer

import pandas as pd
import requests
from bs4 import BeautifulSoup
import urllib, pymysql, calendar, time, json
from urllib.request import urlopen
from datetime import datetime


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
                      last_update DATE,
                      PRIMARY KEY (code,last_update))
                  """
            curs.execute(sql)
        self.conn.commit()
        self.codes = dict()

    def __del__(self):
        """소멸자: MariaDB 연결 해제"""
        self.conn.close()

    def update_srim_db(self):
        #excel 파일 열기
        curdate = datetime.now().strftime('%Y%m%d')
        df = pd.read_excel('./srim_my_daily/srim_hh_'+curdate+'.xlsx')
        with self.conn.cursor() as curs:
            for r in df.itertuples():
                sql = f"REPLACE INTO my_srim_result VALUES ('{r.code}','{r.name}', {r.price}," \
                      f"{r.est_level},{r.est_price},{r.est_price1},{r.est_price2},DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i:%s'))"
                print(sql)
                curs.execute(sql)
                self.conn.commit()

if __name__ == '__main__':
    dbu = SrimDbUpdater()
    dbu.update_srim_db()