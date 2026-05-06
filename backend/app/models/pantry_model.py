import uuid
from datetime import datetime
from .utils import get_datetime_utc

from sqlalchemy import DateTime
from sqlmodel import Field, Relationship, SQLModel

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .user_model import User

class PantryItem(SQLModel, table=True):
    __tablename__ = "pantry_items"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    ingredient_id: int = Field(index=True)
    name: str = Field(index=True, max_length=255)
    image_url: str = Field(default=None, max_length=255)
    aisle: str = Field(default=None, max_length=255)
    quantity: int = Field(default=1, ge=0)

    user_id: uuid.UUID = Field(
        foreign_key="users.id", 
        nullable=False, 
        ondelete="CASCADE"
    )

    user: "User" = Relationship(back_populates="pantry_items")

    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )

class PantryItemCreate(SQLModel):
    ingredient_id: int
    name: str
    image_url: str | None = None
    aisle: str | None = None
    quantity: int = 1

class PantryItemPublic(SQLModel):
    id: uuid.UUID
    ingredient_id: int
    name: str
    image_url: str | None
    aisle: str | None
    quantity: int

