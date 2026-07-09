-- GreenSpot 논리 스키마 (MySQL 스타일 DDL 참고)
-- 최종 갱신: 2026-07-09
--
-- 주의:
-- 1) 개발 기본 DB는 SQLite (`sqlite+aiosqlite:///./greenspot.db`).
--    테이블명은 구현에서 snake_case 복수형 (users, parcels, bookmarks …).
-- 2) 본 문서는 명세·마이그레이션 참고용 camelCase 단일 테이블명을 유지한다.
-- 3) **라이브 부지 `VW-{pnu}`** 는 parcels 행 없이 동작한다.
--    Bookmark / Share 의 parcelId 는 구현상 **Parcel FK 없음** (스냅샷).
-- 4) Scenario 는 DB Parcel 에만 FK. 라이브 시뮬 결과는 저장하지 않는다.
--
-- 구현 모델: app/models/models.py
-- API: docs/api.md

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ==================== User ====================

-- 사용자 유형: 회원만 테이블 저장. 관리자 role 없음.
-- 구현(SQLite): users 테이블에 role 컬럼 없음 (email + passwordHash 만).
CREATE TABLE IF NOT EXISTS `User` (
  `id` VARCHAR(30) NOT NULL,
  `email` VARCHAR(255) NOT NULL,
  `name` VARCHAR(100) NULL,
  `passwordHash` VARCHAR(255) NOT NULL,
  `createdAt` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updatedAt` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==================== Parcel ====================

CREATE TABLE IF NOT EXISTS `Parcel` (
  `id` VARCHAR(30) NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `district` VARCHAR(100) NOT NULL,
  `neighborhood` VARCHAR(100) NOT NULL,
  `lat` DOUBLE NOT NULL,
  `lng` DOUBLE NOT NULL,
  `areaSqm` DOUBLE NOT NULL,
  -- parcelType: VACANT_LOT/ROOFTOP/UNUSED_LAND/ABANDONED/BROWNFIELD (UI 유형)
  -- 지목 상세(MIXED/FOREST 등)는 API 응답 landCategory 로 제공 (DB 컬럼 선택 사항)
  `parcelType` VARCHAR(50) NOT NULL,
  -- ownership: PUBLIC/PRIVATE/UNKNOWN (VWorld 소유구분 정규화)
  `ownership` VARCHAR(50) NOT NULL,
  -- soilType: LOAM/CLAY/SAND/ROCKY/UNKNOWN (농촌진흥청 표토토성 정규화)
  `soilType` VARCHAR(50) NOT NULL,
  `elevationM` DOUBLE NOT NULL,
  `slopeDegree` DOUBLE NOT NULL,
  `solarIrradiance` DOUBLE NOT NULL,
  `monthlyIrradiance` JSON NOT NULL COMMENT '월별 일사량 배열',
  `sunlightHours` DOUBLE NOT NULL,
  `heatIsland` DOUBLE NOT NULL,
  `surfaceTempSummer` DOUBLE NOT NULL,
  `airQuality` DOUBLE NOT NULL,
  -- 사회·접근성: API 라이브 응답에서는 null 가능(가짜 0 금지).
  -- nearbyHouseholds 는 KOSIS 자치구 총가구로 채울 수 있음.
  -- schools/hospitals/parks/subway 는 미연동(null). DB 컬럼은 하위 호환 유지.
  `nearbyHouseholds` INT NOT NULL DEFAULT 0,
  `pedestrianFlow` INT NOT NULL DEFAULT 0,
  `nearbySchools` INT NOT NULL DEFAULT 0,
  `nearbyHospitals` INT NOT NULL DEFAULT 0,
  `nearbyParks` INT NOT NULL DEFAULT 0,
  `nearbySubwayStations` INT NOT NULL DEFAULT 0,

  -- roadAdjacent: VWorld 토지특성 접면도로 가능. water/electricity 는 추정.
  `roadAdjacent` BOOLEAN NOT NULL DEFAULT FALSE,
  `waterAccess` BOOLEAN NOT NULL DEFAULT FALSE,
  `electricityAccess` BOOLEAN NOT NULL DEFAULT TRUE,

  -- 규제 요약 캐시. 원천은 ParcelRegulation.
  `regulations` JSON NULL COMMENT '규제 정보 배열 예: [{"code":"GREEN_BELT","severity":"restricted"}]',
  `regulationsUpdatedAt` DATETIME NULL,

  -- 수목 식재 가능성 요약 캐시. 원천은 ParcelScore.sumokFeasibilitySnapshot.
  `sumokFeasibility` JSON NULL COMMENT '수목 식재 가능성 요약 {status, score, reason}',
  `sumokFeasibilityUpdatedAt` DATETIME NULL,

  -- KOSIS 인구·가구 통계 스냅샷 (선택 사양). 원천은 KosisStatSnapshot.
  -- 계획 문서에서는 snake_case `kosis_population_snapshot`으로 명시되어 있으나,
  -- Parcel 테이블의 기존 camelCase 컬럼 명명 관례에 따라 `kosisPopulationSnapshot`을 사용한다.
  `kosisPopulationSnapshot` JSON NULL COMMENT 'KOSIS 인구·가구 통계 스냅샷 {district, year, population, households, source, dataAvailable, createdAt}',

  -- GEE LST/열섬 분석 스냅샷 (선택 사양). 원천은 GeeLstSnapshot.
  `geeLstSnapshot` JSON NULL COMMENT 'GEE LST/열섬 분석 스냅샷 {dataset, radiusM, period, meanLstC, heatIslandIntensityC, sampleCount, dataAvailable, createdAt}',

  `estimatedAcquisitionCostWon` BIGINT NOT NULL DEFAULT 0,
  `dataSource` VARCHAR(100) NOT NULL DEFAULT 'sample',
  `confidence` DOUBLE NOT NULL DEFAULT 0.9,
  `createdAt` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updatedAt` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_parcel_district` (`district`),
  KEY `idx_parcel_neighborhood` (`neighborhood`),
  KEY `idx_parcel_type` (`parcelType`),
  KEY `idx_parcel_area` (`areaSqm`),
  KEY `idx_parcel_location` (`lat`, `lng`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- MySQL 8.0.17+ JSON multi-valued index.
-- regulations가 문자열 배열이면 사용 가능. 객체 배열이면 ParcelRegulation 인덱스를 사용하세요.
-- CREATE INDEX `idx_parcel_regulations_mvi` ON `Parcel` ((CAST(`regulations` AS CHAR(50) ARRAY)));

-- ==================== ParcelScore ====================

CREATE TABLE IF NOT EXISTS `ParcelScore` (
  `id` VARCHAR(30) NOT NULL,
  `parcelId` VARCHAR(30) NOT NULL,
  -- 구현 컬럼: tree_score (API treeScore). sumokScore 는 동의어/캐시 필드.
  `sumokScore` DOUBLE NOT NULL COMMENT '수목 식재 적합도 점수 (= treeScore)',
  `gardenScore` DOUBLE NOT NULL,
  `solarScore` DOUBLE NOT NULL,
  -- 구현 API 값은 주로 TREE/GARDEN/SOLAR. SUMOK 는 TREE 동의어.
  `topRecommendation` VARCHAR(20) NOT NULL COMMENT 'TREE(SUMOK), GARDEN, SOLAR, MIXED, RESTRICTED',
  `uncertainty` DOUBLE NOT NULL,
  `scoreBreakdown` JSON NOT NULL COMMENT '규제 적용 전/후 점수 및 페널티 내역',

  -- 수목 식재 가능성 판단 결과
  `sumokFeasibilitySnapshot` JSON NULL COMMENT '{status, score, reason, blockingRegulations, warningRegulations, requiredChecks, confidence}',

  -- 점수 재현성
  `isLatest` BOOLEAN NOT NULL DEFAULT FALSE COMMENT '최신 점수 여부',
  `algorithmVersion` VARCHAR(50) NULL COMMENT '점수 계산 알고리즘 버전',
  `regulationRulesetVersion` VARCHAR(50) NULL COMMENT '규제 페널티 룰셋 버전',
  `regulationsSnapshot` JSON NULL COMMENT '계산 당시 규제 정보 스냅샷',
  `inputSnapshot` JSON NULL COMMENT '계산에 사용된 입력 데이터 스냅샷',

  -- MySQL은 partial unique index가 없어 최신 점수 유일성 보장을 위한 generated column 사용
  `latestParcelId` VARCHAR(30) GENERATED ALWAYS AS (CASE WHEN `isLatest` THEN `parcelId` ELSE NULL END) STORED,

  `computedAt` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_parcelscore_parcelId` (`parcelId`),
  KEY `idx_parcelscore_isLatest` (`parcelId`, `isLatest`),
  KEY `idx_parcelscore_sumokScore` (`sumokScore`),
  KEY `idx_parcelscore_topRecommendation` (`topRecommendation`),
  UNIQUE KEY `uk_parcelscore_one_latest` (`latestParcelId`),
  CONSTRAINT `fk_parcelscore_parcel` FOREIGN KEY (`parcelId`) REFERENCES `Parcel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==================== Bookmark ====================
-- 구현(SQLAlchemy): parcel_id 에 Parcel FK 없음 → VW-* 스냅샷 저장 가능.
-- MySQL 운영에서 FK를 두려면 시드 Parcel 만 북마크하거나, 라이브 행을 먼저 upsert 해야 한다.
-- 권장: FK 없이 스냅샷 컬럼으로 조회 (현재 구현과 동일).

CREATE TABLE IF NOT EXISTS `Bookmark` (
  `id` VARCHAR(30) NOT NULL,
  `userId` VARCHAR(30) NOT NULL,
  -- DB 시드 ID 또는 라이브 `VW-{pnu}`. Parcel 테이블에 없을 수 있음.
  `parcelId` VARCHAR(30) NOT NULL,

  -- 조회 최적화용 스냅샷 (라이브 필지 필수)
  `parcelName` VARCHAR(255) NOT NULL,
  `district` VARCHAR(100) NOT NULL,
  `topRecommendation` VARCHAR(20) NOT NULL COMMENT 'TREE/GARDEN/SOLAR/NONE',
  `topScore` DOUBLE NOT NULL,
  -- 아래 두 컬럼은 확장 여지. 현재 SQLite 모델에는 미포함.
  `sumokScore` DOUBLE NULL,
  `sumokFeasibilityStatus` VARCHAR(20) NULL,

  `createdAt` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_bookmark_user_parcel` (`userId`, `parcelId`),
  KEY `idx_bookmark_userId` (`userId`),
  KEY `idx_bookmark_parcelId` (`parcelId`),
  CONSTRAINT `fk_bookmark_user` FOREIGN KEY (`userId`) REFERENCES `User` (`id`) ON DELETE CASCADE
  -- 의도적으로 Parcel FK 없음 (라이브 VW-* 지원)
  -- CONSTRAINT `fk_bookmark_parcel` FOREIGN KEY (`parcelId`) REFERENCES `Parcel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==================== Share ====================
-- 공유 링크. parcelId 는 VW-* 가능. Parcel FK 없음.
-- 구현 테이블: shares (share_id unique)

CREATE TABLE IF NOT EXISTS `Share` (
  `id` VARCHAR(30) NOT NULL,
  `shareId` VARCHAR(50) NOT NULL COMMENT '공개 토큰',
  `parcelId` VARCHAR(30) NOT NULL COMMENT '시드 ID 또는 VW-{pnu}',
  `createdAt` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_share_shareId` (`shareId`),
  KEY `idx_share_parcelId` (`parcelId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==================== RefreshToken / UserPreference (구현 있음) ====================
-- SQLite: refresh_tokens, user_preferences
-- 명세 DDL 생략 가능. 구현 모델 참고.

-- ==================== Scenario ====================

-- 시나리오: DB에 존재하는 Parcel 에만 저장한다.
-- 라이브 부지(VW-{pnu}) 시뮬레이션은 API 계산만 하고 이 테이블에 insert 하지 않는다.
-- 시나리오 타입: PLANT_TREES / CREATE_GARDEN / INSTALL_SOLAR
-- (요청 별칭 TREE/SUMOK, GARDEN, SOLAR → 위 정규 타입으로 저장)
CREATE TABLE IF NOT EXISTS `Scenario` (
  `id` VARCHAR(30) NOT NULL,
  `parcelId` VARCHAR(30) NOT NULL,
  `scenarioType` VARCHAR(50) NOT NULL COMMENT 'PLANT_TREES / CREATE_GARDEN / INSTALL_SOLAR',
  `quantity` INT NOT NULL,
  `effects` JSON NOT NULL COMMENT '시나리오 효과 JSON',
  `aiExplanation` TEXT NULL,
  `createdAt` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_scenario_parcelId` (`parcelId`),
  KEY `idx_scenario_type` (`scenarioType`),
  CONSTRAINT `fk_scenario_parcel` FOREIGN KEY (`parcelId`) REFERENCES `Parcel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==================== AgentQuery ====================

CREATE TABLE IF NOT EXISTS `AgentQuery` (
  `id` VARCHAR(30) NOT NULL,
  `userId` VARCHAR(30) NULL,
  `query` TEXT NOT NULL,
  `criteria` JSON NOT NULL COMMENT 'AI가 해석한 검색 조건. sumokFeasibility/규제 제외 조건 포함 가능',
  `resultCount` INT NOT NULL,
  `summary` TEXT NOT NULL,
  `source` VARCHAR(20) NOT NULL DEFAULT 'ai',
  `createdAt` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_agentquery_userId` (`userId`),
  KEY `idx_agentquery_createdAt` (`createdAt`),
  CONSTRAINT `fk_agentquery_user` FOREIGN KEY (`userId`) REFERENCES `User` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==================== ParcelRegulation ====================
-- VWorld WFS 레이어 기반 규제 정보

CREATE TABLE IF NOT EXISTS `ParcelRegulation` (
  `id` VARCHAR(30) NOT NULL,
  `parcelId` VARCHAR(30) NOT NULL,
  `regulationType` VARCHAR(50) NOT NULL COMMENT 'GREEN_BELT, URBAN_NATURE_PARK, NATURAL_CONSERVATION, PROTECTION_DISTRICT 등',
  `regulationName` VARCHAR(100) NULL,

  -- F-03 점수 페널티/0점 처리 기준
  `severity` VARCHAR(20) NOT NULL DEFAULT 'warning' COMMENT 'info, warning, restricted, prohibited',
  `affectedUses` JSON NULL COMMENT '예: ["sumok", "garden", "solar"] 또는 ["all"]',
  `penaltyType` VARCHAR(20) NOT NULL DEFAULT 'none' COMMENT 'none, subtract, multiplier, zero',
  `penaltyValue` DOUBLE NULL COMMENT 'subtract 점수 차감값 또는 multiplier 배율',
  `legalBasis` TEXT NULL,
  `description` TEXT NULL,

  -- VWorld 메타데이터
  `source` VARCHAR(50) NULL DEFAULT 'VWorld' COMMENT 'VWorld 등',
  `sourceLayer` VARCHAR(100) NULL COMMENT '개발제한구역, 도시자연공원구역 등',
  `typename` VARCHAR(50) NULL COMMENT 'lt_c_ud801 등',
  `rawData` JSON NULL COMMENT 'VWorld 원본 속성',

  `effectiveDate` DATE NULL,
  `createdAt` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updatedAt` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_parcel_regulation` (`parcelId`, `regulationType`, `typename`),
  KEY `idx_parcel_regulation_parcelId` (`parcelId`),
  KEY `idx_parcel_regulation_type` (`regulationType`),
  KEY `idx_parcel_regulation_severity` (`severity`),
  KEY `idx_parcel_regulation_typename` (`typename`),
  CONSTRAINT `fk_parcelregulation_parcel` FOREIGN KEY (`parcelId`) REFERENCES `Parcel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==================== GeeLstSnapshot (선택 사양) ====================
-- Google Earth Engine LST / 열섬 분석 결과를 부지 단위로 저장하는 선택적 스냅샷 테이블.

CREATE TABLE IF NOT EXISTS `GeeLstSnapshot` (
  `id` VARCHAR(30) NOT NULL,
  `parcelId` VARCHAR(30) NOT NULL,
  `dataset` VARCHAR(20) NOT NULL COMMENT 'modis 또는 landsat',
  `radiusM` INT NOT NULL COMMENT '분석 반경(m)',
  `innerRadiusM` INT NULL COMMENT '열섬 분석 내부 반경(m). LST 조회 시 NULL',
  `periodStart` DATE NOT NULL COMMENT '분석 시작일',
  `periodEnd` DATE NOT NULL COMMENT '분석 종료일',
  `meanLstC` DOUBLE NULL COMMENT '평균 지표면 온도(℃)',
  `maxLstC` DOUBLE NULL,
  `minLstC` DOUBLE NULL,
  `heatIslandIntensityC` DOUBLE NULL COMMENT '열섬 강도(℃)',
  `sampleCount` INT NOT NULL DEFAULT 0,
  `source` VARCHAR(50) NOT NULL DEFAULT 'gee',
  `dataAvailable` BOOLEAN NOT NULL DEFAULT FALSE COMMENT 'GEE 데이터 확보 여부',
  `rawData` JSON NULL COMMENT 'GEE 분석 원본/메타데이터',
  `createdAt` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_geelstsnapshot_parcelId` (`parcelId`),
  KEY `idx_geelstsnapshot_period` (`periodStart`, `periodEnd`),
  CONSTRAINT `fk_geelstsnapshot_parcel` FOREIGN KEY (`parcelId`) REFERENCES `Parcel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==================== KosisStatSnapshot (선택 사양) ====================
-- KOSIS Open API 연동 결과를 부지 단위로 저장하는 선택적 스냅샷 테이블.

CREATE TABLE IF NOT EXISTS `KosisStatSnapshot` (
  `id` VARCHAR(30) NOT NULL,
  `parcelId` VARCHAR(30) NOT NULL,
  `district` VARCHAR(100) NOT NULL COMMENT '서울 자치구',
  `year` INT NOT NULL COMMENT '통계 연도',
  `population` BIGINT NULL COMMENT '총인구',
  `households` BIGINT NULL COMMENT '총가구',
  `source` VARCHAR(50) NOT NULL DEFAULT 'kosis',
  `dataAvailable` BOOLEAN NOT NULL DEFAULT FALSE COMMENT 'KOSIS 응답 성공 여부',
  `rawData` JSON NULL COMMENT 'KOSIS API 원본 응답',
  `createdAt` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_kosisstatsnapshot_parcelId` (`parcelId`),
  KEY `idx_kosisstatsnapshot_district_year` (`district`, `year`),
  CONSTRAINT `fk_kosisstatsnapshot_parcel` FOREIGN KEY (`parcelId`) REFERENCES `Parcel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;

-- ==================== 구현(SQLite) 테이블 매핑 ====================
-- | 본 문서 (논리)     | SQLAlchemy __tablename__ |
-- | User               | users                    |
-- | Parcel             | parcels                  |
-- | ParcelScore        | parcel_scores            |
-- | ParcelRegulation   | parcel_regulations       |
-- | Scenario           | scenarios                |
-- | AgentQuery         | agent_queries            |
-- | Bookmark           | bookmarks                |
-- | Share              | shares                   |
-- | (RefreshToken)     | refresh_tokens           |
-- | (UserPreference)   | user_preferences         |
--
-- 라이브 캐시: DB 테이블 아님. 프로세스 메모리 TTL (_LIVE_CACHE).

