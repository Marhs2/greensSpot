네, 로그인 기능이 추가된 최신 상태를 반영한 노션 제출용 템플릿을 보내드립니다.

---

# GreenSpot v2 — 노션 제출용 템플릿 (로그인 기능 포함 최종본)

## Team Github Repository

> **GitHub**: https://github.com/[팀이름]/greenspot-v2
>
> **데모 링크**: https://preview-[bot-id].space-z.ai/greenspot
>
> **브랜치 전략**: `main` (배포용) / `develop` (개발통합)
>
> **PR 규칙**: 담당자 1명 이상 리뷰 후 merge
> - 1학년: 데이터 엔지니어링 (VWorld/KOSIS 연동, DB)
> - 2학년: 풀스택 개발 (API, UI, 인증, 반응형)
> - 3학년: AI/발표 (LLM 프롬프트, 할루 방어, 발표)

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

#### 핵심 차별성 6가지

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

**5. 사용자 인증 + 개인화 북마크**
- NextAuth 기반 회원가입/로그인 (이메일/비밀번호)
- bcrypt 비밀번호 해싱 (보안)
- 로그인한 사용자별 북마크 DB 저장 (localStorage 대신 영구 저장)
- 검색 기록도 사용자별 추적

**6. 실사용 기능 8가지**
- 북마크 (DB 영구 저장, 사용자별)
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

### 📋 기능 개요 (18개)

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

#### 인증 기능 (3개)

| 기능 ID | 기능명 | 우선순위 | 담당 | 상태 |
|---|---|---|---|---|
| F-09 | 회원가입 (이메일/비밀번호) | High | 2학년 | ✅ |
| F-10 | 로그인/로그아웃 (NextAuth) | High | 2학년 | ✅ |
| F-11 | 사용자별 북마크 (DB 저장) | High | 2학년 | ✅ |

#### 추가 기능 (7개)

| 기능 ID | 기능명 | 우선순위 | 담당 | 상태 |
|---|---|---|---|---|
| F-12 | 통계 분석 대시보드 | Medium | 2학년 | ✅ |
| F-13 | CSV 내보내기 (Excel 호환) | Medium | 2학년 | ✅ |
| F-14 | 부지 공유 링크 (URL 파라미터) | Medium | 2학년 | ✅ |
| F-15 | 다크모드 토글 | Low | 2학년 | ✅ |
| F-16 | 검색 히스토리 조회 | Medium | 3학년 | ✅ |
| F-17 | 인기 검색어 / 트렌딩 | Medium | 3학년 | ✅ |
| F-18 | 헬스 체크 API | High | 2학년 | ✅ |

---

### F-09: 회원가입 (이메일/비밀번호)

**엔드포인트**: `POST /api/auth/register`

**요청 본문**:
```json
{
  "name": "홍길동",
  "email": "user@example.com",
  "password": "password123"
}
```

**검증 규칙**:
- name: 2~50자
- email: 올바른 이메일 형식
- password: 최소 6자, 최대 100자
- 중복 이메일 체크 (409 Conflict)

**응답 (201 Created)**:
```json
{
  "message": "회원가입이 완료되었습니다.",
  "user": {
    "id": "cmr7ut6i20000tmt3toxeke49",
    "name": "홍길동",
    "email": "user@example.com",
    "role": "user",
    "createdAt": "2026-07-05T13:55:46.346Z"
  }
}
```

**보안**:
- 비밀번호 bcrypt 해싱 (10회 salt rounds)
- 비밀번호 평문 저장 금지
- SQL 인젝션 방지 (Prisma 파라미터화 쿼리)

**상태 코드**:
- 201: 성공
- 400: 잘못된 입력 (검증 실패)
- 409: 중복 이메일
- 500: 서버 오류

---

### F-10: 로그인/로그아웃 (NextAuth)

**엔드포인트**: `POST /api/auth/callback/credentials` (NextAuth 내부)

**요청 본문** (NextAuth signIn):
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**인증 흐름**:
1. 이메일로 사용자 조회
2. bcrypt 비밀번호 검증
3. JWT 토큰 생성 (30일 유효)
4. 세션 쿠키 설정 (HttpOnly, Secure)

**세션 정보**:
```typescript
{
  user: {
    id: string;
    name: string;
    email: string;
    role: string; // "user" | "admin"
  },
  expires: string; // ISO timestamp
}
```

**로그아웃**: `signOut({ callbackUrl: '/greenspot' })`

**페이지**:
- 로그인: `/login`
- 회원가입: `/register`
- 로그인 없이 둘러보기 가능 (공개 페이지)

---

### F-11: 사용자별 북마크 (DB 저장)

**엔드포인트**:
- `GET /api/bookmarks` — 북마크 목록 조회
- `POST /api/bookmarks` — 북마크 추가
- `DELETE /api/bookmarks?parcelId=xxx` — 북마크 삭제

**인증**: 모든 요청에 로그인 필요 (401 if not authenticated)

**POST 요청 본문**:
```json
{
  "parcelId": "DD-001",
  "parcelName": "회기동 빈터 A",
  "district": "동대문구",
  "topRecommendation": "GARDEN",
  "topScore": 90
}
```

**GET 응답 (200)**:
```json
{
  "bookmarks": [
    {
      "id": "cuid123",
      "userId": "user-cuid",
      "parcelId": "DD-001",
      "parcelName": "회기동 빈터 A",
      "district": "동대문구",
      "topRecommendation": "GARDEN",
      "topScore": 90,
      "createdAt": "2026-07-05T14:00:00.000Z"
    }
  ],
  "total": 1
}
```

**특징**:
- 사용자별 DB 저장 (localStorage 대신 영구 저장)
- 중복 방지 (`@@unique([userId, parcelId])`)
- upsert 패턴 (이미 있으면 업데이트)

---

### F-01 ~ F-08: 메인 기능 (이전과 동일)

<details>
<summary>펼쳐서 보기</summary>

#### F-01: 부지 목록 조회
- `GET /api/gs/parcels?district={자치구}&type={부지유형}`
- 23개 부지 + 통계 대시보드 + 점수순 정렬

#### F-02: 부지 상세 조회
- `GET /api/gs/parcels/{id}`
- 25개 필드 + 3개 점수 + 불확실성

#### F-03: 3중 용도 점수 산출
- 가중치 합 1.0 (열섬 0.30, 보행자 0.20, 일조 0.10, 면적 0.15, 유형 0.10, 도로 0.10, 규제 0.05)
- 규제 패널티: GREEN_BELT 0.50, HISTORICAL 0.70, FLOOD_ZONE 0.85
- 불확실성: `(1 - confidence) × 10 + 3`

#### F-04: AI 자연어 부지 검색 에이전트 ⭐
- `POST /api/gs/agent`
- 3단계 할루 방어 (조건 JSON → TypeScript 검색 → AI 요약)
- 매핑 규칙: "빈터"→VACANT_LOT, "식수"→TREE 등

#### F-05: AI 점수 설명 (4섹션)
- `POST /api/gs/parcels/{id}/explain`
- 📍 부지 요약 / 🎯 추천 이유 / 💡 대안 검토 / ⚠️ 한계점

#### F-06: 시나리오 시뮬레이션
- `POST /api/gs/parcels/{id}/simulate`
- USDA i-Tree / 한국에너지공단 / 서울연구원 정적 계수
- 월별 발전량, 투자회수기간

#### F-07: 부지 비교
- `POST /api/gs/compare`
- 2~3개 부지, 5개 지표 랭킹

#### F-08: 리포트 내보내기
- `POST /api/gs/report` (Markdown / JSON)

</details>

---

### F-12 ~ F-18: 추가 기능

<details>
<summary>펼쳐서 보기</summary>

#### F-12: 통계 분석 대시보드
- 페이지: `/greenspot/stats`
- API: `GET /api/gs/stats`
- 자치구별 BarChart, 추천 분포 PieChart, 부지유형별 BarChart
- 인기 검색 키워드, 최근 검색 기록

#### F-13: CSV 내보내기
- `GET /api/gs/export`
- Excel 호환 (UTF-8 BOM), 22개 컬럼

#### F-14: 부지 공유 링크
- `/greenspot?parcel=DD-001` URL 파라미터
- 클립보드 복사 + 토스트 알림

#### F-15: 다크모드 토글
- 헤더 Moon/Sun 버튼
- `document.documentElement.classList` 적용

#### F-16: 검색 히스토리
- `GET /api/gs/history?limit={N}`
- AI/fallback 소스 표시

#### F-17: 인기 검색어
- `GET /api/gs/trending`
- 키워드 빈도, 자치구별 검색 빈도

#### F-18: 헬스 체크
- `GET /api/gs/health`
- DB 연결, 통계, 환경 변수 상태

</details>

---

## 화면 설계도

> **Figma 링크**: [작성 예정 - https://figma.com/...]
>
> **대체 자료**: 스크린샷 첨부

### 화면 목록 (11개)

| 화면 ID | 화면명 | 설명 | 스크린샷 |
|---|---|---|---|
| S-01 | 메인 대시보드 | 통계 카드 + AI 에이전트 + 부지 목록 + 상세 패널 | `/download/greenspot-v2-final.png` |
| S-02 | AI 에이전트 패널 | 자연어 검색 + 추천 질문 + 결과 | (S-01 상단) |
| S-03 | 부지 상세 - 개요 탭 | StatTile 그리드 + 인프라 현황 | (상세 패널) |
| S-04 | 부지 상세 - 점수 탭 | 1순위 Hero + 레이더 차트 | (상세 패널) |
| S-05 | 부지 상세 - AI 분석 탭 | 4섹션 마크다운 | (상세 패널) |
| S-06 | 부지 상세 - 시뮬레이션 탭 | 3개 시나리오 비교 + 월별 차트 | (상세 패널) |
| S-07 | 비교 모달 | 2~3개 부지 비교 + 랭킹 | (비교 버튼 클릭) |
| S-08 | 통계 대시보드 | 자치구별 차트 + 추천 분포 + 트렌드 | `/download/greenspot-v2-stats.png` |
| S-09 | **로그인 페이지** | 이메일/비밀번호 입력 | `/login` |
| S-10 | **회원가입 페이지** | 이름/이메일/비밀번호 입력 | `/register` |
| S-11 | 모바일 반응형 | 375px 뷰포트 | `/download/greenspot-v2.png` |

### 와이어프레임 (메인 대시보드)

```
┌─────────────────────────────────────────────────────────────────┐
│ Header: GreenSpot v2 [NEW] | 통계 | CSV | 북마크 | 🌙 | SafeSpot | [👤 사용자] │
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

### 로그인 페이지 와이어프레임

```
┌─────────────────────────────────────┐
│            🌿 (로고)                 │
│          로그인                      │
│   GreenSpot v2에 로그인하세요        │
├─────────────────────────────────────┤
│  이메일                             │
│  [✉ user@example.com           ]    │
│                                     │
│  비밀번호                           │
│  [🔒 ••••••••                   ]    │
│                                     │
│  [      로그인      ]               │
│                                     │
│  계정이 없으신가요? 회원가입         │
│  ─────────────────────────          │
│  [← 로그인 없이 둘러보기]            │
└─────────────────────────────────────┘
```

### 화면 흐름도

```
[메인 대시보드]
     │
     ├─ AI 에이전트 질문 → [검색 결과] → 부지 클릭 → [상세 패널]
     │                                              │
     ├─ ☆ 북마크 → (로그인 필요) → [DB 저장] → [북마크 패널]
     │                                              │
     ├─ + 비교 체크 (2~3개) → [비교 버튼] → [비교 모달]
     │                                              │
     ├─ 헤더 "통계" 버튼 → [통계 대시보드]
     │                                              │
     ├─ 헤더 [👤 사용자] → [드롭다운] → 로그아웃
     │                                              │
     ├─ 헤더 "로그인" 버튼 → [로그인 페이지] → 성공 → [대시보드]
     │                                              │
     ├─ 헤더 "회원가입" 버튼 → [회원가입 페이지] → 성공 → 자동 로그인
     │                                              │
     └─ 상세 패널 "공유" 버튼 → [클립보드 복사 + 토스트]
```

---

## ERD

> **ERD Cloud URL**: [작성 예정 - https://www.erdcloud.com/...]
>
> **대체: Prisma Schema 기반 ERD 다이어그램** (아래)

### 엔티티 관계도 (6개 모델)

```
┌─────────────────────────────────────────────────────┐
│                    User                              │
│                  (사용자 - 인증)                     │
├─────────────────────────────────────────────────────┤
│  id (PK) ◄──────────────────────────────────┐       │
│  email (unique)                             │       │
│  name                                       │       │
│  passwordHash (bcrypt)                      │       │
│  role (user | admin)                        │       │
│  createdAt, updatedAt                       │       │
└─────────────────────────────────────────────┘       │
        │                                              │
        │ 1:N                                          │
        ↓                                              │
┌─────────────────────────────────────────────────────┐
│                   Bookmark                           │
│              (북마크 - 사용자별)                     │
├─────────────────────────────────────────────────────┤
│  id (PK)                                            │
│  userId (FK) ───────────────────────────────────────┘
│  parcelId                                          │
│  parcelName, district                              │
│  topRecommendation, topScore                       │
│  createdAt                                         │
│  @@unique([userId, parcelId])                      │
└─────────────────────────────────────────────────────┘

        │ 1:N (User → AgentQuery)
        ↓
┌─────────────────────────────────────────────────────┐
│                  AgentQuery                         │
│              (AI 검색 기록)                         │
├─────────────────────────────────────────────────────┤
│  id (PK)                                            │
│  userId (FK, nullable) ──→ User.id                  │
│  query (사용자 자연어 질문)                         │
│  criteria (JSON - AI 생성 검색 조건)                │
│  resultCount                                        │
│  summary (AI 요약)                                  │
│  source (ai/fallback)                               │
│  createdAt                                          │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                    Parcel                           │
│                  (부지 - 메인)                       │
├─────────────────────────────────────────────────────┤
│  id (PK)                                            │
│  name, district, neighborhood                       │
│  lat, lng, areaSqm, parcelType                      │
│  ownership, soilType                                │
│  solarIrradiance, monthlyIrradiance                 │
│  sunlightHours, heatIsland                          │
│  surfaceTempSummer, airQuality                      │
│  nearbyHouseholds, pedestrianFlow                   │
│  roadAdjacent, waterAccess                          │
│  electricityAccess                                  │
│  nearbySchools, nearbyHospitals                     │
│  nearbyParks, nearbySubwayStations                  │
│  regulatoryRestriction                              │
│  confidence, dataSource                             │
│  createdAt, updatedAt                               │
└─────────────────────────────────────────────────────┘
        │ 1:1
        ↓
┌─────────────────────────────────────────────────────┐
│                  ParcelScore                        │
│                  (부지 점수)                         │
├─────────────────────────────────────────────────────┤
│  id (PK)                                            │
│  parcelId (FK, unique) ──→ Parcel.id                │
│  treeScore, gardenScore, solarScore                │
│  topRecommendation (TREE/GARDEN/SOLAR)             │
│  uncertainty (±점수)                                │
│  scoreBreakdown (JSON)                             │
│  computedAt                                        │
└─────────────────────────────────────────────────────┘

        │ 1:N (Parcel → Scenario)
        ↓
┌─────────────────────────────────────────────────────┐
│                   Scenario                          │
│                (시나리오 시뮬레이션)                 │
├─────────────────────────────────────────────────────┤
│  id (PK)                                            │
│  parcelId (FK) ──→ Parcel.id                        │
│  scenarioType                                       │
│  quantity                                           │
│  effects (JSON)                                     │
│  aiExplanation                                      │
│  createdAt                                          │
└─────────────────────────────────────────────────────┘
```

### 관계 요약

| 관계 | 카디널리티 | 설명 |
|---|---|---|
| User → Bookmark | 1:N | 사용자 1명당 북마크 N개 |
| User → AgentQuery | 1:N | 사용자 1명당 검색 기록 N개 (nullable) |
| Parcel → ParcelScore | 1:1 | 부지 1개당 점수 1개 |
| Parcel → Scenario | 1:N | 부지 1개당 시나리오 N개 |

### Prisma Schema (전체)

```prisma
// Prisma Schema - GreenSpot v2
// 6개 모델: User, Bookmark, Parcel, ParcelScore, Scenario, AgentQuery

generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "sqlite"
  url      = env("DATABASE_URL")
}

// 사용자 (인증)
model User {
  id            String   @id @default(cuid())
  email         String   @unique
  name          String
  passwordHash  String
  role          String   @default("user") // user | admin
  createdAt     DateTime @default(now())
  updatedAt     DateTime @updatedAt

  bookmarks     Bookmark[]
  agentQueries  AgentQuery[]
}

// 북마크 (사용자별 DB 저장)
model Bookmark {
  id            String   @id @default(cuid())
  userId        String
  user          User     @relation(fields: [userId], references: [id], onDelete: Cascade)
  parcelId      String
  parcelName    String
  district      String
  topRecommendation String
  topScore      Int
  createdAt     DateTime @default(now())

  @@unique([userId, parcelId])
  @@index([userId])
}

model Parcel {
  id              String   @id @unique
  name            String
  district        String
  neighborhood    String
  lat             Float
  lng             Float
  areaSqm         Float
  parcelType      String
  ownership       String
  soilType        String
  elevationM      Float
  slopeDegree     Float
  solarIrradiance     Float
  monthlyIrradiance   String
  sunlightHours       Float
  heatIsland          Float
  surfaceTempSummer   Float
  airQuality          Float
  nearbyHouseholds    Int
  pedestrianFlow      Int
  roadAdjacent        Boolean @default(true)
  waterAccess         Boolean @default(true)
  electricityAccess   Boolean @default(true)
  nearbySchools       Int     @default(0)
  nearbyHospitals     Int     @default(0)
  nearbyParks         Int     @default(0)
  nearbySubwayStations Int    @default(0)
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
  scoreBreakdown    String
  computedAt        DateTime @default(now())
}

model Scenario {
  id            String   @id @default(cuid())
  parcelId      String
  parcel        Parcel   @relation(fields: [parcelId], references: [id], onDelete: Cascade)
  scenarioType  String
  quantity      Int
  effects       String
  aiExplanation String?
  createdAt     DateTime @default(now())
}

model AgentQuery {
  id          String   @id @default(cuid())
  userId      String?
  user        User?    @relation(fields: [userId], references: [id], onDelete: SetNull)
  query       String
  criteria    String
  resultCount Int
  summary     String
  source      String   @default("ai")
  createdAt   DateTime @default(now())
}
```

> **전체 ERD 문서**: `docs/ERD.md` (273줄)

---

## API Docs

> **Swagger URL**: 현재 Swagger 미사용 (Next.js API Routes 기반)
>
> **대체: API 명세서 문서** (`docs/API.md`)

### API 엔드포인트 목록 (15개)

| Method | Endpoint | 설명 | 인증 | 응답 시간 |
|---|---|---|---|---|
| GET | `/api/gs/health` | 헬스 체크 | 불필요 | ~4ms |
| GET | `/api/gs/parcels` | 부지 목록 조회 | 불필요 | ~50ms |
| GET | `/api/gs/parcels/{id}` | 부지 상세 조회 | 불필요 | ~30ms |
| POST | `/api/gs/agent` | AI 자연어 부지 검색 | 불필요 | ~3-8초 |
| POST | `/api/gs/parcels/{id}/explain` | AI 점수 설명 생성 | 불필요 | ~5-10초 |
| POST | `/api/gs/parcels/{id}/simulate` | 시나리오 시뮬레이션 | 불필요 | ~2ms |
| POST | `/api/gs/compare` | 부지 비교 | 불필요 | ~10ms |
| POST | `/api/gs/report` | 리포트 내보내기 (MD/JSON) | 불필요 | ~5ms |
| GET | `/api/gs/export` | CSV 내보내기 | 불필요 | ~128ms |
| GET | `/api/gs/stats` | 통계 분석 | 불필요 | ~200ms |
| GET | `/api/gs/trending` | 인기 검색어 | 불필요 | ~140ms |
| GET | `/api/gs/history` | 검색 히스토리 | 불필요 | ~250ms |
| POST | `/api/auth/register` | 회원가입 | 불필요 | ~200ms |
| POST | `/api/auth/callback/credentials` | 로그인 (NextAuth) | 불필요 | ~300ms |
| GET | `/api/user` | 현재 사용자 정보 | 세션 | ~10ms |
| GET | `/api/bookmarks` | 북마크 목록 조회 | **필수** | ~20ms |
| POST | `/api/bookmarks` | 북마크 추가 | **필수** | ~30ms |
| DELETE | `/api/bookmarks?parcelId=xxx` | 북마크 삭제 | **필수** | ~20ms |

### Base URL

```
개발: http://localhost:3000
프로덕션: https://[your-domain].vercel.app
```

### 인증 API

#### 회원가입

```http
POST /api/auth/register
Content-Type: application/json

{
  "name": "홍길동",
  "email": "user@example.com",
  "password": "password123"
}
```

**응답 (201)**:
```json
{
  "message": "회원가입이 완료되었습니다.",
  "user": {
    "id": "cmr7ut6i20000tmt3toxeke49",
    "name": "홍길동",
    "email": "user@example.com",
    "role": "user",
    "createdAt": "2026-07-05T13:55:46.346Z"
  }
}
```

**상태 코드**: 201 (성공) / 400 (검증 실패) / 409 (중복 이메일)

#### 로그인 (NextAuth)

```http
POST /api/auth/callback/credentials
Content-Type: application/x-www-form-urlencoded

email=user@example.com&password=password123&csrfToken=xxx&json=true
```

**응답**: 세션 쿠키 설정 (HttpOnly, 30일 유효)

#### 현재 사용자 정보

```http
GET /api/user
Cookie: next-auth.session-token=xxx
```

**응답 (200)**:
```json
{
  "user": {
    "id": "cmr7ut6i20000tmt3toxeke49",
    "name": "홍길동",
    "email": "user@example.com",
    "role": "user"
  },
  "authenticated": true
}
```

### 북마크 API (인증 필요)

#### 북마크 목록 조회

```http
GET /api/bookmarks
Cookie: next-auth.session-token=xxx
```

**응답 (200)**:
```json
{
  "bookmarks": [
    {
      "id": "cuid123",
      "userId": "user-cuid",
      "parcelId": "DD-001",
      "parcelName": "회기동 빈터 A",
      "district": "동대문구",
      "topRecommendation": "GARDEN",
      "topScore": 90,
      "createdAt": "2026-07-05T14:00:00.000Z"
    }
  ],
  "total": 1
}
```

**상태 코드**: 200 (성공) / 401 (인증 필요)

#### 북마크 추가

```http
POST /api/bookmarks
Content-Type: application/json
Cookie: next-auth.session-token=xxx

{
  "parcelId": "DD-001",
  "parcelName": "회기동 빈터 A",
  "district": "동대문구",
  "topRecommendation": "GARDEN",
  "topScore": 90
}
```

**응답 (200)**: `{ "bookmark": {...}, "bookmarked": true }`

#### 북마크 삭제

```http
DELETE /api/bookmarks?parcelId=DD-001
Cookie: next-auth.session-token=xxx
```

**응답 (200)**: `{ "bookmarked": false }`

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
| 201 | Created (회원가입 성공) |
| 400 | Bad Request (입력 검증 실패) |
| 401 | Unauthorized (인증 필요) |
| 404 | Not Found (부지 없음) |
| 409 | Conflict (중복 이메일) |
| 500 | Internal Server Error |
| 503 | Service Unavailable (헬스 체크 실패) |

### 환경 변수

```bash
# .env.example
DATABASE_URL=file:/home/z/my-project/db/custom.db
VWORLD_API_KEY=                    # 선택
KMA_API_KEY=                       # 선택
NEXTAUTH_SECRET=your-secret-key    # 필수 (인증)
NEXTAUTH_URL=http://localhost:3000 # 필수 (콜백 URL)
NODE_ENV=development
```

---

## 📎 첨부 문서 목록

| 문서 | 경로 | 설명 |
|---|---|---|
| README.md | `/` | 프로젝트 개요 |
| API.md | `docs/` | API 명세서 (15개 엔드포인트) |
| ERD.md | `docs/` | ERD (6개 모델) |
| DEPLOYMENT.md | `docs/` | 배포 가이드 |
| SCHEDULE.md | `docs/` | 5일 일정 |
| DEMO-SCRIPT.md | `docs/` | 데모 대본 |
| QA-RESPONSE.md | `docs/` | Q&A 대응 (22가지 질문) |
| prompt-history.md | `docs/` | 프롬프트 히스토리 |

---

이대로 노션에 붙여넣으시면 됩니다. 로그인 기능(회원가입, 로그인, 로그아웃, 사용자별 북마크)이 모두 반영된 최종본입니다.

다음으로 필요하시면:
- **A**: 발표 PPT 제작
- **B**: GitHub 레포지토리 생성 가이드
- **C**: Vercel 배포 가이드
- **D**: 데모 영상 촬영 가이드

어떤 것을 도와드릴까요?