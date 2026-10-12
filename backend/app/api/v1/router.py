from fastapi import APIRouter

from app.api.v1 import (
    ai,
    allocation,
    analytics,
    auth,
    concepts,
    constraints,
    insights,
    labs,
    matching,
    preferences,
    search,
    students,
    websocket,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(students.router)
api_router.include_router(labs.router)
api_router.include_router(preferences.router)
api_router.include_router(constraints.router)
api_router.include_router(allocation.router)
api_router.include_router(matching.router)
api_router.include_router(analytics.router)
api_router.include_router(ai.router)
api_router.include_router(insights.router)
api_router.include_router(concepts.router)
api_router.include_router(search.router)
api_router.include_router(websocket.router)
