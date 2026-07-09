# GreenSpot 기능명세서 수정본 - 수목 식재 기준

작성일: 2026-07-06

수정 기준: 전체 용어를 **수목 식재**, `sumokScore`, `sumokFeasibility`, `SUMOK` 중심으로 통일

---

## 1. 서비스 개요

본 서비스는 공공/민간 부지 데이터를 기반으로 특정 부지가 아래 3가지 활용 목적에 얼마나 적합한지 평가하고, AI 검색/설명/시뮬레이션/리포트 기능을 제공하는 부지 의사결정 지원 플랫폼이다.

- **수목 식재 적합도**
- **도시농업/커뮤니티 가든 적합도**
- **태양광 발전 적합도**

> 용어 주의: 본 문서의 “수목 식재”는 나무를 심는 활용 가능성을 의미한다. “식수/음용수/지하수” 기능은 본 범위에서 제외한다.
> 

---

## 2. 사용자 유형

| 사용자 | 설명 | 주요 권한 |
| --- | --- | --- |
| 비회원 | 로그인하지 않은 방문자 | 부지 목록/상세/검색 일부 조회, 공유 링크 조회 |
| 회원 | 이메일/비밀번호로 가입한 사용자 | 북마크, 검색 히스토리, 리포트, 공유 링크, 환경설정 |
| 시스템 | 배치/AI/스케줄러 | 점수 계산, VWorld 규제 데이터 동기화, 트렌딩 집계, 리포트 생성 |

---

## 3. 공통 정책

### 3.1 인증/인가

- 인증 방식: Access Token + Refresh Token 기반 JWT
- Access Token은 `Authorization: Bearer {token}` 헤더로 전달
- 비회원 허용 API와 회원 전용 API를 명확히 분리

### 3.2 공통 응답 형식

```json
{
  "success": true,
  "data": {},
  "meta": {},
  "error": null
}
```

에러 응답:

```json
{
  "success": false,
  "data": null,
  "meta": {},
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "요청 값이 올바르지 않습니다.",
    "details": [
      { "field": "email", "reason": "이메일 형식이 아닙니다." }
    ]
  }
}
```

### 3.3 페이지네이션

- 기본: `page=1`, `size=20`
- 최대 `size=100`
- 응답 `meta.pagination` 포함

### 3.4 API Prefix

모든 API는 아래 prefix로 통일한다.

```
/api/v1/gs
```

예:

- `GET /api/v1/gs/parcels`
- `GET /api/v1/gs/parcels/{parcelId}`
- `POST /api/v1/gs/agent/search`

---

## 4. 기능 목록

### 4.1 메인 기능

| ID | 기능명 | 우선순위 | 권한 | 관련 API |
| --- | --- | --- | --- | --- |
| F-01 | 부지 목록 조회/대시보드 | High | 비회원 가능 | `GET /api/v1/gs/parcels` |
| F-02 | 부지 상세 정보 조회 | High | 비회원 가능 | `GET /api/v1/gs/parcels/{parcelId}` |
| F-03 | 3중 용도 점수 산출 | High | 비회원 가능 | 라이브 검색·상세 시 즉시 산출 |
| F-04 | AI 자연어 부지 검색 에이전트 | High | 비회원/회원 | `POST /api/v1/gs/agent/search` |
| F-05 | AI 점수 설명 생성 | High | 비회원 가능 | `GET /api/v1/gs/parcels/{parcelId}/explanation` |
| F-06 | 시나리오 시뮬레이션 | High | 회원 권장 | `POST /api/v1/gs/parcels/{parcelId}/scenarios` |
| F-07 | 부지 비교 모드 | Medium | 비회원 가능 | `POST /api/v1/gs/parcels/compare` |
| F-08 | 리포트 내보내기 | Medium | 회원 | `POST /api/v1/gs/exports/reports` |

### 4.2 인증/사용자 기능

| ID | 기능명 | 우선순위 | 권한 | 관련 API |
| --- | --- | --- | --- | --- |
| F-09 | 회원가입 | High | 비회원 | `POST /api/v1/gs/auth/signup` |
| F-10 | 로그인/로그아웃 | High | 비회원/회원 | `POST /api/v1/gs/auth/login`, `POST /api/v1/gs/auth/logout` |
| F-11 | 사용자별 북마크 | High | 회원 | `GET/POST/DELETE /api/v1/gs/bookmarks` |
| F-19 | 토큰 갱신/세션 관리 | High | 회원 | `POST /api/v1/gs/auth/refresh` |
| F-20 | 내 정보/환경설정 | Medium | 회원 | `GET /api/v1/gs/users/me`, `PUT /api/v1/gs/users/me/preferences` |

### 4.3 추가/운영 기능

| ID | 기능명 | 우선순위 | 권한 | 관련 API |
| --- | --- | --- | --- | --- |
| F-12 | 통계 분석 대시보드 | Medium | 비회원 가능 | `GET /api/v1/gs/stats/overview` |
| F-13 | CSV 내보내기 | Medium | 회원 | `GET /api/v1/gs/exports/parcels.csv` |
| F-14 | 부지 공유 링크 | Medium | 회원/비회원 조회 | `POST /api/v1/gs/share-links`, `GET /api/v1/gs/share-links/{token}` |
| F-15 | 다크모드 토글 | Low | 비회원 로컬/회원 저장 | `PUT /api/v1/gs/users/me/preferences` |
| F-16 | 검색 히스토리 조회 | Medium | 회원 | `GET /api/v1/gs/agent/queries` |
| F-17 | 인기 검색어/트렌딩 | Medium | 비회원 가능 | `GET /api/v1/gs/agent/trending` |
| F-18 | 헬스 체크 API | High | 전체 | `GET /api/v1/gs/health` |

---

# 5. 상세 기능 요구사항

## F-01. 부지 목록 조회/대시보드

**목적**: 사용자가 조건에 맞는 부지를 빠르게 탐색한다.

### 입력 조건

- 검색어: 부지명, 행정구, 동네, 주소 일부
- 필터:
    - 행정구
    - 부지 유형
    - 소유 구분
    - 면적 범위
    - 규제 코드
    - 규제 심각도
    - 개발 제한 규제 제외 여부
    - `sumokFeasibility.status`
    - 최소 `sumokScore`
    - 최소 종합 점수
- 정렬:
    - 종합 추천
    - 수목 점수
    - 태양광 점수
    - 정원/도시농업 점수
    - 면적
    - 최신순

### 수용 기준

- 목록은 페이지네이션되어야 한다.
- 각 항목은 아래 필드를 포함한다.
    - `id`
    - `name`
    - `district`
    - `areaSqm`
    - `regulations`
    - `sumokFeasibility`
    - `topRecommendation`
    - `topScore`
    - `uncertainty`
    - `isBookmarked`
- `regulations`는 문자열이 아니라 배열이다.
- `regulations` 배열의 각 항목은 최소 `code`, `name`, `severity`, `affectedUses`, `penaltyType`을 포함한다.
- `sumokFeasibility`는 최소 `status`, `score`, `reason`을 포함한다.
- 그린벨트, 도시자연공원구역, 자연환경보전지역, 보호지구 등 강한 제한 규제는 목록에서 바로 식별 가능해야 한다.
- 회원인 경우 북마크 여부가 표시된다.
- 필터/정렬 조합이 잘못된 경우 400 에러를 반환한다.

---

## F-02. 부지 상세 정보 조회

**목적**: 특정 부지의 원천 데이터, 주변 인프라, 규제, 점수, 시뮬레이션 진입 정보를 확인한다.

### 수용 기준

- 부지 기본 정보, `regulations` 배열, `sumokFeasibility` 객체, 최신 점수 정보를 함께 반환한다.
- 상세 화면에서 아래 정보를 확인할 수 있어야 한다.
    - 규제명
    - 규제 코드
    - 심각도
    - 적용 용도
    - 페널티/0점 처리 사유
    - 수목 식재 가능 상태
    - 수목 식재 제한 사유
    - 인허가 확인 필요 여부
- 점수 데이터가 없으면 `score=null`로 반환하고 에러 처리하지 않는다.
- 삭제/비공개 부지는 404로 처리한다.

---

## F-03. 3중 용도 점수 산출

**목적**: 동일 부지를 아래 3가지 관점에서 점수화한다.

1. 수목 식재 가능성
2. 도시농업/커뮤니티 가든 활용 가능성
3. 태양광 발전 활용 가능성

또한 그린벨트, 도시자연공원구역, 자연환경보전지역, 보호지구 등 VWorld 기반 규제 조건을 최우선으로 반영한다.

### 점수 범위

- 각 점수는 0~100
- 불확실성은 0~1이며, 1에 가까울수록 데이터 신뢰도가 낮다.
- 규제에 의해 특정 용도가 불가한 경우 해당 용도 점수는 0점 또는 강한 페널티 후 하한값으로 보정한다.

### 점수 필드

| 용도 | 필드 | 추천 코드 |
| --- | --- | --- |
| 수목 식재 | `sumokScore` | `SUMOK` |
| 도시농업/커뮤니티 가든 | `gardenScore` | `GARDEN` |
| 태양광 발전 | `solarScore` | `SOLAR` |
| 복합 활용 | - | `MIXED` |
| 제한/추천 불가 | - | `RESTRICTED` |

### `sumokFeasibility` 객체 정의

수목 식재 가능 여부는 단순 점수만으로 표현하지 않고 아래 구조로 함께 반환한다.

```json
{
  "status": "CONDITIONAL",
  "score": 72.5,
  "reason": "도시자연공원구역으로 인허가 확인이 필요하지만 수목 식재 가능성은 있음",
  "blockingRegulations": [],
  "warningRegulations": ["URBAN_NATURE_PARK"],
  "requiredChecks": ["지자체 인허가 확인", "공원녹지계획 확인"],
  "confidence": 0.82
}
```

`status` 값:

| status | 의미 |
| --- | --- |
| `AVAILABLE` | 명확한 제한이 없고 수목 식재 적합도가 높음 |
| `CONDITIONAL` | 가능성은 있으나 인허가/현장 확인 필요 |
| `RESTRICTED` | 강한 제한이 있어 추천 점수 낮음 |
| `PROHIBITED` | 규제상 사실상 불가 또는 0점 처리 |
| `UNKNOWN` | 데이터 부족으로 판단 불가 |

### 규제 데이터 모델 요구사항

- 부지는 0개 이상의 `regulations`를 가진다.
- 각 규제는 아래 필드를 가진다.
    - `code`
    - `name`
    - `severity`
    - `affectedUses`
    - `penaltyType`
    - `penaltyValue`
    - `legalBasis`
    - `description`
    - `sourceLayer`
    - `typename`
- `severity`: `info`, `warning`, `restricted`, `prohibited`
- `affectedUses`: `sumok`, `garden`, `solar`, `all` 중 하나 이상
- `penaltyType`: `none`, `subtract`, `multiplier`, `zero`
- 점수 계산 결과에는 반드시 계산 당시의 `regulationsSnapshot`을 저장한다.

### 주요 VWorld WFS 레이어

수목 식재 관점에서 우선 사용해야 하는 VWorld 레이어는 아래와 같다.

| 레이어 | typename | 우선순위 | 이유 |
| --- | --- | --- | --- |
| 개발제한구역 | `lt_c_ud801` | ★★★★★ | 그린벨트, 강한 개발 제한 |
| 도시자연공원구역 | `lt_c_uq162` | ★★★★★ | 도시 내 식재/개발 제한 판단 |
| 자연환경보전지역 | `lt_c_uq114` | ★★★★★ | 강한 보전 성격 |
| 도시지역 | `lt_c_uq111` | ★★★★☆ | 기본 용도지역 판단 |
| 농림지역 | `lt_c_uq113` | ★★★★☆ | 기본 용도지역 판단 |
| 보호지구 | `lt_c_uq126` | ★★★★☆ | 군사·문화재 등 제한 가능성 |

낮은 우선순위 또는 제외 대상:

- 교통 관련 레이어 대부분
- 산업단지 관련 레이어 대부분
- 학교 관련 레이어 대부분
- 사회복지 관련 레이어 대부분

### 점수 산출 정책

#### 1) `sumokScore`

수목 식재 적합도 점수이다.

반영 요소:

- 열섬 지수
- 여름철 지표면 온도
- 주변 세대 수
- 보행량
- 면적
- 도로 접근성
- 수자원 접근성
- 토양
- 경사도
- 대기질
- 주변 학교/공원 접근성
- VWorld 규제 정보

처리 규칙:

- 열섬이 높고 주변 세대가 많으면 수목 식재 수요가 높으므로 가점한다.
- 보행량이 많은 곳은 그늘/경관 개선 효과가 크므로 가점한다.
- 경사도가 과도하거나 면적이 지나치게 작으면 감점한다.
- 수자원 접근성이 없으면 유지관리 리스크로 감점한다.
- `prohibited` 수준 규제가 수목 식재에 직접 영향을 주면 0점 처리한다.
- `restricted` 수준 규제는 강한 감점 또는 `CONDITIONAL` 처리한다.
- `warning` 수준 규제는 점수는 유지할 수 있으나 explanation에 “인허가 확인 필요” 문구를 반드시 포함한다.

#### 2) `gardenScore`

도시농업/커뮤니티 가든 적합도 점수이다.

반영 요소:

- 수자원 접근성
- 보행량
- 주변 세대 수
- 학교/공원 인접성
- 토양
- 면적
- 규제 여부

#### 3) `solarScore`

태양광 발전 적합도 점수이다.

반영 요소:

- 일사량
- 월별 일사량
- 일조시간
- 경사도
- 전기 접근성
- 면적
- 규제 여부

### 규제 기반 점수 처리 규칙

1. 기본 점수 산출
    - `sumokScore`, `gardenScore`, `solarScore`를 각각 0~100 범위로 산출한다.
2. 규제 적용
    - `penaltyType=zero`: 영향받는 용도 점수는 0점 처리
    - `penaltyType=subtract`: 영향받는 용도 점수에서 `penaltyValue`만큼 차감
    - `penaltyType=multiplier`: 영향받는 용도 점수에 `penaltyValue`를 곱함
    - 다중 규제는 `zero`를 최우선 적용하고, 이후 `subtract`, `multiplier`는 보수적으로 누적 적용한다.
3. `sumokFeasibility` 산출
    - 수목 식재에 영향을 주는 규제와 환경 조건을 기반으로 `status`, `score`, `reason`을 산출한다.
    - `prohibited` 규제가 있으면 `status='PROHIBITED'`, `score=0`으로 처리한다.
    - `restricted` 규제가 있으면 `RESTRICTED` 또는 `CONDITIONAL`로 처리한다.
    - `warning` 규제가 있으면 `CONDITIONAL`로 처리하고 인허가 확인 항목을 추가한다.
4. `topRecommendation` 선정
    - 0점 처리된 용도는 추천 후보에서 제외한다.
    - 모든 용도가 0점 또는 개발 불가이면 `topRecommendation='RESTRICTED'` 또는 API 응답상 `recommendationStatus='NOT_RECOMMENDED'`로 표시한다.
    - 최고 점수와 차순위 점수 차이가 5점 미만이고 두 용도 모두 규제상 가능하면 `MIXED`를 허용한다.
    - `warning` 수준 규제가 있으면 추천은 가능하되 explanation에 인허가 확인 필요 문구를 포함한다.

### 수용 기준

- 계산 시점의 아래 스냅샷을 모두 저장한다.
    - `inputSnapshot`
    - `regulationsSnapshot`
- 점수 알고리즘 버전과 규제 룰셋 버전을 저장한다.
- 최신 점수는 `isLatest=true`로 식별한다.
- 규제 정보, 부지 원천 데이터, 점수 알고리즘이 변경되면 해당 부지 점수는 재계산 대상이 된다.
- 점수 응답에는 아래 내역이 `scoreBreakdown`에 포함되어야 한다.
    - 규제 적용 전 점수
    - 규제 페널티
    - 최종 점수
    - 0점 처리 사유
    - `sumokFeasibility` 판단 근거

---

## F-04. AI 자연어 부지 검색 에이전트

**목적**: 사용자가 자연어로 조건에 맞는 부지를 검색한다.

예시 질의:

- “수목 식재 가능한 부지 찾아줘”
- “그린벨트 제외하고 나무 심기 좋은 부지 보여줘”
- “열섬이 심하고 수목 식재 효과가 큰 곳 찾아줘”
- “인허가 확인 필요한 곳은 제외해줘”
- “태양광보다 수목 식재가 더 적합한 부지 추천해줘”

### 처리 흐름

1. 자연어 질의 수신
2. AI 또는 규칙 기반 파서로 검색 criteria 생성
3. criteria로 부지 검색
4. 결과 요약 생성
5. 회원인 경우 검색 히스토리 저장

### 수용 기준

- AI 실패 시 기본 키워드 검색으로 graceful fallback한다.
- 반환 데이터는 해석된 criteria를 포함해야 한다.
- 아래 조건을 criteria로 변환할 수 있어야 한다.
    - 수목 식재 가능
    - 수목 점수 높은 부지
    - `sumokFeasibility.status=AVAILABLE`
    - 인허가 확인 필요 부지 제외
    - 그린벨트 제외
    - 도시자연공원구역 제외
    - 자연환경보전지역 제외
    - 규제 없는 부지
- 동일 사용자의 검색 히스토리 조회가 가능해야 한다.

---

## F-05. AI 점수 설명 생성

### 4개 섹션

1. 종합 판단
2. 용도별 강점/약점
3. 주요 근거 데이터
4. 리스크 및 추가 확인 사항

### 수용 기준

- 동일 점수 버전에 대한 설명은 캐시할 수 있다.
- 설명에는 과도한 확정 표현을 피하고, 불확실성이 높은 경우 주의 문구를 포함한다.
- `regulationsSnapshot`에 포함된 규제 제한 사항, 페널티 적용 사유, 인허가 확인 필요 여부를 설명에 포함한다.
- `sumokFeasibility`의 `status`, `reason`, `blockingRegulations`, `warningRegulations`, `requiredChecks`를 설명에 포함한다.
- `warning` 수준 규제가 하나라도 있으면 “인허가 확인 필요” 문구를 반드시 포함한다.
- `sumokFeasibility.status=PROHIBITED` 또는 `RESTRICTED`인 경우 수목 식재를 추천하지 않거나 조건부 검토로 설명한다.

---

## F-06. 시나리오 시뮬레이션

### 대상 시나리오

| scenarioType | 설명 |
| --- | --- |
| `sumok_planting` | 수목 식재 시나리오 |
| `community_garden` | 커뮤니티 가든 조성 |
| `solar_panel` | 태양광 패널 설치 |
| `mixed_use` | 복합 활용 |

### 수용 기준

- `sumok_planting` 시나리오는 아래 정보를 반환한다.
    - 예상 식재 가능 수량
    - 수목 식재 가능 상태
    - 열섬 완화 예상 효과
    - 그늘/보행환경 개선 효과
    - 유지관리 리스크
    - 규제/인허가 확인 필요 여부
- 태양광 시나리오는 월별 발전량 추정치를 반환한다.
- 정원/도시농업 시나리오는 예상 효과를 JSON으로 반환한다.
- 입력 파라미터와 결과를 모두 저장한다.

---

## F-07. 부지 비교 모드

### 수용 기준

- 2~3개 부지를 비교할 수 있다.
- 동일 기준으로 아래 항목을 비교한다.
    - 점수
    - 면적
    - 비용
    - 인프라
    - 규제
    - `sumokFeasibility`
    - 수목 식재 제한 사유
- 규제 비교 항목에는 규제 수, 최고 심각도, 0점 처리 용도, 주요 법적 근거를 포함한다.
- 수목 비교 항목에는 `sumokScore`, `sumokFeasibility.status`, `reason`, `requiredChecks`를 포함한다.
- 없는 부지 ID가 포함되면 404 또는 부분 실패 정책을 명확히 반환한다.

---

## F-08. 리포트 내보내기

### 지원 포맷

- Markdown: `.md`
- JSON: `.json`

### 수용 기준

- 리포트 생성 요청 이력을 저장한다.
- 생성 실패 시 상태와 오류 메시지를 확인할 수 있다.
- 리포트에는 `sumokScore`, `sumokFeasibility`, 규제 내역, 인허가 확인 필요 여부를 포함한다.

---

## F-09~F-11. 인증/북마크

### 회원가입 수용 기준

- 이메일은 유니크해야 한다.
- 비밀번호는 해시로만 저장한다.
- 중복 이메일은 409 에러를 반환한다.

### 로그인 수용 기준

- 성공 시 accessToken, refreshToken, 사용자 정보를 반환한다.
- 로그아웃 시 refreshToken을 폐기한다.

### 북마크 수용 기준

- 한 사용자는 같은 부지를 중복 북마크할 수 없다.
- 북마크 목록은 최신 Parcel/Score 데이터를 조인하여 반환한다.
- 북마크 목록에서 `topRecommendation`, `topScore`, `sumokScore`, `sumokFeasibility.status`를 확인할 수 있어야 한다.

---

## F-12. 통계 분석 대시보드

### 지표 예시

- 전체 부지 수
- 행정구별 부지 수
- 추천 용도별 분포
- 평균 점수
- 데이터 신뢰도 평균
- 수목 식재 가능 부지 수
- 조건부 수목 식재 가능 부지 수
- 수목 식재 제한/불가 부지 수
- 규제 유형별 부지 수

---

## F-13. CSV 내보내기

### 수용 기준

- Excel 호환을 위해 UTF-8 BOM 옵션을 제공한다.
- 필터 조건을 CSV에도 동일하게 적용한다.
- CSV에는 수목 식재 관련 필드를 포함할 수 있다.
    - `sumokScore`
    - `sumokFeasibilityStatus`
    - `sumokFeasibilityReason`
    - `topRecommendation`
    - `regulations`
    - `requiredChecks`

---

## F-14. 공유 링크

### 수용 기준

- 토큰 기반 링크를 생성한다.
- 만료일과 폐기 여부를 관리한다.
- 공유 링크 조회는 비회원도 가능하다.

---

## F-15. 다크모드

### 정책

- 비회원: 브라우저 localStorage 저장
- 회원: 서버 `user_preferences.theme` 저장

---

## F-16. 검색 히스토리

### 수용 기준

- 회원 본인의 검색 이력만 조회할 수 있다.
- 관리자도 원문 query 접근은 개인정보 정책에 맞게 제한할 수 있다.

---

## F-17. 인기 검색어/트렌딩

### 수용 기준

- 기간별(`daily`, `weekly`, `monthly`) 인기 키워드를 제공한다.
- 부적절한 키워드 필터링 정책을 둘 수 있다.
- 개별 검색 히스토리는 F-16에 따라 회원 본인에게만 제공하고, F-17은 익명 집계 결과만 제공한다.
- “수목 식재 가능”, “그린벨트 제외”, “도시자연공원구역 제외” 등 수목 관련 검색어도 집계 가능해야 한다.

---

## F-18. 헬스 체크 API

### 수용 기준

- 서비스 상태, DB 연결 상태, 현재 서버 시간을 반환한다.
- 인증 없이 접근 가능하다.
- VWorld API Key 설정 여부는 `vworldApiKeyConfigured`로 확인할 수 있다.

---

## F-22. 점수 재계산/버전 관리

### 수용 기준

- 아래 중 하나라도 변경되면 재계산 대상이 될 수 있다.
    - 부지 원천 데이터
    - 규제 데이터
    - VWorld 레이어 데이터
    - 점수 알고리즘
    - 규제 룰셋
- 재계산 결과는 기존 점수를 덮어쓰지 않고 새 `ParcelScore` 레코드로 저장한다.
- 새 점수를 최신으로 지정할 때 기존 최신 점수의 `isLatest`는 false로 변경한다.
- 관리자 API는 재계산 대상 수, 성공 수, 실패 수, 실패 사유를 반환한다.

---

# 6. 비기능 요구사항

| 항목 | 요구사항 |
| --- | --- |
| 보안 | 비밀번호 bcrypt/argon2 해시, JWT 만료, refresh token 해시 저장 |
| 개인정보 | 이메일/검색어 등 개인정보성 데이터 접근 최소화 |
| 성능 | 목록 조회 p95 500ms 이하 목표, AI 검색 및 외부 API 실시간 호출 제외 |
| 장애 대응 | AI 실패 시 기본 검색 fallback, VWorld 장애 시 캐시된 규제 데이터 활용 |
| 감사성 | 관리자 작업, 점수 재계산, 데이터 적재, VWorld 규제 데이터 갱신 이력 저장 |
| 데이터 재현성 | 점수 계산 시 `inputSnapshot`, `regulationsSnapshot`, `scoreVersion`, `regulationRulesetVersion` 저장 |
| 규제 설명 책임성 | 수목 식재 가능/불가능 판단 시 규제명, 법적 근거, 페널티 사유, 인허가 확인 필요 여부를 함께 노출 |
| 호환성 | API version prefix `/api/v1/gs` 사용 |

---

# 7. 주요 용어 정리

| 용어 | 의미 |
| --- | --- |
| `sumokScore` | 수목 식재 적합도 점수 |
| `sumokFeasibility` | 수목 식재 가능성 판단 객체 |
| `gardenScore` | 도시농업/커뮤니티 가든 적합도 점수 |
| `solarScore` | 태양광 발전 적합도 점수 |
| `SUMOK` | 수목 식재 추천 코드 |
| `GARDEN` | 정원/도시농업 추천 코드 |
| `SOLAR` | 태양광 추천 코드 |
| `MIXED` | 복합 활용 추천 코드 |
| `RESTRICTED` | 제한 또는 추천 불가 코드 |
| `sumok_planting` | 수목 식재 시나리오 코드 |

---

# 8. 제거/변경 대상

| 기존 표현/필드 | 변경 후 |
| --- | --- |
| `treeScore` | `sumokScore` |
| `tree` | `sumok` 또는 추천 코드에서는 `SUMOK` |
| `TREE` | `SUMOK` |
| `tree_planting` | `sumok_planting` |
| 나무 심기점수 | 수목 점수 |
| 식수/음용수/지하수 API | 제거 또는 별도 보조 기능으로 분리 |