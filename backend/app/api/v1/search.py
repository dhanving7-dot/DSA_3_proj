from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services import search_service

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
def search(
    q: str = Query(min_length=1, max_length=100),
    algorithm: Literal["NAIVE", "KMP", "Z_FUNCTION", "RABIN_KARP", "SUFFIX_ARRAY"] = "KMP",
    fuzzy: bool = True,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return search_service.entity_search(db, q, algorithm, fuzzy, limit)
