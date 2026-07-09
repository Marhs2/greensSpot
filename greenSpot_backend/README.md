# GreenSpot API

FastAPI 기반 GreenSpot 백엔드. VWorld 실시간 필지 + 공공 API enrich + 3중 용도 점수(수목/텃밭/태양광).

## 설치

```bash
pip install -r requirements.txt
```

## 환경 변수 (`.env`)

`greenSpot_backend/.env` 에 설정. 값이 비어 있으면 해당 소스는 추정/미제공으로 폴백.

```bash
# 필수에 가까움
VWORLD_API_KEY=
LAND_OWNERSHIP_API_KEY=          # 보통 VWorld 키와 동일 계열
LAND_OWNERSHIP_BASE_URL=https://api.vworld.kr/ned/data/getPossessionAttr

# 공공데이터포털 (인코딩 키를 넣어도 서버가 한 번 디코딩)
AIRKOREA_API_KEY=
AIRKOREA_BASE_URL=https://apis.data.go.kr/B552584/ArpltnInforInqireSvc
SOIL_API_KEY=
SOIL_BASE_URL=https://apis.data.go.kr/1390802/SoilEnviron/SoilCharac/V3

# 기후
VISUAL_CROSSING_API_KEY=
VISUAL_CROSSING_BASE_URL=https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline

# 통계 (서울 25개 자치구)
KOSIS_API_KEY=

# legacy / AI
KMA_API_KEY=                     # health 호환용 (enrich 는 VC 사용)
OPENAI_API_KEY=                  # 또는 GROQ_API_KEY
GROQ_API_KEY=
```

| 변수 | 용도 |
| --- | --- |
| `VWORLD_API_KEY` | 연속지적도, WFS 규제, 토지특성, 지역 resolve |
| `LAND_OWNERSHIP_*` | 토지 소유구분 (`getPossessionAttr`) |
| `AIRKOREA_*` | 구 단위 PM2.5 |
| `SOIL_*` | 토양 토성 (`getSoilCharacter?PNU_CD=`) |
| `VISUAL_CROSSING_*` | 일사·기온 (열섬 파생). 429 시 쿨다운 |
| `KOSIS_API_KEY` | 자치구 인구·가구 (서울 25구) |
| `KMA_API_KEY` | legacy (실사용은 VC) |

키 발급:

- VWorld: https://www.vworld.kr/dev/v4dv_wmsguide2_s001.do  
- 공공데이터포털 AirKorea / 토양: data.go.kr  
- KOSIS: https://kosis.kr/openapi/openApiIntro.do  
- Visual Crossing: https://www.visualcrossing.com/weather-api  

## 실행

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
# 또는
python run.py
```

## 시드 데이터

```bash
python -m scripts.seed
```

## 문서

| 문서 | 설명 |
| --- | --- |
| [docs/README.md](docs/README.md) | 문서 인덱스 · 핵심 개념 |
| [docs/api.md](docs/api.md) | REST API 상세 |
| [docs/기능명세서.md](docs/기능명세서.md) | 기능 요구사항 F-01~F-28 |
| [docs/sql.md](docs/sql.md) | 스키마 DDL · SQLite 매핑 |
| [docs/HALLUCINATION_TEST_CASES.md](docs/HALLUCINATION_TEST_CASES.md) | **문서↔구현 불일치·환각 탐지** TC |
| [docs/TEST_CASES.md](docs/TEST_CASES.md) | 기능 수용·자동화 매핑 매트릭스 |
| Swagger | http://localhost:8000/docs |

## API Prefix

| Prefix | 용도 |
| --- | --- |
| `/api/gs` | 부지, 에이전트, 시뮬, 통계, 리포트 |
| `/api` | 인증, 북마크, 공유, 환경설정 |
| `/api/v1/gs` | KOSIS, VWorld 토지, Visual Crossing, 규제 |

## 엔드포인트 요약

### Health / Parcels / Agent
- `GET /api/gs/health`
- `GET /api/gs/parcels?district=&live=true&limit=15` — DB 또는 VWorld 라이브
- `GET /api/gs/parcels/{id}` — DB 또는 `VW-{pnu}`
- `POST /api/gs/agent` — 자연어 검색 (용도 키워드는 **소프트 정렬**)
- `POST /api/gs/parcels/{id}/explain`
- `POST /api/gs/parcels/{id}/simulate` — DB + 라이브, body `area_sqm` 힌트
- `POST /api/gs/compare` — DB + `VW-*` 혼합
- `POST /api/gs/report`
- `GET /api/gs/export`
- `GET /api/gs/stats` — **DB 시드** 집계 (프론트 다지역은 클라이언트 집계)
- `GET /api/gs/trending` · `GET /api/gs/history`

### Auth / Bookmarks
- `POST /api/auth/signup|login|refresh|logout`
- `GET /api/users/me`
- `GET|POST|DELETE /api/bookmarks` — **라이브 `VW-*` 스냅샷 가능** (Parcel FK 없음)
- `POST /api/share` — `VW-*` 허용
- `PATCH /api/users/me/preferences`

### 외부 연동 `/api/v1/gs`
- `GET /api/v1/gs/vworld/layers`
- `GET|POST /api/v1/gs/parcels/{id}/regulations[ /sync]`
- `POST /api/v1/gs/parcels/{id}/enrich`
- `GET /api/v1/gs/kosis/population|households` — 서울 **25구**
- `GET /api/v1/gs/vworld/possession/{pnu}` — WMS PNG
- `GET /api/v1/gs/vworld/characteristics/{pnu}`
- `GET /api/v1/gs/visualcrossing/climate|heat|timeline`

## 데이터 연동 개요

라이브 부지 구축 시:

1. VWorld 지적도 필지 → 면적·좌표 (`VW-{pnu}`)
2. 병렬: 토지특성(지목/용도지역/접면도로), 소유, 토양, AirKorea, WFS 규제, KOSIS 가구  
3. Visual Crossing climate 1회 → 일사 + 기온 기반 열섬  
4. 점수·`sumokFeasibility` 산출 (`dataProvenance` 포함)  

성능: 외부 API 병렬화, 성공 응답 TTL 캐시, VC 429 쿨다운.

### Agent 용도 정렬

`"금천구 수목"` 처럼 용도를 지정하면 **해당 점수 내림차순 정렬**한다.  
1위 추천이 SOLAR여도 수목 점수가 있으면 결과에 포함한다 (`strictTopRecommendation` 시에만 하드 필터).

상세 규칙·`actual` 플래그: **docs/api.md**.

## 테스트

```bash
python -m pytest tests/ -q
```
