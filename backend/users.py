from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session
from fastapi import APIRouter
from fastapi import status
from fastapi import Depends, HTTPException, status
import jwt
from jwt import JWTError
from pydantic import BaseModel
from typing import Annotated, Optional
from sqlalchemy import DateTime, String, func, create_engine, JSON
from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy.engine import Engine
from google.cloud.sql.connector import Connector, IPTypes
from datetime import datetime, timedelta
import os

from integrations.auth import get_google_api_service

""" FastAPI Router """
router = APIRouter()


""" Encrypted Authentication Keys """
SECRET_KEY = os.environ.get('SECRET_AUTH_KEY')
ALGORITHM = os.environ.get('AUTH_ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = 60


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
    recommendations = mapped_column(JSON, nullable=True, description="Recommendations for the user")


""" Pydantic Models """
class CurrentUser(BaseModel):
    email: str
    google_token: str
    recommendations: Optional[dict] = None

class GoogleToken(BaseModel):
    access_token: str

class AccessToken(BaseModel):
    access_token: str
    expiry_time: Optional[int] = None
    token_type: Optional[str] = "bearer"


""" Functions for Auth and Users """
def get_session():
    session = sessionlocal()
    try:
        yield session
    finally:
        session.close()


def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_user(email: str, session: Session):
    db_user = UserDB(email=email, recommendations=None)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


async def get_current_user(token: str, session: Annotated[Session, Depends(get_session)]) -> CurrentUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("email")
        google_token: str = payload.get("google_token")
        if email is None or google_token is None:
            raise credentials_exception

        user = session.query(UserDB).filter(UserDB.email == email).first()
        if user is None:
            raise credentials_exception

        return CurrentUser(email=email, google_token=google_token, recommendations=user.recommendations)
    except JWTError:
        raise credentials_exception


def query_google(service):
    profile = service.people().get(resourceName='people/me', personFields='emailAddresses').execute()
    email = profile.get('emailAddresses', [{}])[0].get('value')
    return email


@router.post("/api/token", tags=["login"], response_model=AccessToken)
async def register_user(token: GoogleToken, session: Session = Depends(get_session)):
    google_access_token = token.access_token
    credentials = get_google_api_service('people', 'v1', google_access_token)
    email = query_google(credentials)

    # Check if user exists in db, create if not
    user = session.query(UserDB).filter(UserDB.email == email).first()
    if user is None:
        user = create_user(email, session)

    # Create JWT token encoding email and google_access_token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    jwt_token = create_access_token(
        data={"email": email, "google_token": google_access_token},
        expires_delta=access_token_expires
    )

    return AccessToken(access_token=jwt_token, expiry_time=ACCESS_TOKEN_EXPIRE_MINUTES*60, token_type="bearer")


async def loginflow(token: AccessToken) -> CurrentUser:
    access_token = token.access_token
    current_user = get_current_user(access_token)
    return current_user
