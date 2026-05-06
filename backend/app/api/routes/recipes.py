from fastapi import APIRouter, HTTPException, Depends
from app.api.deps import CurrentUser, get_current_user, SessionDep
from app.core.config import settings
from app.models.recipe_model import RecipeSearchRequest, RecipeSearchResult, Recipe, RecipePublic
from sqlmodel import select
import uuid

from bs4 import BeautifulSoup

import httpx

router = APIRouter(
    prefix="/recipes",
    tags=["recipes"],
    dependencies=[Depends(get_current_user)],
)

RECIPE_URL = "https://api.spoonacular.com/recipes/complexSearch"
INGREDIENTS_URL = "https://api.spoonacular.com/food/ingredients/search"


def strip_html(html: str | None) -> str | None:
    if not html:
        return html
    return BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True)

@router.post("/fetchrecipes", response_model=list[RecipeSearchResult])
async def fetch_recipes(
    *,
    _session: SessionDep,
    _current_user: CurrentUser,
    recipe_request: RecipeSearchRequest,
):
    api_key = settings.SPOONACULAR_API_KEY

    params = {
        "apiKey": api_key,
        "query": recipe_request.query if recipe_request.query else None,
        "cuisine": recipe_request.cuisine if recipe_request.cuisine else None,
        "diet": recipe_request.diet if recipe_request.diet else None,
        "intolerances": ",".join(recipe_request.intolerances) if recipe_request.intolerances else None,
        "includeIngredients": ",".join(recipe_request.include_ingredients)
        if recipe_request.include_ingredients
        else None,
        "type": recipe_request.type_of_recipe if recipe_request.type_of_recipe else None,
        "addRecipeInformation": True,
        "addRecipeInstructions": True,
        "sort": "max-used-ingredients",
        "number": 10,
    }

    params = {key: value for key, value in params.items() if value is not None}

    async with httpx.AsyncClient() as client:
        response = await client.get(RECIPE_URL, params=params)

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail="Failed to fetch recipes from Spoonacular",
        )

    spoonacular_results = response.json().get("results", [])

    recipes = [
        RecipeSearchResult(
            id=recipe["id"],
            image=recipe.get("image"),
            title=recipe.get("title"),
            ready_in_minutes=recipe.get("readyInMinutes"),
            servings=recipe.get("servings"),
            source_url=recipe.get("sourceUrl"),
            vegetarian=recipe.get("vegetarian"),
            vegan=recipe.get("vegan"),
            gluten_free=recipe.get("glutenFree"),
            dairy_free=recipe.get("dairyFree"),
            summary=strip_html(recipe.get("summary")),
            cuisines=recipe.get("cuisines", []),
            diets=recipe.get("diets", []),
            analyzed_instructions=recipe.get("analyzedInstructions", []),
        )
        for recipe in spoonacular_results
    ]

    return recipes

@router.post("/saverecipe")
async def save_recipe(
    *,
    _session: SessionDep,
    _current_user: CurrentUser,
    recipe: RecipeSearchResult
):
    existing_recipe = _session.exec(
        select(Recipe).where(Recipe.recipe_id == recipe.id)
    ).first()

    if existing_recipe:
        raise HTTPException(status_code=409, detail="Recipe already saved.")

    new_recipe = Recipe(
        recipe_id=recipe.id,
        image=recipe.image,
        title=recipe.title,
        ready_in_minutes=recipe.ready_in_minutes,
        servings=recipe.servings,
        source_url=recipe.source_url,
        vegetarian=recipe.vegetarian or False,
        vegan=recipe.vegan or False,
        gluten_free=recipe.gluten_free or False,
        dairy_free=recipe.dairy_free or False,
        summary=recipe.summary or "",
        cuisines=recipe.cuisines,
        diets=recipe.diets,
        analyzed_instructions=recipe.analyzed_instructions,
        user_id=_current_user.id,
    )

    _session.add(new_recipe)
    _session.commit()
    _session.refresh(new_recipe)

    return {"message": "Recipe saved successfully", "recipe_id": new_recipe.id}

@router.get("/savedrecipes", response_model=list[RecipeSearchResult])
async def get_saved_recipes(
    *,
    _session: SessionDep,
    _current_user: CurrentUser
):
    fetched_recipes = _session.exec(
        select(Recipe).where(Recipe.user_id == _current_user.id)
    ).all()

    return [
        RecipeSearchResult(
            id=recipe.recipe_id,
            image=recipe.image,
            title=recipe.title,
            ready_in_minutes=recipe.ready_in_minutes,
            servings=recipe.servings,
            source_url=recipe.source_url,
            vegetarian=recipe.vegetarian,
            vegan=recipe.vegan,
            gluten_free=recipe.gluten_free,
            dairy_free=recipe.dairy_free,
            summary=recipe.summary,
            cuisines=recipe.cuisines,
            diets=recipe.diets,
            analyzed_instructions=recipe.analyzed_instructions,
        )
        for recipe in fetched_recipes
    ]

@router.get("/fetchingredients")
async def fetch_ingredients(ingredient: str):

    async with httpx.AsyncClient() as client:
         
        api_key = settings.SPOONACULAR_API_KEY

        params = {
            'query': ingredient,
            'apiKey': api_key,
            'number': 30,
            'metaInformation': True
        }
        response = await client.get(INGREDIENTS_URL, params=params)
        if response.status_code == 200:
            return response.json()["results"]
        else:             
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch ingredient from external API")   
    