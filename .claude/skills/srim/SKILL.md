---
name: srim
description: >-
  pystocklib S-RIM 파이프라인 운영·조회 도구 모음. 사용자가 S-RIM 일일 실행/크롤링/DB 적재,
  적정주가·괴리율(상승여력) 결과 조회, 특정 한국 종목 재무 분석(FnGuide, ROE/EPS/PER/PBR),
  구글 드라이브/시트 업로드·열기, 파이프라인이 왜 결과를 안 만드는지 디버깅할 때 사용.
  트리거 예: "오늘자 데이터 만들어줘", "크롤링 돌려줘", "DB 적재", "괴리율/상승여력 상위 종목",
  "시총 상위 보여줘", "OO종목 분석/이익 분석", "구글 시트 열어줘", "왜 안 올라가있어", "왜 안 돌았어".
---

# S-RIM 운영 스킬

pystocklib S-RIM(사경인 기반 적정주가) 파이프라인의 자주 쓰는 명령 모음.

## 공통 전제
- venv: `/Users/umzzi/dev/hh-harness/repos/pystocklib/venv` (시스템 python3엔 패키지 없음 — 반드시 이 venv)
- PY=`/Users/umzzi/dev/hh-harness/repos/pystocklib/venv/bin/python`
- SRIM 디렉터리: `/Users/umzzi/dev/hh-harness/repos/pystocklib/examples/S-RIM`
- DB: pymysql `host=localhost user=srim_user password=srim_user_123 db=srim charset=utf8`, 테이블 `my_srim_result`
- brew(rclone/mysql): `eval "$(/opt/homebrew/bin/brew shellenv)"`
- 출력 로그 필터: `2>&1 | grep -vE "NotOpenSSLWarning|warnings.warn|FutureWarning|read_html|StringIO"`

## 1. 전체 파이프라인 (크롤링→DB→구글시트 업로드)
```sh
cd /Users/umzzi/dev/hh-harness/repos/pystocklib/examples/S-RIM && sh exec_srim.sh
```
- 전 종목(~2627) **스레드 풀 병렬 크롤링**(기본 6워커) — **약 3분 소요** (검증: 2627종목/6워커/3분17초/129종목 후보). 예전엔 순차라 20~40분 걸렸으나 병렬화로 단축됨. 그래도 백그라운드로 돌리는 게 안전.
- crontab용: `exec_srim_cron.sh` (로그: `examples/S-RIM/logs/srim_YYYYMMDD.log`). launchd plist: `~/Library/LaunchAgents/com.umzzi.srim.plist` (평일 18:00 자동 실행).
- **먼저 반드시 § Gotchas의 "FnGuide 2026-06-22 개편" 항목을 읽을 것** — 이 파이프라인이 몇 주간 조용히 0종목만 생성했던 사고의 원인이자 재발 방지 포인트.

## 2. 단계별 실행
```sh
# 크롤링만 → CSV 생성 (진행률 실시간으로 보려면 -u). 5번째=워커 수(선택,기본6), 6번째=출력 파일명 날짜(선택,기본 오늘)
$PY -u getFnGuide.py TRUE TRUE FALSE 6
# DB 적재만 (오늘자 CSV 읽음). 특정 날짜 CSV를 적재하려면 인자로 YYYYMMDD 전달
$PY SrimDbUpdater.py
$PY SrimDbUpdater.py 20260610   # srim_hh_20260610.csv를 읽어 2026-06-10로 적재(재적재/백필)
```
- 결과: `examples/S-RIM/srim_my_daily/srim_hh_YYYYMMDD.csv` (+ `_dividend.csv`), `utf-8-sig`, 시가총액 내림차순.
- 인자 `TRUE TRUE FALSE` = roeCheck, capitalCheck, inputCheck(FALSE=전체), 5번째(선택)=워커 수, 6번째(선택)=출력 파일명 날짜(`YYYYMMDD`, 미지정시 오늘). ⚠️ 크롤은 항상 FnGuide/네이버의 **현재 시점** 데이터를 가져온다 — 6번째 인자는 과거 시세를 재현하는 게 아니라 결과 파일의 날짜 라벨만 바꾼다(자정 걸친 실행·백필용).
- `SrimDbUpdater.py [YYYYMMDD]` — 인자 없으면 오늘자 CSV를 오늘 날짜로 적재. 인자를 주면 그 날짜의 기존 CSV를 그 날짜로 재적재(검증: 20260610 → DB `last_update='2026-06-10'` 283종목 정상 반영).
- 소규모 스모크테스트: `inputCheck=TRUE`로 주면 내장 ~40종목 샘플만 돌아 수 초 내 확인 가능 — `$PY getFnGuide.py FALSE FALSE TRUE 4`.
- `$PY screen_metrics.py [워커수=8]` — S-RIM 필터 없이 전 종목 PER/PBR/EPS성장/PEG 원시 지표만 뽑는 별도 도구(마법공식/PEG 등 커스텀 스크린 베이스용). `./screen_metrics_YYYYMMDD.csv`로 저장, 검증: 2627종목 중 2473종목(94%) 수집.

## 3. 결과 조회 (DB)
```sh
$PY - <<'PY'
import pymysql
c=pymysql.connect(host='localhost',user='srim_user',password='srim_user_123',db='srim',charset='utf8').cursor()
c.execute("SELECT MAX(last_update) FROM my_srim_result"); d=c.fetchone()[0]
# 상승여력(괴리율) 상위 — disparity0: 저평가 +, 고평가 -
c.execute("SELECT code,name,cur_price,est_price0,disparity0,rep_roe,market_cap FROM my_srim_result WHERE last_update=%s ORDER BY disparity0 DESC LIMIT 10",(d,))
for r in c.fetchall(): print(r)
PY
```
- 정렬 바꾸기: `ORDER BY market_cap DESC`(시총), `disparity0 DESC`(상승여력).
- ⚠️ ROE 30%+ 종목은 고ROE/일회성이익 왜곡 의심 → 별도 확인. mysql CLI에 한글 쓰면 인코딩 깨짐, 검증은 pymysql로.

## 3b. 결과 파일(CSV) 보기 — 오늘자 없으면 최신 자동
"오늘자 결과 보여줘 / 최신 결과 파일" 류 요청에 사용. DB가 아니라 파이프라인이 떨군 CSV를 직접 읽는다.
```sh
$PY - <<'PY'
import glob, os, datetime, pandas as pd
d = '/Users/umzzi/dev/hh-harness/repos/pystocklib/examples/S-RIM/srim_my_daily'
today = datetime.date.today().strftime('%Y%m%d')
f = os.path.join(d, f'srim_hh_{today}.csv')
if not os.path.exists(f):
    # 오늘자 없음 → 날짜 내림차순 최신 CSV (배당 변형 제외)
    cands = sorted(g for g in glob.glob(os.path.join(d,'srim_hh_*.csv')) if '_dividend' not in g)
    assert cands, '결과 CSV가 없음'
    f = cands[-1]
    print(f'⚠️ 오늘자({today}) 없음 → 최신 사용: {os.path.basename(f)}')
df = pd.read_csv(f)            # utf-8-sig BOM 자동 처리
print(f'파일: {os.path.basename(f)} | {len(df)}종목 | 시총 내림차순')
cols = ['name','price','est_price','disparity','rep_roe','market_cap']
cols = [c for c in cols if c in df.columns]
import pandas as pd; pd.set_option('display.width',160); pd.set_option('display.unicode.east_asian_width',True)
print(df[cols].head(15).to_string(index=False))   # 상위 15 (시총 기준)
PY
```
- 정렬 바꾸기: `df.sort_values('disparity', ascending=False)`(상승여력 상위), `df.sort_values('rep_roe', ascending=False)`(고ROE).
- 특정일: `today` 자리에 `'YYYYMMDD'` 직접 지정. 배당 포함본은 `_dividend.csv`.
- ⚠️ disparity는 +면 저평가(상승여력), −면 고평가. ROE 30%+는 왜곡 의심(단 `DISPARITY_MAX=200`으로 극단값은 이미 후보에서 자동 제외됨).
- ⚠️ CSV의 `지배주주자본` 컬럼은 **총액이 아니라 BPS(주당순자산) 리스트**다(2026-06-22 이후 소스 변경, 컬럼명은 유지됨 — Gotchas 참고).

## 4. 특정 종목 매출/영업이익 분석 (FnGuide gb=1, 비금융주 전용)
```sh
$PY - <<'PY'
import pandas as pd, warnings; warnings.filterwarnings('ignore')
from pystocklib.srim import reader_hh as hh
code='A005930'  # 코드 (A+6자리). 이름→코드: common.get_code_list_by_market(1)
t=pd.read_html(hh.get_html_fnguide(code,gb=1))[0]  # gb=0죽음(아래 Gotchas) 1재무제표 2재무비율(죽음) 3투자지표
cols=list(t.columns); lab=t.iloc[:,0].astype(str).str.replace('계산에 참여한 계정 펼치기','',regex=False)
for k in ['매출액','영업이익','지배주주순이익']:
    m=lab.str.contains(k)
    if m.any(): print(f'{k:<14}',[t[m].iloc[0][col] for col in cols[1:]])
PY
```
- 분석 포인트: 영업이익률, 순이익/영업이익(70~80% 정상, 높으면 비영업이익 큼).
- ⚠️ **금융업(은행/증권/보험/지주) 종목은 gb=1 재무제표 구조가 완전히 달라 이 방식이 실패한다** — 매출액 항목 자체가 없음. ROE/EPS/BPS/PER/PBR이 필요하면 아래 4b(gb=3 기반, 전 업종 동일 구조)를 쓸 것.

## 4b. 종목 ROE/EPS/BPS/PER/PBR 분석 — 전 업종 대응 (권장)
gb=1보다 안정적인 소스. 은행/증권 등 금융업종에서도 동일하게 동작함을 확인함(검증: KB금융).
```sh
$PY - <<'PY'
from pystocklib.srim import reader_hh as hh
code='A105560'  # KB금융
price, vol, name = hh.get_naver_snapshot(code)          # 현재가/거래량 (네이버)
inv = hh.get_invest_tables(code)                        # EPS/BPS/DPS/PER/PBR/SPS/시총 (FnGuide gb=3)
roes = [round(e/b*100,2) for e,b in zip(inv['eps_list'], inv['bps_list']) if e and b]
print(name, price, '연도별ROE:', roes, '대표ROE(5년가중):', round(hh.get_roe_average(roes),2), '시총(억):', inv['market_cap'])
print('PER 히스토리:', inv['per_list'], 'PBR 히스토리:', inv['pbr_list'])
PY
```
- `get_invest_tables()`가 리스트로 주는 값은 전부 **오래된→최근 연도 순**.
- `getFnguide.py`의 `process_stock()`이 이 두 함수로 전체 파이프라인을 돌린다 — 개별 종목 디버깅 시 참고할 실제 코드 위치.

## 5. 구글 드라이브/시트
```sh
eval "$(/opt/homebrew/bin/brew shellenv)"
# 업로드 (네이티브 구글시트 변환). 날짜 치환.
rclone copy examples/S-RIM/srim_my_daily/srim_hh_YYYYMMDD.csv gdrive:srim/ --drive-import-formats csv --drive-export-formats csv -v
# 시트 ID 얻어 브라우저로 열기
id=$(rclone lsjson gdrive:srim/ | $PY -c "import json,sys;[print(f['ID']) for f in json.load(sys.stdin) if f['Name'].startswith('srim_hh_YYYYMMDD.')]")
open "https://docs.google.com/spreadsheets/d/$id"
```
- ⚠️ Drive 업로드는 외부로 데이터를 반출하는 작업이라 자동 모드에서 실행이 막힐 수 있다 — 이 경우 사용자에게 명시적으로 승인받고 진행할 것.

## 6. 단위 테스트
```sh
$PY -m unittest pystocklib.srim.test_srim_calculator
```

## Gotchas
- **⚠️ FnGuide 2026-06-22 개편으로 gb=0(Snapshot)·gb=2(재무비율)가 완전히 죽었다 (회귀 시 재발하는 사고 원인)**: 그날 FnGuide 프론트 배포 이후 (1) gb=0은 어떤 `gicode`를 넣어도 항상 삼성전자 페이지를 반환하는 서버측 캐시 버그가 생겼고, (2) 그 안의 재무하이라이트 표가 JS 렌더링으로 바뀌어 `pd.read_html`이 빈 `<table>`에서 `IndexError`로 페이지 전체 파싱에 실패하며, (3) gb=2는 완전히 빈 페이지가 됐다. 이 때문에 2026-06-29~07-10 동안 크롤은 매일 정상 실행됐지만 **모든 종목이 예외로 스킵돼 후보 0종목 → CSV 미생성 → DB 적재/Drive 업로드가 전부 조용히(에러 없이) 실패**했다. 증상은 "launchd가 안 돈다"처럼 보이지만 실제로는 launchd/크롤/MySQL/rclone 전부 정상이었고 데이터 소스만 죽어 있었다 — 실제로 launchd/스레드수 등을 먼저 의심하면 헛수고다, `srim_my_daily/`에 오늘자 CSV가 실제로 생겼는지부터 확인할 것. **gb=0/gb=2는 다시 쓰지 말 것** — 대신 `get_naver_snapshot`(현재가)+`get_invest_tables`(gb=3, EPS/BPS/PER/PBR/시총)를 쓴다(§4b).
- **`rederive_today.py`는 여전히 gb=0 기반이라 지금 깨져 있음(미수정)**: 재현·재도출용 보조 스크립트인데, `getFnguide.py`처럼 `get_invest_tables`/`get_naver_snapshot` 기반으로 재작성되지 않았다. 이 스크립트를 쓰기 전에 먼저 재작성이 필요하다.
- 모든 `requests.get`에 `timeout=15` 필수 (없으면 무한 hang).
- 괴리율 `disparity = ((적정가/현재가)-1)*100` → 저평가 +, 고평가 -.
- 결과는 CSV(`set_index('code')`+`to_csv`), 시가총액 내림차순. 0종목이면 파일 자체가 생성되지 않는다(`if data:`) — CSV가 없다는 건 곧 "크롤이 실패했다"는 신호.
- 대표 ROE는 5년 가중평균(최근 연도 가중치 큼), 음수 ROE는 0으로 가리지 않고 그대로 반영, 단년 급등은 양수해 중앙값의 2배로 완충. 상승여력이 `DISPARITY_MAX=200%`를 넘으면 후보에서 자동 제외.
- 자세한 함정·전체 아키텍처는 저장소 루트 `CLAUDE.md` 참조(이 스킬보다 더 자세함).
