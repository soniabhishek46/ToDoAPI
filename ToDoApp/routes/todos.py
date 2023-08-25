from fastapi import Body, APIRouter, Depends, Path, status, HTTPException
from pydantic import BaseModel, Field
from database import SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from models import ToDo
from .auth import get_current_user




router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ToDoRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=100)
    priority: int = Field(gt=0, lt=6)
    complete: bool


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@router.get("/")
async def get_all_todos(user: user_dependency, db: db_dependency):

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed.")

    return db.query(ToDo).filter(ToDo.ownerid == user.get('userid')).all()


@router.get("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def get_single_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed.")

    fetched_todo = db.query(ToDo).filter(ToDo.id == todo_id)\
                                 .filter(ToDo.ownerid == user.get('userid')).first()

    if fetched_todo is not None:
        return fetched_todo
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ToDo with given id, not found")


@router.post("/todo", status_code=status.HTTP_201_CREATED)
async def create_todo(user: user_dependency, db: db_dependency, new_todo: ToDoRequest):

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed.")

    todo_model = ToDo(**new_todo.model_dump(), ownerid=user.get('userid'))
    db.add(todo_model)
    db.commit()


@router.put("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(db: db_dependency, 
                      user: user_dependency,
                      updated_todo: ToDoRequest, 
                      todo_id: int = Path(gt=0)):

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed.")

    todo_model = ToDo(**updated_todo.model_dump())
    todo_db = db.query(ToDo).filter(ToDo.id == todo_id)\
                .filter(ToDo.ownerid == user.get('userid')).first()

    todo_db.title = todo_model.title
    todo_db.description = todo_model.description
    todo_db.priority = todo_model.priority
    todo_db.complete = todo_model.complete

    db.add(todo_db)
    db.commit()

    """
    Here we do not do db.add(todo_model), because it will be concidered as
    (1) A new ToDo, wherein it will be added as an Insert
    (2) As a ToDo Insert having same id as a already existing ToDo
    Both these scenarios are wrong
    We need to modify the ToDo returned from the db, modify its fields, and then add
    it back to the db, which will be taken as an update
    """

@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed.")

    todo_to_delete = db.query(ToDo).filter(ToDo.id == todo_id)\
                        .filter(ToDo.ownerid == user.get('userid')).first()

    if todo_to_delete is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ToDo not found.")
    
    db.query(ToDo).filter(ToDo.id == todo_id).filter(ToDo.ownerid == user.get('userid')).delete()
    db.commit()

