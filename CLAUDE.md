# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

pystocklib — S-RIM(사경인 회계사) 기반 한국 주식 적정주가 평가 라이브러리 + 일일 크롤링/DB 파이프라인.

## 환경
- **venv**: `/Users/umzzi/dev/hh-harness/repos/pystocklib/venv` (Python 3.9, arm64)
- **의존성**: `requirements.txt` (pandas, requests, beautifulsoup4, pymysql, numpy, urllib3, lxml, openpyxl, html5lib, xlsxwriter 등) + `pystocklib`(editable `pip install -e .`). 재현: `python3 -m venv venv && ./venv/bin/pip install -r requirements.txt && ./venv/bin/pip install -e .`
- 시스템 python3에는 패키지가 없으므로 반드시 위 venv 사용. (`source venv/bin/activate`)

## 자주 쓰는 명령
- **S-RIM 일일 실행**: `cd examples/S-RIM && sh exec_srim.sh` (crontab용은 `exec_srim_cron.sh`)
- **단일 단계 디버깅**: `python examples/S-RIM/getFnguide.py TRUE TRUE FALSE` (크롤링만), `python examples/S-RIM/SrimDbUpdater.py` (DB 적재만)
- **단위 테스트**: `python -m unittest pystocklib.srim.test_srim_calculator` (단일: `... test_srim_calculator.TestCase.test_self_shares_count`). pytest 미설치, `unittest` 사용.
- **라이브러리 단독 확인**: 대부분의 모듈에 `if __name__ == "__main__"` 블록이 있어 직접 실행 가능.
- **`srim` 스킬**: `.claude/skills/srim`에 일일 실행·크롤링·DB 적재·결과 조회(괴리율/시총 상위)·종목 분석·구글 업로드 절차가 캡슐화돼 있다. 해당 작업은 명령을 직접 조립하기 전에 이 스킬을 먼저 확인.

## 아키텍처 (big picture)
두 개의 계층 — 재사용 패키지 `pystocklib/`와 운영 스크립트 `examples/S-RIM/`.

### `pystocklib/` 패키지 (데이터 소스 = comp.fnguide.com 스크래핑)
- `common/__init__.py` — 스크래핑 헬퍼. `get_element(s)_by_css_selector`(CSS 셀렉터로 FnGuide 페이지 파싱), `get_code_list_by_market`(상장종목 코드/명 조회, market 1=전체/2=코스피/3=코스닥).
- **S-RIM 구현이 두 갈래로 병존** (둘 다 FnGuide에서 읽지만 방식이 다름):
  1. **per-stock API** — `srim/reader.py` + `srim/__init__.py`. 종목당 `SVD_main.asp` 페이지를 **행 인덱스가 하드코딩된 CSS 셀렉터**(예: `tr:nth-child(10) > td:nth-child(4)`)로 단건 추출. `estimate_company_value`/`estimate_price`/`get_disparity` 제공.
  2. **bulk 엔진 ("hh")** — `srim/reader_hh.py` + `srim/srim_calculator.py`. FnGuide 5개 리포트 탭(main/Finance/FinanceRatio/Invest/Consensus) 전체 HTML을 받아 테이블 파싱 후 항목 추출. **운영 파이프라인이 쓰는 쪽.** 순수 계산 함수(`estimate_rim`, `estimate_rim_price`, `get_srim_disparity`, PEGR/기하평균 등)는 `srim_calculator.py`에 있고 I/O와 분리되어 단위 테스트 대상.
- ⚠️ 모든 데이터가 FnGuide HTML 레이아웃에 의존 → 셀렉터/행 위치가 바뀌면 조용히 깨짐(잘못된 값 또는 None). 값 이상 시 먼저 셀렉터를 의심할 것.

### `examples/S-RIM/` 파이프라인
- `getFnguide.py` → `SrimDbUpdater.py` 2단계 (`exec_srim.sh`가 순차 실행).
  - ① `getFnguide.py <roeCheck> <capitalCheck> <inputCheck>` (예: `TRUE TRUE FALSE`): 전 종목(~2629개)을 `reader_hh`로 순차 크롤링 → 적정주가 계산 → CSV 출력(시가총액 내림차순 정렬). 1회 20~40분 소요(정상). `inputCheck=FALSE`면 전체, `TRUE`면 스크립트 상단 `input_data` 화이트리스트만.
  - ② `SrimDbUpdater.py`: CSV(`pd.read_csv`)를 읽어 MySQL `my_srim_result` 테이블 upsert.
- 출력: `examples/S-RIM/srim_my_daily/srim_hh_YYYYMMDD.csv` (배당 있으면 `srim_hh_YYYYMMDD_dividend.csv` 추가, 인코딩 `utf-8-sig`). code는 인덱스로 첫 컬럼에 기록.
- `01~03_*.py`, `my_portfolio*.py` 등은 패키지 사용 예제/분석 스크립트(파이프라인 비포함).

## DB (MySQL, brew, localhost:3306)
- 접속: user `srim_user` / pw `srim_user_123` / db `srim` (root 아님)
- 테이블 `my_srim_result` (PK: code, last_update) — 스크립트가 자동 생성.
- brew 경로: `eval "$(/opt/homebrew/bin/brew shellenv)"`; 서비스: `brew services start mysql`
- ⚠️ mysql CLI에 한글 별칭/문자 쓰면 셸 인코딩 깨짐 → 검증은 pymysql(charset utf8)로.

## 알려진 함정 (이미 해결됨 — 회귀 주의)
- **HTTP 타임아웃 필수**: `requests.get`에 `timeout=` 없으면 FnGuide 응답 지연 시 무한 hang. `common/__init__.py`, `srim/reader_hh.py`의 모든 요청에 `timeout=15` 적용됨. 새 요청 추가 시에도 반드시 붙일 것.
- **결과 출력은 CSV**: `getFnguide.py`는 `df.set_index('code')` 후 `to_csv`로 저장(code가 첫 컬럼, name은 일반 컬럼). 정렬 기준은 시가총액 내림차순(`market_cap`을 숫자로 변환 후 정렬). 과거 xlsx 출력 시절의 "커스텀 헤더 루프 한 칸 밀림" 함정은 CSV 전환으로 제거됨.
- `SrimDbUpdater.py`는 CSV를 `pd.read_csv`로 읽고 `itertuples`로 `r.code`/`r.name` 등 접근. 컬럼명이 코드의 `r.xxx`와 일치해야 함.
- **괴리율(disparity) 부호 = 상승여력**: `srim_calculator.get_srim_disparity`의 disparity = `((적정가/현재가) - 1) * 100`. 저평가(적정가>현재가)면 **+**, 고평가면 **−**. (과거 `(1 - 적정가/현재가)`로 부호가 뒤집혀 있던 버그 수정함 — 회귀 주의.)
- **FnGuide 표 파싱은 라벨 기반**: `getFnguide.py`는 Financial Highlight 표(`df[10]`)의 행을 위치 인덱스가 아니라 `reader_hh.get_row_by_label(jemu, 'ROE', 17)`로 찾음. FnGuide가 행을 추가/삭제해도 ROE/EPS/지배주주지분을 라벨로 찾아 인덱스 밀림에 강건(못 찾으면 기존 위치로 폴백). 단 표 자체의 순번(`df[8]`=stock, `df[10]`=jemu, `df[4]`=자사주)은 아직 위치 의존이므로 표 추가/삭제 시 별도 점검 필요.
- **자본잠식/비정상 ROE 종목은 S-RIM 제외**: 자본이 0에 수렴했던(완전잠식 또는 지배주주지분 ≤ 0 이력) 회사는 ROE가 1270%처럼 폭주해 적정주가를 왜곡함. `reader_hh.is_roe_reliable`(`|ROE|>100%`·'잠식' 마커)와 `is_equity_positive`(지배주주지분 이력에 0 이하)로 거른다. 정상 종목 ROE는 한 자리~수십%라 영향 없음. 결과의 ROE가 60%+로 보이면 이 가드를 의심.
- **큰 괴리율은 버그가 아님**: ROE ≫ k(요구수익률)인 고ROE주는 S-RIM 공식상 적정가가 현재가의 수 배로 나옴(초과이익 영구 자본화). 파싱 오류와 구분할 것.
- **오늘자 결과 재도출 도구**: `examples/S-RIM/rederive_today.py` — DB 최신일 종목을 라벨 파싱+가드로 재계산해 `srim_today_fixed_<날짜>.csv` 생성(전체 파이프라인 20~40분 없이 검증용).
