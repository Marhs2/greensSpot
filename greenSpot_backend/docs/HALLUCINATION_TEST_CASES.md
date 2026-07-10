# GreenSpot — 문서·구현 불일치(환각) 탐지 테스트 케이스

| 항목 | 내용 |
| --- | --- |
| 문서 버전 | 1.0 |
| 작성일 | 2026-07-09 |
| 목적 | **문서가 주장하는 기능/계약과 실제 구현이 다른 지점**을 찾기 위함 |
| 범위 | 백엔드 (`app/`, 라우트, 서비스, 모델) ↔ `docs/api.md`, `docs/기능명세서.md`, `docs/sql.md` |
| 비범위 | 단순 사용성 QA, 성능 튜닝, 프론트 UI 픽셀 |

### 용어

| 용어 | 의미 |
| --- | --- |
| **스펙 드리프트** | 문서에 적힌 동작·필드·상태코드와 구현이 다름 |
| **데이터 환각** | 실제 조회/계산하지 않은 값을 실측처럼 표시 (`actual:true`, 가짜 0, 출처 위장) |
| **LLM 환각** | explain/agent 요약이 facts·검색 결과에 없는 수치·부지·출처를 생성 |
| **과대 문서화** | 구현에 없는 API·필드·역할을 문서가 존재하는 것처럼 기술 |
| **과소 문서화** | 구현은 있으나 문서에 없거나 반대로 기술 |

### 판정

| 판정 | 의미 |
| --- | --- |
| **MATCH** | 문서 주장 = 구현 동작 |
| **DRIFT** | 문서 ≠ 구현 (수정 대상: 문서 또는 코드) |
| **HALLUC** | 데이터가 출처·실측 주장과 모순 |
| **N/A** | 키 없음 등으로 검증 불가 |

각 TC는 **문서 Claim → 관측 방법 → DRIFT/HALLUC 조건** 구조다.  
“기능이 잘 된다”가 아니라 **“문서/출처 주장과 같은가?”** 를 본다.

### 기준 문서 버전 앵커

- `docs/api.md` (2026-07-09)
- `docs/기능명세서.md` (2026-07-09)
- `docs/sql.md` (2026-07-09)
- `docs/README.md` 핵심 개념

### 관측 수단

1. OpenAPI: `GET http://localhost:8000/openapi.json`
2. 실제 HTTP 응답 (Swagger 또는 REST client)
3. 코드 대조: `app/api/v1/*`, `app/services/*`, `app/models/models.py`, `app/schemas/schemas.py`
4. (선택) DB: `greenspot.db` 테이블/컬럼

---

# A. 라우트·스코프 계약 (과대/과소 문서화)

문서에 있는 엔드포인트가 실제로 존재하는가, 문서에 없다고 한 것이 실제로 없는가.

### TC-A-001 OpenAPI ↔ api.md 엔드포인트 집합

| 항목 | 내용 |
| --- | --- |
| Claim | `api.md` Prefix 표 및 엔드포인트 목록이 서버 라우트와 일치 |
| 절차 | 1. `openapi.json` paths 추출 2. `api.md` 표의 Method+URL 목록 추출 3. 집합 diff |
| DRIFT | 문서만 있음 / 구현만 있음 / method 불일치 |
| 심각도 | P0 |
| 비고 | 중복 등록(`/api/gs/history` 이중 등)도 기록 |

### TC-A-002 Visual Crossing 열섬·기온

| 항목 | 내용 |
| --- | --- |
| Claim | 열섬·일사·기온은 **Visual Crossing** (`/api/v1/gs/visualcrossing/climate\|heat\|timeline` 및 라이브 enrich) |
| 절차 | 1. openapi에 visualcrossing 경로 존재 2. `GET /api/v1/gs/visualcrossing/heat` 호출 |
| DRIFT | VC heat/climate 미존재 |
| MATCH | VC heat/climate/timeline 존재 |
| 심각도 | P1 |

### TC-A-003 관리자 API 부재

| 항목 | 내용 |
| --- | --- |
| Claim | 관리자 역할·점수 재계산 admin API 없음 |
| 절차 | `POST /api/v1/gs/admin/scores/recompute` 및 openapi에 admin 경로 검색 |
| DRIFT | 200/인증 게이트가 있는 admin 경로 존재 |
| MATCH | 404 또는 openapi 미등재 |
| 심각도 | P1 |

### TC-A-004 비밀번호 재설정 부재

| 항목 | 내용 |
| --- | --- |
| Claim | F-21 비밀번호 재설정 미제공 |
| 절차 | openapi / 라우트에 reset, forgot-password 검색 |
| DRIFT | 관련 엔드포인트 존재 |
| 심각도 | P2 |

### TC-A-005 API Prefix 이중 구조

| 항목 | 내용 |
| --- | --- |
| Claim | 메인 앱 `/api/gs`, 인증 `/api`, 연동 `/api/v1/gs` (문서 초안의 단일 `/api/v1/gs/parcels` 아님) |
| 절차 | `GET /api/v1/gs/parcels` vs `GET /api/gs/parcels` |
| DRIFT | 문서가 “통일됨”으로 읽히는데 한쪽만 동작; 또는 둘 다 동작해 문서 설명과 불일치 |
| 심각도 | P1 |

### TC-A-006 trending/history 미제공

| 항목 | 내용 |
| --- | --- |
| Claim | `GET /api/gs/trending`, `GET /api/gs/history` 는 **미제공 (404)** |
| 절차 | 각 path 호출 → 404 |
| DRIFT | 문서/OpenAPI에 살아 있거나 200 응답 |
| 심각도 | P1 |

---

# B. 요청·응답 스키마 드리프트

문서 예시 JSON 필드와 실제 응답 키·타입이 같은가.

### TC-B-001 목록 응답 필수 키 (F-01 / api List Parcels)

| 항목 | 내용 |
| --- | --- |
| Claim | `parcels`, `stats`, `source` (+ 문서 예: `vworldEnabled`) |
| 절차 | `GET /api/gs/parcels?live=false` 키 집합 비교 |
| DRIFT | 필수 키 누락, 문서-only 키, 타입 불일치 |
| 심각도 | P0 |

### TC-B-002 상세 응답 필수 키 (F-02)

| 항목 | 내용 |
| --- | --- |
| Claim | `parcel`, `scores`, `source`. parcel 내 `regulations`, `sumokFeasibility`, `dataProvenance` |
| 절차 | 시드 ID 상세 + 라이브 `VW-*` 상세 각각 확인 |
| DRIFT | **목록에는 있는데 상세에 없는 필드** (특히 DB 상세의 `regulations` / `sumokFeasibility`) |
| 심각도 | P0 |
| 의심 포인트 | `get_parcel_detail` 가 목록 serializer 와 필드 집합이 다를 수 있음 |

### TC-B-003 `sumokScore` vs `treeScore`

| 항목 | 내용 |
| --- | --- |
| Claim | 명세: `sumokScore`/`treeScore` 병행, API는 주로 `treeScore` |
| 절차 | 목록·상세·agent 결과의 scores 키에 `sumokScore` 존재 여부 |
| DRIFT | 문서가 “병행 반환”처럼 읽히는데 응답에 `sumokScore` 없음 (또는 반대) |
| 심각도 | P1 |

### TC-B-004 `topRecommendation` 허용 값

| 항목 | 내용 |
| --- | --- |
| Claim | API `TREE` \| `GARDEN` \| `SOLAR` (SUMOK≡TREE). 선택적으로 MIXED/RESTRICTED 언급 |
| 절차 | 시드 전량 또는 라이브 샘플의 topRecommendation unique set |
| DRIFT | 문서 미기재 값(SUMOK, NONE, MIXED 등)이 API에 등장하거나, 문서 허용값 누락 |
| 심각도 | P1 |

### TC-B-005 `regulations` 타입

| 항목 | 내용 |
| --- | --- |
| Claim (명세) | 배열, 항목에 `code`, `name`, `severity` … |
| Claim (api.md 일부 예) | `"regulations": "NONE"` 문자열 |
| 절차 | 실제 타입 확인 (array vs string) |
| DRIFT | 문서 예시끼리 모순; 구현 타입이 어느 쪽과도 불일치 |
| 심각도 | P0 |

### TC-B-006 score breakdown

| 항목 | 내용 |
| --- | --- |
| Claim | 점수 breakdown 문자열 제공 (F-27, api scores 예) |
| 절차 | DB 상세 vs 라이브 상세의 `treeBreakdown` 등 |
| DRIFT | 문서 “반드시 제공”인데 항상 `[]` 이거나 라이브만 채움 |
| 심각도 | P1 |

### TC-B-007 시드 ID 형식

| 항목 | 내용 |
| --- | --- |
| Claim (api.md) | 시드 예: `DD-001`, `GN-001` |
| 절차 | `GET /api/gs/parcels?live=false` 의 id 패턴 |
| DRIFT | 실제 시드가 `VW-…` 단축형 등 문서 예와 체계가 다름 (문서 오해 유발) |
| 심각도 | P1 |

### TC-B-008 Compare 요청 한도

| 항목 | 내용 |
| --- | --- |
| Claim (api/명세) | 2개 이상 |
| 절차 | schema `CompareRequest.ids` min/max; body 4개 전송 |
| DRIFT | 문서에 상한 없는데 구현 max=3 → 422; 또는 무제한인데 문서와 불일치 |
| 심각도 | P1 |

### TC-B-009 Agent 요청 body

| 항목 | 내용 |
| --- | --- |
| Claim | body `query` only (공개 API). `strictTopRecommendation` 은 내부 criteria |
| 절차 | OpenAPI AgentSearchRequest 스키마 확인; body에 strict 플래그 넣어 무시/422 여부 |
| DRIFT | 문서가 클라이언트 옵션처럼 읽히는데 필드 없음; 또는 필드 있는데 문서 없음 |
| 심각도 | P1 |

### TC-B-010 Explain `promptVersion`

| 항목 | 내용 |
| --- | --- |
| Claim (api.md 예) | `promptVersion`: `v3-greenspot2` |
| 절차 | `POST …/explain` 응답 값 |
| DRIFT | 실제 버전이 문서 예와 다름 (예: v3-greenspot3) |
| 심각도 | P2 |

### TC-B-011 Health environment 키

| 항목 | 내용 |
| --- | --- |
| Claim (api 예) | `vworldApiKeyConfigured`, `kmaApiKeyConfigured`, `kosisApiKeyConfigured`, `visualCrossingApiKeyConfigured`, `nodeEnv` |
| 절차 | `GET /api/gs/health` environment 키 집합 |
| DRIFT | 문서 예 키 누락/추가; bool 아닌 타입 |
| 심각도 | P2 |

### TC-B-012 에러 바디 형식

| 항목 | 내용 |
| --- | --- |
| Claim (기능명세 3.2) | `{ "detail": "…" }` |
| Claim (api List 500 예) | `{ "error", "detail" }` |
| 절차 | 404/400/422/500 샘플 수집 |
| DRIFT | 상태별로 형식이 갈리거나 문서 예시와 전부 불일치 |
| 심각도 | P1 |

### TC-B-013 인증 응답 필드명

| 항목 | 내용 |
| --- | --- |
| Claim | access/refresh 토큰 필드명 (snake: `access_token` 등) |
| 절차 | login 응답 vs 문서 TokenResponse |
| DRIFT | camelCase/snake_case 혼선 |
| 심각도 | P1 |

### TC-B-014 User 필드 (login 응답)

| 항목 | 내용 |
| --- | --- |
| Claim | `GET /api/users/me` 미제공. 사용자 정보는 login 응답 `user` (`id`, `email`, `created_at`) |
| 절차 | `GET /api/users/me` → 404; login 응답에 `user` 포함 |
| DRIFT | me 엔드포인트 문서/구현 잔존; login에 user 없음 |
| 심각도 | P1 |

---

# C. 권한·공개 범위 드리프트

### TC-C-001 비회원 허용 API 집합

| 항목 | 내용 |
| --- | --- |
| Claim | 목록/상세/검색/시뮬/비교/리포트/공유 발급 등 비회원 가능; 북마크만 회원. me·preferences 미제공 |
| 절차 | Authorization 없이 각 엔드포인트 호출 → 401 여부 표 작성 |
| DRIFT | 문서 “비회원 가능”인데 401; 문서 “회원 전용”인데 200 |
| 심각도 | P0 |

### TC-C-002 리포트·CSV 권한

| 항목 | 내용 |
| --- | --- |
| Claim (명세 각주) | 초안은 회원 전용이었으나 구현은 인증 없이 허용. history API 미제공 |
| 절차 | 무토큰으로 report/export |
| DRIFT | 문서 본문이 아직 “회원 전용”으로 읽히고 구현은 공개(또는 반대) |
| 심각도 | P1 |

### TC-C-003 Share 인증 “선택”

| 항목 | 내용 |
| --- | --- |
| Claim | `POST /api/share` 선택 인증 |
| 절차 | 무토큰 share / 토큰 share 동작 차이 (사용자 귀속 여부) |
| DRIFT | 문서 “선택”인데 인증 필수; 또는 인증해도 사용자 연결 없어 문서 의미 공허 |
| 심각도 | P2 |

### TC-C-004 AgentQuery userId

| 항목 | 내용 |
| --- | --- |
| Claim (sql) | AgentQuery.userId nullable FK |
| 절차 | agent 호출 후 DB 또는 history 응답에 user 연결 여부; 로그인 상태 agent 시 userId 기록 여부 |
| DRIFT | 스키마에 userId 있는데 모델/저장 로직이 무시 |
| 심각도 | P2 |

---

# D. 라이브 vs DB 이중 경로

동일 API가 시드와 `VW-*` 에서 문서와 같이 동작하는가.

### TC-D-001 목록 source 전환 규칙

| 항목 | 내용 |
| --- | --- |
| Claim | `live=true` + key + district → `vworld_live`; 아니면 `database` |
| 절차 | 조합 행렬: live×key×district 존재 여부 |
| DRIFT | district 없이 live=true 인데 vworld_live; key 없는데 vworld_live; 실패 시 문서와 다른 source |
| 심각도 | P0 |

### TC-D-002 상세 source 값

| 항목 | 내용 |
| --- | --- |
| Claim | `database` / `vworld_live` / `vworld_live_cache` |
| 절차 | 시드 1회, 라이브 1회, 라이브 즉시 재조회 |
| DRIFT | 문서 미기재 source 문자열; 캐시인데 live로 표기 등 |
| 심각도 | P1 |

### TC-D-003 19자리 PNU path

| 항목 | 내용 |
| --- | --- |
| Claim | path에 19자리 PNU 허용 → 라이브 조회 |
| 절차 | `VW-` 없는 19 digit path 상세 |
| DRIFT | 문서 허용인데 404 only; 또는 잘못된 길이도 라이브 시도 |
| 심각도 | P1 |

### TC-D-004 시뮬 라이브 지원·DB 미저장

| 항목 | 내용 |
| --- | --- |
| Claim | `VW-*` 시뮬 200; scenarios 테이블 insert 없음. DB 부지만 저장 |
| 절차 | 1. 시드 시뮬 후 scenarios count 증가 여부 2. 라이브 시뮬 후 count 불변 |
| DRIFT | 라이브 404; 라이브 insert 발생; 시드 미저장 |
| 심각도 | P0 |

### TC-D-005 비교 DB+VW 혼합

| 항목 | 내용 |
| --- | --- |
| Claim | ids 혼합 허용 |
| 절차 | `[seedId, liveId]` compare |
| DRIFT | 라이브 무시/400; ranking 키 누락 |
| 심각도 | P0 |

### TC-D-006 북마크 VW 스냅샷 (Parcel FK 없음)

| 항목 | 내용 |
| --- | --- |
| Claim | FK 없이 VW 북마크; body 스냅샷 필드 |
| 절차 | 1. 모델/SQLAlchemy FK 확인 2. parcels 에 없는 VW- id 북마크 3. GET 스냅샷 필드 |
| DRIFT | FK 위반 500; 스냅샷 필드 문서와 불일치 |
| 심각도 | P0 |

### TC-D-007 Share VW

| 항목 | 내용 |
| --- | --- |
| Claim | VW share 허용, Parcel FK 없음 |
| 절차 | VW parcelId share; 존재하지 않는 비-VW 404 |
| DRIFT | VW 404; 임의 문자열도 200 (문서보다 관대/엄격) |
| 심각도 | P1 |

### TC-D-008 explain/report 라이브 해상도

| 항목 | 내용 |
| --- | --- |
| Claim | 상세는 라이브 지원. explain/report 문서상 parcelId 일반화 |
| 절차 | 동일 LIVE_ID 로 explain, report |
| DRIFT | 상세는 200인데 explain/report 만 404 (경로 불일치) |
| 심각도 | P1 |

### TC-D-009 stats 범위

| 항목 | 내용 |
| --- | --- |
| Claim | `GET /api/gs/stats` = **DB 시드 전역** (라이브 지역 통계 아님) |
| 절차 | 라이브로 특정 구만 본 뒤 stats 가 시드 전체인지 확인 |
| DRIFT | stats 가 라이브 결과처럼 보이거나 문서와 다른 스코프 |
| 심각도 | P1 |

---

# E. dataProvenance · 실측 주장 (데이터 환각)

**가장 중요.** `actual:true` / 출처 문자열 / null vs 0 위장.

### TC-E-001 actual 규칙은 “조회 성공 시에만 true”

| 항목 | 내용 |
| --- | --- |
| Claim (F-27) | 키 존재만으로 true 금지; 실패·쿨다운 시 false |
| 절차 | 1. 키 있는 환경 라이브 상세 2. 의도적 실패(잘못된 키/쿨다운) 후 동일 필드 3. provenance 비교 |
| HALLUC | 실패했는데 `actual:true` |
| 심각도 | P0 |

### TC-E-002 시드 DB provenance 의 is_vworld 오인

| 항목 | 내용 |
| --- | --- |
| Claim | 시드/`dataSource` 표기와 actual 의 정직성 |
| 절차 | `live=false` 상세의 `dataProvenance.boundary.actual` 등 확인. data_source 문자열에 "VWorld" 포함만으로 actual=true 되는지 코드·응답 대조 |
| HALLUC | 시드 하드코딩 값인데 boundary/location/area `actual:true` |
| 심각도 | P0 |
| 의심 포인트 | `DEFAULT_DB_DATA_SOURCE = "VWorld/…"` + `is_vworld = "VWorld" in data_source` |

### TC-E-003 monthlyIrradiance.actual == false

| 항목 | 내용 |
| --- | --- |
| Claim | 계절계수 모델, actual false |
| 절차 | 라이브·DB 모두 provenance 확인 |
| HALLUC | actual true 또는 월별 실측 문구 |
| 심각도 | P0 |

### TC-E-004 waterAccess / electricityAccess 추정

| 항목 | 내용 |
| --- | --- |
| Claim | 추정, actual false |
| 절차 | provenance 확인 |
| HALLUC | actual true |
| 심각도 | P1 |

### TC-E-005 미연동 사회지표 null (가짜 0 금지)

| 항목 | 내용 |
| --- | --- |
| Claim (F-27, 라이브) | schools/hospitals/parks/subway/pedestrian 등 미연동 → null |
| 절차 | 라이브 상세 vs DB 상세 동일 필드 |
| HALLUC | 라이브에서 0으로 채워 “있는 것처럼” 표시 |
| DRIFT | 문서 “null 권장”인데 DB 시드는 NOT NULL 0 (문서가 라이브만 말하는지 불명) |
| 심각도 | P0 (라이브) / P1 (DB 정책 문서화) |

### TC-E-006 ownership / soil / air 키 없을 때

| 항목 | 내용 |
| --- | --- |
| Claim | 키 미설정 시 추정 + actual false, 응답 200 |
| 절차 | health environment 로 키 상태 확인 후 해당 필드 provenance |
| HALLUC | 키 미설정인데 ownership.actual true 등 |
| 심각도 | P0 |

### TC-E-007 scores.actual / sumokFeasibility.actual

| 항목 | 내용 |
| --- | --- |
| Claim | 알고리즘 결과 actual true (입력 일부 추정 가능 문구) |
| 절차 | provenance 문구와 실제 입력 추정 비율 대조; 오해 소지 기록 |
| HALLUC | “전부 실측 점수”처럼 읽히는 클라이언트 해석을 유도하는 문서/필드 |
| 심각도 | P2 |

### TC-E-008 Visual Crossing 429 쿨다운 시

| 항목 | 내용 |
| --- | --- |
| Claim | 실패 응답 캐시 금지; actual false |
| 절차 | (가능 시) 429 유도 후 heat/climate/live enrich |
| HALLUC | 쿨다운 중 이전 성공값을 actual true 로 재사용하거나, 실패를 성공으로 표시 |
| 심각도 | P1 |

### TC-E-009 출처 문자열 정직성 (Visual Crossing 등)

| 항목 | 내용 |
| --- | --- |
| Claim | explain 출처: VWorld / AirKorea / Visual Crossing / KOSIS / GreenSpot |
| 구현 실사용 | 열섬·일사 = Visual Crossing |
| 절차 | explain 본문 출처가 실연동과 모순되지 않는지 |
| HALLUC | 미사용 출처를 실측 근거처럼 기재 |
| 심각도 | P0 |

### TC-E-010 KOSIS dataAvailable 와 nearbyHouseholds

| 항목 | 내용 |
| --- | --- |
| Claim | households 성공 시 보강 + provenance households actual true |
| 절차 | KOSIS 성공/실패 구에서 라이브 필지 nearbyHouseholds 와 provenance |
| HALLUC | dataAvailable false 인데 가구수 숫자 + actual true |
| 심각도 | P0 |

---

# F. 점수·규제·sumokFeasibility 일관성

### TC-F-001 점수 범위 0~100

| 항목 | 내용 |
| --- | --- |
| Claim | 각 점수 0~100 |
| 절차 | 시드·라이브 샘플 min/max |
| DRIFT | 범위 밖 |
| 심각도 | P0 |

### TC-F-002 규제 zero/all 페널티

| 항목 | 내용 |
| --- | --- |
| Claim | affectedUses all + zero → 관련 점수 0 |
| 절차 | 규제 있는 필지 또는 unit/fixture; GREEN_BELT 등 |
| DRIFT | 문서 페널티 규칙과 점수 불일치 |
| 심각도 | P0 |

### TC-F-003 sumokFeasibility.status 집합

| 항목 | 내용 |
| --- | --- |
| Claim | AVAILABLE / CONDITIONAL / RESTRICTED / PROHIBITED / UNKNOWN |
| 절차 | 응답 status unique set |
| DRIFT | 미정의 문자열 |
| 심각도 | P1 |

### TC-F-004 자연녹지 → CONDITIONAL + 인허가 문구

| 항목 | 내용 |
| --- | --- |
| Claim (F-27) | 자연녹지 등 → CONDITIONAL 및 인허가 안내 |
| 절차 | 용도지역 자연녹지 필지 상세 |
| DRIFT | AVAILABLE 이거나 문구 없음 |
| 심각도 | P1 |

### TC-F-005 regulations 항목 스키마

| 항목 | 내용 |
| --- | --- |
| Claim | code, name, severity, affectedUses, penaltyType, penaltyValue, … |
| 절차 | 비어 있지 않은 regulations[0] 키 집합 |
| DRIFT | 필수 키 대량 누락; severity 값 집합 불일치 |
| 심각도 | P1 |

### TC-F-006 topRecommendation 과 점수 정합

| 항목 | 내용 |
| --- | --- |
| Claim | top = 세 점수 중 최고 용도 (동점 정책은 문서 약함) |
| 절차 | tree/garden/solar 와 top 불일치 건수 |
| DRIFT | top 이 최고점이 아닌 용도 (동점 제외) |
| 심각도 | P1 |

---

# G. Agent 검색 — 소프트 정렬 · 환각 방어 (F-04)

### TC-G-001 소프트 정렬 (하드 필터 금지)

| 항목 | 내용 |
| --- | --- |
| Claim | 기본: 선호 용도 점수 내림차순. **1위 추천 불일치로 제거하지 않음** |
| 절차 | `POST /api/gs/agent` `{"query":"금천구 수목"}` → results 중 topRecommendation≠TREE 비율; treeScore 정렬 |
| DRIFT | TREE가 아닌 top 전부 탈락(구 하드필터 잔존); 정렬 키가 top 점수 |
| 심각도 | P0 |

### TC-G-002 키워드 → criteria 매핑

| 항목 | 내용 |
| --- | --- |
| Claim | 수목/식재/나무/식수→TREE, 텃밭→GARDEN, 태양광/솔라→SOLAR |
| 절차 | 쿼리별 criteria.topRecommendation |
| DRIFT | 매핑 누락·오매핑 (문서 표와 불일치) |
| 심각도 | P1 |

### TC-G-003 지역 없음 안내

| 항목 | 내용 |
| --- | --- |
| Claim | 지역명 없으면 안내, 빈 검색 |
| 절차 | `{"query":"수목 추천해줘"}` |
| DRIFT | 전국 환각 결과 다량 반환; 500 |
| 심각도 | P1 |

### TC-G-004 LLM 요약 환각 방어

| 항목 | 내용 |
| --- | --- |
| Claim | 검색은 결정론적; LLM은 결과 **이름** 기반 요약만, 새 수치 금지 |
| 절차 | 1. results 의 면적·점수 목록 고정 2. summary 에 results 에 없는 숫자·없는 동명 부지 있는지 대조 |
| HALLUC | 없는 부지명, 없는 점수, 없는 면적 |
| 심각도 | P0 |
| 전제 | OPENAI/GROQ 키 있을 때와 없을 때(규칙 요약) 각각 |

### TC-G-005 minScore 기준 용도

| 항목 | 내용 |
| --- | --- |
| Claim | minScore 는 **선호 용도 점수** 기준 |
| 절차 | “70점” + “수목” 쿼리 시 garden만 높은 부지 포함/제외 |
| DRIFT | top 점수 또는 다른 용도 점수로 필터 |
| 심각도 | P1 |

### TC-G-006 limit 상한 20

| 항목 | 내용 |
| --- | --- |
| Claim | agent limit 기본 10, 최대 20 |
| 절차 | “상위 100개” 파싱 결과 criteria.limit |
| DRIFT | 100 그대로 또는 문서와 다른 cap |
| 심각도 | P2 |

### TC-G-007 AgentQuery 로그 (공개 history 없음)

| 항목 | 내용 |
| --- | --- |
| Claim | agent 호출 시 `AgentQuery` 저장. 공개 `history`/`trending` API는 미제공 (404) |
| 절차 | 고유 쿼리 후 DB AgentQuery 행 확인; GET /api/gs/history → 404 |
| DRIFT | 미기록; 공개 history 엔드포인트 잔존 |
| 심각도 | P1 |

### TC-G-008 liveMeta 필드

| 항목 | 내용 |
| --- | --- |
| Claim (api 예) | criteria.liveMeta: preferredUse, strictTopRecommendation, candidates … |
| 절차 | VWorld 키 있을 때 agent 응답 criteria |
| DRIFT | 문서 예 필드 전무; 이름 불일치 |
| 심각도 | P2 |

---

# H. Explain LLM 환각 (F-05)

### TC-H-001 facts 외 수치 금지

| 항목 | 내용 |
| --- | --- |
| Claim | facts 객체 외 수치 사용 금지 |
| 절차 | 1. explain 응답 facts 스냅샷 2. explanation 의 모든 숫자 추출 3. facts·scores 에 없는 숫자 목록화 |
| HALLUC | facts 밖 숫자 (연도·인구·점수 등) |
| 심각도 | P0 |

### TC-H-002 4섹션 스키마

| 항목 | 내용 |
| --- | --- |
| Claim | 부지 요약 / 추천 / 대안 / 한계 |
| 절차 | 헤딩 존재 여부 |
| DRIFT | 섹션 누락 또는 다른 구조 (규칙 fallback 포함) |
| 심각도 | P1 |

### TC-H-003 정치적 단어 금지

| 항목 | 내용 |
| --- | --- |
| Claim | 불평등/격차/소외/차별 금지 |
| 절차 | explanation 키워드 스캔 |
| DRIFT | 금칙어 포함 |
| 심각도 | P2 |

### TC-H-004 LLM 실패 시 fallback

| 항목 | 내용 |
| --- | --- |
| Claim | LLM 실패 시 규칙 기반 fallback, 200 유지 |
| 절차 | LLM 키 제거 또는 mock 실패 |
| DRIFT | 500; 빈 explanation |
| 심각도 | P1 |

### TC-H-005 출처 강제 vs 실파이프라인 (E-009 연동)

| 항목 | 내용 |
| --- | --- |
| Claim | 출처 명시 강제 |
| 절차 | fallback 문구에 고정 출처 목록이 실제 미사용 소스를 포함하는지 |
| HALLUC | 미연동 출처를 근거처럼 상시 출력 |
| 심각도 | P0 |

---

# I. 시뮬레이션·비교 수치 정직성

### TC-I-001 시나리오 타입 별칭

| 항목 | 내용 |
| --- | --- |
| Claim | SUMOK/TREE→PLANT_TREES, GARDEN→CREATE_GARDEN, SOLAR→INSTALL_SOLAR |
| 절차 | 별칭 요청 후 응답 scenarios 키 |
| DRIFT | 별칭 422; 키가 별칭 문자열로 남음 |
| 심각도 | P1 |

### TC-I-002 수량 상한

| 항목 | 내용 |
| --- | --- |
| Claim | TREE 200 / GARDEN 150 / SOLAR 500 |
| 절차 | 경계값 max, max+1 |
| DRIFT | 상한 무시 또는 다른 숫자 |
| 심각도 | P1 |

### TC-I-003 COMPARE_ALL 키 집합

| 항목 | 내용 |
| --- | --- |
| Claim | 세 시나리오 키 모두 |
| 절차 | COMPARE_ALL 응답 keys |
| DRIFT | 키 누락·이름 불일치 |
| 심각도 | P0 |

### TC-I-004 계수 출처 문서 vs 코드 상수

| 항목 | 내용 |
| --- | --- |
| Claim | USDA i-Tree, 한국에너지공단 14.2%, 서울연구원 |
| 절차 | simulation_service 상수와 문서 출처 표 대조; 응답 summary 문구 |
| DRIFT | 문서 출처와 다른 계수; 출처 미표기 |
| 심각도 | P2 |

### TC-I-005 비교 ranking 키

| 항목 | 내용 |
| --- | --- |
| Claim | tree, garden, solar, carbon, costEfficiency |
| 절차 | compare 응답 ranking keys |
| DRIFT | 키 누락/이름 변경 |
| 심각도 | P0 |

### TC-I-006 비교 탄소 = PLANT_TREES 1회

| 항목 | 내용 |
| --- | --- |
| Claim | 면적 기반 나무 시나리오 1회 → carbon ranking |
| 절차 | comparison[].effects.PLANT_TREES 존재; 단독 시뮬과 대략 일치 |
| DRIFT | effects 없음; 탄소 랭킹이 점수 정렬과 동일 복제 |
| 심각도 | P1 |

---

# J. 외부 연동 API 계약

### TC-J-001 KOSIS 25구만

| 항목 | 내용 |
| --- | --- |
| Claim | 서울 25구; 그 외 400 |
| 절차 | 강남구 200 / 해운대구 400 / 금천구 포함 |
| DRIFT | 25구 매핑 누락(금천 등); 비서울 200 |
| 심각도 | P0 |

### TC-J-002 KOSIS 키 없음

| 항목 | 내용 |
| --- | --- |
| Claim | dataAvailable false 또는 400 (문서 문구 혼재) |
| 절차 | 키 제거 후 population/households |
| DRIFT | 문서가 허용한 두 형태 밖 (500, 가짜 population) |
| 심각도 | P1 |

### TC-J-003 VC climate/heat 필드

| 항목 | 내용 |
| --- | --- |
| Claim | api.md 필드 집합 |
| 절차 | 키 있을 때/없을 때 응답 |
| DRIFT | 필드명·dataAvailable 규칙 불일치 |
| 심각도 | P1 |

### TC-J-004 heat 추정 식

| 항목 | 내용 |
| --- | --- |
| Claim | surfaceTempSummer = avg+5; heatIsland = max(0, avg-25) |
| 절차 | avgTemperature 있는 응답에서 역산 |
| DRIFT | 식과 불일치 |
| 심각도 | P1 |

### TC-J-005 possession bbox

| 항목 | 내용 |
| --- | --- |
| Claim | bbox 필수 ymin,xmin,ymax,xmax; 없으면 422 |
| 절차 | bbox 누락/형식 오류 |
| DRIFT | 다른 상태코드 |
| 심각도 | P2 |

### TC-J-006 characteristics fallback

| 항목 | 내용 |
| --- | --- |
| Claim | 실패 시 200 + dataAvailable false |
| 절차 | 키 없음/잘못된 pnu |
| DRIFT | 500 또는 문서와 다른 400-only |
| 심각도 | P2 |

---

# K. SQL/스키마 문서 드리프트 (sql.md ↔ models.py)

### TC-K-001 테이블 매핑 표

| 항목 | 내용 |
| --- | --- |
| Claim | sql.md 하단 논리명 → SQLAlchemy __tablename__ |
| 절차 | models 의 __tablename__ 전수 vs 표 |
| DRIFT | 표에 없는 테이블/컬럼; 표에만 있는 테이블 |
| 심각도 | P1 |

### TC-K-002 Bookmark/Share Parcel FK 없음

| 항목 | 내용 |
| --- | --- |
| Claim | parcel_id FK 없음 |
| 절차 | models.Bookmark / Share 의 ForeignKey 목록 |
| DRIFT | parcels FK 존재 |
| 심각도 | P0 |

### TC-K-003 sql.md only 컬럼

| 항목 | 내용 |
| --- | --- |
| Claim 예 | estimatedAcquisitionCostWon, dataSource, kosisPopulationSnapshot, name on User, Scenario.aiExplanation … |
| 절차 | models.Parcel/User/Scenario 컬럼 존재 여부 |
| DRIFT | 문서 DDL 에만 있고 구현 없음 (과대 스키마 문서) |
| 심각도 | P1 |

### TC-K-004 AgentQuery.userId

| 항목 | 내용 |
| --- | --- |
| Claim | userId FK nullable |
| 절차 | models.AgentQuery 컬럼 |
| DRIFT | 문서에만 존재 |
| 심각도 | P2 |

### TC-K-005 ParcelScore 이력/isLatest

| 항목 | 내용 |
| --- | --- |
| Claim | isLatest, 다건 이력, latest unique |
| 절차 | 모델 unique(parcel_id) vs 문서 다건 이력 |
| DRIFT | 구현 1:1 only 인데 문서는 이력형 |
| 심각도 | P1 |

---

# L. 헬스·운영 신호 정직성

### TC-L-001 DB disconnected 시 status

| 항목 | 내용 |
| --- | --- |
| Claim (api 503 예) | unhealthy + disconnected |
| 절차 | DB 장애 유도 또는 코드 경로 확인: status 필드가 항상 healthy 인지 |
| DRIFT | database=disconnected 인데 status=healthy 200 |
| 심각도 | P1 |

### TC-L-002 environment 플래그 vs 실제 키

| 항목 | 내용 |
| --- | --- |
| Claim | configured bool 이 실제 settings 반영 |
| 절차 | .env on/off 후 health 재확인 |
| HALLUC | 키 없는데 true |
| 심각도 | P0 |

---

# M. CSV·리포트 문서 정합

### TC-M-001 CSV 컬럼 집합

| 항목 | 내용 |
| --- | --- |
| Claim (api) | 수목/텃밭/태양광 점수 포함; 보행·학교·지하철 컬럼 없음 |
| 절차 | export 헤더 토큰 집합 diff |
| DRIFT | 문서 컬럼 누락/추가 |
| 심각도 | P1 |

### TC-M-002 리포트 구조

| 항목 | 내용 |
| --- | --- |
| Claim | 부지 정보 / 환경 / 점수 / 시나리오 섹션 |
| 절차 | markdown 헤딩 추출 |
| DRIFT | 섹션 누락; 시뮬 실패 시 문서와 다른 처리 |
| 심각도 | P2 |

---

# N. 정적 의심 목록 (코드 리딩 기반 — 반드시 관측으로 확정)

> 아래는 **이미 DRIFT 확정 판정이 아니다.** 테스터가 TC로 닫아야 할 우선 의심이다.

| ID | 의심 | 관련 TC |
| --- | --- | --- |
| S-01 | DB 상세에 `regulations`/`sumokFeasibility` 미포함 가능 (목록과 비대칭) | B-002 |
| S-02 | 시드 data_source 문자열에 VWorld 포함 → boundary actual true 오인 | E-002 |
| S-03 | api.md `regulations: "NONE"` 문자열 예시 vs 구현 배열 | B-005 |
| S-04 | 시드 ID 예 `DD-001` vs 실제 `VW-` 단축 시드 | B-007 |
| S-05 | Compare max_length=3 문서 미기재 | B-008 |
| S-06 | 열섬·일사 출처는 Visual Crossing | A-002 |
| S-07 | explain 출처는 Visual Crossing 등 실연동과 일치해야 함 | E-009, H-005 |
| S-08 | promptVersion 문서 v3-greenspot2 vs 코드 v3-greenspot3 | B-010 |
| S-09 | health 가 DB 실패에도 healthy 일 수 있음 | L-001 |
| S-10 | DB nearby* 가 0 (라이브 null 정책과 이원화) | E-005 |
| S-11 | sql.md 전용 컬럼 다수 미구현 | K-003 |
| S-12 | scores.breakdown DB 경로 빈 배열 | B-006 |
| S-13 | AgentQuery.userId 문서 vs 모델 | K-004, C-004 |
| S-14 | 500 에러 바디 문서 이중 형식 | B-012 |

---

# O. 실행 순서 (환각 감사 워크플로)

문서 감사 시 추천 순서:

| 단계 | 목적 | TC |
| --- | --- | --- |
| 1 | 문서 내부 모순 | A-002, B-005, C-002 |
| 2 | 라우트 집합 diff | A-001, A-003~006 |
| 3 | 스키마 샘플링 | B-001~014 |
| 4 | 권한 행렬 | C-001~003 |
| 5 | 라이브/DB 이중성 | D-001~009 |
| 6 | provenance 정직성 | E-001~010 |
| 7 | 점수·규제 | F-* |
| 8 | Agent/Explain 환각 | G-*, H-* |
| 9 | 시뮬·연동·SQL | I, J, K, L, M |
| 10 | S-* 의심 닫기 | 해당 TC 재실행 |

---

# P. 결과 기록 템플릿

```
TC-ID:
문서 Claim: (문서명 § / 인용 1줄)
관측: (요청 + 응답 핵심 또는 코드 위치)
판정: MATCH | DRIFT | HALLUC | N/A
심각도: P0/P1/P2
수정 권고: 문서 수정 / 코드 수정 / 둘 다
증거: (응답 JSON 일부, openapi path, 파일:라인)
```

### 총괄 표

| TC | 판정 | 심각도 | 수정 권고 | 증거 링크 |
| --- | --- | --- | --- | --- |
| TC-A-001 |  |  |  |  |
| TC-A-002 |  |  |  |  |
| … |  |  |  |  |

---

# Q. 기능 ID 추적

| 기능 | 환각/드리프트 TC |
| --- | --- |
| F-01 목록 | B-001, D-001, E-* |
| F-02 상세 | B-002, D-002~003, E-* |
| F-03 점수 | F-*, B-003~006 |
| F-04 Agent | G-* |
| F-05 Explain | H-*, E-009 |
| F-06 Simulate | D-004, I-* |
| F-07 Compare | D-005, I-005~006, B-008 |
| F-08 Report | D-008, M-002, C-002 |
| F-09~20 Auth | B-013~014, C-* |
| F-11 Bookmark | D-006 |
| F-12 Stats | D-009 |
| F-13 CSV | M-001 |
| F-14 Share | D-007, C-003 |
| F-16~17 History/Trend | G-007, A-006 |
| F-18 Health | B-011, L-* |
| F-25 KOSIS | J-001~002, E-010 |
| Visual Crossing 열섬 | A-002 |
| F-27 Provenance | E-* |
| F-28 Live | D-*, G-001 |

---

# R. 이 문서가 다루지 않는 것

- “버튼이 예쁘다” 수준 UI QA  
- 단순 로드타임 SLO  
- 문서에 **없는** 신규 기능 아이디어  
- 외부 API 벤더 장애 자체를 제품 버그로 단정 (다만 **표시 정직성**은 범위 안)

자동화 매핑·pytest 대응은 [TEST_CASES.md](./TEST_CASES.md) 참고.  
본 문서는 **문서 주장 vs 구현 관측** 감사 전용이다.
