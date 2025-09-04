import uuid
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select, func, Session

from app.models import Item, ItemCreate, ItemUpdate, ItemPublic, ItemsPublic, Message
from app.api.deps import SessionDep
from app.models import TokenPayload
from app.api.deps import get_current_user  # JWT-based dependency

router = APIRouter(prefix="/items", tags=["items"])

# -------------------------------
# Helper function for permission check
# -------------------------------
def check_permissions(item: Item, current_user: TokenPayload):
    if not current_user.is_superuser and item.owner_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

# -------------------------------
# List items
# -------------------------------
@router.get("/", response_model=ItemsPublic)
def read_items(
    skip: int = 0,
    limit: int = 100,
    session: Session =  Depends(SessionDep),
    current_user: TokenPayload = Depends(get_current_user),
) -> Any:
    if current_user.is_superuser:
        count = session.exec(select(func.count()).select_from(Item)).one()[0]
        items = session.exec(select(Item).offset(skip).limit(limit)).all()
    else:
        count = session.exec(
            select(func.count()).select_from(Item).where(Item.owner_id == current_user.user_id)
        ).one()[0]
        items = session.exec(
            select(Item).where(Item.owner_id == current_user.user_id).offset(skip).limit(limit)
        ).all()

    return ItemsPublic(data=items, count=count)

# -------------------------------
# Get single item
# -------------------------------
@router.get("/{item_id}", response_model=ItemPublic)
def read_item(
    item_id: uuid.UUID,
    session: Session =  Depends(SessionDep),
    current_user: TokenPayload = Depends(get_current_user),
) -> Any:
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    check_permissions(item, current_user)
    return item

# -------------------------------
# Create item
# -------------------------------
@router.post("/", response_model=ItemPublic)
def create_item(
    item_in: ItemCreate,
    session: Session =  Depends(SessionDep),
    current_user: TokenPayload = Depends(get_current_user),
) -> Any:
    item = Item.model_validate(item_in, update={"owner_id": current_user.user_id})
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

# -------------------------------
# Update item
# -------------------------------
@router.put("/{item_id}", response_model=ItemPublic)
def update_item(
    item_id: uuid.UUID,
    item_in: ItemUpdate,
    session: Session =  Depends(SessionDep),
    current_user: TokenPayload = Depends(get_current_user),
) -> Any:
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    check_permissions(item, current_user)
    update_data = item_in.model_dump(exclude_unset=True)
    item.sqlmodel_update(update_data)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

# -------------------------------
# Delete item
# -------------------------------
@router.delete("/{item_id}", response_model=Message)
def delete_item(
    item_id: uuid.UUID,
    session: Session =  Depends(SessionDep),
    current_user: TokenPayload = Depends(get_current_user),
) -> Any:
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    check_permissions(item, current_user)
    session.delete(item)
    session.commit()
    return Message(message="Item deleted successfully")
