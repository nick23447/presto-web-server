import uuid
from datetime import datetime
from typing import Any

from pydantic import ConfigDict

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel

from .utils import get_datetime_utc

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user_model import User


# Properties to receive when searching for recipes
class RecipeSearchRequest(SQLModel):
    query: str | None = None
    cuisine: str | None = None
    diet: str | None = None
    intolerances: list[str] | None = None
    include_ingredients: list[str] | None = None
    type_of_recipe: str | None = None

class RecipeSearchResult(SQLModel):
    model_config = ConfigDict(populate_by_name=True)
    
    id: int
    image: str | None = None
    title: str | None = None
    ready_in_minutes: int | None = Field(default=None, alias="readyInMinutes")
    servings: int | None = None
    source_url: str | None = Field(default=None, alias="sourceUrl")
    vegetarian: bool | None = None
    vegan: bool | None = None
    gluten_free: bool | None = Field(default=None, alias="glutenFree")
    dairy_free: bool | None = Field(default=None, alias="dairyFree")
    summary: str | None = None
    cuisines: list[str] = Field(default_factory=list)
    diets: list[str] = Field(default_factory=list)
    analyzed_instructions: list[dict[str, Any]] = Field(
        default_factory=list,
        alias="analyzedInstructions"
    )

# Database model, database table inferred from class name
class Recipe(SQLModel, table=True):
    __tablename__ = "recipes"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    recipe_id: int = Field(index=True)
    image: str | None = None
    title: str
    ready_in_minutes: int
    servings: int
    source_url: str
    vegetarian: bool = False
    vegan: bool = False
    gluten_free: bool = False
    dairy_free: bool = False
    summary: str

    cuisines: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSONB)
    )
    diets: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSONB)
    )
    analyzed_instructions: list[dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSONB)
    )

    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )
    user_id: uuid.UUID = Field(
        foreign_key="users.id", nullable=False, ondelete="CASCADE"
    )
    user: "User" = Relationship(back_populates="saved_recipes")


# Properties to return via API
class RecipePublic(SQLModel):
    id: uuid.UUID
    recipe_id: int
    image: str | None = None
    title: str
    ready_in_minutes: int
    servings: int
    source_url: str
    vegetarian: bool
    vegan: bool
    gluten_free: bool
    dairy_free: bool
    summary: str
    cuisines: list[str] = []
    diets: list[str] = []
    analyzed_instructions: list[dict[str, Any]] = []
    user_id: uuid.UUID
    created_at: datetime | None = None

