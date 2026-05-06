from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import select
from app.api.deps import CurrentUser, get_current_user, SessionDep
from app.models.pantry_model import PantryItem, PantryItemCreate, PantryItemPublic

router = APIRouter(
    prefix="/pantry",
    tags=["pantry"],
    dependencies=[Depends(get_current_user)],
)

@router.get("/", response_model=list[PantryItemPublic])
def get_pantry(*, session: SessionDep, current_user: CurrentUser):
    pantry_items = session.exec(
        select(PantryItem).where(PantryItem.user_id == current_user.id)
    ).all()
    return pantry_items

@router.post("/", response_model=PantryItemPublic)
def add_to_pantry(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    pantry_item_in: PantryItemCreate,
):
    existing_item = session.exec(
        select(PantryItem).where(
            PantryItem.user_id == current_user.id,
            PantryItem.ingredient_id == pantry_item_in.ingredient_id,
        )
    ).first()

    if existing_item:
        raise HTTPException(status_code=409, detail="Ingredient already exists in pantry.")

    item = PantryItem(
        ingredient_id=pantry_item_in.ingredient_id,
        name=pantry_item_in.name,
        image_url=pantry_item_in.image_url,
        aisle=pantry_item_in.aisle,
        quantity=pantry_item_in.quantity,
        user_id=current_user.id,
    )

    session.add(item)
    session.commit()
    session.refresh(item)
    return item

@router.delete("/", response_model=PantryItemPublic)
def remove_from_pantry(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    pantry_item_in: PantryItemCreate,
):
    existing_item = session.exec(
        select(PantryItem).where(
            PantryItem.user_id == current_user.id,
            PantryItem.ingredient_id == pantry_item_in.ingredient_id,
        )
    ).first()

    if not existing_item:
        raise HTTPException(status_code=404, detail="Ingredient not found in pantry.")

    session.delete(existing_item)
    session.commit()
    return existing_item
        



