"""
전체 시장 독립 스크리너용 원시 지표 수집기 (S-RIM 필터 없음).

KOSPI+KOSDAQ 전 종목의 PER / PBR / 추정PER(forward) / EPS성장 / PEG / ROE 등을
크롤·파싱해 그대로 CSV로 저장한다. S-RIM 적합성 판정을 하지 않으므로, 이후
어떤 스크린(PEG/마법공식/주도주 등)이든 이 CSV에 오프라인으로 적용할 수 있다.

크롤은 getFnguide.py와 동일하게 스레드 풀 병렬. gb=3(투자지표) 한 번만 받아 빠르다.
가격은 네이버 polling API, EPS/BPS/PER/PBR/시총은 FnGuide gb=3. gb=0/gb=2가
2026-06-22 FnGuide 개편으로 무력화된 이후의 대체 소스 — 자세한 내용은
getFnguide.py의 process_stock() 주석과 CLAUDE.md 참고.
사용:  python screen_metrics.py [워커수=8]
출력:  ./screen_metrics_<YYYYMMDD>.csv
"""
import sys
from datetime import date
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from pystocklib.common import *
import pystocklib.srim.reader_hh as hh
import pystocklib.srim.srim_calculator as calc

MAX_WORKERS = int(sys.argv[1]) if len(sys.argv) > 1 else 8


def fnum(x):
    try:
        return float(str(x).replace(',', ''))
    except (TypeError, ValueError):
        return None


kospi = get_code_list_by_market(market=2)
kosdaq = get_code_list_by_market(market=3)
mdf = pd.concat([kospi, kosdaq])
codes = list(mdf.index)

rows = []


def process(acode):
    """한 종목의 원시 지표를 rows(전역)에 append. 실패/데이터부족이면 그냥 return.
    필터 없음 — 값이 있으면 다 담는다. list.append는 GIL 하 원자적이라 스레드 안전."""
    code = acode[0]
    name = acode[1]
    try:
        price, trading, _ = hh.get_naver_snapshot(code)
        if not price:
            return
        inv = hh.get_invest_tables(code)
        if inv is None:
            return
        eps_list, bps_list = inv['eps_list'], inv['bps_list']
        if len(eps_list) < 2 or bps_list[-1] is None or bps_list[-1] <= 0:
            return

        roes = [round(e / b * 100, 2) if e is not None and b else None
                for e, b in zip(eps_list, bps_list)]
        rep_roe = hh.get_roe_average(roes)
        eps_incr_percent, eps_geo_avg, _ = hh.calculate_eps(eps_list)

        eps_now = eps_list[-1]
        pbr = inv['pbr_list'][-1] if inv['pbr_list'] else None
        per = round(price / eps_now, 2) if eps_now else None
        growth = eps_incr_percent[-1] if eps_incr_percent else None
        fwd_per = per  # gb=3에는 별도 컨센서스 추정EPS가 없어, 최근 실적 기준 PER을 그대로 사용
        peg = (fwd_per / growth) if (fwd_per and growth and growth > 0) else None

        rows.append({
            'code': code,
            'name': name,
            'price': price,
            'market_cap': inv['market_cap'],
            'trading_cnt': trading,
            'per': per,
            'pbr': round(pbr, 2) if pbr else None,
            'fwd_per': round(fwd_per, 2) if fwd_per else None,
            'eps': eps_now,
            'eps_expect': eps_now,
            'eps_growth': round(growth, 1) if growth is not None else None,
            'eps_geo_avg': round(eps_geo_avg, 1) if eps_geo_avg is not None else None,
            'peg': round(peg, 3) if peg else None,
            'rep_roe': round(rep_roe, 2),
            'equity': bps_list[-1],
        })
    except Exception:
        return


total = len(codes)
print(f'대상 {total}종목, {MAX_WORKERS} 스레드 병렬 수집 시작')
done = 0
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
    futures = [ex.submit(process, ac) for ac in codes]
    for fut in as_completed(futures):
        done += 1
        if done % 300 == 0:
            print(f'  {done}/{total} ...')
        try:
            fut.result()
        except Exception:
            pass

print(f'수집 완료: {len(rows)}종목')
if rows:
    out = pd.DataFrame(rows).set_index('code')
    out['_m'] = pd.to_numeric(out['market_cap'], errors='coerce')
    out = out.sort_values('_m', ascending=False).drop(columns='_m')
    fn = f"./screen_metrics_{date.today().strftime('%Y%m%d')}.csv"
    out.to_csv(fn, encoding='utf-8-sig')
    print(f'저장: {fn} ({len(out)}종목)')
