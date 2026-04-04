"""Pydantic schemas for matching engine results."""
from typing import Optional
from pydantic import BaseModel


class MatchResult(BaseModel):
    target_type: str
    target_id: int
    target_name: str
    match_score: float  # 0-100
    match_reasons: list[str]
    weak_points: list[str]


class MatchResponse(BaseModel):
    company_id: int
    company_name: str
    matches: list[MatchResult]


class AllMatchesResponse(BaseModel):
    company_id: int
    company_name: str
    streamers: list[MatchResult]
    investors: list[MatchResult]
    outlets: list[MatchResult]
