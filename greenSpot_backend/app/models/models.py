from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(30), primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    bookmarks = relationship("Bookmark", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(String(30), primary_key=True, index=True)
    user_id = Column(String(30), ForeignKey("users.id"), nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="refresh_tokens")


class Parcel(Base):
    __tablename__ = "parcels"

    id = Column(String(30), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    district = Column(String(100), nullable=False, index=True)
    neighborhood = Column(String(100), nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    area_sqm = Column(Float, nullable=False)
    parcel_type = Column(String(30), nullable=False, index=True)
    ownership = Column(String(30), nullable=False)
    soil_type = Column(String(30), nullable=False)
    solar_irradiance = Column(Float, nullable=False)
    monthly_irradiance = Column(SQLiteJSON, nullable=True)
    sunlight_hours = Column(Float, nullable=False)
    heat_island = Column(Float, nullable=False)
    surface_temp_summer = Column(Float, nullable=False)
    air_quality = Column(Float, nullable=False)
    nearby_households = Column(Integer, nullable=False)
    pedestrian_flow = Column(Integer, nullable=False)
    road_adjacent = Column(Boolean, nullable=False, default=False)
    water_access = Column(Boolean, nullable=False, default=False)
    electricity_access = Column(Boolean, nullable=False, default=False)
    nearby_schools = Column(Integer, nullable=False, default=0)
    nearby_hospitals = Column(Integer, nullable=False, default=0)
    nearby_parks = Column(Integer, nullable=False, default=0)
    nearby_subway_stations = Column(Integer, nullable=False, default=0)
    regulatory_restriction = Column(String(30), nullable=False)

    # VWorld 기반 규제 정보 배열 (명세서 F-01/F-02)
    # 예: [{"code":"GREEN_BELT","name":"개발제한구역","severity":"prohibited",...}]
    regulations = Column(SQLiteJSON, nullable=True)
    regulations_updated_at = Column(DateTime, nullable=True)

    # 수목 식재 가능성 요약 캐시 (명세서 sumokFeasibility)
    sumok_feasibility = Column(SQLiteJSON, nullable=True)
    sumok_feasibility_updated_at = Column(DateTime, nullable=True)

    confidence = Column(Float, nullable=False)

    regulations_rel = relationship(
        "ParcelRegulation", back_populates="parcel", cascade="all, delete-orphan"
    )

    scores = relationship("ParcelScore", back_populates="parcel", uselist=False, cascade="all, delete-orphan")
    scenarios = relationship("Scenario", back_populates="parcel", cascade="all, delete-orphan")


class ParcelScore(Base):
    __tablename__ = "parcel_scores"

    id = Column(String(30), primary_key=True, index=True)
    parcel_id = Column(String(30), ForeignKey("parcels.id"), nullable=False, unique=True, index=True)
    tree_score = Column(Float, nullable=False)
    garden_score = Column(Float, nullable=False)
    solar_score = Column(Float, nullable=False)
    top_recommendation = Column(String(20), nullable=False)
    uncertainty = Column(Float, nullable=False)

    # 명세서 F-03: 수목 식재 적합도 점수 (tree_score 를 기본값으로 사용)
    sumok_score = Column(Float, nullable=True)
    score_breakdown = Column(SQLiteJSON, nullable=True)

    # 수목 식재 가능성 판단 결과 (명세서 sumokFeasibility)
    sumok_feasibility_snapshot = Column(SQLiteJSON, nullable=True)
    regulations_snapshot = Column(SQLiteJSON, nullable=True)
    algorithm_version = Column(String(50), nullable=True)
    is_latest = Column(Boolean, nullable=False, default=True)

    parcel = relationship("Parcel", back_populates="scores")


class ParcelRegulation(Base):
    __tablename__ = "parcel_regulations"

    id = Column(String(30), primary_key=True, index=True)
    parcel_id = Column(String(30), ForeignKey("parcels.id"), nullable=False, index=True)

    # 명세서 F-03 규제 데이터 모델
    regulation_type = Column(String(50), nullable=False)
    regulation_name = Column(String(100), nullable=True)
    severity = Column(String(20), nullable=False, default="warning")
    affected_uses = Column(SQLiteJSON, nullable=True)
    penalty_type = Column(String(20), nullable=False, default="none")
    penalty_value = Column(Float, nullable=True)
    legal_basis = Column(Text, nullable=True)
    description = Column(Text, nullable=True)

    # VWorld 메타데이터
    source = Column(String(50), nullable=True, default="VWorld")
    source_layer = Column(String(100), nullable=True)
    typename = Column(String(50), nullable=True)
    raw_data = Column(SQLiteJSON, nullable=True)

    effective_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    parcel = relationship("Parcel", back_populates="regulations_rel")

    __table_args__ = (
        Index("ix_parcel_regulation_type", "regulation_type"),
        Index("ix_parcel_regulation_severity", "severity"),
        Index("ix_parcel_regulation_typename", "typename"),
    )


class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(String(30), primary_key=True, index=True)
    parcel_id = Column(String(30), ForeignKey("parcels.id"), nullable=False, index=True)
    scenario_type = Column(String(30), nullable=False)
    quantity = Column(Integer, nullable=False)
    effects = Column(SQLiteJSON, nullable=False)

    parcel = relationship("Parcel", back_populates="scenarios")


class AgentQuery(Base):
    __tablename__ = "agent_queries"

    id = Column(String(30), primary_key=True, index=True)
    query = Column(Text, nullable=False)
    criteria = Column(SQLiteJSON, nullable=True)
    result_count = Column(Integer, nullable=False, default=0)
    summary = Column(Text, nullable=True)
    source = Column(String(20), nullable=False, default="ai")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class Bookmark(Base):
    __tablename__ = "bookmarks"

    id = Column(String(30), primary_key=True, index=True)
    user_id = Column(String(30), ForeignKey("users.id"), nullable=False, index=True)
    parcel_id = Column(String(30), nullable=False, index=True)
    parcel_name = Column(String(255), nullable=False)
    district = Column(String(100), nullable=False)
    top_recommendation = Column(String(20), nullable=False)
    top_score = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="bookmarks")

    __table_args__ = (
        Index("ix_bookmarks_user_parcel", "user_id", "parcel_id", unique=True),
    )


class Share(Base):
    __tablename__ = "shares"

    id = Column(String(30), primary_key=True, index=True)
    share_id = Column(String(50), unique=True, nullable=False, index=True)
    parcel_id = Column(String(30), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(String(30), primary_key=True, index=True)
    user_id = Column(String(30), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    theme = Column(String(20), nullable=False, default="system")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="preferences")