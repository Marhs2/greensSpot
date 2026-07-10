# GreenSpot — API 명세서

> Base URL: `http://localhost:8000` (개발)  
> 최종 갱신: **2026-07-10**  
> 범위: 실제 공공 API 연동 · dataProvenance · 라이브 `VW-*` · agent 소프트 정렬 · 북마크/비교/시뮬 라이브 지원  
> 문서 인덱스: [README.md](./README.md)  
> **제품 범위 제외 (미제공):** `GET /api/users/me`, `PATCH /api/users/me/preferences`, `GET /api/gs/trending`, `GET /api/gs/history`, `GET /api/v1/gs/kosis/*`

모든 POST 요청은 `Content-Type: application/json` 헤더 필요.  
응답은 JSON (리포트/CSV 및 possession WMS PNG 제외).

### Prefix

| Prefix | 설명 |
| --- | --- |
| `/api/gs` | 메인 앱 (부지·에이전트·시뮬·통계) |
| `/api` | 인증·북마크·공유 |
| `/api/v1/gs` | 외부 연동 (VWorld 토지, Visual Crossing, 규제; KOSIS는 내부 enrich 전용) |

### 라이브 ID

- `VW-{19자리PNU}` 또는 path에 19자리 PNU → VWorld 라이브 필지
- DB 시드 ID 예: `DD-001`, `GN-001`

---

## API 엔드포인트 목록

### `/api/gs`

| Method | Endpoint | 설명 | 인증 |
| --- | --- | --- | --- |
| GET | `/api/gs/health` | 헬스 체크 | 불필요 |
| GET | `/api/gs/parcels` | 부지 목록 (DB 또는 라이브) | 불필요 |
| GET | `/api/gs/parcels/{id}` | 부지 상세 (DB 또는 `VW-*`) | 불필요 |
| POST | `/api/gs/agent` | AI 자연어 부지 검색 (VWorld 라이브) | 불필요 |
| POST | `/api/gs/parcels/{id}/explain` | AI 점수 설명 | 불필요 |
| POST | `/api/gs/parcels/{id}/simulate` | 시나리오 시뮬 (DB + 라이브) | 불필요 |
| POST | `/api/gs/compare` | 부지 비교 (DB + 라이브 혼합) | 불필요 |
| POST | `/api/gs/report` | 리포트 (MD/JSON) | 불필요 |
| GET | `/api/gs/export` | CSV 내보내기 | 불필요 |
| GET | `/api/gs/stats` | DB 시드 통계 | 불필요 |

### `/api` (auth)

| Method | Endpoint | 설명 | 인증 |
| --- | --- | --- | --- |
| POST | `/api/auth/signup` | 회원가입 | 불필요 |
| POST | `/api/auth/login` | 로그인 (JWT; 응답에 `user` 포함) | 불필요 |
| POST | `/api/auth/refresh` | Access 재발급 | 불필요 |
| POST | `/api/auth/logout` | 로그아웃 (body `refresh_token`) | 불필요\* |
| GET/POST/DELETE | `/api/bookmarks` | 북마크 (DB + `VW-*`) | 필요 |
| POST | `/api/share` | 공유 링크 (`VW-*` 허용) | 불필요 |

\* logout은 Bearer 없이 `refresh_token` 폐기만 수행.

### `/api/v1/gs` (integration)

| Method | Endpoint | 설명 | 인증 |
| --- | --- | --- | --- |
| GET | `/api/v1/gs/vworld/layers` | VWorld 레이어 목록 | 불필요 |
| GET | `/api/v1/gs/parcels/{id}/regulations` | 규제 조회 (DB 시드) | 불필요 |
| POST | `/api/v1/gs/parcels/{id}/regulations/sync` | 규제 동기화 (DB 시드) | 불필요 |
| POST | `/api/v1/gs/parcels/{id}/enrich` | (legacy) KMA enrich | 불필요 |
| GET | `/api/v1/gs/vworld/possession/{pnu}` | 소유정보 WMS PNG | 불필요 |
| GET | `/api/v1/gs/vworld/characteristics/{pnu}` | 토지특성 JSON | 불필요 |
| GET | `/api/v1/gs/visualcrossing/climate` | 일사·기온 요약 | 불필요 |
| GET | `/api/v1/gs/visualcrossing/heat` | 열섬 추정 | 불필요 |
| GET | `/api/v1/gs/visualcrossing/timeline` | Timeline 원자료 | 불필요 |

> 관리자 전용 API는 없다. 사용자 유형은 **비회원 / 회원** 만 둔다.

---

## ✅ Endpoints

- **`[GET]`** **Health Check**
    
    
    | Description | 서버 상태, DB 연결, 통계, 환경 변수 설정 상태를 반환합니다. |
    | --- | --- |
    | URL | `/api/gs/health` |
    | Auth Required | No |
    - **✅ Response 200**
        
        ```json
        {
          "status": "healthy",
          "timestamp": "2026-07-05T12:19:37.039Z",
          "database": "connected",
          "stats": {
            "parcels": 23,
            "scores": 23,
            "scenarios": 0,
            "agentQueries": 2
          },
          "environment": {
            "nodeEnv": "development",
            "vworldApiKeyConfigured": false,
            "kmaApiKeyConfigured": false,
            "kosisApiKeyConfigured": false,
            "visualCrossingApiKeyConfigured": false
          },
          "elapsed_ms": 4
        }
        ```
        
    - **✅ Response 503**
        
        ```json
        {
          "status": "unhealthy",
          "database": "disconnected",
          "error": "..."
        }
        ```
        

---

- **`[GET]`** **List Parcels**
    
    
    | Description | 부지 목록을 반환합니다. `live=true`(기본) 이고 `district`·`VWORLD_API_KEY` 가 있으면 **VWorld 실시간** 목록, 아니면 **DB 시드** 목록. |
    | --- | --- |
    | URL | `/api/gs/parcels` |
    | Auth Required | No |
    
    | Parameter | Type | Required | Place | Description |
    | --- | --- | --- | --- | --- |
    | district | string | No\* | query | 지역명 (예: 금천구, 용산구, 해운대구). 라이브 모드에서는 권장/사실상 필요 |
    | type | string | No | query | 부지 유형 (VACANT_LOT/ROOFTOP/UNUSED_LAND/ABANDONED/BROWNFIELD) |
    | live | bool | No | query | 기본 `true`. VWorld 실시간 조회 시도 |
    | limit | int | No | query | 라이브 결과 상한 1~20, 기본 15 |

    - 라이브 성공 시 `source: "vworld_live"`, ID는 `VW-{pnu}`
    - 라이브 실패/키 없음/district 없음 → `source: "database"`
    - **✅ Response 200**
        
        ```json
        {
          "parcels": [
            {
              "id": "DD-001",
              "name": "회기동 빈터 A",
              "district": "동대문구",
              "neighborhood": "회기동",
              "lat": 37.5894,
              "lng": 127.0586,
              "areaSqm": 680,
              "parcelType": "VACANT_LOT",
              "ownership": "PUBLIC",
              "soilType": "LOAM",
              "solarIrradiance": 4.0,
              "monthlyIrradiance": [2.1, 2.8, 3.5, 4.2, 4.6, 4.4, 4.0, 3.8, 3.3, 2.8, 2.2, 1.9],
              "sunlightHours": 5.9,
              "heatIsland": 2.1,
              "surfaceTempSummer": 34.5,
              "airQuality": 25,
              "roadAdjacent": true,
              "waterAccess": true,
              "electricityAccess": true,
              "regulations": "NONE",
              "confidence": 0.93,
              "landCategory": null,
              "dataProvenance": {
                "boundary": { "source": "VWorld", "dataType": "지적도(연속지적도)", "actual": true },
                "location": { "source": "VWorld", "dataType": "좌표(EPSG:4326)", "actual": true },
                "areaSqm": { "source": "VWorld 도형 면적", "dataType": "geometry 산출", "actual": true },
                "regulations": { "source": "VWorld WFS+토지특성", "dataType": "규제/용도지역 레이어", "actual": true },
                "parcelType": { "source": "VWorld 토지특성정보", "dataType": "지목→UI유형", "actual": true },
                "ownership": { "source": "VWorld/국토부 토지소유정보", "dataType": "소유구분(실제)", "actual": true },
                "soilType": { "source": "농촌진흥청 토양정보", "dataType": "토성(실제)", "actual": true },
                "solarIrradiance": { "source": "Visual Crossing", "dataType": "일사량(kWh/㎡/day)", "actual": true },
                "sunlightHours": { "source": "Visual Crossing (미조회/실패)", "dataType": "일사량 기반 추정", "actual": false },
                "monthlyIrradiance": { "source": "GreenSpot", "dataType": "연간일사×계절계수 (월별 실측 아님)", "actual": false },
                "heatIsland": { "source": "Visual Crossing", "dataType": "기온 기반 추정", "actual": true },
                "surfaceTempSummer": { "source": "Visual Crossing", "dataType": "기온+오프셋 추정", "actual": true },
                "airQuality": { "source": "AirKorea", "dataType": "PM2.5(실제)", "actual": true },
                "roadAdjacent": { "source": "VWorld 토지특성(접면도로)", "dataType": "roadSideCode", "actual": true },
                "waterAccess": { "source": "GreenSpot", "dataType": "도로인접 기반 추정", "actual": false },
                "electricityAccess": { "source": "GreenSpot", "dataType": "도시지역 기본 가정", "actual": false },
                "nearbyHouseholds": { "source": "KOSIS", "dataType": "자치구 총가구", "actual": false },
                "scores": { "source": "GreenSpot", "dataType": "알고리즘(입력 일부 추정 가능)", "actual": true },
                "sumokFeasibility": { "source": "GreenSpot", "dataType": "규제 기반 수목 식재 가능성", "actual": true },
                "visualCrossingConfigured": true
              },
              "scores": {
                "treeScore": 69,
                "gardenScore": 90,
                "solarScore": 74,
                "topRecommendation": "GARDEN",
                "uncertainty": 4,
                "confidence": 0.93,
                "treeBreakdown": ["..."],
                "gardenBreakdown": ["..."],
                "solarBreakdown": ["..."]
              }
            }
          ],
          "stats": {
            "total": 23,
            "avgTreeScore": 63,
            "avgGardenScore": 74,
            "avgSolarScore": 67,
            "topTreeCount": 2,
            "topGardenCount": 16,
            "topSolarCount": 5,
            "totalAreaSqm": 9120
          },
          "source": "database",
          "vworldEnabled": false
        }
        ```
        
    - **✅ Response 500**
        
        ```json
        {
          "error": "서버 오류",
          "detail": "..."
        }
        ```
        

---

- **`[GET]`** **VWorld Possession WMS**

    | Description | VWorld 토지소유정보 WMS(`getPossessionWMS`)를 호출해 PNU 기준으로 토지 소유정보가 오버레이된 PNG 이미지를 반환합니다. |
    | --- | --- |
    | URL | `/api/v1/gs/vworld/possession/{pnu}` |
    | Auth Required | No |

    | Parameter | Type | Required | Place | Description |
    | --- | --- | --- | --- | --- |
    | pnu | string | Yes | path | 토지 고유번호 (예: `1111010100100010000`) |
    | bbox | string | Yes | query | EPSG:4326 bbox `ymin,xmin,ymax,xmax` (위/경도 순서) |
    | width | int | No | query | 이미지 너비(px), 기본 915, 1~2048 |
    | height | int | No | query | 이미지 높이(px), 기본 700, 1~2048 |
    - **✅ Response 200 (image/png)**
        - `Content-Type: image/png` 으로 PNG 바이트를 반환합니다.
    - **✅ Response 200 (이미지 미가용 시 metadata)**
        ```json
        {
          "pnu": "1111010100100010000",
          "contentType": "image/png",
          "dataAvailable": false
        }
        ```
    - **✅ Response 400**
        ```json
        { "detail": "bbox는 'ymin,xmin,ymax,xmax' 4개 값이 필요합니다." }
        ```
        ```json
        { "detail": "VWORLD_API_KEY가 설정되지 않았습니다. .env에 키를 입력하세요." }
        ```
    - **✅ Response 422**
        - `bbox` 누락 또는 `width`/`height` 범위 위반 시 검증 에러.
    - **⚠️ Notes**
        - WMS 레이어는 토지소유정보 `dt_d160` (단일 레이어, EPSG:4326 고정).
        - bbox 는 `ymin,xmin,ymax,xmax` 4개의 부동소수점. 위도는 -90~90, 경도는 -180~180.
        - VWorld 호출 실패/HTML 응답/바이트 누락 등 예외 상황에서는 `dataAvailable: false` 의 200 JSON으로 응답합니다.
        - 호출 URL 예: `https://api.vworld.kr/ned/wms/getPossessionWMS?key=...&domain=localhost&layer=dt_d160&format=image/png&bbox=...&width=...&height=...&pnu=...`

---

- **`[GET]`** **VWorld Land Characteristics**

    | Description | VWorld 토지특성정보(`getLandCharacteristics`)를 호출해 PNU/기준연도 기준 토지 특성 항목들을 JSON 으로 반환합니다. |
    | --- | --- |
    | URL | `/api/v1/gs/vworld/characteristics/{pnu}` |
    | Auth Required | No |

    | Parameter | Type | Required | Place | Description |
    | --- | --- | --- | --- | --- |
    | pnu | string | Yes | path | 토지 고유번호 (예: `1111010100100010000`) |
    | stdrYear | string | No | query | 조회 기준 연도 `YYYY` (미지정 시 현재 연도) |
    - **✅ Response 200**
        ```json
        {
          "pnu": "1111010100100010000",
          "items": [
            { "pnu": "1111010100100010000", "ldCode": "11110", "stdrYear": "2024" }
          ],
          "count": 1,
          "source": "vworld",
          "dataAvailable": true,
          "year": "2024"
        }
        ```
    - **✅ Response 400**
        ```json
        { "detail": "VWORLD_API_KEY가 설정되지 않았습니다. .env에 키를 입력하세요." }
        ```
    - **⚠️ Notes**
        - 호출 URL 예: `https://api.vworld.kr/ned/data/getLandCharacteristics?key=...&domain=localhost&pnu=...&stdrYear=...&format=json&numOfRows=100&pageNo=1`
        - 응답 본문은 `landCharacteristics.items` / `result.items` / `item` / `list` 등 다양한 키 구조를 정규화하여 `items` 배열로 평탄화합니다.
        - VWorld 호출 실패/네트워크 오류 시 `dataAvailable: false`, `items: []`, `count: 0` 의 fallback 응답을 200 으로 반환합니다.
        - `stdrYear` 미지정 시 `datetime.utcnow().year` 를 사용합니다.

---

- **`[GET]`** **Visual Crossing Climate**

    | Description | Visual Crossing Timeline API로 좌표 기준 최근 기간의 일사량(`solarIrradiance` kWh/㎡/day), 일조시간(`sunlightHours`), 평균 기온(`avgTemperature`)을 요약해 반환합니다. |
    | --- | --- |
    | URL | `/api/v1/gs/visualcrossing/climate` |
    | Auth Required | No |

    | Parameter | Type | Required | Place | Description |
    | --- | --- | --- | --- | --- |
    | lat | float | Yes | query | 위도 (-90~90) |
    | lng | float | Yes | query | 경도 (-180~180) |
    | days | int | No | query | 조회 기간(일), 1~365, 기본 30 |
    - **✅ Response 200**
        ```json
        {
          "source": "visualcrossing",
          "district": null,
          "location": "37.5145,127.0533",
          "start": "2025-06-08",
          "end": "2025-07-08",
          "solarIrradiance": 4.21,
          "sunlightHours": 6.12,
          "avgTemperature": 24.5,
          "dataAvailable": true
        }
        ```
    - **✅ Response 400**
        ```json
        { "detail": "lat은 -90~90 범위여야 합니다." }
        ```
        ```json
        { "detail": "VISUAL_CROSSING_API_KEY가 설정되지 않았습니다. .env에 입력하세요." }
        ```
    - **⚠️ Notes**
        - `solarenergy`(MJ/m²/day) 평균값에 `0.2777778` 을 곱해 kWh/㎡/day 로 변환합니다.
        - `days` 대신 `start`/`end` 도 내부 헬퍼로 정규화되며, 미지정 시 최근 30일.

---

- **`[GET]`** **Visual Crossing Heat**

    | Description | Visual Crossing Timeline API로 여름 기간의 평균 기온을 조회해 열섬 강도(`heatIsland`)와 지표면 온도(`surfaceTempSummer`)를 추정합니다. |
    | --- | --- |
    | URL | `/api/v1/gs/visualcrossing/heat` |
    | Auth Required | No |

    | Parameter | Type | Required | Place | Description |
    | --- | --- | --- | --- | --- |
    | lat | float | Yes | query | 위도 (-90~90) |
    | lng | float | Yes | query | 경도 (-180~180) |
    | days | int | No | query | 여름 산정 윈도우(일), 1~365, 기본 30 |
    - **✅ Response 200**
        ```json
        {
          "source": "visualcrossing",
          "district": null,
          "location": "37.5145,127.0533",
          "period": { "start": "2024-06-01", "end": "2024-08-31" },
          "heatIsland": 2.3,
          "surfaceTempSummer": 32.4,
          "avgTemperature": 27.4,
          "maxTemperature": 33.1,
          "dataAvailable": true
        }
        ```
    - **⚠️ Notes**
        - `surfaceTempSummer` = 여름 평균 기온 + 5.0 ℃
        - `heatIsland` = max(0, 여름 평균 기온 - 25.0 ℃)
        - 미연동/오류 시 모든 추정값은 `null` 이고 `dataAvailable: false`.

---

- **`[GET]`** **Visual Crossing Timeline**

    | Description | Visual Crossing Timeline API 의 일별 원자료(`days`)를 그대로 반환합니다. 도시명(`Seoul,South Korea`) 또는 `lat,lng` 문자열을 그대로 location 으로 사용할 수 있습니다. |
    | --- | --- |
    | URL | `/api/v1/gs/visualcrossing/timeline` |
    | Auth Required | No |

    | Parameter | Type | Required | Place | Description |
    | --- | --- | --- | --- | --- |
    | location | string | Yes | query | Visual Crossing location (도시명 또는 `lat,lng`) |
    | start | string | No | query | 시작일 (YYYY-MM-DD) |
    | end | string | No | query | 종료일 (YYYY-MM-DD) |
    - **✅ Response 200**
        ```json
        {
          "source": "visualcrossing",
          "location": "Seoul,South Korea",
          "start": "2025-07-01",
          "end": "2025-07-02",
          "days": [
            { "datetime": "2025-07-01", "temp": 27.0, "solarenergy": 18.0 },
            { "datetime": "2025-07-02", "temp": 28.5, "solarenergy": 19.2 }
          ],
          "count": 2,
          "dataAvailable": true
        }
        ```
    - **⚠️ Notes**
        - `start`/`end` 미지정 시 최근 30일.
        - 호출 URL 예: `https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/<location>?key=...&unitGroup=metric&include=days&startDateTime=...&endDateTime=...&contentType=json`

---



- **`[GET]`** **Get Parcel Detail**
    
    
    | Description | 단일 부지의 상세 정보와 점수를 반환합니다. DB 시드 또는 라이브 `VW-*` / 19자리 PNU. |
    | --- | --- |
    | URL | `/api/gs/parcels/{id}` |
    | Auth Required | No |
    
    | Parameter | Type | Required | Place | Description |
    | --- | --- | --- | --- | --- |
    | id | string | Yes | path | `DD-001` 또는 `VW-1117012500100010000` 또는 19자리 PNU |
    - **✅ Response 200**
        
        ```json
        {
          "parcel": {
            "id": "VW-1117012500100010000",
            "name": "한강로2가 1 부지",
            "district": "용산구",
            "areaSqm": 7161,
            "ownership": "PUBLIC",
            "soilType": "LOAM",
            "landCategory": "MIXED",
            "regulations": [],
            "sumokFeasibility": { "status": "AVAILABLE", "score": 72, "reason": "..." },
            "dataProvenance": { "...": "필드별 actual 플래그" },
            "scores": { "treeScore": 68, "gardenScore": 71, "solarScore": 74, "topRecommendation": "SOLAR" }
          },
          "scores": {
            "treeScore": 68,
            "gardenScore": 71,
            "solarScore": 74,
            "topRecommendation": "SOLAR",
            "uncertainty": 8,
            "treeBreakdown": ["..."],
            "gardenBreakdown": ["..."],
            "solarBreakdown": ["..."]
          },
          "source": "vworld_live"
        }
        ```
        
        - 캐시 히트: `source: "vworld_live_cache"`
        - DB: `source: "database"`
    - **✅ Response 404** — DB·라이브 모두 없음
    - **ℹ️ Notes**
        - 추천 코드: API `topRecommendation` 은 **`TREE` | `GARDEN` | `SOLAR`** (명세 초안의 `SUMOK` 와 동의어로 취급)
        - UI 수목 점수는 `treeScore` / `sumokScore` 매핑

---

- **`[POST]`** **AI Natural Language Parcel Search (Agent)** ⭐
    
    
    | Description | 자연어를 조건으로 파싱한 뒤 **VWorld 실시간**(`live_search`) 검색합니다. 키 없으면 DB 폴백. |
    | --- | --- |
    | URL | `/api/gs/agent` |
    | Auth Required | No |
    
    | Parameter | Type | Required | Place | Description |
    | --- | --- | --- | --- | --- |
    | query | string | Yes | body | 자연어 검색 문장 (지역명 포함 권장) |
    - **📌 Request Body Example**
        
        ```json
        {
          "query": "금천구 수목"
        }
        ```
        
    - **🧠 Search Keyword Mapping Rules**
        
        
        | 자연어 키워드 | 매핑 |
        | --- | --- |
        | 지역명 (용산구, 금천구, 해운대구, 성남시 …) | `district` / `region` (VWorld 행정구역 resolve) |
        | 동 이름 (가능 시) | `neighborhood` |
        | 빈터/옥상/유휴지/방치건물/오염정화지 | `parcelType` |
        | 수목·식재·나무·식수 / 텃밭 / 태양광·솔라 | `topRecommendation` = TREE / GARDEN / SOLAR |
        | N점 / 점수 높은 | `minScore` |
        | 상위 N개 | `limit` (최대 20, 기본 10) |
        
    - **🔀 topRecommendation 정책 (중요)**
        - **기본 = 소프트 정렬**: 해당 용도 점수(`treeScore` 등) **내림차순**으로 정렬.
        - **1위 추천 불일치로 결과를 버리지 않음.**  
          예: `"금천구 수목"` → TREE 정렬. 필지 1위가 SOLAR여도 수목 점수가 있으면 포함.
        - **하드 필터**는 criteria `strictTopRecommendation: true` 일 때만 (`topRecommendation` 완전 일치).
        - `minScore` 가 있으면 **선호 용도 점수** 기준으로 필터.
        - 응답 meta(내부): `preferredUse`, `strictTopRecommendation`, `candidates`, `sampled_emd`.
        
    - **✅ Response 200**
        
        ```json
        {
          "query": "금천구 수목",
          "criteria": {
            "district": "금천구",
            "region": "금천구",
            "topRecommendation": "TREE",
            "sortBy": "score",
            "limit": 10,
            "live": true,
            "explanation": "지역=금천구 · 추천=TREE · 상위 10개 · VWorld 실시간",
            "liveMeta": {
              "source": "vworld_live",
              "region": "금천구",
              "preferredUse": "TREE",
              "strictTopRecommendation": false,
              "candidates": 8
            }
          },
          "results": [
            {
              "id": "VW-11545...",
              "name": "가산동 … 부지",
              "district": "금천구",
              "areaSqm": 1200,
              "scores": {
                "treeScore": 71,
                "gardenScore": 68,
                "solarScore": 74,
                "topRecommendation": "SOLAR"
              },
              "dataProvenance": { "...": "..." }
            }
          ],
          "summary": "… 부지가 추천됩니다. 금천구 · VWorld 실시간 조회 2건 (수목 점수 71 기준 정렬)",
          "count": 2,
          "elapsed_ms": 4500,
          "source": "ai"
        }
        ```
        
    - **🛡️ Hallucination Defense**
        1. 규칙 기반 criteria 추출 (지역·용도·유형·점수)
        2. `live_search` 결정론적 검색 (VWorld + enrich)
        3. LLM 요약 시 결과 이름만 전달, 새 수치 금지. LLM 미설정 시 규칙 요약
    - **✅ Errors / empty**
        - 지역 없음: summary 안내 메시지, `count: 0`
        - VWorld 미해석 지역: message 포함
        - 500: 서버 오류

---

- **`[POST]`** **Explain Parcel Scores**
    
    
    | Description | 부지 점수에 대한 AI 자연어 설명을 생성합니다. |
    | --- | --- |
    | URL | `/api/gs/parcels/{id}/explain` |
    | Auth Required | No |
    
    | Parameter | Type | Required | Place | Description |
    | --- | --- | --- | --- | --- |
    | id | string | Yes | path | 부지 ID |
    - **📌 Request Body Example**
        
        ```json
        {}
        ```
        
    - **✅ Response 200**
        
        ```json
        {
          "parcelId": "DD-001",
          "explanation": "## 📍 부지 요약\n...\n## 🎯 추천 결과 및 이유\n...\n## 💡 대안 용도 검토\n...\n## ⚠️ 한계 및 보완점\n...",
          "facts": { "...": "사전 계산된 수치 객체" },
          "promptVersion": "v3-greenspot2",
          "uncertainty": 4
        }
        ```
        
    - **🧾 Output Schema (Markdown 4 sections)**
        - 📍 부지 요약: 위치, 면적, 유형, 소유권, 규제
        - 🎯 추천 결과 및 이유: 1순위 + 상위 2-3개 기여 항목
        - 💡 대안 용도 검토: 2순위, 3순위 설명
        - ⚠️ 한계 및 보완점: 불확실성, 신뢰도, 추가 검토사항
    - **🛡️ Rules**
        - facts 객체 외 수치 사용 금지
        - 출처 명시: VWorld / AirKorea / Visual Crossing / KOSIS / GreenSpot 알고리즘
        - 정치적 단어 금지 (불평등/격차/소외/차별)
        - LLM 실패 시 규칙 기반 fallback

---

- **`[POST]`** **Simulate Scenarios**
    
    
    | Description | 부지에 대한 인프라 설치 시나리오를 시뮬레이션합니다. **DB 시드 부지**와 **VWorld 라이브 부지(`VW-{pnu}`)** 모두 지원합니다. |
    | --- | --- |
    | URL | `/api/gs/parcels/{id}/simulate` |
    | Auth Required | No |
    
    | Parameter | Type | Required | Place | Description |
    | --- | --- | --- | --- | --- |
    | id | string | Yes | path | 부지 ID (`DD-001` 또는 `VW-1117...`) |
    | scenarioType / scenario_type | string | Yes | body | `PLANT_TREES` / `CREATE_GARDEN` / `INSTALL_SOLAR` / `COMPARE_ALL` (별칭: `SUMOK`/`TREE`→PLANT_TREES, `GARDEN`→CREATE_GARDEN, `SOLAR`→INSTALL_SOLAR) |
    | quantity | number | No | body | 수량 (기본값: 10) |
    | areaSqm / area_sqm | number | No | body | 라이브 필지용 면적 힌트. 상세 화면이 이미 알고 있는 면적. VWorld 재조회 실패 시 폴백 |
    | parcelName / parcel_name | string | No | body | 라이브 필지용 이름 힌트 |
    - **📌 Request Body Example**
        
        ```json
        {
          "scenario_type": "COMPARE_ALL",
          "quantity": 10,
          "area_sqm": 7161,
          "parcel_name": "한강로2가 1 부지"
        }
        ```
        
    - **🔢 Quantity Limits**
        - PLANT_TREES / SUMOK / TREE: 최대 200
        - CREATE_GARDEN / GARDEN: 최대 150
        - INSTALL_SOLAR / SOLAR: 최대 500
    - **라이브 필지 동작**
        1. DB에서 `parcel_id` 조회
        2. 없으면 `live_get_parcel` (메모리 캐시 → VWorld PNU 단건)
        3. 그래도 없으면 `area_sqm` 힌트로 계산만 수행
        4. 라이브 필지는 `scenarios` 테이블에 **저장하지 않음** (FK `parcels.id` 없음)
        5. DB 부지만 시나리오 행 저장
    - **✅ Response 200 (COMPARE_ALL)**
        
        ```json
        {
          "parcelId": "VW-1117012500100010000",
          "parcelName": "한강로2가 1 부지",
          "parcelArea": 7161.0,
          "scenarios": {
            "PLANT_TREES": {
              "label": "나무 28그루",
              "effects": {
                "carbonKgPerYear": 2223,
                "pm25ReductionKgPerYear": 4.424,
                "temperatureReductionC": 2.2,
                "rainwaterLitersPerYear": 30800,
                "costEstimateWon": 5600000,
                "annualMaintenanceWon": 420000,
                "costPerCarbonKgWon": 2519,
                "paybackYears": null,
                "summary": "은행나무 성목 28그루 식재 시 연간 CO2 2223kg 흡수..."
              }
            },
            "CREATE_GARDEN": { "...": "..." },
            "INSTALL_SOLAR": {
              "effects": {
                "energyKwhPerYear": 23870,
                "energyMonthly": [1800, 2400, "..."],
                "carbonKgPerYear": 9930,
                "paybackYears": 24,
                "costPerCarbonKgWon": 933
              }
            }
          },
          "elapsed_ms": 12
        }
        ```
        
    - **📚 Static Coeff Sources**
        - USDA i-Tree Eco (나무 심기)
        - 한국에너지공단 14.2% (태양광)
        - 서울연구원 도시농업 보고서 (텃밭)
    - **✅ Errors**
        - 400: 잘못된 입력 (수량 초과 등)
        - 404: 부지 없음 (DB·라이브·면적 힌트 모두 실패)
        - 500: 서버 오류

---

- **`[POST]`** **Compare Parcels**
    
    
    | Description | 2개 이상 부지를 비교합니다. **DB 시드 + 라이브 `VW-*` 혼합** 가능. |
    | --- | --- |
    | URL | `/api/gs/compare` |
    | Auth Required | No |
    
    | Parameter | Type | Required | Place | Description |
    | --- | --- | --- | --- | --- |
    | ids | string[] | Yes | body | 비교할 부지 ID 배열 (2개 이상, 중복 제거) |
    - **📌 Request Body Example**
        
        ```json
        {
          "ids": ["DD-001", "VW-1117012500100010000"]
        }
        ```
        
    - **처리**
        1. DB에서 ID 일괄 조회
        2. 없는 ID는 `live_get_parcel` 로 보강
        3. 면적 기반 나무 시나리오 1회 실행 → `effects.PLANT_TREES` (탄소 랭킹용)
        4. 유효 항목 2개 미만이면 400
    - **✅ Response 200**
        
        ```json
        {
          "comparison": [
            {
              "id": "VW-1117012500100010000",
              "name": "한강로2가 1 부지",
              "district": "용산구",
              "areaSqm": 7161,
              "scores": { "tree": 68, "garden": 71, "solar": 74, "top": "SOLAR" },
              "effects": {
                "PLANT_TREES": {
                  "carbonKgPerYear": 2223,
                  "costEstimateWon": 5600000
                }
              }
            }
          ],
          "ranking": {
            "tree": ["..."],
            "garden": ["..."],
            "solar": ["..."],
            "carbon": ["..."],
            "costEfficiency": ["..."]
          }
        }
        ```
        
    - **✅ Errors**
        - 400: 비교할 부지 2개 이상 필요 / 유효한 부지 2개 이상 필요

---

- **`[POST]`** **Export Report (MD/JSON)**
    
    
    | Description | 부지 분석 리포트를 Markdown 또는 JSON으로 내보냅니다. |
    | --- | --- |
    | URL | `/api/gs/report` |
    | Auth Required | No |
    
    | Parameter | Type | Required | Place | Description |
    | --- | --- | --- | --- | --- |
    | parcelId | string | Yes | body | 부지 ID |
    | format | string | Yes | body | `markdown` 또는 `json` |
    - **📌 Request Body Example**
        
        ```json
        {
          "parcelId": "DD-001",
          "format": "markdown"
        }
        ```
        
    - **✅ Response 200**
        - Markdown: `Content-Type: text/markdown`, 파일명 `greenspot-{id}.md`
        - JSON: `Content-Type: application/json`, 파일명 `greenspot-{id}.json`
    - **🧾 Markdown Report Structure**
        
        ```markdown
        # GreenSpot 분석 리포트
        
        ## 부지 정보
        - 부지명, 위치, 좌표, 면적, 유형, 소유권, 토양, 규제
        
        ## 환경 데이터
        - 일사량, 일조시간, 열섬강도, 지표면온도, PM2.5, 도로/수자원/전력
        
        ## 점수 분석 (불확실성 ±N점, 신뢰도 N%)
        | 용도 | 점수 |
        
        ## 시나리오 시뮬레이션
        ### 나무 심기 / 텃밭 / 태양광
        - 효과, 투자비, 유지비, 효율성
        ```
        

---

- **`[GET]`** **Export Parcels CSV**
    
    
    | Description | 부지 데이터를 Excel 호환 CSV 파일로 내보냅니다. |
    | --- | --- |
    | URL | `/api/gs/export` |
    | Auth Required | No |
    - **✅ Response 200**
        - Content-Type: `text/csv; charset=utf-8`
        - Content-Disposition: `attachment; filename="greenspot-parcels-YYYY-MM-DD.csv"`
        - UTF-8 BOM 포함 (Excel 호환)
    - **📌 CSV Columns**
        
        ```
        ID, 부지명, 자치구, 행정동, 위도, 경도,
        면적(㎡), 부지유형, 소유권, 토양,
        일사량(kWh/㎡/일), 일조시간, 열섬강도(℃), 여름지표면온도(℃), PM2.5(μg/m³),
        도로접면, 수자원접근, 전력접근,
        수목점수, 텃밭점수, 태양광점수, 1순위추천, 불확실성(±)
        ```
        (보행·학교·지하철 등 미연동 사회지표 컬럼 없음)
        
    - **📌 Example**
        
        ```bash
        curl -O https://your-domain.com/api/gs/export
        # 또는 브라우저에서 헤더의 "CSV" 버튼 클릭
        ```
        

---

- **`[GET]`** **Stats**
    
    
    | Description | **DB 시드 부지** 기준 자치구별·유형별·추천 분포 통계. |
    | --- | --- |
    | URL | `/api/gs/stats` |
    | Auth Required | No |
    - **✅ Response 200**
        
        ```json
        {
          "totalParcels": 23,
          "byDistrict": [
            {
              "district": "동대문구",
              "count": 5,
              "totalArea": 2200,
              "avgTreeScore": 65,
              "avgGardenScore": 78,
              "avgSolarScore": 70,
              "topRecs": { "TREE": 0, "GARDEN": 4, "SOLAR": 1 }
            }
          ],
          "byType": [
            {
              "parcelType": "VACANT_LOT",
              "count": 8,
              "totalArea": 3500,
              "avgScore": 82
            }
          ],
          "byRecommendation": { "TREE": 2, "GARDEN": 16, "SOLAR": 5 },
          "generatedAt": "2026-07-05T12:57:58.319Z"
        }
        ```
        
    - **ℹ️ Notes**
        - 본 API는 **시드 DB 전역** 집계이며 선택 지역 라이브 통계가 아님.
        - 프론트 통계 화면은 사용자가 고른 지역의 `GET /api/gs/parcels?district=…&live=true` 결과로 **클라이언트 집계**할 수 있다 (다지역 지원).
        - 목록 응답의 `stats` (`live_stats_from_results`) 도 현재 결과 집합 요약에 사용 가능.
        - agent 호출 시 `AgentQuery` 테이블에 로그를 남기지만, 공개 `trending`/`history` API는 **제공하지 않는다**.

---

- **`[POST]`** **Sign Up (Email/Password)**
    
    
    | Description | 이메일/비밀번호 기반 회원가입을 수행합니다. |
    | --- | --- |
    | URL | `/api/auth/signup` |
    | Auth Required | No |
    
    | Parameter | Type | Required | Place | Description |
    | --- | --- | --- | --- | --- |
    | email | string | Yes | body | 이메일 |
    | password | string | Yes | body | 비밀번호 (해시 저장) |
    - **✅ Response 201**
        
        ```json
        { "ok": true }
        ```
        
    - **✅ Errors**
        - 400: 입력 검증 실패
        - 409: 이미 존재하는 이메일

---

- **`[POST]`** **Login (JWT)**
    
    
    | Description | 이메일/비밀번호로 로그인하고 JWT(Access/Refresh)를 발급합니다. |
    | --- | --- |
    | URL | `/api/auth/login` |
    | Auth Required | No |
    - **✅ Response 200**

        ```json
        {
          "access_token": "...",
          "refresh_token": "...",
          "token_type": "bearer",
          "user": {
            "id": "usr_...",
            "email": "user@example.com",
            "created_at": "2026-07-05T12:19:37.039Z"
          }
        }
        ```

    - **ℹ️ Notes**
        - Access Token은 API 호출 시 `Authorization: Bearer <token>` 헤더로 전달합니다.
        - Refresh Token은 만료 시 `/api/auth/refresh`로 재발급합니다.
        - `GET /api/users/me` 는 **미제공**. 사용자 정보는 로그인 응답 `user` 및 클라이언트 세션으로 처리.

---

- **`[GET]`** **List Bookmarks**
    
    
    | Description | 현재 로그인한 사용자의 북마크 목록 (스냅샷 필드 포함). |
    | --- | --- |
    | URL | `/api/bookmarks` |
    | Auth Required | Yes (`Authorization: Bearer`) |
    - **✅ Response 200**
        
        ```json
        {
          "bookmarks": [
            {
              "parcelId": "VW-1117012500100010000",
              "parcelName": "한강로2가 1 부지",
              "district": "용산구",
              "topRecommendation": "SOLAR",
              "topScore": 74,
              "createdAt": "2026-07-09T12:19:37.039Z"
            }
          ]
        }
        ```
        

---

- **`[POST]`** **Add Bookmark**
    
    
    | Description | 부지를 북마크에 추가합니다. **DB 시드 + 라이브 `VW-*`** 모두 가능. Parcel FK 없음. |
    | --- | --- |
    | URL | `/api/bookmarks` |
    | Auth Required | Yes |
    
    | Parameter | Type | Required | Place | Description |
    | --- | --- | --- | --- | --- |
    | parcelId | string | Yes | body | 부지 ID (`DD-001` 또는 `VW-…`) |
    | parcelName | string | No | body | 라이브 스냅샷 이름 (권장) |
    | district | string | No | body | 라이브 스냅샷 지역 (권장) |
    | topRecommendation | string | No | body | TREE/GARDEN/SOLAR |
    | topScore | number | No | body | 대표 점수 |
    - **처리 순서**
        1. DB `parcels` 조회 → 점수 스냅샷
        2. 없으면 body 메타 충분 시 외부 호출 생략 후 저장
        3. 아니면 `live_get_parcel` → 메타 채움
        4. `VW-` ID + body 일부만으로도 저장 허용
        5. 전혀 해석 불가면 404
    - **📌 Request Body Example (라이브)**
        
        ```json
        {
          "parcelId": "VW-1117012500100010000",
          "parcelName": "한강로2가 1 부지",
          "district": "용산구",
          "topRecommendation": "SOLAR",
          "topScore": 74
        }
        ```
        
    - **✅ Response 201** — `{ "ok": true }`
    - **✅ Errors**
        - 404: 부지 해석 불가
        - 409: 이미 북마크됨

---

- **`[DELETE]`** **Remove Bookmark**
    
    
    | Description | 북마크를 삭제합니다. |
    | --- | --- |
    | URL | `/api/bookmarks?parcelId={id}` |
    | Auth Required | Yes |
    - **✅ Response 200** — `{ "ok": true }`
    - **✅ Errors** — 404: Bookmark not found

---

- **`[POST]`** **Create Share Link**
    
    
    | Description | 공유용 `shareId` 발급. **DB 부지 또는 `VW-*`** (Share 테이블에 Parcel FK 없음). |
    | --- | --- |
    | URL | `/api/share` |
    | Auth Required | Optional |
    
    | Parameter | Type | Required | Place | Description |
    | --- | --- | --- | --- | --- |
    | parcelId | string | Yes | body | 공유할 부지 ID |
    - **처리**: DB 있으면 저장. 없으면 `VW-` 이고 live resolve 성공 시 저장.
    - **✅ Response 200**
        
        ```json
        {
          "shareId": "sh_abc123",
          "url": "https://your-domain.com/greenspot/share/sh_abc123"
        }
        ```
        

---

## 📊 Data Sources (`dataProvenance`)

라이브/상세 응답의 `dataProvenance` 는 **필드별로 실제 외부 데이터가 반영됐을 때만** `actual: true` 이다.  
API 키만 설정되고 조회 실패·쿨다운 중이면 `actual: false` 이며 `source` 에 `(미연동)` 또는 `(미조회/실패)` 가 붙는다.

| Field | Source (성공 시) | Data Type | `actual` Rule |
| --- | --- | --- | --- |
| `boundary` | VWorld | 연속지적도 (LP_PA_CBND_BUBUN) | VWorld 출처이면 `true` |
| `location` | VWorld | 좌표 (EPSG:4326) | VWorld 출처이면 `true` |
| `areaSqm` | VWorld 토지특성 `lndpclAr` 또는 도형 면적 | 대장면적 / geometry | VWorld 출처이면 `true` (대장 우선) |
| `regulations` | VWorld WFS + 토지특성 용도지역 | 규제/용도지역 | 규제 1건 이상이면 `true` |
| `parcelType` | VWorld 토지특성 지목 → UI 유형 | 지목→UI유형 | 지목 조회·매핑 성공 시 `true` |
| `ownership` | VWorld `getPossessionAttr` | 소유구분 PUBLIC/PRIVATE | 조회 성공 시 `true` |
| `soilType` | 흙토람 (농진청) V3 `getSoilCharacter` | PNU 표토토성 (Surtture_Cd). 부가: `soilTypeLabel`, `soilDetail` | 조회·매핑 성공 시 `true`. 라이브=PNU, DB상세=좌표→PNU |
| `solarIrradiance` | Visual Crossing climate | 일사량 kWh/㎡/day | VC 일사 조회 성공 시만 `true` |
| `sunlightHours` | Visual Crossing climate | 일조시간 | VC sunshine 성공 시만 `true` |
| `monthlyIrradiance` | GreenSpot | **연간일사×계절계수 (월별 실측 아님)** | 항상 `false` |
| `heatIsland` | Visual Crossing (기온 파생) | 기온 기반 추정 | VC 기온 성공 시 `true` |
| `surfaceTempSummer` | Visual Crossing (기온+오프셋) | 기온 기반 추정 | VC 기온 성공 시 `true` |
| `airQuality` | AirKorea | PM2.5 | 시도 실시간 조회 성공 시 `true` |
| `roadAdjacent` | VWorld 토지특성 roadSideCode | 접면도로 | 코드/명칭 있을 때 `true` |
| `waterAccess` | GreenSpot | 도로인접 기반 추정 | 기본 `false` (실측 아님) |
| `electricityAccess` | GreenSpot | 도시지역 기본 가정 | 기본 `false` (실측 아님) |
| `nearbyHouseholds` | KOSIS (내부 서비스, 공개 API 없음) | 자치구 총가구 | 라이브 enrich 성공 시 `true`, 미제공 시 `null`+`false` |
| `scores` | GreenSpot | 알고리즘 (입력 일부 추정 가능) | 항상 `true` |
| `sumokFeasibility` | GreenSpot | 규제 기반 수목 식재 가능성 | 항상 `true` |

부가 플래그: `kmaApiKeyConfigured` (legacy), `visualCrossingConfigured`.

### 외부 API · 환경 변수

| 용도 | env | 비고 |
| --- | --- | --- |
| VWorld 지적/WFS/토지특성/소유 | `VWORLD_API_KEY`, `LAND_OWNERSHIP_API_KEY`, `LAND_OWNERSHIP_BASE_URL` | 소유: `https://api.vworld.kr/ned/data/getPossessionAttr` |
| AirKorea PM2.5 | `AIRKOREA_API_KEY`, `AIRKOREA_BASE_URL` | 공공데이터 키는 URL-디코딩 후 전송 (이중 인코딩 방지) |
| 토양 (흙토람) | `SOIL_API_KEY`, `SOIL_BASE_URL` | `.../SoilEnviron/SoilCharac/V3/getSoilCharacter?PNU_CD=`. DB 시드 상세는 VWorld PNU 역조회 후 동일 호출 |
| Visual Crossing | `VISUAL_CROSSING_API_KEY`, `VISUAL_CROSSING_BASE_URL` | climate 1회 호출로 일사+기온 파생. 429 시 쿨다운 |
| KOSIS | `KOSIS_API_KEY` | 서울 25개 자치구 `objL1` 매핑. 연도 작년→재작년 폴백 |

### 라이브 부지 파이프라인 성능

`build_parcel_from_feature` 는 다음을 수행한다.

1. land / ownership / soil / air / regulations / kosis **병렬** 조회  
2. 성공 응답 **TTL 캐시** (PNU·자치구 단위, 실패 응답은 캐시하지 않음)  
3. Visual Crossing climate **1회** + 자치구 캐시, 429 시 재호출 억제  
4. WFS 규제 레이어 **병렬**  
5. 점수: 면적 log 스케일, breakdown 문자열 포함. 상한 92  

`live_search` 는 후보 수집 후 enrich 동시 4개, 읍면동 샘플을 제한한다.

- 면적 기본 필터: `minArea` 기본 350㎡, `maxArea` 기본 15000㎡  
- `topRecommendation`: **정렬 키** (기본 하드 필터 아님, `strictTopRecommendation` 시에만 일치 필터)  
- 성공 필지는 메모리 TTL 캐시에 넣어 상세/시뮬/북마크 재조회를 가속

### 추천 코드 용어

| 용도 | API `topRecommendation` | 시나리오 별칭 | 점수 필드 |
| --- | --- | --- | --- |
| 수목 식재 | `TREE` (명세 초안 `SUMOK` 동의어) | `PLANT_TREES`, `TREE`, `SUMOK` | `treeScore` / `sumokScore` |
| 도시농업 | `GARDEN` | `CREATE_GARDEN`, `GARDEN` | `gardenScore` |
| 태양광 | `SOLAR` | `INSTALL_SOLAR`, `SOLAR` | `solarScore` |

### parcelType / landCategory

| 지목 예 | landCategory | parcelType (UI) |
| --- | --- | --- |
| 잡종지 | MIXED | UNUSED_LAND |
| 임야 | FOREST | UNUSED_LAND |
| 대/전 | AGRICULTURE | VACANT_LOT |
| 공장용지 | INDUSTRIAL | BROWNFIELD |

`parcelType` 허용: `VACANT_LOT` | `ROOFTOP` | `UNUSED_LAND` | `ABANDONED` | `BROWNFIELD`  
`ownership`: `PUBLIC` | `PRIVATE` | `UNKNOWN`  
`soilType`: `LOAM` | `CLAY` | `SAND` | `ROCKY` | `UNKNOWN`

### sumokFeasibility

- 자연녹지 등 용도지역은 severity `warning` → status **`CONDITIONAL`**
- primary `regulatoryRestriction` 은 URBAN_ZONE 보다 구체 용도지역(ZONING_*) 우선
- 문구 예: *"자연녹지지역 등으로 수목 식재는 가능하나 행위 제한·인허가 확인이 필요합니다."*

## 📊 Data Model

- **Parcel (API 응답 / 라이브)**
    
    
    | 필드 | 타입 | 설명 |
    | --- | --- | --- |
    | id | string | 부지 ID (`VW-{pnu}` 또는 시드 ID) |
    | name | string | 부지명 |
    | district | string | 자치구 |
    | neighborhood | string | 행정동 |
    | lat, lng | float | 위도, 경도 (WGS84) |
    | areaSqm | float | 면적 (㎡). 대장 `lndpclAr` 우선 |
    | parcelType | string | VACANT_LOT/ROOFTOP/UNUSED_LAND/ABANDONED/BROWNFIELD |
    | landCategory | string\|null | 지목 상세 (MIXED/FOREST/…) |
    | ownership | string | PUBLIC/PRIVATE/UNKNOWN |
    | soilType | string | LOAM/CLAY/SAND/ROCKY/UNKNOWN |
    | solarIrradiance | float | 일사량 (kWh/㎡/day) |
    | monthlyIrradiance | number[12] | 연간×계절계수 (실측 월별 아님) |
    | sunlightHours | float | 일조시간 |
    | heatIsland | float | 열섬강도 (℃, 기온 기반 추정) |
    | surfaceTempSummer | float | 여름 지표면온도 추정 (℃) |
    | airQuality | float | PM2.5 (μg/m³) |
    | nearbyHouseholds 등 | number\|null | 미연동 시 `null` (가짜 0 금지) |
    | roadAdjacent | bool | 접면도로 (토지특성) |
    | waterAccess | bool | 추정 (도로인접 기반) |
    | electricityAccess | bool | 추정 (도시 기본 가정) |
    | regulations | array | WFS + 용도지역 객체 배열 |
    | sumokFeasibility | object | status/score/reason/… |
    | confidence | float | 실데이터 필드 수 기반 (약 0.58~0.97) |
    | dataProvenance | object | 필드별 출처·actual |
    | pnu | string | 19자리 필지 고유번호 |
- **ParcelScore (응답 scores)**
    
    
    | 필드 | 타입 | 설명 |
    | --- | --- | --- |
    | treeScore / gardenScore / solarScore | float | 0–92 권장 상한, 규제 반영 후 |
    | topRecommendation | string | TREE/GARDEN/SOLAR |
    | uncertainty | float | 실데이터 부족 시 증가 |
    | treeBreakdown 등 | string[] | 점수 근거 문장 |
- **Scenario**
    
    
    | 필드 | 타입 | 설명 |
    | --- | --- | --- |
    | parcelId | string | 부지 ID (FK, **DB 부지만** 저장) |
    | scenarioType | string | PLANT_TREES/CREATE_GARDEN/INSTALL_SOLAR |
    | quantity | int | 수량 |
    | effects | JSON | 효과 데이터 |
- **AgentQuery**
    
    
    | 필드 | 타입 | 설명 |
    | --- | --- | --- |
    | query | string | 사용자 질문 |
    | criteria | string | JSON (검색 조건) |
    | resultCount | int | 결과 수 |
    | summary | string | AI 요약 |
    | source | string | ai/fallback |

---

## 🛡️ Error Handling

- **Standard Error Response**
    
    ```json
    {
      "error": "에러 메시지",
      "detail": "상세 정보 (개발 모드만)"
    }
    ```
    
- **Status Codes**
    
    
    | 코드 | 의미 | 발생 상황 |
    | --- | --- | --- |
    | 200 | OK | 정상 응답 |
    | 400 | Bad Request | 입력 검증 실패 |
    | 404 | Not Found | 부지 ID 없음 |
    | 500 | Internal Server Error | 서버 오류 |
    | 503 | Service Unavailable | 헬스 체크 실패 (DB) |

---

## 📈 Performance

| 엔드포인트 | 평균 응답 시간 | 비고 |
| --- | --- | --- |
| GET /api/gs/health | ~4ms | DB count 쿼리 |
| GET /api/gs/parcels | ~50ms | DB 시드 목록 |
| GET /api/gs/parcels/{id} (DB) | ~30ms | 단일 부지 |
| GET /api/gs/parcels/{id} (라이브 첫 조회) | ~2–5초 | 외부 API 병렬 + WFS. 캐시 재조회 ~0.5초 |
| POST /api/gs/agent (라이브) | 수 초~ | VWorld 검색 + enrich 병렬 |
| POST /api/gs/parcels/{id}/explain | ~5-10초 | AI 호출 1회 |
| POST /api/gs/parcels/{id}/simulate | ~수 ms–수 초 | DB면 즉시. 라이브면 resolve/캐시 후 계산. 면적 힌트 시 외부 재조회 최소화 |
| POST /api/gs/compare | ~10ms+ | 부지수에 비례 |
| POST /api/gs/report | ~5ms+ | Markdown 생성 |
| GET /api/gs/export | ~100ms+ | CSV |
| GET /api/gs/stats | ~200ms | 통계 집계 |

### 캐시 TTL (프로세스 메모리)

| 키 패턴 | TTL | 조건 |
| --- | --- | --- |
| `vworld:land:{pnu}` | 30분 | dataAvailable |
| `own:{pnu}` / `soil:{pnu}` | 30분 | dataAvailable |
| `air:{district}` | 10분 | dataAvailable |
| `regs:{lat4}:{lng4}` | 15분 | 규제 1건 이상 |
| `kosis:hh:{district}` | 1일 | dataAvailable |
| `vc:climate:{district}` | 1시간 | climate 응답 |
| VC 429 쿨다운 | 30분 | 전역 재호출 억제 |
