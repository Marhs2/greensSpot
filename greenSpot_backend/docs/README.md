# GreenSpot Backend 문서

최종 갱신: **2026-07-09**

구현 코드(`app/`)를 기준으로 한 백엔드 문서 모음입니다.  
기능 초안과 경로가 다를 수 있으므로, **실제 라우트는 `api.md`를 우선**합니다.

---

## 문서 목록

| 문서 | 설명 |
| --- | --- |
| [api.md](./api.md) | REST API 엔드포인트, 요청/응답, dataProvenance, 라이브 파이프라인 |
| [기능명세서.md](./기능명세서.md) | 기능 요구사항(F-01~F-28), 수용 기준, 데이터 소스 |
| [sql.md](./sql.md) | 논리 스키마(MySQL 스타일 DDL) + SQLite 구현 차이 메모 |
| [TEST_CASES.md](./TEST_CASES.md) | **수동 테스트 케이스** (TC ID · 내용/조건 · 절차 · 결과 · 체크) |
| [HALLUCINATION_TEST_CASES.md](./HALLUCINATION_TEST_CASES.md) | 문서↔구현 불일치·환각 탐지용 상세 TC |
| [BROWSER_TEST_RESULTS.md](./BROWSER_TEST_RESULTS.md) | 브라우저 실측 감사 결과 (참고) |

상위: [../README.md](../README.md) — 설치, 환경 변수, 실행

---

## API Prefix (구현 기준)

| Prefix | 라우터 | 용도 |
| --- | --- | --- |
| `/api/gs` | `gs_router` | 부지, 에이전트, 시뮬레이션, 통계, 리포트 |
| `/api` | `auth_router` | 인증, 북마크, 공유 (`/auth/*`, `/bookmarks`, `/share`) |
| `/api/v1/gs` | `integration_router` | KOSIS, VWorld 토지정보, Visual Crossing, 규제 동기화 |

Swagger: `http://localhost:8000/docs`

---

## 핵심 개념 요약

### 라이브 부지 (`VW-{pnu}`)

- VWorld 실시간 검색/상세로 만든 필지. ID 형식: `VW-` + 19자리 PNU.
- DB `parcels` 테이블에 없을 수 있음.
- **지원**: 상세, 시뮬레이션, 비교, 북마크, 공유(스냅샷).
- **미저장**: 시뮬레이션 결과(`scenarios` FK), 선택적 규제/KOSIS 스냅샷 테이블.

### `topRecommendation` 정렬 정책 (Agent / live_search)

- 자연어 용도 키워드(`수목`→TREE, `텃밭`→GARDEN, `태양광`→SOLAR)는 **정렬 우선 키**이다.
- **기본은 하드 필터가 아님**: 1위 추천이 달라도 해당 용도 점수가 높으면 결과에 포함.
- 엄격 필터가 필요하면 `strictTopRecommendation: true` (내부 criteria; 기본 false).
- 예: `"금천구 수목"` → 후보를 `treeScore` 내림차순 정렬. 1위가 SOLAR여도 수목 점수가 있으면 반환.

### dataProvenance

- 필드별 `actual: true`는 **외부 API 조회 성공 시에만**.
- 키만 있고 실패/쿨다운이면 `actual: false`.
- 사회지표 미연동 필드는 가짜 `0` 대신 `null` 권장.

### 통계

- `GET /api/gs/stats`: **DB 시드 부지** 집계.
- 프론트 통계 화면: 선택 지역의 **라이브 목록(`useParcels`)** 으로 클라이언트 집계 가능 (다지역).

### 북마크 / Share (SQLite 구현)

- `bookmarks.parcel_id` / `shares.parcel_id`에 **Parcel FK 없음** → `VW-*` 스냅샷 저장 가능.
- 북마크 POST body 선택 필드: `parcelName`, `district`, `topRecommendation`, `topScore`.

---

## 변경 이력 (문서)

| 날짜 | 내용 |
| --- | --- |
| 2026-07-09 | 실제 공공 API 연동, dataProvenance, 라이브 시뮬/북마크/비교, agent 소프트 정렬, KOSIS 25구, Bookmark FK 정합 |
| 2026-07-06 | 수목 식재 용어 통일, 기능명세 초안 정리 |
