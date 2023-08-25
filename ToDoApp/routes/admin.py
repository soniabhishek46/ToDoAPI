from fastapi import Body, APIRouter, Depends, Path, status, HTTPException
from pydantic import BaseModel, Field
from database import SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from models import ToDo
from .auth import get_current_user




router = APIRouter(
    prefix='/admin',
    tags=['admin']     
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@router.get("/todo", status_code=status.HTTP_200_OK)
async def get_all_todos(user: user_dependency, db: db_dependency):
    if user is None or user.get('role').lower() != 'admin':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    return db.query(ToDo).all()


@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):
    if user is None or user.get('role').lower() != 'admin':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    todo_todel = db.query(ToDo).filter(ToDo.id == todo_id).first()
    if todo_todel is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed.")
    
    db.query(ToDo).filter(ToDo.id == todo_id).delete()
    db.commit()