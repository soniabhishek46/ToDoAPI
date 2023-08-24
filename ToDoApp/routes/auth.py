from datetime import datetime, timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from database import SessionLocal
from models import Users
from passlib.hash import bcrypt
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import JWTError, jwt

# openssl rand -hex 32
secret_key = '1cadabfaab1e5bf9973dedd5bf9b5e5ba462552dbb5072e935e15f764b257ea2'
algorithm = 'HS256'

router = APIRouter(
    prefix='/auth',
    tags=['auth']    
)

class CreateUserRequest(BaseModel):
    email: str
    username: str
    first_name: str
    last_name: str
    password: str
    role: str


class Token(BaseModel):
    access_token: str
    token_type: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')

@router.post("/create_user", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_req: CreateUserRequest):
    user = Users(
        email = create_user_req.email,
        username = create_user_req.username,
        first_name = create_user_req.first_name,
        last_name = create_user_req.last_name,
        hashed_password = bcrypt.hash(create_user_req.password),
        role = create_user_req.role,
        isactive = True
    )

    db.add(user)
    db.commit()

# To Hash the password we need to install a library
# pip install "passlib[bcrypt]"
# passlib is a popular library for managing passwords, and it has bcrypt

# We also need to install the following library for getting username & password from a form
# pip install python-multipart

# To work with JWT tokens, we need to install the library
# pip install "python-jose[cryptography]"


@router.post("/token", response_model=Token)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                db: db_dependency):
    
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Could not validate credentials')
    
    token = generate_jwt_token(user.username, user.id, timedelta(minutes=20))
    return {'access_token': token, 'token_type':'bearer'}


def authenticate_user(username: str, password:str, db):
    user_in_db = db.query(Users).filter(Users.username == username).first()

    if not user_in_db:
        return False
    
    if not bcrypt.verify(password, user_in_db.hashed_password):
        return False

    return user_in_db


def generate_jwt_token(username:str, userid: int, expires_delta: timedelta):
    expires = datetime.utcnow() + expires_delta
    
    payload = {
        'sub' : username,
        'id' : userid,
        'exp' : expires
    }

    return jwt.encode(payload, secret_key, algorithm=algorithm)

#Decoding the JWT
#JWT token needs to be decoded by our API enpoints to ensure that
#the token is a valid one
#to add this functionality, we will write a simple python function as shown below

async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        username: str = payload.get('sub')
        userid: int = payload.get('id')

        if username is None or userid is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail='Could not validate credentials')
        
        return {'username': username, 'userid': userid}
    
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Could not validate credentials')
    