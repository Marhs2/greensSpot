from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.db.database import get_db
from app.core.config import settings
from app.models.models import Bookmark, Parcel, User, UserPreference
from app.services.auth_service import (
    create_user, get_user_by_email, verify_password,
    create_access_token, create_refresh_token_db,
    validate_refresh_token, revoke_refresh_token, generate_id
)
from app.services.parcel_service import get_parcel_by_id
from app.services.stats_service import get_trending, get_history
from app.schemas.schemas import (
    SignupRequest, LoginRequest, RefreshRequest, TokenResponse,
    UserResponse, UserPreferencesRequest, UserPreferencesResponse,
    BookmarkResponse, BookmarkCreateRequest, BookmarkCreateResponse, BookmarkDeleteResponse,
    ShareCreateRequest, ShareCreateResponse, TrendingResponse, HistoryResponse,
    HealthResponse, ParcelListResponse, ParcelDetailResponse, AgentSearchResponse,
    ExplainResponse, ScenarioResponse, CompareResponse, StatsResponse
)
from datetime import datetime

router = APIRouter(prefix="/api", tags=["auth"])
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    from app.services.auth_service import decode_token, get_user_by_id
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


@router.post("/auth/signup", response_model=dict, status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest, db: AsyncSession = Depends(get_db)):
    existing = await get_user_by_email(db, request.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    user = await create_user(db, request.email, request.password)
    return {"ok": True}


@router.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, request.email)
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    access_token = create_access_token(user.id)
    refresh_token = await create_refresh_token_db(db, user.id)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh(request: RefreshRequest, db: AsyncSession = Depends(get_db)):
    from app.services.auth_service import validate_refresh_token, revoke_refresh_token
    user = await validate_refresh_token(db, request.refresh_token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    await revoke_refresh_token(db, request.refresh_token)
    access_token = create_access_token(user.id)
    new_refresh_token = await create_refresh_token_db(db, user.id)
    return TokenResponse(access_token=access_token, refresh_token=new_refresh_token)


@router.post("/auth/logout")
async def logout(request: RefreshRequest, db: AsyncSession = Depends(get_db)):
    await revoke_refresh_token(db, request.refresh_token)
    return {"ok": True}


@router.get("/users/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        created_at=current_user.created_at,
    )


@router.get("/bookmarks", response_model=BookmarkResponse)
async def get_bookmarks(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Bookmark).where(Bookmark.user_id == current_user.id).order_by(Bookmark.created_at.desc())
    )
    bookmarks = result.scalars().all()
    return BookmarkResponse(bookmarks=[
        {
            "parcelId": b.parcel_id,
            "parcelName": b.parcel_name,
            "district": b.district,
            "topRecommendation": b.top_recommendation,
            "topScore": b.top_score,
            "createdAt": b.created_at,
        }
        for b in bookmarks
    ])


@router.post("/bookmarks", response_model=BookmarkCreateResponse, status_code=status.HTTP_201_CREATED)
async def add_bookmark(
    request: BookmarkCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """DB 시드 부지 + 라이브 VW-{pnu} 부지 모두 북마크 가능.

    라이브 필지는 parcels 테이블에 없을 수 있으므로:
    1) DB 조회 → 2) live_get_parcel → 3) 요청 body 스냅샷 순으로 메타 확보.
    """
    parcel_name: Optional[str] = None
    district: Optional[str] = None
    top_rec = "NONE"
    top_score = 0

    parcel = await get_parcel_by_id(db, request.parcelId)
    if parcel:
        parcel_name = parcel.name
        district = parcel.district
        score = parcel.scores
        if score:
            top_rec = score.top_recommendation or "NONE"
            # API tree_score ≈ UI sumok / topScore
            top_score = round(
                max(
                    float(getattr(score, "tree_score", 0) or 0),
                    float(getattr(score, "garden_score", 0) or 0),
                    float(getattr(score, "solar_score", 0) or 0),
                )
            )
    else:
        # 라이브 필지: VWorld 재조회는 느리고 실패할 수 있음 → body 메타 우선, 없으면 VW- ID 만으로도 저장
        live = None
        # body 메타가 충분하면 외부 호출 생략 (속도·404 방지)
        if not (request.parcelName and request.district):
            try:
                from app.services.live_search_service import live_get_parcel

                live = await live_get_parcel(request.parcelId)
            except Exception:  # noqa: BLE001
                live = None

        if live and live.get("parcel"):
            p = live["parcel"]
            s = live.get("scores") or p.get("scores") or {}
            parcel_name = request.parcelName or p.get("name")
            district = request.district or p.get("district")
            top_rec = (
                request.topRecommendation
                or s.get("topRecommendation")
                or "NONE"
            )
            top_score = round(
                float(
                    request.topScore
                    if request.topScore is not None
                    else (s.get("treeScore") or s.get("gardenScore") or s.get("solarScore") or 0)
                )
            )
        elif request.parcelName or request.district or str(request.parcelId).startswith("VW-"):
            # 프론트 스냅샷 또는 VW- ID 만으로 북마크 (parcels FK 없음)
            parcel_name = request.parcelName or request.parcelId
            district = request.district or "미상"
            top_rec = request.topRecommendation or "NONE"
            top_score = round(float(request.topScore or 0))
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parcel not found",
            )

    existing = await db.execute(
        select(Bookmark).where(
            Bookmark.user_id == current_user.id,
            Bookmark.parcel_id == request.parcelId,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already bookmarked")

    bookmark = Bookmark(
        id=generate_id(),
        user_id=current_user.id,
        parcel_id=request.parcelId,
        parcel_name=parcel_name or request.parcelId,
        district=district or "",
        top_recommendation=str(top_rec),
        top_score=int(top_score),
    )
    db.add(bookmark)
    await db.commit()
    return BookmarkCreateResponse(ok=True)


@router.delete("/bookmarks", response_model=BookmarkDeleteResponse)
async def remove_bookmark(
    parcelId: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Bookmark).where(
            Bookmark.user_id == current_user.id,
            Bookmark.parcel_id == parcelId,
        )
    )
    bookmark = result.scalar_one_or_none()
    if not bookmark:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bookmark not found")
    await db.delete(bookmark)
    await db.commit()
    return BookmarkDeleteResponse(ok=True)


@router.post("/share", response_model=ShareCreateResponse)
async def create_share(request: ShareCreateRequest, db: AsyncSession = Depends(get_db)):
    from app.models.models import Share
    parcel = await get_parcel_by_id(db, request.parcelId)
    if not parcel:
        # 라이브 VW- 필지도 공유 허용 (Share 테이블에 parcel FK 없음)
        if not str(request.parcelId).startswith("VW-"):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcel not found")
        try:
            from app.services.live_search_service import live_get_parcel
            live = await live_get_parcel(request.parcelId)
            if not live:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcel not found")
        except HTTPException:
            raise
        except Exception:  # noqa: BLE001
            # 캐시/힌트 없이 실패해도 VW- ID 형태면 공유 링크 발급
            pass

    share_id = generate_id()
    share = Share(
        id=generate_id(),
        share_id=share_id,
        parcel_id=request.parcelId,
    )
    db.add(share)
    await db.commit()

    base = (settings.public_base_url or "").rstrip("/")
    if base:
        url = f"{base}/?parcel={request.parcelId}&share={share_id}"
    else:
        # FE 딥링크와 동일 형식 (도메인 미설정 시 상대 경로 안내)
        url = f"/?parcel={request.parcelId}&share={share_id}"
    return ShareCreateResponse(
        shareId=share_id,
        url=url,
    )


@router.patch("/users/me/preferences", response_model=UserPreferencesResponse)
async def update_preferences(
    request: UserPreferencesRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == current_user.id)
    )
    pref = result.scalar_one_or_none()

    if not pref:
        pref = UserPreference(
            id=generate_id(),
            user_id=current_user.id,
            theme=request.theme or "system",
        )
        db.add(pref)
    else:
        if request.theme:
            pref.theme = request.theme

    await db.commit()
    return UserPreferencesResponse(theme=pref.theme)


@router.get("/gs/trending", response_model=TrendingResponse)
async def get_trending_endpoint(db: AsyncSession = Depends(get_db)):
    data = await get_trending(db)
    return TrendingResponse(**data)


@router.get("/gs/history", response_model=HistoryResponse)
async def get_history_endpoint(limit: int = Query(20, le=100), db: AsyncSession = Depends(get_db)):
    data = await get_history(db, limit)
    return HistoryResponse(**data)