"""Search API schemas"""

from typing import List, Union
from pydantic import BaseModel
from src.schemas.post import PostResponse
from src.schemas.user import UserResponse
from src.schemas.comment import CommentResponse


class SearchResultItem(BaseModel):
    """Single search result item"""

    type: str  # "post", "user", or "comment"
    score: float  # Relevance score
    data: Union[PostResponse, UserResponse, CommentResponse]


class SearchResponse(BaseModel):
    """Schema for search results"""

    query: str
    results: List[SearchResultItem]
    total: int
    page: int
    page_size: int
