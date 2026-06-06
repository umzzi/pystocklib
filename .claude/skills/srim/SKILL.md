---
name: srim
description: >-
  pystocklib S-RIM 파이프라인 운영·조회 도구 모음. 사용자가 S-RIM 일일 실행/크롤링/DB 적재,
  적정주가·괴리율(상승여력) 결과 조회, 특정 한국 종목 재무 분석(FnGuide), 구글 드라이브/시트
  업로드·열기를 요청할 때 사용. 트리거 예: "오늘자 데이터 만들어줘", "크롤링 돌려줘", "DB 적재",
  "괴리율/상승여력 상위 종목", "시총 상위 보여줘", "OO종목 분석/이익 분석", "구글 시트 열어줘".
---

# S-RIM 운영 스킬

pystocklib S-RIM(사경인 기반 적정주가) 파이프라인의 자주 쓰는 명령 모음.

## 공통 전제
- venv: `/Users/umzzi/dev/PycharmProjects/pystocklib/venv` (시스템 python3엔 패키지 없음 — 반드시 이 venv)
- PY=`/Users/umzzi/dev/PycharmProjects/pystocklib/venv/bin/python`
- SRIM 디렉터리: `/Users/umzzi/dev/PycharmProjects/pystocklib/examples/S-RIM`
- DB: pymysql `host=localhost user=srim_user password=srim_user_123 db=srim charset=utf8`, 테이블 `my_srim_result`
- brew(rclone/mysql): `eval "$(/opt/homebrew/bin/brew shellenv)"`
- 출력 로그 필터: `2>&1 | grep -vE "NotOpenSSLWarning|warnings.warn|FutureWarning|read_html|StringIO"`

## 1. 전체 파이프라인 (크롤링→DB→구글시트 업로드)
```sh
cd /Users/umzzi/dev/PycharmProjects/pystocklib/examples/S-RIM && sh exec_srim.sh
```
- 전 종목(~2629) 순차 크롤링이라 **20~40분 소요(정상)**. 백그라운드로 돌리고 진행률(`N/2629`)을 모니터링할 것.
- crontab용: `exec_srim_cron.sh` (로그: `examples/S-RIM/logs/srim_YYYYMMDD.log`).

## 2. 단계별 실행
```sh
# 크롤링만 → CSV 생성 (진행률 실시간으로 보려면 -u)
$PY -u getFnGuide.py TRUE TRUE FALSE
# DB 적재만 (오늘자 CSV 읽음). 특정일: update_srim_db('YYYYMMDD')
$PY SrimDbUpdater.py
```
- 결과: `examples/S-RIM/srim_my_daily/srim_hh_YYYYMMDD.csv` (+ `_dividend.csv`), `utf-8-sig`, 시가총액 내림차순.
- 인자 `TRUE TRUE FALSE` = roeCheck, capitalCheck, inputCheck(FALSE=전체).

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

## 4. 특정 종목 재무 분석 (FnGuide 직접)
```sh
$PY - <<'PY'
import pandas as pd, warnings; warnings.filterwarnings('ignore')
from pystocklib.srim import reader_hh as hh
code='A005930'  # 코드 (A+6자리). 이름→코드: common.get_code_list_by_market(1)
t=pd.read_html(hh.get_html_fnguide(code,gb=1))[0]  # gb=0스냅샷 1재무 2비율 3투자 4컨센
cols=list(t.columns); lab=t.iloc[:,0].astype(str).str.replace('계산에 참여한 계정 펼치기','',regex=False)
for k in ['매출액','영업이익','금융수익','금융원가','기타수익','기타비용','종속기업','세전계속사업이익','법인세비용','지배주주순이익']:
    m=lab.str.contains(k)
    if m.any(): print(f'{k:<14}',[t[m].iloc[0][col] for col in cols[1:]])
PY
```
- 분석 포인트: 영업이익률, 순이익/영업이익(70~80% 정상, 높으면 비영업이익 큼), ROE 추세·왜곡, 멀티플(PER=시총/순이익, 시총/영업이익).

## 5. 구글 드라이브/시트
```sh
eval "$(/opt/homebrew/bin/brew shellenv)"
# 업로드 (네이티브 구글시트 변환). 날짜 치환.
rclone copy examples/S-RIM/srim_my_daily/srim_hh_YYYYMMDD.csv gdrive:srim/ --drive-import-formats csv --drive-export-formats csv -v
# 시트 ID 얻어 브라우저로 열기
id=$(rclone lsjson gdrive:srim/ | $PY -c "import json,sys;[print(f['ID']) for f in json.load(sys.stdin) if f['Name'].startswith('srim_hh_YYYYMMDD.')]")
open "https://docs.google.com/spreadsheets/d/$id"
```

## 6. 단위 테스트
```sh
$PY -m unittest pystocklib.srim.test_srim_calculator
```

## 핵심 도메인 주의 (회귀 방지)
- 모든 `requests.get`에 `timeout=15` 필수 (없으면 무한 hang).
- 괴리율 `disparity = ((적정가/현재가)-1)*100` → 저평가 +, 고평가 -.
- 결과는 CSV(`set_index('code')`+`to_csv`), 시가총액 내림차순.
- 고ROE(>100% 가드, 그 미만이라도 30%+) 종목은 적정가 왜곡 의심.
- 자세한 함정은 저장소 루트 `CLAUDE.md` 참조.
