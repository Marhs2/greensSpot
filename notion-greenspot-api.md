
> Base URL: `http://localhost:8000` (개발)
> Base URL: [https://greensspot.onrender.com/docs](https://greensspot.onrender.com/docs) (외부)
<empty-block/>
> 범위: 실제 공공 API 연동 · dataProvenance · 라이브 `VW-*` · agent 소프트 정렬 · 북마크/비교/시뮬 라이브 지원
> 최종 갱신: **2026-07-10** — 미제공 엔드포인트 문서 삭제 (me / preferences / kosis 공개 / trending / history)
> **제품 범위 제외 (미제공):** `GET /api/users/me`, `PATCH /api/users/me/preferences`, `GET /api/gs/trending`, `GET /api/gs/history`, `GET /api/v1/gs/kosis/*`
모든 POST 요청은 `Content-Type: application/json` 헤더 필요.  
응답은 JSON (리포트/CSV 및 possession WMS PNG 제외).
### Prefix
<table header-row="true">
<tr>
<td>Prefix</td>
<td>설명</td>
</tr>
<tr>
<td>`/api/gs`</td>
<td>메인 앱 (부지·에이전트·시뮬·통계)</td>
</tr>
<tr>
<td>`/api`</td>
<td>인증·북마크·공유</td>
</tr>
<tr>
<td>`/api/v1/gs`</td>
<td>외부 연동 (VWorld 토지, Visual Crossing, 규제; KOSIS는 내부 enrich 전용)</td>
</tr>
</table>
### 라이브 ID
- **라이브**: `VW-{19자리PNU}` 또는 path에 19자리 PNU → VWorld 실시간 필지 (DB에 없을 수 있음)
- **DB 시드**: `seed_data.json` 의 ID (예: `VW-0103160000`). 접두사 `VW-` 여도 **시드 단축 ID** 이며 19자리 라이브 PNU 와 다름
- **상세 라우팅**: `GET /api/gs/parcels/{id}` 는 `VW-` 접두사 또는 19자리 PNU 이면 **라이브 먼저**, 실패 시 DB 폴백. 시드 단축 ID도 `VW-` 때문에 라이브 경로를 경유한다.
---
## API 엔드포인트 목록
<empty-block/>
### `/api/gs`
<table header-row="true">
<tr>
<td>Method</td>
<td>Endpoint</td>
<td>설명</td>
<td>인증</td>
</tr>
<tr>
<td>GET</td>
<td>`/api/gs/health`</td>
<td>헬스 체크</td>
<td>불필요</td>
</tr>
<tr>
<td>GET</td>
<td>`/api/gs/parcels`</td>
<td>부지 목록 (DB 또는 라이브)</td>
<td>불필요</td>
</tr>
<tr>
<td>GET</td>
<td>`/api/gs/parcels/{id}`</td>
<td>부지 상세 (DB 또는 `VW-*`)</td>
<td>불필요</td>
</tr>
<tr>
<td>POST</td>
<td>`/api/gs/agent`</td>
<td>AI 자연어 부지 검색 (VWorld 라이브)</td>
<td>불필요</td>
</tr>
<tr>
<td>POST</td>
<td>`/api/gs/parcels/{id}/explain`</td>
<td>AI 점수 설명</td>
<td>불필요</td>
</tr>
<tr>
<td>POST</td>
<td>`/api/gs/parcels/{id}/simulate`</td>
<td>시나리오 시뮬 (DB + 라이브)</td>
<td>불필요</td>
</tr>
<tr>
<td>POST</td>
<td>`/api/gs/compare`</td>
<td>부지 비교 (DB + 라이브 혼합)</td>
<td>불필요</td>
</tr>
<tr>
<td>POST</td>
<td>`/api/gs/report`</td>
<td>리포트 (MD/JSON)</td>
<td>불필요</td>
</tr>
<tr>
<td>GET</td>
<td>`/api/gs/export`</td>
<td>CSV 내보내기</td>
<td>불필요</td>
</tr>
<tr>
<td>GET</td>
<td>`/api/gs/stats`</td>
<td>DB 시드 통계</td>
<td>불필요</td>
</tr>
</table>
### `/api` (auth)
<table header-row="true">
<tr>
<td>Method</td>
<td>Endpoint</td>
<td>설명</td>
<td>인증</td>
</tr>
<tr>
<td>POST</td>
<td>`/api/auth/signup`</td>
<td>회원가입</td>
<td>불필요</td>
</tr>
<tr>
<td>POST</td>
<td>`/api/auth/login`</td>
<td>로그인 (JWT)</td>
<td>불필요</td>
</tr>
<tr>
<td>POST</td>
<td>`/api/auth/refresh`</td>
<td>Access 재발급</td>
<td>불필요</td>
</tr>
<tr>
<td>POST</td>
<td>`/api/auth/logout`</td>
<td>로그아웃 (body `refresh_token`)</td>
<td>불필요\*</td>
</tr>

<tr>
<td>GET/POST/DELETE</td>
<td>`/api/bookmarks`</td>
<td>북마크 (DB + `VW-*`)</td>
<td>필요</td>
</tr>
<tr>
<td>POST</td>
<td>`/api/share`</td>
<td>공유 링크 (`VW-*` 허용)</td>
<td>불필요</td>
</tr>

</table>
### `/api/v1/gs` (integration)
<table header-row="true">
<tr>
<td>Method</td>
<td>Endpoint</td>
<td>설명</td>
<td>인증</td>
</tr>
<tr>
<td>GET</td>
<td>`/api/v1/gs/vworld/layers`</td>
<td>VWorld 레이어 목록</td>
<td>불필요</td>
</tr>
<tr>
<td>GET</td>
<td>`/api/v1/gs/parcels/{id}/regulations`</td>
<td>규제 조회</td>
<td>불필요</td>
</tr>
<tr>
<td>POST</td>
<td>`/api/v1/gs/parcels/{id}/regulations/sync`</td>
<td>규제 동기화</td>
<td>불필요</td>
</tr>
<tr>
<td>POST</td>
<td>`/api/v1/gs/parcels/{id}/enrich`</td>
<td>(legacy) KMA enrich — 현재 미설정 시 400</td>
<td>불필요</td>
</tr>


<tr>
<td>GET</td>
<td>`/api/v1/gs/vworld/possession/{pnu}`</td>
<td>소유정보 WMS PNG</td>
<td>불필요</td>
</tr>
<tr>
<td>GET</td>
<td>`/api/v1/gs/vworld/characteristics/{pnu}`</td>
<td>토지특성 JSON</td>
<td>불필요</td>
</tr>
<tr>
<td>GET</td>
<td>`/api/v1/gs/visualcrossing/climate`</td>
<td>일사·기온 요약</td>
<td>불필요</td>
</tr>
<tr>
<td>GET</td>
<td>`/api/v1/gs/visualcrossing/heat`</td>
<td>열섬 추정</td>
<td>불필요</td>
</tr>
<tr>
<td>GET</td>
<td>`/api/v1/gs/visualcrossing/timeline`</td>
<td>Timeline 원자료</td>
<td>불필요</td>
</tr>
</table>
---
## ✅ Endpoints
<details>
<summary>**`[GET]`** **Health Check**</summary>
	<table header-row="true">
<tr>
<td>Description</td>
<td>서버 상태, DB 연결, 통계, 환경 변수 설정 상태를 반환합니다.</td>
</tr>
<tr>
<td>URL</td>
<td>`/api/gs/health`</td>
</tr>
<tr>
<td>Auth Required</td>
<td>No</td>
</tr>
	</table>
	<details>
	<summary>**✅ Response 200** (항상 HTTP 200 — degraded 모드 포함)</summary>
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
	</details>
	<details>
	<summary>**ℹ️ Notes**</summary>
		- DB 조회 실패 시에도 HTTP **200**, `status` 는 `"healthy"` 를 유지하고 `database` 만 `"disconnected"` 로 표기한다. (503/`unhealthy` 는 미구현)
		- `stats` 카운트 실패 시 해당 값은 `0`
		- `kmaApiKeyConfigured` 는 legacy 플래그 (enrich 스텁용). 실제 기후 연동은 Visual Crossing.
	</details>
</details>
---
<details>
<summary>**`[GET]`** **List Parcels**</summary>
	<table header-row="true">
<tr>
<td>Description</td>
<td>부지 목록을 반환합니다. `live=true`(기본) 이고 `district`·`VWORLD_API_KEY` 가 있으면 **VWorld 실시간** 목록, 아니면 **DB 시드** 목록.</td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>URL</td>
<td>`/api/gs/parcels`</td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>Auth Required</td>
<td>No</td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>Parameter</td>
<td>Type</td>
<td>Required</td>
<td>Place</td>
<td>Description</td>
</tr>
<tr>
<td>---</td>
<td>---</td>
<td>---</td>
<td>---</td>
<td>---</td>
</tr>
<tr>
<td>district</td>
<td>string</td>
<td>No\*</td>
<td>query</td>
<td>지역명 (예: 금천구, 용산구, 해운대구). 라이브 모드에서는 권장/사실상 필요</td>
</tr>
<tr>
<td>type</td>
<td>string</td>
<td>No</td>
<td>query</td>
<td>부지 유형 (VACANT_LOT/ROOFTOP/UNUSED_LAND/ABANDONED/BROWNFIELD)</td>
</tr>
<tr>
<td>live</td>
<td>bool</td>
<td>No</td>
<td>query</td>
<td>기본 `true`. VWorld 실시간 조회 시도</td>
</tr>
<tr>
<td>limit</td>
<td>int</td>
<td>No</td>
<td>query</td>
<td>라이브 결과 상한 1\~20, 기본 15</td>
</tr>
	</table>
	- 라이브 성공 시 `source: "vworld_live"`, ID는 `VW-{pnu}`
	- 라이브 실패/키 없음/district 없음 → `source: "database"`
	<details>
	<summary>**✅ Response 200**</summary>
		```json
{
  "parcels": [
    {
      "id": "VW-0103160000",
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
      "regulatoryRestriction": "NONE",
      "regulations": [],
      "sumokFeasibility": null,
      "confidence": 0.93,
      "landCategory": null,
      "dataProvenance": {
        "boundary": { "source": "VWorld/LP_PA_CBND_BUBUN", "dataType": "지적도(연속지적도)", "actual": true },
        "location": { "source": "VWorld/LP_PA_CBND_BUBUN", "dataType": "좌표(EPSG:4326)", "actual": true },
        "areaSqm": { "source": "VWorld/LP_PA_CBND_BUBUN", "dataType": "geometry 산출", "actual": true },
        "regulations": { "source": "GreenSpot", "dataType": "규제/용도지역 레이어", "actual": false },
        "parcelType": { "source": "GreenSpot", "dataType": "지목→UI유형", "actual": false },
        "ownership": { "source": "GreenSpot", "dataType": "소유구분", "actual": false },
        "soilType": { "source": "흙토람 (농진청)", "dataType": "PNU 표토토성(Surtture_Cd)", "actual": true },
        "solarIrradiance": { "source": "GreenSpot", "dataType": "일사량(kWh/㎡/day)", "actual": false },
        "sunlightHours": { "source": "GreenSpot", "dataType": "일조시간", "actual": false },
        "monthlyIrradiance": { "source": "GreenSpot", "dataType": "연간일사×계절계수 (월별 실측 아님)", "actual": false },
        "heatIsland": { "source": "GreenSpot", "dataType": "기온 기반 추정", "actual": false },
        "surfaceTempSummer": { "source": "GreenSpot", "dataType": "기온+오프셋 추정", "actual": false },
        "airQuality": { "source": "GreenSpot", "dataType": "PM2.5", "actual": false },
        "roadAdjacent": { "source": "GreenSpot", "dataType": "접면도로", "actual": false },
        "waterAccess": { "source": "GreenSpot", "dataType": "도로인접 기반 추정", "actual": false },
        "electricityAccess": { "source": "GreenSpot", "dataType": "도시지역 기본 가정", "actual": false },
        "nearbyHouseholds": { "source": "KOSIS", "dataType": "자치구 총가구", "actual": false },
        "scores": { "source": "GreenSpot", "dataType": "알고리즘(입력 일부 추정 가능)", "actual": true },
        "sumokFeasibility": { "source": "GreenSpot", "dataType": "규제 기반 수목 식재 가능성", "actual": true },
        "visualCrossingConfigured": false
      },
      "scores": {
        "treeScore": 69,
        "gardenScore": 90,
        "solarScore": 74,
        "topRecommendation": "GARDEN",
        "uncertainty": 4,
        "treeBreakdown": [],
        "gardenBreakdown": [],
        "solarBreakdown": []
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
	</details>
	<details>
	<summary>**ℹ️ Notes**</summary>
		- `regulations` 는 **객체 배열** (문자열 `"NONE"` 아님). 요약 문자열은 `regulatoryRestriction`
		- `confidence` 는 **parcel 필드**. `scores` 객체에는 `confidence` 없음
		- DB 시드 목록의 `treeBreakdown` 등은 빈 배열. 라이브 enrich 경로에서만 문장 배열이 채워질 수 있음
		- DB 시드 `dataProvenance`: `data_source` 문자열에 `"VWorld"` 가 포함되면 boundary/location/area 에 `actual:true` 가 붙을 수 있음 (시드 출처 표기). 라이브 경로의 “조회 성공 시 true” 규칙과 구분
	</details>
	<details>
	<summary>**✅ Response 500**</summary>
		```json
{
  "error": "서버 오류",
  "detail": "..."
}
		```
	</details>
</details>
---
<details>
<summary>**`[GET]`** **VWorld Possession WMS**</summary>
	<table header-row="true">
<tr>
<td>Description</td>
<td>VWorld 토지소유정보 WMS(`getPossessionWMS`)를 호출해 PNU 기준으로 토지 소유정보가 오버레이된 PNG 이미지를 반환합니다.</td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>URL</td>
<td>`/api/v1/gs/vworld/possession/{pnu}`</td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>Auth Required</td>
<td>No</td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>Parameter</td>
<td>Type</td>
<td>Required</td>
<td>Place</td>
<td>Description</td>
</tr>
<tr>
<td>---</td>
<td>---</td>
<td>---</td>
<td>---</td>
<td>---</td>
</tr>
<tr>
<td>pnu</td>
<td>string</td>
<td>Yes</td>
<td>path</td>
<td>토지 고유번호 (예: `1111010100100010000`)</td>
</tr>
<tr>
<td>bbox</td>
<td>string</td>
<td>Yes</td>
<td>query</td>
<td>EPSG:4326 bbox `ymin,xmin,ymax,xmax` (위/경도 순서)</td>
</tr>
<tr>
<td>width</td>
<td>int</td>
<td>No</td>
<td>query</td>
<td>이미지 너비(px), 기본 915, 1\~2048</td>
</tr>
<tr>
<td>height</td>
<td>int</td>
<td>No</td>
<td>query</td>
<td>이미지 높이(px), 기본 700, 1\~2048</td>
</tr>
	</table>
	<details>
	<summary>**✅ Response 200 (image/png)**</summary>
		- `Content-Type: image/png` 으로 PNG 바이트를 반환합니다.
	</details>
	<details>
	<summary>**✅ Response 200 (이미지 미가용 시 metadata)**</summary>
		```json
{
  "pnu": "1111010100100010000",
  "contentType": "image/png",
  "dataAvailable": false
}
		```
	</details>
	<details>
	<summary>**✅ Response 400**</summary>
		```json
{ "detail": "bbox는 'ymin,xmin,ymax,xmax' 4개 값이 필요합니다." }
		```
		```json
{ "detail": "VWORLD_API_KEY가 설정되지 않았습니다. .env에 키를 입력하세요." }
		```
	</details>
	<details>
	<summary>**✅ Response 422**</summary>
		- `bbox` 누락 또는 `width`/`height` 범위 위반 시 검증 에러.
	</details>
	<details>
	<summary>**⚠️ Notes**</summary>
		- WMS 레이어는 토지소유정보 `dt_d160` (단일 레이어, EPSG:4326 고정).
		- bbox 는 `ymin,xmin,ymax,xmax` 4개의 부동소수점. 위도는 -90\~90, 경도는 -180\~180.
		- VWorld 호출 실패/HTML 응답/바이트 누락 등 예외 상황에서는 `dataAvailable: false` 의 200 JSON으로 응답합니다.
		- 호출 URL 예: `https://api.vworld.kr/ned/wms/getPossessionWMS?key=...&domain=localhost&layer=dt_d160&format=image/png&bbox=...&width=...&height=...&pnu=...`
	</details>
</details>
---
<details>
<summary>**`[GET]`** **VWorld Land Characteristics**</summary>
	<table header-row="true">
<tr>
<td>Description</td>
<td>VWorld 토지특성정보(`getLandCharacteristics`)를 호출해 PNU/기준연도 기준 토지 특성 항목들을 JSON 으로 반환합니다.</td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>URL</td>
<td>`/api/v1/gs/vworld/characteristics/{pnu}`</td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>Auth Required</td>
<td>No</td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>Parameter</td>
<td>Type</td>
<td>Required</td>
<td>Place</td>
<td>Description</td>
</tr>
<tr>
<td>---</td>
<td>---</td>
<td>---</td>
<td>---</td>
<td>---</td>
</tr>
<tr>
<td>pnu</td>
<td>string</td>
<td>Yes</td>
<td>path</td>
<td>토지 고유번호 (예: `1111010100100010000`)</td>
</tr>
<tr>
<td>stdrYear</td>
<td>string</td>
<td>No</td>
<td>query</td>
<td>조회 기준 연도 `YYYY` (미지정 시 현재 연도)</td>
</tr>
	</table>
	<details>
	<summary>**✅ Response 200**</summary>
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
	</details>
	<details>
	<summary>**✅ Response 400**</summary>
		```json
{ "detail": "VWORLD_API_KEY가 설정되지 않았습니다. .env에 키를 입력하세요." }
		```
	</details>
	<details>
	<summary>**⚠️ Notes**</summary>
		- 호출 URL 예: `https://api.vworld.kr/ned/data/getLandCharacteristics?key=...&domain=localhost&pnu=...&stdrYear=...&format=json&numOfRows=100&pageNo=1`
		- 응답 본문은 `landCharacteristics.items` / `result.items` / `item` / `list` 등 다양한 키 구조를 정규화하여 `items` 배열로 평탄화합니다.
		- VWorld 호출 실패/네트워크 오류 시 `dataAvailable: false`, `items: []`, `count: 0` 의 fallback 응답을 200 으로 반환합니다.
		- `stdrYear` 미지정 시 `datetime.utcnow().year` 를 사용합니다.
	</details>
</details>
---
<details>
<summary>**`[GET]`** **Visual Crossing Climate**</summary>
	<table header-row="true">
<tr>
<td>Description</td>
<td>Visual Crossing Timeline API로 좌표 기준 최근 기간의 일사량(`solarIrradiance` kWh/㎡/day), 일조시간(`sunlightHours`), 평균 기온(`avgTemperature`)을 요약해 반환합니다.</td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>URL</td>
<td>`/api/v1/gs/visualcrossing/climate`</td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>Auth Required</td>
<td>No</td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>Parameter</td>
<td>Type</td>
<td>Required</td>
<td>Place</td>
<td>Description</td>
</tr>
<tr>
<td>---</td>
<td>---</td>
<td>---</td>
<td>---</td>
<td>---</td>
</tr>
<tr>
<td>lat</td>
<td>float</td>
<td>Yes</td>
<td>query</td>
<td>위도 (-90\~90)</td>
</tr>
<tr>
<td>lng</td>
<td>float</td>
<td>Yes</td>
<td>query</td>
<td>경도 (-180\~180)</td>
</tr>
<tr>
<td>days</td>
<td>int</td>
<td>No</td>
<td>query</td>
<td>조회 기간(일), 1\~365, 기본 30</td>
</tr>
	</table>
	<details>
	<summary>**✅ Response 200**</summary>
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
	</details>
	<details>
	<summary>**✅ Response 400**</summary>
		```json
{ "detail": "lat은 -90~90 범위여야 합니다." }
		```
		```json
{ "detail": "VISUAL_CROSSING_API_KEY가 설정되지 않았습니다. .env에 입력하세요." }
		```
	</details>
	<details>
	<summary>**⚠️ Notes**</summary>
		- `solarenergy`(MJ/m²/day) 평균값에 `0.2777778` 을 곱해 kWh/㎡/day 로 변환합니다.
		- `days` 대신 `start`/`end` 도 내부 헬퍼로 정규화되며, 미지정 시 최근 30일.
	</details>
</details>
---
<details>
<summary>**`[GET]`** **Visual Crossing Heat**</summary>
	<table header-row="true">
<tr>
<td>Description</td>
<td>Visual Crossing Timeline API로 여름 기간의 평균 기온을 조회해 열섬 강도(`heatIsland`)와 지표면 온도(`surfaceTempSummer`)를 추정합니다.</td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>URL</td>
<td>`/api/v1/gs/visualcrossing/heat`</td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>Auth Required</td>
<td>No</td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>Parameter</td>
<td>Type</td>
<td>Required</td>
<td>Place</td>
<td>Description</td>
</tr>
<tr>
<td>---</td>
<td>---</td>
<td>---</td>
<td>---</td>
<td>---</td>
</tr>
<tr>
<td>lat</td>
<td>float</td>
<td>Yes</td>
<td>query</td>
<td>위도 (-90\~90)</td>
</tr>
<tr>
<td>lng</td>
<td>float</td>
<td>Yes</td>
<td>query</td>
<td>경도 (-180\~180)</td>
</tr>
<tr>
<td>days</td>
<td>int</td>
<td>No</td>
<td>query</td>
<td>**현재 구현에서 무시됨.** 기간은 항상 당해(또는 로직) 여름(6/1–8/31)</td>
</tr>
	</table>
	<details>
	<summary>**✅ Response 200**</summary>
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
	</details>
	<details>
	<summary>**⚠️ Notes**</summary>
		- `surfaceTempSummer` = 여름 평균 기온 + 5.0 ℃
		- `heatIsland` = max(0, 여름 평균 기온 - 25.0 ℃)
		- 미연동/오류 시 추정값은 `null` 이고 `dataAvailable: false` (라우터/스키마 경로).
	</details>
</details>
---
<details>
<summary>**`[GET]`** **Visual Crossing Timeline**</summary>
	<table header-row="true">
<tr>
<td>Description</td>
<td>Visual Crossing Timeline API 의 일별 원자료(`days`)를 그대로 반환합니다. 도시명(`Seoul,South Korea`) 또는 `lat,lng` 문자열을 그대로 location 으로 사용할 수 있습니다.</td>
</tr>
<tr>
<td>URL</td>
<td>`/api/v1/gs/visualcrossing/timeline`</td>
</tr>
<tr>
<td>Auth Required</td>
<td>No</td>
</tr>
<tr>
<td>Parameter</td>
<td>Type</td>
</tr>
<tr>
<td>---</td>
<td>---</td>
</tr>
<tr>
<td>location</td>
<td>string</td>
</tr>
<tr>
<td>start</td>
<td>string</td>
</tr>
<tr>
<td>end</td>
<td>string</td>
</tr>
	</table>
	<details>
	<summary>**✅ Response 200**</summary>
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
	</details>
	<details>
	<summary>**⚠️ Notes**</summary>
		- `start`/`end` 미지정 시 최근 30일.
		- 업스트림 호출 형식(구현): path 에 기간 포함  
			`.../timeline/{location}/{start}/{end}?key=...&unitGroup=metric&include=days&contentType=json`
	</details>
</details>
---
<details>
<summary>**`[GET]`** **Get Parcel Detail**</summary>
	<table header-row="true">
<tr>
<td>Description</td>
<td>단일 부지의 상세 정보와 점수를 반환합니다. DB 시드 또는 라이브 `VW-*` / 19자리 PNU.</td>
</tr>
<tr>
<td>URL</td>
<td>`/api/gs/parcels/{id}`</td>
</tr>
<tr>
<td>Auth Required</td>
<td>No</td>
</tr>
<tr>
<td>Parameter</td>
<td>Type</td>
</tr>
<tr>
<td>---</td>
<td>---</td>
</tr>
<tr>
<td>id</td>
<td>string</td>
</tr>
	</table>
	<details>
	<summary>**✅ Response 200**</summary>
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
    "dataProvenance": { "...": "필드별 actual 플래그" }
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
	</details>
	<details>
	<summary>**✅ Response 404** — DB·라이브 모두 없음</summary>
	</details>
	<details>
	<summary>**ℹ️ Notes**</summary>
		- **라우팅**: `VW-` 접두사 또는 19자리 PNU → 라이브 우선, 실패 시 DB. 시드 단축 ID(`VW-0103…`)도 라이브 경로를 먼저 탄다.
		- **라이브** 응답의 `parcel` 은 `regulations` / `sumokFeasibility` 를 포함한다.
		- **DB 시드 상세**(`get_parcel_detail`) 현재 구현은 목록과 달리 `regulations`·`sumokFeasibility` 를 parcel 에 실지 않을 수 있다. (목록 API 에는 포함)
		- 추천 코드: API `topRecommendation` 은 **`TREE`**** \| ****`GARDEN`**** \| ****`SOLAR`** (명세 초안의 `SUMOK` 와 동의어로 취급)
		- UI 수목 점수는 `treeScore` / `sumokScore` 매핑
	</details>
</details>
---
<details>
<summary>**`[POST]`** **AI Natural Language Parcel Search (Agent)** ⭐</summary>
	<table header-row="true">
<tr>
<td>Description</td>
<td>자연어를 조건으로 파싱한 뒤 **VWorld 실시간**(`live_search`) 검색합니다. 키 없으면 DB 폴백.</td>
</tr>
<tr>
<td>URL</td>
<td>`/api/gs/agent`</td>
</tr>
<tr>
<td>Auth Required</td>
<td>No</td>
</tr>
<tr>
<td>Parameter</td>
<td>Type</td>
</tr>
<tr>
<td>---</td>
<td>---</td>
</tr>
<tr>
<td>query</td>
<td>string</td>
</tr>
	</table>
	<details>
	<summary>**📌 Request Body Example**</summary>
		```json
{
  "query": "금천구 수목"
}
		```
	</details>
	<details>
	<summary>**🧠 Search Keyword Mapping Rules**</summary>
		<table header-row="true">
<tr>
<td>자연어 키워드</td>
<td>매핑</td>
</tr>
<tr>
<td>지역명 (용산구, 금천구, 해운대구, 성남시 …)</td>
<td>`district` / `region` (VWorld 행정구역 resolve)</td>
</tr>
<tr>
<td>동 이름 (가능 시)</td>
<td>`neighborhood`</td>
</tr>
<tr>
<td>빈터/옥상/유휴지/방치건물/오염정화지</td>
<td>`parcelType`</td>
</tr>
<tr>
<td>수목·식재·나무·식수 / 텃밭 / 태양광·솔라</td>
<td>`topRecommendation` = TREE / GARDEN / SOLAR</td>
</tr>
<tr>
<td>N점 / 점수 높은</td>
<td>`minScore`</td>
</tr>
<tr>
<td>상위 N개</td>
<td>`limit` (최대 20, 기본 10)</td>
</tr>
		</table>
	</details>
	<details>
	<summary>**🔀 topRecommendation 정책 (중요)**</summary>
		- **기본 = 소프트 정렬**: 해당 용도 점수(`treeScore` 등) **내림차순**으로 정렬.
		- **1위 추천 불일치로 결과를 버리지 않음.**  
			예: `"금천구 수목"` → TREE 정렬. 필지 1위가 SOLAR여도 수목 점수가 있으면 포함.
		- **하드 필터**는 criteria `strictTopRecommendation: true` 일 때만 (`topRecommendation` 완전 일치).
		- `minScore` 가 있으면 **선호 용도 점수** 기준으로 필터.
		- 응답 meta(내부): `preferredUse`, `strictTopRecommendation`, `candidates`, `sampled_emd`.
	</details>
	<details>
	<summary>**✅ Response 200**</summary>
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
	</details>
	<details>
	<summary>**🛡️ Hallucination Defense**</summary>
		1. 규칙 기반 criteria 추출 (지역·용도·유형·점수)
		2. `live_search` 결정론적 검색 (VWorld + enrich)
		3. LLM 요약 시 결과 이름만 전달, 새 수치 금지. LLM 미설정 시 규칙 요약
	</details>
	<details>
	<summary>**✅ Errors / empty**</summary>
		- 지역 없음: summary 안내 메시지, `count: 0`
		- VWorld 미해석 지역: message 포함
		- 500: 서버 오류
	</details>
</details>
---
<details>
<summary>**`[POST]`** **Explain Parcel Scores**</summary>
	<table header-row="true">
<tr>
<td>Description</td>
<td>부지 점수에 대한 AI 자연어 설명을 생성합니다.</td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>URL</td>
<td>`/api/gs/parcels/{id}/explain`</td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>Auth Required</td>
<td>No</td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>Parameter</td>
<td>Type</td>
<td>Required</td>
<td>Place</td>
<td>Description</td>
</tr>
<tr>
<td>---</td>
<td>---</td>
<td>---</td>
<td>---</td>
<td>---</td>
</tr>
<tr>
<td>id</td>
<td>string</td>
<td>Yes</td>
<td>path</td>
<td>부지 ID</td>
</tr>
	</table>
	<details>
	<summary>**📌 Request Body Example**</summary>
		```json
{}
		```
	</details>
	<details>
	<summary>**✅ Response 200**</summary>
		```json
{
  "parcelId": "VW-0103160000",
  "explanation": "## 📍 부지 요약\n...\n## 🎯 추천 결과 및 이유\n...\n## 💡 대안 용도 검토\n...\n## ⚠️ 한계 및 보완점\n...",
  "facts": { "...": "사전 계산된 수치 객체" },
  "promptVersion": "v3-greenspot3",
  "uncertainty": 4
}
		```
	</details>
	<details>
	<summary>**🧾 Output Schema (Markdown 4 sections)**</summary>
		- 📍 부지 요약: 위치, 면적, 유형, 소유권, 규제
		- 🎯 추천 결과 및 이유: 1순위 + 상위 2-3개 기여 항목
		- 💡 대안 용도 검토: 2순위, 3순위 설명
		- ⚠️ 한계 및 보완점: 불확실성, 신뢰도, 추가 검토사항
	</details>
	<details>
	<summary>**🛡️ Rules**</summary>
		- facts 객체 외 수치 사용 금지
		- 출처는 구현 기준: VWorld / AirKorea / Visual Crossing / KOSIS / GreenSpot 알고리즘. 출처를 단정할 때는 facts·dataProvenance 를 따른다
		- 정치적 단어 금지 (불평등/격차/소외/차별)
		- LLM 실패 시 규칙 기반 fallback
	</details>
</details>
---
<details>
<summary>**`[POST]`** **Simulate Scenarios**</summary>
	<table header-row="true">
<tr>
<td>Description</td>
<td>부지에 대한 인프라 설치 시나리오를 시뮬레이션합니다. **DB 시드 부지**와 **VWorld 라이브 부지(****`VW-{pnu}`****)** 모두 지원합니다.</td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>URL</td>
<td>`/api/gs/parcels/{id}/simulate`</td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>Auth Required</td>
<td>No</td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>Parameter</td>
<td>Type</td>
<td>Required</td>
<td>Place</td>
<td>Description</td>
</tr>
<tr>
<td>---</td>
<td>---</td>
<td>---</td>
<td>---</td>
<td>---</td>
</tr>
<tr>
<td>id</td>
<td>string</td>
<td>Yes</td>
<td>path</td>
<td>부지 ID (시드 또는 `VW-{19자리PNU}`)</td>
</tr>
<tr>
<td>scenarioType / scenario_type</td>
<td>string</td>
<td>Yes</td>
<td>body</td>
<td>`PLANT_TREES` / `CREATE_GARDEN` / `INSTALL_SOLAR` / `COMPARE_ALL` (별칭: `SUMOK`/`TREE`→PLANT_TREES, `GARDEN`→CREATE_GARDEN, `SOLAR`→INSTALL_SOLAR)</td>
</tr>
<tr>
<td>quantity</td>
<td>number</td>
<td>No</td>
<td>body</td>
<td>수량 (기본값: 10)</td>
</tr>
<tr>
<td>areaSqm / area_sqm</td>
<td>number</td>
<td>No</td>
<td>body</td>
<td>라이브 필지용 면적 힌트. 상세 화면이 이미 알고 있는 면적. VWorld 재조회 실패 시 폴백</td>
</tr>
<tr>
<td>parcelName / parcel_name</td>
<td>string</td>
<td>No</td>
<td>body</td>
<td>라이브 필지용 이름 힌트</td>
</tr>
	</table>
	<details>
	<summary>**📌 Request Body Example**</summary>
		```json
{
  "scenario_type": "COMPARE_ALL",
  "quantity": 10,
  "area_sqm": 7161,
  "parcel_name": "한강로2가 1 부지"
}
		```
	</details>
	<details>
	<summary>**🔢 Quantity Limits**</summary>
		- PLANT_TREES / SUMOK / TREE: 최대 200
		- CREATE_GARDEN / GARDEN: 최대 150
		- INSTALL_SOLAR / SOLAR: 최대 500
		- **라이브 필지 동작**
			1. DB에서 `parcel_id` 조회
			2. 없으면 `live_get_parcel` (메모리 캐시 → VWorld PNU 단건)
			3. 그래도 없으면 `area_sqm` 힌트로 계산만 수행
			4. 라이브 필지는 `scenarios` 테이블에 **저장하지 않음** (FK `parcels.id` 없음)
			5. DB 부지만 시나리오 행 저장
	</details>
	<details>
	<summary>**✅ Response 200 (COMPARE_ALL)**</summary>
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
	</details>
	<details>
	<summary>**📚 Static Coeff Sources**</summary>
		- USDA i-Tree Eco (나무 심기)
		- 한국에너지공단 14.2% (태양광)
		- 서울연구원 도시농업 보고서 (텃밭)
	</details>
	<details>
	<summary>**✅ Errors**</summary>
		- 400: 잘못된 입력 (수량 초과 등)
		- 404: 부지 없음 (DB·라이브·면적 힌트 모두 실패)
		- 500: 서버 오류
	</details>
</details>
---
<details>
<summary>**`[POST]`** **Compare Parcels**</summary>
	<table header-row="true">
<tr>
<td>Description</td>
<td>2\~3개 부지를 비교합니다. **DB 시드 + 라이브 ****`VW-*`**** 혼합** 가능.</td>
</tr>
<tr>
<td>URL</td>
<td>`/api/gs/compare`</td>
</tr>
<tr>
<td>Auth Required</td>
<td>No</td>
</tr>
<tr>
<td>Parameter</td>
<td>Type</td>
</tr>
<tr>
<td>---</td>
<td>---</td>
</tr>
<tr>
<td>ids</td>
<td>string\[\]</td>
</tr>
	</table>
	<details>
	<summary>**📌 Request Body Example**</summary>
		```json
{
  "ids": ["VW-0103160000", "VW-1117012500100010000"]
}
		```
		- **처리**
			1. DB에서 ID 일괄 조회
			2. 없는 ID는 `live_get_parcel` 로 보강
			3. 면적 기반 나무 시나리오 1회 실행 → `effects.PLANT_TREES` (탄소 랭킹용)
			4. 유효 항목 2개 미만이면 400
	</details>
	<details>
	<summary>**✅ Response 200**</summary>
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
	</details>
	<details>
	<summary>**✅ Errors**</summary>
		- 422: `ids` 길이 2–3 위반
		- 400: 비교할 부지 2개 이상 필요 / 유효한 부지 2개 이상 필요
	</details>
</details>
---
<details>
<summary>**`[POST]`** **Export Report (MD/JSON)**</summary>
	<table header-row="true">
<tr>
<td>Description</td>
<td>부지 분석 리포트를 Markdown 또는 JSON으로 내보냅니다.</td>
</tr>
<tr>
<td>URL</td>
<td>`/api/gs/report`</td>
</tr>
<tr>
<td>Auth Required</td>
<td>No</td>
</tr>
<tr>
<td>Parameter</td>
<td>Type</td>
</tr>
<tr>
<td>---</td>
<td>---</td>
</tr>
<tr>
<td>parcelId</td>
<td>string</td>
</tr>
<tr>
<td>format</td>
<td>string</td>
</tr>
	</table>
	<details>
	<summary>**📌 Request Body Example**</summary>
		```json
{
  "parcelId": "VW-0103160000",
  "format": "markdown"
}
		```
	</details>
	<details>
	<summary>**✅ Response 200**</summary>
		- Markdown: `Content-Type: text/markdown`, 파일명 `greenspot-{id}.md`
		- JSON: `Content-Type: application/json`, 파일명 `greenspot-{id}.json`
	</details>
	<details>
	<summary>**🧾 Markdown Report Structure**</summary>
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
	</details>
</details>
---
<details>
<summary>**`[GET]`** **Export Parcels CSV**</summary>
	<table header-row="true">
<tr>
<td>Description</td>
<td>부지 데이터를 Excel 호환 CSV 파일로 내보냅니다.</td>
</tr>
<tr>
<td>URL</td>
<td>`/api/gs/export`</td>
</tr>
<tr>
<td>Auth Required</td>
<td>No</td>
</tr>
	</table>
	<details>
	<summary>**✅ Response 200**</summary>
		- Content-Type: `text/csv; charset=utf-8`
		- Content-Disposition: `attachment; filename="greenspot-parcels-YYYY-MM-DD.csv"`
		- UTF-8 BOM 포함 (Excel 호환)
	</details>
	<details>
	<summary>**📌 CSV Columns**</summary>
		```javascript
ID, 부지명, 자치구, 행정동, 위도, 경도,
면적(㎡), 부지유형, 소유권, 토양,
일사량(kWh/㎡/일), 일조시간, 열섬강도(℃), 여름지표면온도(℃), PM2.5(μg/m³),
도로접면, 수자원접근, 전력접근,
수목점수, 텃밭점수, 태양광점수, 1순위추천, 불확실성(±)
		```
		(보행·학교·지하철 등 미연동 사회지표 컬럼 없음)
	</details>
	<details>
	<summary>**📌 Example**</summary>
		```bash
curl -O https://your-domain.com/api/gs/export
# 또는 브라우저에서 헤더의 "CSV" 버튼 클릭
		```
	</details>
</details>
---
<details>
<summary>**`[GET]`** **Stats**</summary>
	<table header-row="true">
<tr>
<td>Description</td>
<td>**DB 시드 부지** 기준 자치구별·유형별·추천 분포 통계.</td>
</tr>
<tr>
<td>URL</td>
<td>`/api/gs/stats`</td>
</tr>
<tr>
<td>Auth Required</td>
<td>No</td>
</tr>
	</table>
	<details>
	<summary>**✅ Response 200**</summary>
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
	</details>
	<details>
	<summary>**ℹ️ Notes**</summary>
		- 본 API는 **시드 DB 전역** 집계이며 선택 지역 라이브 통계가 아님.
		- 프론트 통계 화면은 사용자가 고른 지역의 `GET /api/gs/parcels?district=…&live=true` 결과로 **클라이언트 집계**할 수 있다 (다지역 지원).
		- 목록 응답의 `stats` (`live_stats_from_results`) 도 현재 결과 집합 요약에 사용 가능.
	</details>
</details>
---
<details>
<summary>**`[POST]`** **Sign Up (Email/Password)**</summary>
	<table header-row="true">
<tr>
<td>Description</td>
<td>이메일/비밀번호 기반 회원가입. **name 필드 없음.**</td>
</tr>
<tr>
<td>URL</td>
<td>`/api/auth/signup`</td>
</tr>
<tr>
<td>Auth Required</td>
<td>No</td>
</tr>
<tr>
<td>Parameter</td>
<td>Type</td>
</tr>
<tr>
<td>---</td>
<td>---</td>
</tr>
<tr>
<td>email</td>
<td>string</td>
</tr>
<tr>
<td>password</td>
<td>string</td>
</tr>
	</table>
	<details>
	<summary>**📌 Request Body**</summary>
		```json
{ "email": "user@example.com", "password": "secret1" }
		```
	</details>
	<details>
	<summary>**✅ Response 201**</summary>
		```json
{ "ok": true }
		```
	</details>
	<details>
	<summary>**✅ Errors**</summary>
		- **422**: 입력 검증 실패 (Pydantic — 짧은 비밀번호, 잘못된 이메일 등)
		- **409**: 이미 존재하는 이메일
	</details>
</details>
---
<details>
<summary>**`[POST]`** **Login (JWT)**</summary>
	<table header-row="true">
<tr>
<td>Description</td>
<td>이메일/비밀번호로 로그인하고 JWT(Access/Refresh)를 발급합니다.</td>
</tr>
<tr>
<td>URL</td>
<td>`/api/auth/login`</td>
</tr>
<tr>
<td>Auth Required</td>
<td>No</td>
</tr>
	</table>
	<details>
	<summary>**📌 Request Body**</summary>
		```json
{ "email": "user@example.com", "password": "secret1" }
		```
	</details>
	<details>
	<summary>**✅ Response 200**</summary>
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
	</details>
	<details>
	<summary>**ℹ️ Notes**</summary>
		- Access Token은 API 호출 시 `Authorization: Bearer <token>` 헤더로 전달합니다.
		- Refresh: `POST /api/auth/refresh` body `{ "refresh_token": "..." }`
		- Logout: `POST /api/auth/logout` body `{ "refresh_token": "..." }` — **Bearer 불필요**, 해당 refresh 폐기
		- `GET /api/users/me` · `PATCH /api/users/me/preferences` 는 **미제공** (login 응답 `user` + 프론트 localStorage 테마)
	</details>
</details>
<details>
<summary>**`[GET]`** **List Bookmarks**</summary>
	<table header-row="true">
<tr>
<td>Description</td>
<td>현재 로그인한 사용자의 북마크 목록 (스냅샷 필드 포함).</td>
</tr>
<tr>
<td>URL</td>
<td>`/api/bookmarks`</td>
</tr>
<tr>
<td>Auth Required</td>
<td>Yes (`Authorization: Bearer`)</td>
</tr>
	</table>
	<details>
	<summary>**✅ Response 200**</summary>
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
	</details>
</details>
---
<details>
<summary>**`[POST]`** **Add Bookmark**</summary>
	<table header-row="true">
<tr>
<td>Description</td>
<td>부지를 북마크에 추가합니다. **DB 시드 + 라이브 ****`VW-*`** 모두 가능. Parcel FK 없음.</td>
</tr>
<tr>
<td>URL</td>
<td>`/api/bookmarks`</td>
</tr>
<tr>
<td>Auth Required</td>
<td>Yes</td>
</tr>
<tr>
<td>Parameter</td>
<td>Type</td>
</tr>
<tr>
<td>---</td>
<td>---</td>
</tr>
<tr>
<td>parcelId</td>
<td>string</td>
</tr>
<tr>
<td>parcelName</td>
<td>string</td>
</tr>
<tr>
<td>district</td>
<td>string</td>
</tr>
<tr>
<td>topRecommendation</td>
<td>string</td>
</tr>
<tr>
<td>topScore</td>
<td>number</td>
</tr>
	</table>
	- **처리 순서**
		1. DB `parcels` 조회 → 점수 스냅샷
		2. 없으면 body 메타 충분 시 외부 호출 생략 후 저장
		3. 아니면 `live_get_parcel` → 메타 채움
		4. `VW-` ID + body 일부만으로도 저장 허용
		5. 전혀 해석 불가면 404
	<details>
	<summary>**📌 Request Body Example (라이브)**</summary>
		```json
{
  "parcelId": "VW-1117012500100010000",
  "parcelName": "한강로2가 1 부지",
  "district": "용산구",
  "topRecommendation": "SOLAR",
  "topScore": 74
}
		```
	</details>
	<details>
	<summary>**✅ Response 201** — `{ "ok": true }`</summary>
	</details>
	<details>
	<summary>**✅ Errors**</summary>
		- 404: 부지 해석 불가
		- 409: 이미 북마크됨
	</details>
</details>
---
<details>
<summary>**`[DELETE]`** **Remove Bookmark**</summary>
	<table header-row="true">
<tr>
<td>Description</td>
<td>북마크를 삭제합니다.</td>
</tr>
<tr>
<td>URL</td>
<td>`/api/bookmarks?parcelId={id}`</td>
</tr>
<tr>
<td>Auth Required</td>
<td>Yes</td>
</tr>
	</table>
	<details>
	<summary>**✅ Response 200** — `{ "ok": true }`</summary>
	</details>
	<details>
	<summary>**✅ Errors** — 404: Bookmark not found</summary>
	</details>
</details>
---
<details>
<summary>**`[POST]`** **Create Share Link**</summary>
	<table header-row="true">
<tr>
<td>Description</td>
<td>공유용 `shareId` 발급. **DB 부지 또는 ****`VW-*`** (Share 테이블에 Parcel FK 없음). 인증 불필요(공개).</td>
</tr>
<tr>
<td>URL</td>
<td>`/api/share`</td>
</tr>
<tr>
<td>Auth Required</td>
<td>No</td>
</tr>
<tr>
<td>Parameter</td>
<td>Type</td>
</tr>
<tr>
<td>---</td>
<td>---</td>
</tr>
<tr>
<td>parcelId</td>
<td>string</td>
</tr>
	</table>
	- **처리**: DB 있으면 저장. 없으면 `VW-` 형태면 live resolve 시도 후 저장. **resolve 실패해도 ****`VW-*`**** ID 형태면 발급 허용** (현재 구현).
	<details>
	<summary>**✅ Response 200**</summary>
		```json
{
  "shareId": "sh_abc123",
  "url": "https://your-domain.com/?parcel=VW-1117012500100010000&share=sh_abc123"
}
		```
	</details>
	<details>
	<summary>**ℹ️ Notes**</summary>
		- URL 형식: `{PUBLIC_BASE_URL}/?parcel={parcelId}&share={shareId}`  
			(`PUBLIC_BASE_URL` 미설정 시 `/?parcel=...&share=...` 상대 경로)
		- `/greenspot/share/{shareId}` 경로 형식은 **아님**
	</details>
</details>
## 📊 Data Sources (`dataProvenance`)
**라이브 경로**: 필드별로 외부 조회 성공 시 `actual: true`. 키만 있고 실패·쿨다운이면 `false` 이며 `source` 에 `(미연동)`/`(미조회/실패)` 가 붙을 수 있다.
**DB 시드 경로**: `build_data_provenance(data_source=...)` 가 문자열에 `"VWorld"` 포함 여부 등으로 boundary/location/area 플래그를 올린다. 시드 행이 라이브 재조회된 것은 아니다.
<table header-row="true">
<tr>
<td>Field</td>
<td>Source (성공 시)</td>
<td>Data Type</td>
<td>`actual` Rule</td>
</tr>
<tr>
<td>`boundary`</td>
<td>VWorld</td>
<td>연속지적도 (LP_PA_CBND_BUBUN)</td>
<td>라이브: 조회 성공 / 시드: data_source 에 VWorld 표기 시 `true` 가능</td>
</tr>
<tr>
<td>`location`</td>
<td>VWorld</td>
<td>좌표 (EPSG:4326)</td>
<td>동일</td>
</tr>
<tr>
<td>`areaSqm`</td>
<td>VWorld 토지특성 `lndpclAr` 또는 도형 면적</td>
<td>대장면적 / geometry</td>
<td>동일 (대장 우선)</td>
</tr>
<tr>
<td>`regulations`</td>
<td>VWorld WFS + 토지특성 용도지역</td>
<td>규제/용도지역</td>
<td>규제 1건 이상이면 `true`</td>
</tr>
<tr>
<td>`parcelType`</td>
<td>VWorld 토지특성 지목 → UI 유형</td>
<td>지목→UI유형</td>
<td>지목 조회·매핑 성공 시 `true`</td>
</tr>
<tr>
<td>`ownership`</td>
<td>VWorld `getPossessionAttr`</td>
<td>소유구분 PUBLIC/PRIVATE</td>
<td>조회 성공 시 `true`</td>
</tr>
<tr>
<td>`soilType`</td>
<td>흙토람 (농진청) V3 `getSoilCharacter`</td>
<td>PNU 표토토성 (Surtture_Cd). 부가 soilTypeLabel/soilDetail. 라이브=PNU, DB상세=좌표→PNU</td>
<td>조회 성공 시 `true`</td>
</tr>
<tr>
<td>`solarIrradiance`</td>
<td>Visual Crossing climate</td>
<td>일사량 kWh/㎡/day</td>
<td>VC 일사 조회 성공 시만 `true`</td>
</tr>
<tr>
<td>`sunlightHours`</td>
<td>Visual Crossing climate</td>
<td>일조시간</td>
<td>VC sunshine 성공 시만 `true`</td>
</tr>
<tr>
<td>`monthlyIrradiance`</td>
<td>GreenSpot</td>
<td>**연간일사×계절계수 (월별 실측 아님)**</td>
<td>항상 `false`</td>
</tr>
<tr>
<td>`heatIsland`</td>
<td>Visual Crossing (기온 파생)</td>
<td>기온 기반 추정</td>
<td>VC 기온 성공 시 `true`</td>
</tr>
<tr>
<td>`surfaceTempSummer`</td>
<td>Visual Crossing (기온+오프셋)</td>
<td>기온 기반 추정</td>
<td>VC 기온 성공 시 `true`</td>
</tr>
<tr>
<td>`airQuality`</td>
<td>AirKorea</td>
<td>PM2.5</td>
<td>시도 실시간 조회 성공 시 `true`</td>
</tr>
<tr>
<td>`roadAdjacent`</td>
<td>VWorld 토지특성 roadSideCode</td>
<td>접면도로</td>
<td>코드/명칭 있을 때 `true`</td>
</tr>
<tr>
<td>`waterAccess`</td>
<td>GreenSpot</td>
<td>도로인접 기반 추정</td>
<td>기본 `false` (실측 아님)</td>
</tr>
<tr>
<td>`electricityAccess`</td>
<td>GreenSpot</td>
<td>도시지역 기본 가정</td>
<td>기본 `false` (실측 아님)</td>
</tr>
<tr>
<td>`nearbyHouseholds`</td>
<td>KOSIS</td>
<td>자치구 총가구</td>
<td>조회 성공 시 `true`, 미제공 시 `null`+`false`</td>
</tr>
<tr>
<td>`scores`</td>
<td>GreenSpot</td>
<td>알고리즘 (입력 일부 추정 가능)</td>
<td>항상 `true`</td>
</tr>
<tr>
<td>`sumokFeasibility`</td>
<td>GreenSpot</td>
<td>규제 기반 수목 식재 가능성</td>
<td>항상 `true`</td>
</tr>
</table>
부가 플래그: `kmaApiKeyConfigured` (legacy), `visualCrossingConfigured`.
### 외부 API · 환경 변수
<table header-row="true">
<tr>
<td>용도</td>
<td>env</td>
<td>비고</td>
</tr>
<tr>
<td>VWorld 지적/WFS/토지특성/소유</td>
<td>`VWORLD_API_KEY`, `LAND_OWNERSHIP_API_KEY`, `LAND_OWNERSHIP_BASE_URL`</td>
<td>소유: `https://api.vworld.kr/ned/data/getPossessionAttr`</td>
</tr>
<tr>
<td>AirKorea PM2.5</td>
<td>`AIRKOREA_API_KEY`, `AIRKOREA_BASE_URL`</td>
<td>공공데이터 키는 URL-디코딩 후 전송 (이중 인코딩 방지)</td>
</tr>
<tr>
<td>토양</td>
<td>`SOIL_API_KEY`, `SOIL_BASE_URL`</td>
<td>`.../SoilEnviron/SoilCharac/V3/getSoilCharacter?PNU_CD=`</td>
</tr>
<tr>
<td>Visual Crossing</td>
<td>`VISUAL_CROSSING_API_KEY`, `VISUAL_CROSSING_BASE_URL`</td>
<td>climate 1회 호출로 일사+기온 파생. 429 시 쿨다운</td>
</tr>
<tr>
<td>KOSIS</td>
<td>`KOSIS_API_KEY`</td>
<td>서울 25개 자치구 `objL1` 매핑. 연도 작년→재작년 폴백</td>
</tr>
</table>
### 라이브 부지 파이프라인 성능
`build_parcel_from_feature` 는 다음을 수행한다.
1. land / ownership / soil / air / regulations **병렬** 조회  
2. 성공 응답 **TTL 캐시** (PNU·자치구 단위, 실패 응답은 캐시하지 않음)  
3. Visual Crossing climate **1회** + 자치구 캐시, 429 시 재호출 억제  
4. WFS 규제 레이어 **병렬**  
5. 점수: 면적 log 스케일, breakdown 문자열 포함. **하한 18 · 상한 92** 클램프  
`live_search` 는 후보 수집 후 enrich 동시 4개, 읍면동 샘플을 제한한다.
- 면적 기본 필터: `minArea` 기본 350㎡, `maxArea` 기본 15000㎡  
- `topRecommendation`: **정렬 키** (기본 하드 필터 아님, `strictTopRecommendation` 시에만 일치 필터)  
- 성공 필지는 메모리 TTL 캐시에 넣어 상세/시뮬/북마크 재조회를 가속
### 추천 코드 용어
<table header-row="true">
<tr>
<td>용도</td>
<td>API `topRecommendation`</td>
<td>시나리오 별칭</td>
<td>점수 필드</td>
</tr>
<tr>
<td>수목 식재</td>
<td>`TREE` (명세 초안 `SUMOK` 동의어)</td>
<td>`PLANT_TREES`, `TREE`, `SUMOK`</td>
<td>`treeScore` / `sumokScore`</td>
</tr>
<tr>
<td>도시농업</td>
<td>`GARDEN`</td>
<td>`CREATE_GARDEN`, `GARDEN`</td>
<td>`gardenScore`</td>
</tr>
<tr>
<td>태양광</td>
<td>`SOLAR`</td>
<td>`INSTALL_SOLAR`, `SOLAR`</td>
<td>`solarScore`</td>
</tr>
</table>
### parcelType / landCategory
<table header-row="true">
<tr>
<td>지목 예</td>
<td>landCategory</td>
<td>parcelType (UI)</td>
</tr>
<tr>
<td>잡종지</td>
<td>MIXED</td>
<td>UNUSED_LAND</td>
</tr>
<tr>
<td>임야</td>
<td>FOREST</td>
<td>UNUSED_LAND</td>
</tr>
<tr>
<td>대/전</td>
<td>AGRICULTURE</td>
<td>VACANT_LOT</td>
</tr>
<tr>
<td>공장용지</td>
<td>INDUSTRIAL</td>
<td>BROWNFIELD</td>
</tr>
</table>
`parcelType` 허용: `VACANT_LOT` \| `ROOFTOP` \| `UNUSED_LAND` \| `ABANDONED` \| `BROWNFIELD`  
`ownership`: `PUBLIC` \| `PRIVATE` \| `UNKNOWN`  
`soilType`: `LOAM` \| `CLAY` \| `SAND` \| `ROCKY` \| `UNKNOWN`
### sumokFeasibility
- 자연녹지 등 용도지역은 severity `warning` → status **`CONDITIONAL`**
- primary `regulatoryRestriction` 은 URBAN_ZONE 보다 구체 용도지역(ZONING_\*) 우선
- 문구 예: *"자연녹지지역 등으로 수목 식재는 가능하나 행위 제한·인허가 확인이 필요합니다."*
## 📊 Data Model
<details>
<summary>**Parcel (API 응답 / 라이브)**</summary>
	<table header-row="true">
<tr>
<td>필드</td>
<td>타입</td>
<td>설명</td>
<td></td>
</tr>
<tr>
<td>id</td>
<td>string</td>
<td>부지 ID (`VW-{pnu}` 또는 시드 ID)</td>
<td></td>
</tr>
<tr>
<td>name</td>
<td>string</td>
<td>부지명</td>
<td></td>
</tr>
<tr>
<td>district</td>
<td>string</td>
<td>자치구</td>
<td></td>
</tr>
<tr>
<td>neighborhood</td>
<td>string</td>
<td>행정동</td>
<td></td>
</tr>
<tr>
<td>lat, lng</td>
<td>float</td>
<td>위도, 경도 (WGS84)</td>
<td></td>
</tr>
<tr>
<td>areaSqm</td>
<td>float</td>
<td>면적 (㎡). 대장 `lndpclAr` 우선</td>
<td></td>
</tr>
<tr>
<td>parcelType</td>
<td>string</td>
<td>VACANT_LOT/ROOFTOP/UNUSED_LAND/ABANDONED/BROWNFIELD</td>
<td></td>
</tr>
<tr>
<td>landCategory</td>
<td>string\\</td>
<td>null</td>
<td>지목 상세 (MIXED/FOREST/…)</td>
</tr>
<tr>
<td>ownership</td>
<td>string</td>
<td>PUBLIC/PRIVATE/UNKNOWN</td>
<td></td>
</tr>
<tr>
<td>soilType</td>
<td>string</td>
<td>LOAM/CLAY/SAND/ROCKY/UNKNOWN</td>
<td></td>
</tr>
<tr>
<td>solarIrradiance</td>
<td>float</td>
<td>일사량 (kWh/㎡/day)</td>
<td></td>
</tr>
<tr>
<td>monthlyIrradiance</td>
<td>number\[12\]</td>
<td>연간×계절계수 (실측 월별 아님)</td>
<td></td>
</tr>
<tr>
<td>sunlightHours</td>
<td>float</td>
<td>일조시간</td>
<td></td>
</tr>
<tr>
<td>heatIsland</td>
<td>float</td>
<td>열섬강도 (℃, 기온 기반 추정)</td>
<td></td>
</tr>
<tr>
<td>surfaceTempSummer</td>
<td>float</td>
<td>여름 지표면온도 추정 (℃)</td>
<td></td>
</tr>
<tr>
<td>airQuality</td>
<td>float</td>
<td>PM2.5 (μg/m³)</td>
<td></td>
</tr>
<tr>
<td>nearbyHouseholds 등</td>
<td>number\\</td>
<td>null</td>
<td>미연동 시 `null` (가짜 0 금지)</td>
</tr>
<tr>
<td>roadAdjacent</td>
<td>bool</td>
<td>접면도로 (토지특성)</td>
<td></td>
</tr>
<tr>
<td>waterAccess</td>
<td>bool</td>
<td>추정 (도로인접 기반)</td>
<td></td>
</tr>
<tr>
<td>electricityAccess</td>
<td>bool</td>
<td>추정 (도시 기본 가정)</td>
<td></td>
</tr>
<tr>
<td>regulations</td>
<td>array</td>
<td>WFS + 용도지역 객체 배열</td>
<td></td>
</tr>
<tr>
<td>sumokFeasibility</td>
<td>object</td>
<td>status/score/reason/…</td>
<td></td>
</tr>
<tr>
<td>confidence</td>
<td>float</td>
<td>실데이터 필드 수 기반 (약 0.58\~0.97)</td>
<td></td>
</tr>
<tr>
<td>dataProvenance</td>
<td>object</td>
<td>필드별 출처·actual</td>
<td></td>
</tr>
<tr>
<td>pnu</td>
<td>string</td>
<td>19자리 필지 고유번호</td>
<td></td>
</tr>
	</table>
</details>
<details>
<summary>**ParcelScore (응답 scores)**</summary>
	<table header-row="true">
<tr>
<td>필드</td>
<td>타입</td>
<td>설명</td>
</tr>
<tr>
<td>treeScore / gardenScore / solarScore</td>
<td>float</td>
<td>라이브 산출 시 대략 **18–92** 클램프(상한 92), 규제 반영 후</td>
</tr>
<tr>
<td>topRecommendation</td>
<td>string</td>
<td>TREE/GARDEN/SOLAR</td>
</tr>
<tr>
<td>uncertainty</td>
<td>float</td>
<td>실데이터 부족 시 증가</td>
</tr>
<tr>
<td>treeBreakdown 등</td>
<td>string\[\]</td>
<td>점수 근거 문장</td>
</tr>
	</table>
</details>
<details>
<summary>**Scenario**</summary>
	<table header-row="true">
<tr>
<td>필드</td>
<td>타입</td>
<td>설명</td>
</tr>
<tr>
<td>parcelId</td>
<td>string</td>
<td>부지 ID (FK, **DB 부지만** 저장)</td>
</tr>
<tr>
<td>scenarioType</td>
<td>string</td>
<td>PLANT_TREES/CREATE_GARDEN/INSTALL_SOLAR</td>
</tr>
<tr>
<td>quantity</td>
<td>int</td>
<td>수량</td>
</tr>
<tr>
<td>effects</td>
<td>JSON</td>
<td>효과 데이터</td>
</tr>
	</table>
</details>
<details>
<summary>**AgentQuery**</summary>
	<table header-row="true">
<tr>
<td>필드</td>
<td>타입</td>
<td>설명</td>
</tr>
<tr>
<td>query</td>
<td>string</td>
<td>사용자 질문</td>
</tr>
<tr>
<td>criteria</td>
<td>string</td>
<td>JSON (검색 조건)</td>
</tr>
<tr>
<td>resultCount</td>
<td>int</td>
<td>결과 수</td>
</tr>
<tr>
<td>summary</td>
<td>string</td>
<td>AI 요약</td>
</tr>
<tr>
<td>source</td>
<td>string</td>
<td>ai/fallback</td>
</tr>
	</table>
</details>
---
## 🛡️ Error Handling
- **Standard Error Response** (FastAPI 네이티브)
	```json
{
  "detail": "에러 메시지 또는 검증 오류 배열"
}
	```
	HTTPException 핸들러도 `{ "detail": "..." }` 만 반환한다. `{ "error", "detail" }` envelope 는 쓰지 않는다.
- **Status Codes**
	<table header-row="true">
<tr>
<td>코드</td>
<td>의미</td>
<td>발생 상황</td>
</tr>
<tr>
<td>200</td>
<td>OK</td>
<td>정상 응답 (헬스 degraded 포함)</td>
</tr>
<tr>
<td>201</td>
<td>Created</td>
<td>회원가입·북마크 생성</td>
</tr>
<tr>
<td>400</td>
<td>Bad Request</td>
<td>비즈니스 규칙 위반 (수량 초과 등)</td>
</tr>
<tr>
<td>401/403</td>
<td>Unauthorized</td>
<td>인증 필요 엔드포인트 토큰 없음/무효</td>
</tr>
<tr>
<td>404</td>
<td>Not Found</td>
<td>부지 ID 없음</td>
</tr>
<tr>
<td>409</td>
<td>Conflict</td>
<td>중복 이메일·북마크</td>
</tr>
<tr>
<td>422</td>
<td>Unprocessable Entity</td>
<td>Pydantic 입력 검증 실패</td>
</tr>
<tr>
<td>500</td>
<td>Internal Server Error</td>
<td>서버 오류</td>
</tr>
	</table>
---
## 📈 Performance
<table header-row="true">
<tr>
<td>엔드포인트</td>
<td>평균 응답 시간</td>
<td>비고</td>
</tr>
<tr>
<td>GET /api/gs/health</td>
<td>\~4ms</td>
<td>DB count 쿼리</td>
</tr>
<tr>
<td>GET /api/gs/parcels</td>
<td>\~50ms</td>
<td>DB 시드 목록</td>
</tr>
<tr>
<td>GET /api/gs/parcels/\{id\} (DB)</td>
<td>\~30ms</td>
<td>단일 부지</td>
</tr>
<tr>
<td>GET /api/gs/parcels/\{id\} (라이브 첫 조회)</td>
<td>\~2–5초</td>
<td>외부 API 병렬 + WFS. 캐시 재조회 \~0.5초</td>
</tr>
<tr>
<td>POST /api/gs/agent (라이브)</td>
<td>수 초\~</td>
<td>VWorld 검색 + enrich 병렬</td>
</tr>
<tr>
<td>POST /api/gs/parcels/\{id\}/explain</td>
<td>\~5-10초</td>
<td>AI 호출 1회</td>
</tr>
<tr>
<td>POST /api/gs/parcels/\{id\}/simulate</td>
<td>\~수 ms–수 초</td>
<td>DB면 즉시. 라이브면 resolve/캐시 후 계산. 면적 힌트 시 외부 재조회 최소화</td>
</tr>
<tr>
<td>POST /api/gs/compare</td>
<td>\~10ms+</td>
<td>부지수에 비례</td>
</tr>
<tr>
<td>POST /api/gs/report</td>
<td>\~5ms+</td>
<td>Markdown 생성</td>
</tr>
<tr>
<td>GET /api/gs/export</td>
<td>\~100ms+</td>
<td>CSV</td>
</tr>
<tr>
<td>GET /api/gs/stats</td>
<td>\~200ms</td>
<td>통계 집계</td>
</tr>

</table>
### 캐시 TTL (프로세스 메모리)
<table header-row="true">
<tr>
<td>키 패턴</td>
<td>TTL</td>
<td>조건</td>
</tr>
<tr>
<td>`vworld:land:{pnu}`</td>
<td>30분</td>
<td>dataAvailable</td>
</tr>
<tr>
<td>`own:{pnu}` / `soil:{pnu}`</td>
<td>30분</td>
<td>dataAvailable</td>
</tr>
<tr>
<td>`air:{district}`</td>
<td>10분</td>
<td>dataAvailable</td>
</tr>
<tr>
<td>`regs:{lat4}:{lng4}`</td>
<td>15분</td>
<td>규제 1건 이상</td>
</tr>
<tr>
<td>`kosis:hh:{district}`</td>
<td>1일</td>
<td>dataAvailable</td>
</tr>
<tr>
<td>`vc:climate:{district}`</td>
<td>1시간</td>
<td>climate 응답</td>
</tr>
<tr>
<td>VC 429 쿨다운</td>
<td>30분</td>
<td>전역 재호출 억제</td>
</tr>
</table>