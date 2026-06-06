"""
수정된 라벨 기반 파싱으로 오늘자(DB 최신일) 종목을 재파싱하여 올바른 S-RIM 결과 도출.
- get_row_by_label 로 ROE/EPS/지배주주지분 행을 '라벨'로 찾음(인덱스 밀림 방지)
- is_roe_reliable + 지배주주지분<=0 으로 자본잠식 종목 제외
출력: 콘솔 표 + srim_today_fixed_<날짜>.csv
"""
import warnings; warnings.filterwarnings('ignore')
import sys, time, csv
import pandas as pd
import pymysql
import pystocklib.srim.reader as srim_reader
import pystocklib.srim.reader_hh as hh
import pystocklib.srim.srim_calculator as calc

# 1) 대상 코드 = DB 최신일 적재 종목
conn = pymysql.connect(host='localhost', user='srim_user', password='srim_user_123', db='srim', charset='utf8')
cur = conn.cursor()
cur.execute("SELECT MAX(last_update) FROM my_srim_result")
day = cur.fetchone()[0]
cur.execute("SELECT code, name FROM my_srim_result WHERE last_update=%s ORDER BY code", (day,))
targets = cur.fetchall()
conn.close()
print(f'기준일 {day} / 대상 {len(targets)}종목 재파싱 시작')

k = srim_reader.get_5years_earning_rate()
print('요구수익률 k =', k)

rows = []
excluded = []
for i, (code, name) in enumerate(targets, 1):
    if i % 50 == 0:
        print(f'  {i}/{len(targets)} ...')
        time.sleep(0.5)
    try:
        df = pd.read_html(hh.get_html_fnguide(code, gb=0))
        cur_price = calc.won_convert_to_float(calc.parsing_string_sep(df[0][1][0], "/", 0))
        total_shares = calc.won_convert_to_float(calc.parsing_string_sep(df[0][1][6], "/", 0))
        jemu = df[10].values
        jasa = df[4].values
        self_hold_shares = jasa[4][2]

        roe_row = hh.get_row_by_label(jemu, 'ROE', 17)
        capital_row = hh.get_row_by_label(jemu, '지배주주지분', 9)

        # 자본잠식/비정상 ROE 가드
        if not hh.is_roe_reliable(roe_row):
            excluded.append((name, code, 'ROE비정상(자본잠식/일회성)'))
            continue
        capital = hh.get_financial_highlight(capital_row)
        if not hh.is_equity_positive(capital):
            excluded.append((name, code, '지배주주지분<=0 이력'))
            continue

        roes = hh.get_financial_highlight(roe_row)
        rep_roe = hh.get_roe_average(roes)
        net_worth = capital[2] * 100000000

        disparity, d10, d20, est0, est1, est2 = calc.get_srim_disparity(
            cur_price, net_worth, rep_roe, k, total_shares, self_hold_shares, w=0)
        rows.append([name, code, int(cur_price or 0), est0, est1, est2,
                     disparity, round(rep_roe, 2)])
    except Exception as e:
        excluded.append((name, code, f'parse err: {e}'))
        continue

# 정렬: 괴리율(disparity) 높은 순 = 현재가가 적정가 대비 저렴(=상승여력 큼)
rows = [r for r in rows if r[6] is not None]
rows.sort(key=lambda r: r[6], reverse=True)

out = f'/Users/umzzi/dev/PycharmProjects/pystocklib/examples/S-RIM/srim_today_fixed_{day}.csv'
with open(out, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['name', 'code', 'cur_price', 'est0', 'est1', 'est2', 'disparity(%)', 'rep_roe'])
    w.writerows(rows)

print()
print(f'유효 결과: {len(rows)}종목 / 제외: {len(excluded)}종목')
print(f'CSV 저장: {out}')
print()
print(f'{"name":<16}{"cur":>9}{"est0":>10}{"disp%":>8}{"roe":>8}')
print('-' * 51)
for r in rows[:25]:
    name, code, cur, est0, est1, est2, disp, roe = r
    print(f'{name[:15]:<16}{cur:>9}{est0:>10}{disp:>8}{roe:>8}')

print()
print('--- 제외 사유 상위 ---')
from collections import Counter
for reason, cnt in Counter(e[2].split(':')[0] for e in excluded).most_common(6):
    print(f'  {cnt:>4}  {reason}')
