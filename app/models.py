"""
Pydantic models for request/response validation
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# ==================== User Models ====================

class UserCreate(BaseModel):
    """Request model for creating a new user"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    """Request model for user login"""
    username: str
    password: str


class UserResponse(BaseModel):
    """Response model for user data"""
    id: int
    username: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== Category Models ====================

class CategoryCreate(BaseModel):
    """Request model for creating a category"""
    name: str = Field(..., min_length=1, max_length=100)
    parent: Optional[str] = None
    full_path: str = Field(..., min_length=1, max_length=200)


class CategoryResponse(BaseModel):
    """Response model for category data"""
    id: int
    name: str
    parent: Optional[str]
    full_path: str
    usage_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== Batch Models (Phase 2 stubs) ====================

class BatchCreate(BaseModel):
    """Request model for creating a batch (Phase 2)"""
    name: str = Field(..., min_length=1, max_length=200)
    # CSV file will be uploaded separately as multipart/form-data


class BatchResponse(BaseModel):
    """Response model for batch data (Phase 2)"""
    id: int
    name: str
    user_id: int
    status: str
    date_range_start: Optional[str]
    date_range_end: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime] = None
    total_count: int = 0
    categorized_count: int = 0
    progress_percent: float = 0.0

    model_config = ConfigDict(from_attributes=True)


# ==================== Transaction Models (Phase 2 stubs) ====================

class TransactionUpdate(BaseModel):
    """Request model for updating a transaction (Phase 2)"""
    category: Optional[str] = None
    note: Optional[str] = None


class BulkTransactionUpdate(BaseModel):
    """Request model for bulk updating transactions (Phase 2)"""
    transaction_ids: list[int] = Field(..., min_length=1)
    category: Optional[str] = None
    note: Optional[str] = None


class TransactionResponse(BaseModel):
    """Response model for transaction data (Phase 2)"""
    id: int
    batch_id: int
    date: str
    payee: str
    amount: float
    category: Optional[str]
    note: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== Rule Models (Phase 5) ====================

class RuleCreate(BaseModel):
    """Request model for creating a rule"""
    pattern: str = Field(..., min_length=1, max_length=200, description="Pattern to match in payee")
    match_type: str = Field(..., pattern="^(contains|exact)$", description="How to match the pattern")
    category: str = Field(..., description="Category to suggest")


class RuleUpdate(BaseModel):
    """Request model for updating a rule"""
    pattern: Optional[str] = Field(None, min_length=1, max_length=200)
    match_type: Optional[str] = Field(None, pattern="^(contains|exact)$")
    category: Optional[str] = None


class RuleResponse(BaseModel):
    """Response model for rule data"""
    id: int
    user_id: int
    pattern: str
    match_type: str
    category: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RuleSuggestion(BaseModel):
    """Suggestion from a matching rule"""
    rule_id: int
    category: str
    pattern: str
    match_type: str


class RulePreviewRequest(BaseModel):
    """Request to preview which transactions match a rule pattern"""
    pattern: str = Field(..., min_length=1)
    match_type: str = Field(..., pattern="^(contains|exact)$")
