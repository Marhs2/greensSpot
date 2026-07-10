# GreenSpot 브라우저 실측 결과 — 문서↔구현 불일치 감사

| 항목 | 내용 |
| --- | --- |
| 실행일 | 2026-07-09 |
| 방법 | Chrome DevTools MCP → `http://localhost:8000/docs` 페이지에서 `fetch` 일괄 호출 |
| 서버 | `localhost:8000` |
| 환경 (health) | VWorld ✅ · KMA ✅ · KOSIS ✅ · Visual Crossing ✅ |
| DB | parcels=63, scores=63 |
| 기준 TC | [HALLUCINATION_TEST_CASES.md](./HALLUCINATION_TEST_CASES.md) |
| 스크린샷 | [browser_test_swagger.png](./browser_test_swagger.png) |

### 판정 요약

| 판정 | 건수 (핵심 TC 합산) | 의미 |
| --- | --- | --- |
| **MATCH** | ~51 | 문서/정책과 일치 |
| **DRIFT** | **10+** | 문서 ≠ 구현 |
| **HALLUC** | **2~3** | 출처·실측 주장 모순 |
| **N/A / 주의** | 수건 | 외부 API 빈 응답 등 |

> 아래 **확정 이슈**만 우선 수정 대상으로 보면 됩니다. MATCH 상세는 부록.

---

## 1. 확정 DRIFT / HALLUC (우선순위순)

### 🔴 H-01 · TC-E-002 · P0 · **데이터 환각**

| 항목 | 내용 |
| --- | --- |
| Claim | `actual:true` 는 외부 API 조회 성공 시에만 (F-27) |
| 관측 | DB 시드 상세 `source=database` 인데 |
| | `dataProvenance.boundary.actual=true` |
| | `location.actual=true` |
| | `areaSqm.actual=true` |
| | 출처 문자열 `"VWorld"` |
| 샘플 | `GET /api/gs/parcels/JG-001` |
| 원인 추정 | `DEFAULT_DB_DATA_SOURCE` 에 `"VWorld"` 포함 → `is_vworld=true` |
| 권고 | **코드 수정**: 시드 경로는 actual=false 또는 dataType에 “시드/캐시” 명시 |

---

### 🔴 H-02 · TC-E-009 · P0 · **출처 환각 (Explain)**

| 항목 | 내용 |
| --- | --- |
| Claim | 실제 사용 파이프라인 출처만 정직하게 |
| 관측 | explain 출처는 Visual Crossing 등 실연동과 일치해야 함 (과거 레거시 문구 수정됨) |
| | 구현 열섬/일사는 Visual Crossing |
| 스니펫 | `데이터 출처: USDA i-Tree, 기상청, KOSIS, Landsat, 서울연구원` |
| 권고 | **코드 수정**: fallback/system prompt 출처를 VC·VWorld·AirKorea 등으로 정합 |

---

### 🔴 D-01 · TC-B-002 · P0 · **상세 필드 누락 (목록과 비대칭)**

| 항목 | 내용 |
| --- | --- |
| Claim (F-02) | 상세에 `regulations`, `sumokFeasibility` 포함 |
| 관측 | **목록** `GET /parcels?live=false`: `regulations` ✅ `sumokFeasibility` ✅ |
| | **상세** `GET /parcels/JG-001` parcel: **둘 다 없음** (`hasRegs=false`, `hasSumok=false`) |
| | `dataProvenance` 만 있음 |
| 목록 대비 상세 누락 | `regulations`, `sumokFeasibility` (+ 목록의 nested `scores` 는 상세 루트 `scores` 로 분리) |
| 권고 | **코드 수정**: `get_parcel_detail` 을 목록 serializer 와 필드 정합 |

---

### 🔴 D-02 · TC-F-001 · P0 · **점수 범위 위반**

| 항목 | 내용 |
| --- | --- |
| Claim | 각 점수 0~100 |
| 관측 | **20건** `solarScore=110` (예: JR-002, YS-002, GJ-002, … 대부분 `*-002` ROOFTOP 계열) |
| 권고 | **코드/시드 수정**: clamp 0~100 또는 시드 재계산 |

---

### 🟠 D-03 · TC-B-005 · P0 · **문서 자기모순 + 예시 오류**

| 항목 | 내용 |
| --- | --- |
| api.md 예시 | `"regulations": "NONE"` **문자열** |
| 기능명세 | regulations **배열** |
| 구현 | **배열** (`type=array`) |
| 판정 | 구현↔명세 **MATCH** / 구현↔api 예시 **DRIFT** |
| 권고 | **문서 수정**: api.md 예시를 배열로 통일 |

---

### 🟠 D-04 · TC-B-003 · P1 · **sumokScore 미반환**

| 항목 | 내용 |
| --- | --- |
| Claim | sumokScore / treeScore 병행 (명세) |
| 관측 | scores 키: `treeScore, gardenScore, solarScore, topRecommendation, uncertainty, *Breakdown` only |
| 권고 | 문서에서 “API는 treeScore만”으로 확정 **또는** 응답에 sumokScore 별칭 추가 |

---

### 🟠 D-05 · TC-B-006 · P1 · **DB breakdown 항상 빈 배열**

| 항목 | 내용 |
| --- | --- |
| Claim | breakdown 문자열 제공 |
| 관측 | DB 상세 `treeBreakdown=[]` |
| | 라이브 상세 `treeBreakdown` 4개 (예: 열섬 기여, 면적 log기여) |
| 권고 | DB 경로도 저장/재계산하거나 문서에 “라이브 only” 명시 |

---

### 🟠 D-06 · TC-B-008 · P1 · **compare 상한 3 (문서 미기재)**

| 항목 | 내용 |
| --- | --- |
| Claim | 2개 이상 (상한 없음처럼 기술) |
| 관측 | ids 4개 → **422** `List should have at most 3 items` |
| 권고 | **문서**에 max 3 명시 또는 스키마 완화 |

---

### 🟠 D-07 · TC-B-010 · P2 · **promptVersion 불일치**

| 항목 | 내용 |
| --- | --- |
| api.md 예 | `v3-greenspot2` |
| 관측 | `v3-greenspot3` |
| 권고 | 문서 예시 갱신 |

---

### 🟠 D-08 · TC-E-005-db · P1 · **미연동 지표 0 위장 (DB)**

| 항목 | 내용 |
| --- | --- |
| Claim (F-27 라이브) | 미연동 사회지표 null, 가짜 0 금지 |
| 관측 DB | `nearbySchools=2`, `hospitals=1`, `parks=0`, `subway=2`, `pedestrianFlow=5200` |
| 관측 라이브 | 전부 `null` ✅ (TC-E-005-live MATCH) |
| 권고 | DB 시드가 추정치면 provenance에 actual:false + 문서에 “시드는 샘플 수치” 명시 |

---

### 🟡 D-09 · TC-J / 외부키 “설정됨” vs 빈 데이터

| 항목 | 내용 |
| --- | --- |
| health | `kosisApiKeyConfigured=true`, `visualCrossingApiKeyConfigured=true` |
| KOSIS | 금천/강남 모두 `dataAvailable:false`, population/households `null` (200) |
| VC heat | `dataAvailable:false`, 전 필드 null |
| VC climate | 간헐적: 성공 시 irradiance 있음 → 재호출 시 `dataAvailable:false` + **0** |
| 판정 | 키 플래그 true ≠ 데이터 확보. climate **0 + dataAvailable false** 는 정직. |
| | 다만 **0이 실측처럼 보일 위험** → UI는 dataAvailable 필수 확인 |
| 권고 | 감사 시 “키 있음=연동 성공”으로 문서/헬스 해석하지 말 것. KOSIS 빈 응답 원인 별도 조사 |

---

## 2. 통과(MATCH) — 핵심 경로

| TC | 결과 | 증거 요약 |
| --- | --- | --- |
| TC-A-002 Visual Crossing heat | MATCH | VC 경로 존재 |
| TC-A-003 admin 없음 | MATCH | 404 |
| TC-A-005 `/api/v1/gs/parcels` 없음 | MATCH | 404 |
| TC-B-001 목록 키 | MATCH | parcels/stats/source, n=63 |
| TC-B-007 시드 ID 형식 | MATCH | `JG-001`, `SD-001` 등 `XX-###` (문서 예 DD-001 과 패턴 동형) |
| TC-D-001 라이브 목록 | MATCH | `source=vworld_live`, id `VW-1154510100104480000` |
| TC-D-002/cache | MATCH | 상세 `vworld_live` → 재조회 `vworld_live_cache` |
| TC-D-004 라이브 시뮬 | MATCH | COMPARE_ALL 3키 200 |
| TC-D-005 혼합 비교 | MATCH | seed+VW 2건 |
| TC-D-006 VW 북마크 | MATCH | 201, 목록 포함 |
| TC-D-007 VW 공유 | MATCH | shareId+url |
| TC-D-008 explain/report 라이브 | MATCH | 200 |
| TC-E-003 monthly actual false | MATCH | DB·라이브 |
| TC-E-004 water/elec estimated | MATCH | actual false |
| TC-E-005-live null | MATCH | schools 등 null |
| TC-G-001 소프트 정렬 | MATCH | 금천구 수목 TREE, treeScore 84→42 정렬, summary 정렬 힌트 |
| TC-G-002 텃밭 매핑 | MATCH | 용산구 텃밭 → GARDEN, count=8 |
| TC-G-003 지역 없음 | MATCH | count=0, 지역 안내 |
| TC-G-007 history | MATCH | 금천구 수목 기록 |
| TC-I-* 시뮬/비교 | MATCH | 별칭·상한·ranking |
| TC-C-001 권한 | MATCH | me/bookmarks 403 without token |
| TC-M-001 CSV | MATCH | 수목점수 있음, 학교 컬럼 없음 |
| TC-J-001-bad 해운대 | MATCH | 400 서울 25구 |

---

## 3. 라이브 샘플 (참고)

| 필드 | 값 |
| --- | --- |
| LIVE_ID | `VW-1154510100104480000` |
| SEED_ID | `JG-001` (중구 을지로 인쇄골목 빈터) |
| 라이브 목록 | 금천구 `limit=5` → 실제 2건 |
| sumokFeasibility | AVAILABLE |
| agent 금천구 수목 | count=2, topRec=TREE, trees=84,42 |

---

## 4. 수정 권고 백로그 (감사 산출물)

| 우선 | ID | 조치 | 담당 후보 |
| --- | --- | --- | --- |
| P0 | H-01 | 시드 provenance actual 로직 수정 | `build_data_provenance` / parcel_service |
| P0 | H-02 | explain 출처 문자열 정합 | explain_service fallback |
| P0 | D-01 | 상세에 regulations·sumokFeasibility | get_parcel_detail |
| P0 | D-02 | solarScore 110 clamp / 시드 수정 | seed + score compute |
| P1 | D-03 | api.md regulations 예시 배열화 | docs |
| P1 | D-04 | sumokScore 문서 또는 별칭 | docs or API |
| P1 | D-05 | DB breakdown 정책 | code or docs |
| P1 | D-06 | compare max=3 문서화 | api.md |
| P1 | D-08 | DB 사회지표 샘플 고지 | docs |
| P2 | D-07 | promptVersion 문서 | api.md |
| 조사 | D-09 | KOSIS/VC heat 빈 응답 | 키·쿼리·쿨다운 |

---

## 5. 실행 로그 메타

- Phase 1 (스키마·DB·explain·시뮬): MATCH 20 / DRIFT 8 / HALLUC 2  
- Phase 2 (라이브·agent·auth·연동): MATCH 31 / DRIFT 1 / HALLUC 0 / N/A 1  
- 브라우저 컨텍스트: Swagger UI origin에서 CORS 없이 same-origin fetch  

### 재현 (브라우저 콘솔)

```javascript
// Swagger http://localhost:8000/docs 열린 상태에서
const r = await fetch('/api/gs/parcels/JG-001').then(x => x.json());
console.log(r.parcel.regulations, r.parcel.sumokFeasibility, r.parcel.dataProvenance.boundary);
```

---

## 6. 결론

문서·구현 감사 관점에서 **가장 위험한 확정 이슈 4건**:

1. **시드 상세가 VWorld 실측처럼 provenance 표기** (HALLUC)  
2. **Explain 출처가 실연동(Visual Crossing 등)과 일치해야 함** (HALLUC)  
3. **상세 API가 목록에 있는 규제·수목가능성 필드를 빠뜨림** (DRIFT / F-02 위반)  
4. **solarScore=110 이 다수 존재** (DRIFT / 0~100 위반)

라이브 경로(목록·캐시·시뮬·비교·북마크·소프트 정렬·null 사회지표)는 대체로 문서와 **일치**했습니다.
