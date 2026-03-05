from fastapi import APIRouter

from app.api.routes import analytics, auth, candidates, companies, interviews, superadmin, tests, vacancies

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(vacancies.router, prefix="/vacancies", tags=["vacancies"])
api_router.include_router(candidates.router, prefix="/candidates", tags=["candidates"])
api_router.include_router(interviews.router, prefix="/interviews", tags=["interviews"])
api_router.include_router(tests.router, prefix="/tests", tags=["tests"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(superadmin.router, prefix="/superadmin", tags=["superadmin"])
