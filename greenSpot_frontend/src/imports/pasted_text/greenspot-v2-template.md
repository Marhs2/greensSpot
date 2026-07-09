노션 템플릿에 바로 복사해서 붙여넣을 수 있는 최종 완성본입니다. 추가된 8가지 기능(북마크, 통계 대시보드, CSV 내보내기, 공유 링크, 다크모드, 검색 히스토리, 인기 검색어, 할루 방어 강화)이 모두 반영되었습니다.

---

# GreenSpot v2 — 노션 제출용 템플릿 (최종본)

## Team Github Repository

> **GitHub**: https://github.com/[팀이름]/greenspot-v2
>
> **데모 링크**: https://preview-[bot-id].space-z.ai/greenspot
>
> **브랜치 전략**: `main` (배포용) / `develop` (개발통합)
>
> **PR 규칙**: 담당자 1명 이상 리뷰 후 merge
> - 1학년: 데이터 엔지니어링 (VWorld/KOSIS 연동, DB)
> - 2학년: 풀스택 개발 (API, UI, 반응형)
> - 3학년: AI/발표 (LLM 프롬프트, 할루 방어)

---

## 문제 정의 및 기획

### 🎯 Target & Problem

#### Target (누구의)

**1차 타겟: 지자체 도시계획·환경 부서 실무자**
- 서울시 25개 자치구 그린인프라담당, 도시숲경관과, 환경정책과
- 연간 녹지 인프라 예산 배정을 결정하는 공무원
- 현재는 직관·경험·민원 기반으로 우선설치지를 결정하며, 객관적 데이터 기반 도구 부재

**2차 타겟: 도시 농업 / 커뮤니티 가든 활동가**
- 자치구 도시농업 네트워크, 텃밭 운영진, 어르신 복지시설
- 우리 동네에 텃밭 조성 가능한 부지를 찾고 싶은 시민

**3차 타겟: 에너지 프로슈머 / 태양광 설치 업체**
- 옥상 태양광 설치를 검토하는 건물주, 설치 업체
- "이 건물 옥상이 태양광에 적합한가?"를 데이터로 판단하려는 사용자

#### Problem (어떤 문제를)

**핵심 문제 1: 도시 열섬으로 인한 폭염사망자 급증**
- 한국 폭염사망자 집계 기준 변경 후 4배 증가 (134명→518명, 뉴스타파 보도)
- 2023년 폭염일수 14.2일, 사망자 85명 (보험연구원)
- 서울 동별 녹지율 격차 3.5%~55.9% — **16배 차지** (한국조경학회지, 서울연구원 2018)
- 나무 1그루당 주변 온도 0.08℃ 강하, 연간 CO2 21.7kg 흡수 (USDA i-Tree)

**핵심 문제 2: 유휴지 활용 매칭 부재**
- 서울에 수천 개의 방치된 빈터·공유지·노후 옥상이 존재
- 지자체가 "식수 1만 그루" 발표는 하지만, "어디에 심을지"는 직관에 의존
- 부지마다 식수/텃밭/태양광 중 무엇이 최적인지 비교하는 도구 부재

**핵심 문제 3: ESG 인프라 효과 정량화 부재**
- "나무 심으면 얼마나 좋아지는가" 수치화 도구 부재
- 탄소·온도·대기질·투자비 효율 비교 불가
- 정책 제안서 작성 시 객관적 근거 부족

**한 문장 정의**
> "도시에는 가치 있는 빈터가 많지만, 그 부지에 무엇을 해야 할지 결정하는 객관적 도구가 없다."

---

### 🤖 AI Solution (왜 AI가 필요했는가)

#### AI의 3가지 역할 (모두 제한적 설계)

**역할 1: 자연어 부지 검색 에이전트 (핵심 차별성)**
- 사용자가 "중구에 식수 추천해줘"라고 자연어로 질문
- AI가 검색 조건 JSON 생성 (자치구, 부지유형, 추천용도, 최소점수 등)
- TypeScript로 실제 부지 데이터 검색
- AI가 결과를 자연어로 요약

**역할 2: 점수 자연어 설명**
- 7개 이상 변수를 결합한 점수를 인간이 이해하기 쉽게 자연어로 풀어 설명
- 1순위 추천 이유를 facts 기반 4섹션 마크다운 출력
- 대안 용도가 왜 1순위보다 낮은지 논리적 근거 제공
- 불확실성 구간(±3~10점)과 데이터 신뢰도 함께 명시

**역할 3: 시나리오 시뮬레이션 요약**
- "나무 13그루 식수 시 연간 CO2 1,032kg 흡수, 투자비 260만원" 형태
- 수량별 효과 비교로 예산 배분 의사결정 지원

#### 왜 AI가 필요한가 (당위성)

**이유 1: 다변량 점수의 자연어 변환**
- 한 부지의 점수는 7개 항목 × 3개 용도 = 21개 변수의 가중 합
- 공무원/시민이 이를 직관 이해하기 어려움
- AI가 "왜 90점인지" facts 기반으로 풀어 설명하면 의사결정 투명성 확보

**이유 2: 자연어 인터페이스**
- 비개발자(공무원, 시민)도 "강남구 옥상 중 태양광 80점 이상" 같은 자연어로 검색 가능
- 복잡한 필터 UI 없이 대화형으로 부지 발굴
- ESG 인프라 의사결정의 접근성 혁신

**이유 3: 정책 제안서 초안 자동화**
- 지자체 제출용 보고서는 반복적이고 시간 소모적
- AI가 4섹션(요약/이유/대안/한계) 구조로 정책 제안 형식 초안 생성
- Markdown/JSON/CSV 내보내기로 바로 활용 가능

#### 할루시네이션 방어 아키텍처 (3단계)

```
┌─────────────────────────────────────────────────────┐
│  Step 1: AI가 검색 조건 JSON만 생성                  │
│  - 부지 데이터 직접 접근 금지                        │
│  - district, parcelType, minScore 등 조건만 생성     │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│  Step 2: TypeScript로 실제 검색 (결정론적)           │
│  - 23개 부지 필터링/정렬                             │
│  - 모든 가중치 공개, 정적 계수 사용                   │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│  Step 3: AI가 결과 요약 (facts만 전달)               │
│  - 새 수치 생성 금지                                 │
│  - 출처 명시 강제                                    │
│  - 4섹션 마크다운 스키마 강제                        │
└─────────────────────────────────────────────────────┘
```

**정적 계수 출처 (모두 검증된 표준)**
- USDA i-Tree Eco (탄소·PM2.5·우수 저류 계수)
- 한국에너지공단 (태양광 용량계수 14.2%)
- 서울연구원 도시농업 보고서 (텃밭 탄소·식량 계수)
- 기상청 (일사량·일조시간)
- KOSIS (인구·가구 통계)
- Landsat 8 (지표면 온도)

---

### 🌟 차별성

#### 기존 서비스/연구와의 비교

| 기존 | 특징 | 한계 | GreenSpot v2 차별점 |
|---|---|---|---|
| American Forests Tree Equity Score | 동별 녹지 불균형 진단 | 진단만, 처방 없음 | 3개 용도 동시 추천 + 시뮬레이션 |
| 수원시 전기차 충전소 API | 단일 용도 입지 분석 | 복합 비교 불가 | 식수/텃밭/태양광 동시 비교 |
| 서울시 빈집 활용 | 주거 중심 | 녹지 인프라 X | 녹지 인프라 특화 |
| i-Tree Tools (USDA) | 단일 나무 효과 계산 | 공간 추천 X | 부지별 복합 추천 |
| 서울연구원 녹지형평성 논문 | 학술 분석 | 실사용 도구 X | 인터랙티브 대시보드 |

#### 핵심 차별성 5가지

**1. 3개 용도 동시 점수화 (한국 유사 사례 부재)**
- 기존: 식수 연구는 식수만, 태양광 연구는 태양광만
- GreenSpot v2: 동일 부지에서 식수/텃밭/태양광 3개 점수를 동시 산출
- "저희가 조사한 범위에서는 3개 용도를 동시 비교 추천하는 도구를 찾지 못했습니다" (겸손 톤)

**2. AI 부지 검색 에이전트**
- 자연어 질문 → AI가 검색 조건 해석 → TypeScript로 검색 → AI가 요약
- 할루시네이션 3단계 방어 설계
- 비개발자도 대화형으로 부지 발굴

**3. 불확실성 구간 + 데이터 신뢰도 표시**
- 기존: 점수만 제시 (검은 상자)
- GreenSpot v2: ±3~10점 불확실성 구간, 데이터 신뢰도(0~1) 표시
- 의사결정자가 리스크 평가 가능

**4. 시나리오 시뮬레이션 + 비교 모드**
- 수량별 효과 비교 (나무 10그루 vs 50그루)
- 2~3개 부지 동시 비교 (랭킹 5개 지표)
- 투자회수기간, 탄소 1kg당 비용 등 효율성 지표

**5. 실사용 기능 8가지 (추가 구현)**
- 북마크 (localStorage 영구 저장)
- 통계 분석 대시보드 (자치구별/유형별 차트)
- CSV/Markdown/JSON 내보내기 (엑셀 호환)
- 부지 공유 링크 (URL 파라미터)
- 다크모드 토글
- 검색 히스토리 + 인기 검색어
- 헬스 체크 API
- 에러 바운더리 + 로딩 스켈레톤

#### 톤 (겸손)
> "저희가 조사한 범위에서는 식수/텃밭/태양광 3개 용도를 동시 비교 추천하는 도구를 찾지 못했습니다. 미국 Tree Equity Score는 진단에 그치고, 국내 연구는 학술 분석에 머물러 있어 실사용 도구로의 전환이 기회라고 판단했습니다."

---

## 기능명세서

### 📋 기능 개요 (16개)

#### 메인 기능 (8개)

| 기능 ID | 기능명 | 우선순위 | 담당 | 상태 |
|---|---|---|---|---|
| F-01 | 부지 목록 조회 (대시보드) | High | 1학년 | ✅ |
| F-02 | 부지 상세 정보 조회 | High | 2학년 | ✅ |
| F-03 | 3중 용도 점수 산출 (불확실성 포함) | High | 2학년 | ✅ |
| F-04 | AI 자연어 부지 검색 에이전트 | High | 3학년 | ✅ |
| F-05 | AI 점수 설명 생성 (4섹션) | High | 3학년 | ✅ |
| F-06 | 시나리오 시뮬레이션 (월별 발전량) | High | 3학년 | ✅ |
| F-07 | 부지 비교 모드 (2~3개 동시) | Medium | 2학년 | ✅ |
| F-08 | 리포트 내보내기 (MD/JSON) | Medium | 2학년 | ✅ |

#### 추가 기능 (8개)

| 기능 ID | 기능명 | 우선순위 | 담당 | 상태 |
|---|---|---|---|---|
| F-09 | 북마크/즐겨찾기 (localStorage) | Medium | 2학년 | ✅ |
| F-10 | 통계 분석 대시보드 | Medium | 2학년 | ✅ |
| F-11 | CSV 내보내기 (Excel 호환) | Medium | 2학년 | ✅ |
| F-12 | 부지 공유 링크 (URL 파라미터) | Medium | 2학년 | ✅ |
| F-13 | 다크모드 토글 | Low | 2학년 | ✅ |
| F-14 | 검색 히스토리 조회 | Medium | 3학년 | ✅ |
| F-15 | 인기 검색어 / 트렌딩 | Medium | 3학년 | ✅ |
| F-16 | 헬스 체크 API | High | 2학년 | ✅ |

---

### F-01: 부지 목록 조회 (대시보드)

**엔드포인트**: `GET /api/gs/parcels?district={자치구}&type={부지유형}`

**설명**: 서울 5개 자치구(중구/성동구/동대문구/마포구/강남구)의 23개 부지 목록 반환. 상단에 통계 대시보드(총 부지/총 면적/1순위별 카운트/평균 점수) 표시.

**응답 스키마**:
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
      "nearbyHouseholds": 1820,
      "pedestrianFlow": 2400,
      "regulatoryRestriction": "NONE",
      "confidence": 0.93,
      "scores": {
        "treeScore": 69,
        "gardenScore": 90,
        "solarScore": 74,
        "topRecommendation": "GARDEN",
        "uncertainty": 4
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

**데이터 소스**:
- 1차: Prisma DB (23개 서울 부지)
- 2차: VWorld API (키 설정 시 실시간 전환, 하이브리드 모드)

**정렬**: 점수순 자동 정렬 (1순위 점수 내림차순)

**UI 기능**:
- 점수순 자동 정렬
- TOP 1위 Crown 뱃지
- 비교 체크 버튼 (+ 아이콘)
- 북마크 버튼 (☆/★ 토글)
- 3개 점수 미니 바 (한눈에 비교)

---

### F-02: 부지 상세 정보 조회

**엔드포인트**: `GET /api/gs/parcels/{id}`

**응답**: 부지 전체 필드 (25개) + 점수 (3개 + 불확실성)

**부지 필드 25개**:
1. 기본: id, name, district, neighborhood, lat, lng
2. 물리: areaSqm, parcelType, ownership, soilType, elevationM, slopeDegree
3. 환경: solarIrradiance, monthlyIrradiance[12], sunlightHours, heatIsland, surfaceTempSummer, airQuality
4. 사회: nearbyHouseholds, pedestrianFlow, roadAdjacent, waterAccess, electricityAccess
5. 인접: nearbySchools, nearbyHospitals, nearbyParks, nearbySubwayStations
6. 규제: regulatoryRestriction, estimatedAcquisitionCostWon
7. 메타: dataSource, confidence

---

### F-03: 3중 용도 점수 산출 (불확실성 포함)

**엔드포인트**: 내부 로직 (F-01/F-02에서 함께 반환)

**점수 공식** (3개 용도 모두 가중치 합 1.0):

**식수 점수**:
```
TreeScore = (
  열섬완화_정규화 × 0.30 +
  보행자혜택_정규화 × 0.20 +
  일조량_정규화 × 0.10 +
  부지면적_정규화 × 0.15 +
  부지유형_적합도 × 0.10 +
  도로인접 × 0.10 +
  규제패널티 × 0.05
)
```

**규제 패널티**:
- NONE: 1.0 (패널티 없음)
- GREEN_BELT: 0.50 (50% 패널티)
- HISTORICAL: 0.70
- FLOOD_ZONE: 0.85

**토양 적합도** (텃밭 점수용):
- LOAM: 95점 (최적)
- SAND: 70점
- CLAY: 60점
- ROCKY: 25점
- UNKNOWN: 50점 (옥상 등)

**불확실성 구간**:
```
uncertainty = (1 - confidence) × 10 + 3
// confidence 0.93 → ±4점
// confidence 0.82 → ±5점
```

---

### F-04: AI 자연어 부지 검색 에이전트 ⭐ (핵심 차별성)

**엔드포인트**: `POST /api/gs/agent`

**요청 본문**:
```json
{ "query": "강남구 옥상 중 태양광 점수 80점 이상" }
```

**응답 스키마**:
```json
{
  "query": "강남구 옥상 중 태양광 점수 80점 이상",
  "criteria": {
    "district": "강남구",
    "parcelType": "ROOFTOP",
    "topRecommendation": "SOLAR",
    "minScore": 80,
    "sortBy": "score",
    "limit": 5,
    "explanation": "강남구 옥상 중 태양광 1순위 80점 이상 부지 조회"
  },
  "results": [
    {
      "id": "GN-001",
      "name": "삼성동 옥상 A",
      "district": "강남구",
      "topRecommendation": "SOLAR",
      "topScore": 86,
      "areaSqm": 380,
      "parcelType": "ROOFTOP"
    }
  ],
  "summary": "강남구 삼성동 옥상 A 부지가 태양광 설치에 최적화되어 있으며, 면적은 380㎡이고 점수는 86점으로 80점 이상의 조건을 충족합니다.",
  "count": 1,
  "elapsed_ms": 1234,
  "source": "ai"
}
```

**3단계 할루시네이션 방어**:
1. **AI가 검색 조건 JSON만 생성** (부지 데이터 접근 금지)
2. **TypeScript로 실제 검색** (결정론적)
3. **AI가 결과 요약** (facts만 전달, 새 수치 생성 금지)

**매핑 규칙 (AI 프롬프트에 내장)**:
- "빈터" → VACANT_LOT, "옥상" → ROOFTOP, "유휴지" → UNUSED_LAND, "방치건물" → ABANDONED
- "식수/나무" → TREE, "텃밭" → GARDEN, "태양광/솔라" → SOLAR
- "큰/넓은" → minArea 높게, "작은" → maxArea 낮게
- "뜨거운/열섬" → minHeatIsland, "햇빛 많은" → minSolarIrradiance
- "상위 N개" → limit: N (기본 5)
- "점수 높은" → minScore: 80

**Fallback**: AI 실패 시 키워드 매칭으로 대체

**추천 질문 5개** (UI에 표시):
1. "중구에 식수 추천해줘"
2. "강남구 옥상 중 태양광 점수 높은 곳"
3. "가장 넓은 부지 3개"
4. "열섬이 가장 심한 곳"
5. "동대문구 텃밭 추천"

---

### F-05: AI 점수 설명 생성 (4섹션)

**엔드포인트**: `POST /api/gs/parcels/{id}/explain`

**할루시네이션 방어 규칙**:
1. facts 객체 외 수치 사용 금지
2. 출처 명시 강제 (USDA i-Tree / 기상청 / KOSIS / Landsat / 서울연구원)
3. 다른 부지와 비교 표현 금지
4. 정치적 단어 금지 (불평등/격차/소외/차별)
5. 4섹션 마크다운 스키마 강제
6. 불확실성 구간, 데이터 신뢰도 한계점에 명시

**출력 스키마**:
```markdown
## 📍 부지 요약
위치, 면적, 유형, 소유권, 규제 한 줄 요약

## 🎯 추천 결과 및 이유
1순위 용도 + 상위 2-3개 기여 항목 인용. facts 수치 그대로 인용.

## 💡 대안 용도 검토
2순위, 3순위가 왜 낮은지 짧게.

## ⚠️ 한계 및 보완점
불확실성 구간(±N점), 데이터 신뢰도(N%), 실제 시공 시 추가 검토사항.
```

---

### F-06: 시나리오 시뮬레이션 (월별 발전량)

**엔드포인트**: `POST /api/gs/parcels/{id}/simulate`

**요청 본문**:
```json
{
  "scenarioType": "PLANT_TREES" | "CREATE_GARDEN" | "INSTALL_SOLAR" | "COMPARE_ALL",
  "quantity": 10
}
```

**수량 제한**:
- PLANT_TREES: 최대 200
- CREATE_GARDEN: 최대 150
- INSTALL_SOLAR: 최대 500

**응답 (COMPARE_ALL)**:
```json
{
  "scenarios": {
    "PLANT_TREES": {
      "label": "나무 28그루",
      "effects": {
        "carbonKgPerYear": 2223,
        "pm25ReductionKgPerYear": 4.424,
        "temperatureReductionC": 2.2,
        "rainwaterLitersPerYear": 30800,
        "costEstimateWon": 5600000,
        "costPerCarbonKgWon": 2519,
        "summary": "은행나무 성목 28그루 식재 시 연간 CO2 2223kg 흡수..."
      }
    },
    "INSTALL_SOLAR": {
      "effects": {
        "energyKwhPerYear": 23870,
        "energyMonthly": [1800, 2400, ...12개월],
        "carbonKgPerYear": 9930,
        "paybackYears": 24.3,
        "costPerCarbonKgWon": 933
      }
    }
  }
}
```

**정적 계수 (할루 방어)**:
- USDA i-Tree Eco: 은행나무 성목 기준 (CO2 79.4kg/그루/년, PM2.5 0.158kg/그루/년)
- 한국에너지공단: 용량계수 14.2%, 연간 1,242 kWh/kW
- 서울연구원: 텃밭 0.85kg CO2/㎡/년, 2.4kg 식량/㎡/년

---

### F-07: 부지 비교 모드

**엔드포인트**: `POST /api/gs/compare`

**요청 본문**: `{ "ids": ["DD-001", "GN-001", "JG-005"] }`

**응답**:
- 2~3개 부지의 점수/효과 비교
- 5개 지표 랭킹: 식수/텃밭/태양광/탄소효율/비용효율 1위
- 비교 차트 (BarChart)

---

### F-08: 리포트 내보내기 (MD/JSON)

**엔드포인트**: `POST /api/gs/report`

**요청 본문**: `{ "parcelId": "DD-001", "format": "markdown" | "json" }`

**Markdown 리포트 구조**:
1. 부지 정보 (이름, 위치, 면적, 유형, 소유권, 토양, 규제)
2. 환경 데이터 (일사량, 일조, 열섬, 지표면온도, PM2.5)
3. 사회경제 데이터 (가구, 보행자, 인접 시설)
4. 점수 분석 (3개 용도 + 불확실성 + 신뢰도)
5. 시나리오 시뮬레이션 (3개 용도별 효과 + 투자비 + 효율성)

---

### F-09: 북마크/즐겨찾기 (localStorage) ⭐ 추가 기능

**엔드포인트**: 없음 (클라이언트 localStorage)

**구현**: `src/lib/greenspot/use-bookmarks.ts`

**기능**:
- 부지 카드에 ☆/★ 토글 버튼
- 헤더에 북마크 카운트 배지 (빨간색)
- 북마크 패널 (클릭 시 해당 부지로 이동)
- 전체 삭제 기능
- localStorage 영구 저장 (서버 부하 없음)

**데이터 스키마**:
```typescript
interface Bookmark {
  id: string;
  name: string;
  district: string;
  topRecommendation: string;
  topScore: number;
  bookmarkedAt: string; // ISO timestamp
}
```

---

### F-10: 통계 분석 대시보드 ⭐ 추가 기능

**페이지**: `/greenspot/stats`

**API**: `GET /api/gs/stats`

**기능**:
- 요약 통계 카드 4개 (총 부지, 식수/텃밭/태양광 1순위)
- 자치구별 평균 점수 BarChart (3개 용도 동시 비교)
- 추천 분포 PieChart (TREE/GARDEN/SOLAR 비율)
- 부지유형별 분포 BarChart
- 자치구별 상세 표 (9개 컬럼: 부지 수, 총 면적, 평균 점수, 1순위별 카운트)
- 인기 검색 키워드 (진행 바)
- 최근 검색 기록 (스크롤 가능)

---

### F-11: CSV 내보내기 (Excel 호환) ⭐ 추가 기능

**엔드포인트**: `GET /api/gs/export`

**응답**:
- Content-Type: `text/csv; charset=utf-8`
- UTF-8 BOM 포함 (Excel 호환)
- 파일명: `greenspot-parcels-YYYY-MM-DD.csv`

**CSV 컬럼 (22개)**:
```
ID, 부지명, 자치구, 행정동, 위도, 경도,
면적(㎡), 부지유형, 소유권, 토양,
일사량(kWh/㎡/일), 일조시간, 열섬강도(℃), 여름지표면온도(℃), PM2.5(μg/m³),
주변가구, 일일보행자,
식수점수, 텃밭점수, 태양광점수, 1순위추천, 불확실성(±)
```

---

### F-12: 부지 공유 링크 (URL 파라미터) ⭐ 추가 기능

**형식**: `/greenspot?parcel=DD-001`

**기능**:
- 부지 선택 시 URL 자동 업데이트
- "공유" 버튼 클릭 시 클립보드 복사
- 토스트 알림 ("✓ 공유 링크가 복사되었습니다")
- URL 접속 시 자동으로 해당 부지 선택

---

### F-13: 다크모드 토글 ⭐ 추가 기능

**구현**: 헤더 Moon/Sun 아이콘 버튼

**동작**:
- `document.documentElement.classList.add('dark')` 적용
- 사용자 선호도 localStorage 저장 (향후 확장)

---

### F-14: 검색 히스토리 조회 ⭐ 추가 기능

**엔드포인트**: `GET /api/gs/history?limit={N}`

**응답**:
```json
{
  "history": [
    {
      "id": "cuid123",
      "query": "중구에 식수 추천해줘",
      "criteria": { "district": "중구", "topRecommendation": "TREE" },
      "resultCount": 1,
      "summary": "중구 을지로동에 위치한 유휴부지...",
      "source": "ai",
      "createdAt": "2026-07-05T12:19:37.039Z"
    }
  ],
  "total": 2
}
```

**source 값**: `ai` (정상) / `fallback` (AI 실패, 키워드 매칭)

---

### F-15: 인기 검색어 / 트렌딩 ⭐ 추가 기능

**엔드포인트**: `GET /api/gs/trending`

**응답**:
```json
{
  "totalQueries": 2,
  "topKeywords": [
    { "keyword": "식수", "count": 2 },
    { "keyword": "중구", "count": 2 }
  ],
  "topDistricts": [
    { "district": "중구", "count": 2 }
  ],
  "recentQueries": ["중구에 식수 추천해줘"]
}
```

**키워드 추출 규칙**:
- 자치구: 중구, 성동구, 동대문구, 마포구, 강남구
- 용도: 식수, 나무, 텃밭, 태양광, 솔라
- 유형: 옥상, 빈터, 유휴지, 방치
- 속성: 열섬, 넓은, 큰, 점수

---

### F-16: 헬스 체크 API ⭐ 추가 기능

**엔드포인트**: `GET /api/gs/health`

**응답**:
```json
{
  "status": "healthy",
  "database": "connected",
  "stats": {
    "parcels": 23,
    "scores": 23,
    "scenarios": 0,
    "agentQueries": 2
  },
  "environment": {
    "vworldApiKeyConfigured": false,
    "kmaApiKeyConfigured": false
  },
  "elapsed_ms": 4
}
```

---

## 화면 설계도

> **Figma 링크**: [작성 예정 - https://figma.com/...]
>
> **대체 자료**: 스크린샷 첨부 (아래 경로)

### 화면 목록 및 스크린샷

| 화면 ID | 화면명 | 설명 | 스크린샷 경로 |
|---|---|---|---|
| S-01 | 메인 대시보드 | 통계 카드 + AI 에이전트 + 부지 목록 + 상세 패널 | `/download/greenspot-v2-final.png` |
| S-02 | AI 에이전트 패널 | 자연어 검색 + 추천 질문 + 결과 | (위 스크린샷 상단) |
| S-03 | 부지 상세 - 개요 탭 | StatTile 그리드 + 인프라 현황 + 접근성 | (상세 패널 개요 탭) |
| S-04 | 부지 상세 - 점수 탭 | 1순위 Hero + 레이더 차트 + 상세 근거 | (상세 패널 점수 탭) |
| S-05 | 부지 상세 - AI 분석 탭 | 4섹션 마크다운 + 불확실성 표시 | (상세 패널 AI 탭) |
| S-06 | 부지 상세 - 시뮬레이션 탭 | 3개 시나리오 비교 + 월별 차트 | (상세 패널 시뮬 탭) |
| S-07 | 비교 모달 | 2~3개 부지 비교 + 랭킹 | (비교 버튼 클릭 시) |
| S-08 | 통계 대시보드 | 자치구별 차트 + 추천 분포 + 검색 트렌드 | `/download/greenspot-v2-stats.png` |
| S-09 | 북마크 패널 | 저장된 부지 목록 + 전체 삭제 | (헤더 북마크 버튼 클릭) |
| S-10 | 모바일 반응형 | 375px 뷰포트 | `/download/greenspot-v2.png` |

### 와이어프레임 (텍스트)

```
┌─────────────────────────────────────────────────────────────────┐
│ Header: GreenSpot v2 [NEW] | 통계 | CSV | 북마크(2) | 🌙 | SafeSpot │
├─────────────────────────────────────────────────────────────────┤
│ Stats Dashboard: [분석부지] [총면적] [식수1위] [텃밭1위] [...]   │
├─────────────────────────────────────────────────────────────────┤
│ AI Agent Panel (전체 너비)                                      │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ ✨ AI 부지 검색 에이전트 [BETA]                             │ │
│ │ [자연어 입력창..............................] [전송]        │ │
│ │ 추천: [중구에 식수 추천] [강남구 옥상 태양광] [...]         │ │
│ │ ┌─ AI 요약 ────────────────────────────────────────────┐    │ │
│ │ │ "삼성동 옥상 A 부지가 태양광에 최적..."              │    │ │
│ │ │ 검색 조건: 자치구=강남구, 유형=옥상, 최소점수=80     │    │ │
│ │ └──────────────────────────────────────────────────────┘    │ │
│ │ [1순위] 삼성동 옥상 A 86/100  [2위] 역삼동... 80/100       │ │
│ └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ Filters: [자치구 ▾] [부지유형 ▾]                                │
├──────────┬──────────────────────────────────┬───────────────────┤
│ 부지목록 │ 상세 패널                        │                   │
│ (점수순) │ ┌─ 탭: 개요/점수/AI/시뮬 ────┐  │                   │
│          │ │                              │  │                   │
│ TOP 회기 │ │ [공유] [MD] [JSON] 리포트    │  │                   │
│ ☆ + 90점 │ │                              │  │                   │
│          │ │ 1순위 Hero: 텃밭 90/100      │  │                   │
│ 신당동   │ │ ±4점 (신뢰도 93%)            │  │                   │
│ ☆ + 87점 │ │                              │  │                   │
│          │ │ [레이더 차트]                │  │                   │
│ ...      │ │                              │  │                   │
│          │ │ [상세 근거 아코디언]         │  │                   │
│          │ └──────────────────────────────┘  │                   │
└──────────┴──────────────────────────────────┴───────────────────┘
```

### 화면 흐름도

```
[메인 대시보드]
     │
     ├─ AI 에이전트 질문 → [검색 결과] → 부지 클릭 → [상세 패널]
     │                                              │
     ├─ 부지 목록 클릭 ────────────────────→ [상세 패널]
     │                                              │
     ├─ ☆ 북마크 → [헤더 북마크 버튼] → [북마크 패널]
     │                                              │
     ├─ + 비교 체크 (2~3개) → [비교 버튼] → [비교 모달]
     │                                              │
     ├─ 헤더 "통계" 버튼 → [통계 대시보드 페이지]
     │                                              │
     ├─ 헤더 "CSV" 버튼 → [CSV 파일 다운로드]
     │                                              │
     ├─ 상세 패널 "공유" 버튼 → [클립보드 복사 + 토스트]
     │                                              │
     └─ 필터 변경 → [목록 갱신]                     │
                                                    │
                          [상세 패널] ──→ [MD/JSON 리포트 다운로드]
```

---

## ERD

> **ERD Cloud URL**: [작성 예정 - https://www.erdcloud.com/...]
>
> **대체: Prisma Schema 기반 ERD 다이어그램** (아래)

### 엔티티 관계도

```
┌─────────────────────────────────────────────────────┐
│                    Parcel                           │
│                  (부지 - 메인)                       │
├─────────────────────────────────────────────────────┤
│  id (PK) ◄──────────────────────────────────┐       │
│  name                                       │       │
│  district, neighborhood                     │       │
│  lat, lng                                   │       │
│  areaSqm, parcelType                        │       │
│  ownership, soilType                        │       │
│  solarIrradiance, monthlyIrradiance         │       │
│  sunlightHours, heatIsland                  │       │
│  surfaceTempSummer, airQuality              │       │
│  nearbyHouseholds, pedestrianFlow           │       │
│  roadAdjacent, waterAccess                  │       │
│  electricityAccess                          │       │
│  nearbySchools, nearbyHospitals             │       │
│  nearbyParks, nearbySubwayStations          │       │
│  regulatoryRestriction                      │       │
│  confidence, dataSource                     │       │
│  createdAt, updatedAt                       │       │
└─────────────────────────────────────────────┘       │
        │                                              │
        │ 1:1                                          │
        ↓                                              │
┌─────────────────────────────────────────────────────┐
│                  ParcelScore                        │
│                  (부지 점수)                         │
├─────────────────────────────────────────────────────┤
│  id (PK)                                            │
│  parcelId (FK) ─────────────────────────────────────┘
│  treeScore, gardenScore, solarScore                │
│  topRecommendation (TREE/GARDEN/SOLAR)             │
│  uncertainty (±점수)                                │
│  scoreBreakdown (JSON)                             │
│  computedAt                                        │
└─────────────────────────────────────────────────────┘

        │ 1:N
        ↓
┌─────────────────────────────────────────────────────┐
│                   Scenario                          │
│                (시나리오 시뮬레이션)                 │
├─────────────────────────────────────────────────────┤
│  id (PK)                                            │
│  parcelId (FK) ──→ Parcel.id                        │
│  scenarioType (PLANT_TREES/CREATE_GARDEN/INSTALL_   │
│                 SOLAR/COMPARE_ALL)                  │
│  quantity                                           │
│  effects (JSON)                                     │
│  aiExplanation                                      │
│  createdAt                                          │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                  AgentQuery                         │
│              (AI 검색 기록 - 독립)                  │
├─────────────────────────────────────────────────────┤
│  id (PK)                                            │
│  query (사용자 자연어 질문)                         │
│  criteria (JSON - AI 생성 검색 조건)                │
│  resultCount                                        │
│  summary (AI 요약)                                  │
│  source (ai/fallback)                               │
│  createdAt                                          │
└─────────────────────────────────────────────────────┘
```

### 관계 요약

| 관계 | 카디널리티 | 설명 |
|---|---|---|
| Parcel → ParcelScore | 1:1 | 부지 1개당 점수 1개 |
| Parcel → Scenario | 1:N | 부지 1개당 시나리오 N개 (설치 수량별) |
| AgentQuery | 독립 | 검색 기록 (FK 없음) |

### Prisma Schema (전체)

```prisma
// Prisma Schema - GreenSpot v2
// 4개 모델: Parcel, ParcelScore, Scenario, AgentQuery

generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "sqlite"
  url      = env("DATABASE_URL")
}

model Parcel {
  id              String   @id @unique
  name            String
  district        String
  neighborhood    String
  lat             Float
  lng             Float
  areaSqm         Float
  parcelType      String   // VACANT_LOT | ROOFTOP | UNUSED_LAND | ABANDONED | BROWNFIELD
  ownership       String   // PUBLIC | PRIVATE | UNKNOWN
  soilType        String   // LOAM | CLAY | SAND | ROCKY | UNKNOWN
  elevationM      Float
  slopeDegree     Float
  solarIrradiance     Float
  monthlyIrradiance   String  // JSON: [12개월]
  sunlightHours       Float
  heatIsland          Float
  surfaceTempSummer   Float
  airQuality          Float
  nearbyHouseholds    Int
  pedestrianFlow      Int
  roadAdjacent        Boolean @default(true)
  waterAccess         Boolean @default(true)
  electricityAccess   Boolean @default(true)
  nearbySchools         Int     @default(0)
  nearbyHospitals       Int     @default(0)
  nearbyParks           Int     @default(0)
  nearbySubwayStations  Int     @default(0)
  regulatoryRestriction      String  @default("NONE")
  estimatedAcquisitionCostWon Int    @default(0)
  dataSource    String  @default("sample")
  confidence    Float   @default(0.9)
  createdAt     DateTime @default(now())
  updatedAt     DateTime @updatedAt
  scores        ParcelScore?
  scenarios     Scenario[]
}

model ParcelScore {
  id                String   @id @default(cuid())
  parcelId          String   @unique
  parcel            Parcel   @relation(fields: [parcelId], references: [id], onDelete: Cascade)
  treeScore         Float
  gardenScore       Float
  solarScore        Float
  topRecommendation String
  uncertainty       Float
  scoreBreakdown    String   // JSON
  computedAt        DateTime @default(now())
}

model Scenario {
  id            String   @id @default(cuid())
  parcelId      String
  parcel        Parcel   @relation(fields: [parcelId], references: [id], onDelete: Cascade)
  scenarioType  String
  quantity      Int
  effects       String   // JSON
  aiExplanation String?
  createdAt     DateTime @default(now())
}

model AgentQuery {
  id          String   @id @default(cuid())
  query       String
  criteria    String   // JSON
  resultCount Int
  summary     String
  source      String   @default("ai")
  createdAt   DateTime @default(now())
}
```

> **전체 ERD 문서**: `docs/ERD.md` (273줄, 점수 공식 + 데이터 흐름도 포함)

---

## API Docs

> **Swagger URL**: 현재 Swagger 미사용 (Next.js API Routes 기반)
>
> **대체: API 명세서 문서** (`docs/API.md` 691줄)

### API 엔드포인트 목록 (12개)

| Method | Endpoint | 설명 | 응답 시간 |
|---|---|---|---|
| GET | `/api/gs/health` | 헬스 체크 | ~4ms |
| GET | `/api/gs/parcels` | 부지 목록 조회 | ~50ms |
| GET | `/api/gs/parcels/{id}` | 부지 상세 조회 | ~30ms |
| POST | `/api/gs/agent` | AI 자연어 부지 검색 | ~3-8초 |
| POST | `/api/gs/parcels/{id}/explain` | AI 점수 설명 생성 | ~5-10초 |
| POST | `/api/gs/parcels/{id}/simulate` | 시나리오 시뮬레이션 | ~2ms |
| POST | `/api/gs/compare` | 부지 비교 | ~10ms |
| POST | `/api/gs/report` | 리포트 내보내기 (MD/JSON) | ~5ms |
| GET | `/api/gs/export` | CSV 내보내기 | ~128ms |
| GET | `/api/gs/stats` | 통계 분석 | ~200ms |
| GET | `/api/gs/trending` | 인기 검색어 | ~140ms |
| GET | `/api/gs/history` | 검색 히스토리 | ~250ms |

### Base URL

```
개발: http://localhost:3000
프로덕션: https://[your-domain].vercel.app
```

### 1. 헬스 체크

```http
GET /api/gs/health
```

**응답 (200)**:
```json
{
  "status": "healthy",
  "database": "connected",
  "stats": {
    "parcels": 23,
    "scores": 23,
    "scenarios": 0,
    "agentQueries": 2
  },
  "environment": {
    "vworldApiKeyConfigured": false
  },
  "elapsed_ms": 4
}
```

### 2. 부지 목록 조회

```http
GET /api/gs/parcels?district={자치구}&type={부지유형}
```

**쿼리 파라미터**:
- `district`: 중구/성동구/동대문구/마포구/강남구 (선택)
- `type`: VACANT_LOT/ROOFTOP/UNUSED_LAND/ABANDONED (선택)

**응답 (200)**:
```json
{
  "parcels": [{ "id": "DD-001", "name": "회기동 빈터 A", ... }],
  "stats": { "total": 23, "avgTreeScore": 63, ... },
  "source": "database",
  "vworldEnabled": false
}
```

### 3. 부지 상세 조회

```http
GET /api/gs/parcels/{id}
```

**응답 (200)**: `{ "parcel": {...25개 필드}, "scores": {...}, "source": "database" }`

**상태 코드**: 200 / 404 (부지 없음) / 500

### 4. AI 자연어 부지 검색 에이전트 ⭐

```http
POST /api/gs/agent
Content-Type: application/json

{
  "query": "강남구 옥상 중 태양광 점수 80점 이상"
}
```

**응답 (200)**:
```json
{
  "query": "강남구 옥상 중 태양광 점수 80점 이상",
  "criteria": { "district": "강남구", "parcelType": "ROOFTOP", ... },
  "results": [{ "id": "GN-001", "name": "삼성동 옥상 A", "topScore": 86 }],
  "summary": "강남구 삼성동 옥상 A 부지가 태양광 설치에 최적화되어 있으며...",
  "count": 1,
  "elapsed_ms": 1234,
  "source": "ai"
}
```

### 5. AI 점수 설명 생성

```http
POST /api/gs/parcels/{id}/explain
Content-Type: application/json

{}
```

**응답 (200)**:
```json
{
  "parcelId": "DD-001",
  "explanation": "## 📍 부지 요약\n...\n## 🎯 추천 결과 및 이유\n...",
  "facts": { ... },
  "promptVersion": "v3-greenspot2",
  "uncertainty": 4
}
```

### 6. 시나리오 시뮬레이션

```http
POST /api/gs/parcels/{id}/simulate
Content-Type: application/json

{
  "scenarioType": "COMPARE_ALL",
  "quantity": 10
}
```

**scenarioType**: PLANT_TREES / CREATE_GARDEN / INSTALL_SOLAR / COMPARE_ALL

**응답 (200)**:
```json
{
  "parcelId": "DD-001",
  "scenarios": {
    "PLANT_TREES": { "label": "나무 28그루", "effects": {...} },
    "CREATE_GARDEN": { ... },
    "INSTALL_SOLAR": { ... }
  },
  "elapsed_ms": 2
}
```

### 7. 부지 비교

```http
POST /api/gs/compare
Content-Type: application/json

{
  "ids": ["DD-001", "GN-001", "JG-005"]
}
```

**응답 (200)**:
```json
{
  "comparison": [{ "id": "DD-001", "scores": {...}, "effects": {...} }],
  "ranking": {
    "tree": ["DD-001", "GN-001", "JG-005"],
    "garden": [...],
    "solar": [...],
    "carbon": [...],
    "costEfficiency": [...]
  }
}
```

### 8. 리포트 내보내기 (MD/JSON)

```http
POST /api/gs/report
Content-Type: application/json

{
  "parcelId": "DD-001",
  "format": "markdown"
}
```

**format**: `markdown` / `json`

**응답**: 파일 다운로드 (Markdown / JSON)

### 9. CSV 내보내기 ⭐

```http
GET /api/gs/export
```

**응답 (200)**:
- Content-Type: `text/csv; charset=utf-8`
- Content-Disposition: `attachment; filename="greenspot-parcels-YYYY-MM-DD.csv"`
- UTF-8 BOM 포함 (Excel 호환)

**CSV 컬럼 (22개)**:
```
ID, 부지명, 자치구, 행정동, 위도, 경도,
면적(㎡), 부지유형, 소유권, 토양,
일사량(kWh/㎡/일), 일조시간, 열섬강도(℃), 여름지표면온도(℃), PM2.5(μg/m³),
주변가구, 일일보행자,
식수점수, 텃밭점수, 태양광점수, 1순위추천, 불확실성(±)
```

### 10. 통계 분석 ⭐

```http
GET /api/gs/stats
```

**응답 (200)**:
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
    { "parcelType": "VACANT_LOT", "count": 8, "totalArea": 3500, "avgScore": 82 }
  ],
  "byRecommendation": { "TREE": 2, "GARDEN": 16, "SOLAR": 5 }
}
```

### 11. 인기 검색어 / 트렌딩 ⭐

```http
GET /api/gs/trending
```

**응답 (200)**:
```json
{
  "totalQueries": 2,
  "topKeywords": [
    { "keyword": "식수", "count": 2 },
    { "keyword": "중구", "count": 2 }
  ],
  "topDistricts": [
    { "district": "중구", "count": 2 }
  ],
  "recentQueries": ["중구에 식수 추천해줘"]
}
```

### 12. 검색 히스토리 조회 ⭐

```http
GET /api/gs/history?limit={N}
```

**쿼리 파라미터**:
- `limit`: 반환할 기록 수 (기본 20, 최대 100)

**응답 (200)**:
```json
{
  "history": [
    {
      "id": "cuid123",
      "query": "중구에 식수 추천해줘",
      "criteria": { "district": "중구", "topRecommendation": "TREE" },
      "resultCount": 1,
      "summary": "중구 을지로동에 위치한 유휴부지...",
      "source": "ai",
      "createdAt": "2026-07-05T12:19:37.039Z"
    }
  ],
  "total": 2
}
```

### 에러 처리

**표준 에러 응답**:
```json
{
  "error": "에러 메시지",
  "detail": "상세 정보"
}
```

**상태 코드**:
| 코드 | 의미 |
|---|---|
| 200 | OK |
| 400 | Bad Request (입력 검증 실패) |
| 404 | Not Found (부지 없음) |
| 500 | Internal Server Error |
| 503 | Service Unavailable (헬스 체크 실패) |

> **전체 API 문서**: `docs/API.md` (691줄, 요청/읝답 예시 + 성능 지표 포함)

---

## 📎 첨부 문서 목록

| 문서 | 경로 | 줄 수 | 설명 |
|---|---|---|---|
| README.md | `/` | 299 | 프로젝트 개요 |
| API.md | `docs/` | 691 | API 명세서 (12개 엔드포인트) |
| ERD.md | `docs/` | 273 | ERD 상세 |
| DEPLOYMENT.md | `docs/` | 374 | 배포 가이드 |
| SCHEDULE.md | `docs/` | 222 | 5일 일정 |
| DEMO-SCRIPT.md | `docs/` | 267 | 데모 대본 |
| QA-RESPONSE.md | `docs/` | 196 | Q&A 대응 (22가지 질문) |
| prompt-history.md | `docs/` | 332 | 프롬프트 히스토리 |

---

이대로 노션에 붙여넣으시면 됩니다. 다음으로 필요하시면:

- **A**: 발표 PPT 10~12장 제작
- **B**: 데모 영상 90초 촬영 가이드
- **C**: GitHub 레포지토리 생성 + 코드 푸시 가이드
- **D**: Vercel 배포 (실제 데모 URL 확보)
- **E**: ERD Cloud / Swagger 실제 설정 가이드

어떤 것을 도와드릴까요?