from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app import models, schemas, factory
from app.database import get_db
from app.security import get_user_id_from_token

router = APIRouter(prefix="/calculations", tags=["calculations"])


def _get_token_user_id(authorization: str | None) -> int | None:
    if not authorization:
        return None
    # Expecting 'Bearer <token>'
    parts = authorization.split()
    if len(parts) != 2:
        return None
    token = parts[1]
    return get_user_id_from_token(token)


@router.post("/", response_model=schemas.CalculationRead, status_code=status.HTTP_201_CREATED)
def create_calculation(payload: schemas.CalculationCreate, db: Session = Depends(get_db), authorization: str | None = Header(None)):
    user_id = _get_token_user_id(authorization)
    # compute result
    try:
        result = factory.perform_operation(payload.type, payload.a, payload.b)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    calc = models.Calculation(a=payload.a, b=payload.b, type=payload.type, result=result, user_id=user_id)
    db.add(calc)
    db.commit()
    db.refresh(calc)
    return calc


@router.get("/", response_model=List[schemas.CalculationRead])
def browse_calculations(limit: int = 100, db: Session = Depends(get_db)):
    items = db.query(models.Calculation).order_by(models.Calculation.created_at.desc()).limit(limit).all()
    return items


@router.get("/{calc_id}", response_model=schemas.CalculationRead)
def read_calculation(calc_id: int, db: Session = Depends(get_db)):
    calc = db.query(models.Calculation).get(calc_id)
    if not calc:
        raise HTTPException(status_code=404, detail="Calculation not found")
    return calc


@router.put("/{calc_id}", response_model=schemas.CalculationRead)
def update_calculation(calc_id: int, payload: schemas.CalculationCreate, db: Session = Depends(get_db), authorization: str | None = Header(None)):
    calc = db.query(models.Calculation).get(calc_id)
    if not calc:
        raise HTTPException(status_code=404, detail="Calculation not found")

    token_user = _get_token_user_id(authorization)
    # if the calc has an owner, ensure the token belongs to owner
    if calc.user_id is not None and token_user != calc.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this calculation")

    try:
        result = factory.perform_operation(payload.type, payload.a, payload.b)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    calc.a = payload.a
    calc.b = payload.b
    calc.type = payload.type
    calc.result = result
    db.add(calc)
    db.commit()
    db.refresh(calc)
    return calc


@router.delete("/{calc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_calculation(calc_id: int, db: Session = Depends(get_db), authorization: str | None = Header(None)):
    calc = db.query(models.Calculation).get(calc_id)
    if not calc:
        raise HTTPException(status_code=404, detail="Calculation not found")

    token_user = _get_token_user_id(authorization)
    if calc.user_id is not None and token_user != calc.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this calculation")

    db.delete(calc)
    db.commit()
    return None
