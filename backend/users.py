from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session
from fastapi import APIRouter
from fastapi import status
from fastapi import Depends, HTTPException, status
import jwt
from pydantic import BaseModel
from typing import Annotated, Optional
from sqlalchemy import DateTime, String, func, create_engine, JSON, Integer
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.engine import Engine
from google.cloud.sql.connector import Connector, IPTypes
from datetime import datetime, timedelta
import os

from integrations.auth import get_google_api_service
from helpers import DEV

""" FastAPI Router """
router = APIRouter()


""" Encrypted Authentication Keys """
SECRET_KEY = os.environ.get('SECRET_AUTH_KEY')
ALGORITHM = os.environ.get('AUTH_ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 1 week


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


if DEV == 0:
    engine = get_gcp_engine()
    sessionlocal = sessionmaker(bind=engine)


""" SQLAlchemy Models """
class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at = mapped_column(DateTime, default=func.now())


class UserDB(Base):
    __tablename__ = "__users__"
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    recommendations = mapped_column(JSON, nullable=True)


""" Pydantic Models """
class CurrentUser(BaseModel):
    email: str
    google_token: str
    recommendations: Optional[dict] = None

class GoogleToken(BaseModel):
    access_token: str

class UserProfile(BaseModel):
    access_token: str
    user_email: str
    first_name: str
    last_name: str
    profile_pic: str


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


async def get_current_user(token: str) -> CurrentUser:
    session = sessionlocal()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("email")
        google_token: str = payload.get("google_token")
        user = session.query(UserDB).filter(UserDB.email == email).first()
        if user is None:
            raise credentials_exception

        return CurrentUser(email=email, google_token=google_token, recommendations=user.recommendations)
    except Exception:
        raise credentials_exception


def query_google(service):
    profile = service.people().get(resourceName='people/me', personFields='emailAddresses,names,photos').execute()
    email = profile.get('emailAddresses', [{}])[0].get('value')
    first_name = profile.get('names', [{}])[0].get('givenName')
    last_name = profile.get('names', [{}])[0].get('familyName')
    profile_pic = profile.get('photos', [{}])[0].get('url')
    return email, first_name, last_name, profile_pic


@router.post("/api/token", tags=["login"], response_model=UserProfile)
async def register_user(token: GoogleToken, session: Session = Depends(get_session)):
    google_access_token = token.access_token
    credentials = get_google_api_service('people', 'v1', google_access_token)
    email, first_name, last_name, profile_pic = query_google(credentials)
    print(email, first_name, last_name, profile_pic, flush=True)
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
    return UserProfile(access_token=jwt_token, user_email=email, first_name=first_name, last_name=last_name, profile_pic=profile_pic)


if __name__ == "__main__":
    pass
    # Create table if not exists
    # UserDB.metadata.create_all(engine)
    # print tables in database
    # inspector = Inspector.from_engine(engine)
    # print(inspector.get_table_names())
