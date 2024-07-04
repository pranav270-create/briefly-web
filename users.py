from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session
from fastapi import APIRouter
from fastapi import status
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
import jwt
from jwt import JWTError
from pydantic import BaseModel
from typing import Annotated, Union, Optional
from sqlalchemy import DateTime, String, func, create_engine
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from sqlalchemy.engine import Engine
from google.cloud.sql.connector import Connector, IPTypes
from datetime import datetime, timedelta, timezone
import os

""" FastAPI Router """
router = APIRouter()


""" Encrypted Authentication Keys """
SECRET_KEY = os.environ.get('SECRET_AUTH_KEY')
ALGORITHM = os.environ.get('AUTH_ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = 90

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


""" Database Connection """
def get_gcp_engine() -> Engine:
    ip_type = IPTypes.PRIVATE if os.environ.get("PRIVATE_IP") else IPTypes.PUBLIC
    connector = Connector(ip_type)

    def getconn():
        conn = connector.connect(
            os.environ.get("INSTANCE_CONNECTION_NAME"),
            "pg8000",
            user=os.environ.get("INSTANCE_USER"),
            password=os.environ.get("INSTANCE_PASSWORD"),
            db=os.environ.get('DB_NAME'),
        )
        return conn

    engine = create_engine(
        "postgresql+pg8000://",
        creator=getconn,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1200)
    return engine

engine = get_gcp_engine(db_name=os.environ.get('DB_NAME'))
sessionlocal = sessionmaker(bind=engine)


""" SQLAlchemy Models """
class Base(DeclarativeBase):
    __abstract__ = True
    id = mapped_column()
    created_at = mapped_column(
        DateTime,
        default=func.now(),
    )

class UserDB(Base):
    __tablename__ = "users"
    email = mapped_column(String, primary_key=True)
    hashed_password = mapped_column(String)


""" Pydantic Models """
class User(BaseModel):
    username: str
    google_token: str

class Token(BaseModel):
    access_token: str
    token_type: str


""" Functions for Auth and Users """
def get_session():
    session = sessionlocal()
    try:
        yield session
    finally:
        session.close()


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], session: Annotated[Session, Depends(get_session)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user = session.query(UserDB).filter(UserDB.email == email).first()
        if user is None:
            raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_user(session: Session):
    hashed_password = get_password_hash(userForm.password)
    db_user = UserDB(email=userForm.email,
                     hashed_password=hashed_password)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@router.post("/api/token", tags=["login"], response_model=Token)
async def login_for_access_token(request_body: dict, session: Annotated[Session, Depends(get_session)]) -> Token:
    access_token = request_body.get("idToken")
    credentials = get_google_api_service(service_name, version, access_token)
    user = authenticate_user(session, access_token)
    if type(user) is str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=user,
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return Token(access_token=new_access_token, expiry_time=ACCESS_TOKEN_EXPIRE_MINUTES*60, token_type="bearer")
