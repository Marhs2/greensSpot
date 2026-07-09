from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from app.core.config import settings
from app.api.v1.gs_router import router as gs_router
from app.api.v1.auth_router import router as auth_router
from app.api.v1.integration_router import router as integration_router
from app.db.database import init_db

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)

# 운영: CORS_ORIGINS 만 허용.
# 개발: localhost / 127.0.0.1 / 사설망 프론트 포트 허용 (외부 evil origin 차단).
cors_options = {
    "allow_origins": settings.cors_origins,
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}
if settings.environment.lower() == "development":
    cors_options["allow_origin_regex"] = (
        r"https?://("
        r"localhost|127\.0\.0\.1"
        r"|192\.168\.\d{1,3}\.\d{1,3}"
        r"|10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
        r")(:\d+)?"
    )

app.add_middleware(CORSMiddleware, **cors_options)


@app.on_event("startup")
async def startup():
    await init_db()


app.include_router(gs_router)
app.include_router(auth_router)
app.include_router(integration_router)


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    response = JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    origin = request.headers.get("origin")
    # CORSMiddleware 와 동일 정책: 허용 목록 또는 개발 환경 전 origin
    allow = False
    if origin:
        if origin in settings.cors_origins:
            allow = True
        elif settings.environment.lower() == "development":
            # 개발: 로컬 호스트만 예외 헤더 부여 (evil.example.com 차단 테스트와 정합)
            if (
                "localhost" in origin
                or "127.0.0.1" in origin
                or origin.startswith("http://192.168.")
                or origin.startswith("http://10.")
            ):
                allow = True
    if allow and origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/api/gs/health",
    }