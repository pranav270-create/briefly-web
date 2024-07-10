import pickle, os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from fastapi import HTTPException, Header, Depends
from pydantic import BaseModel

from users import get_current_user, CurrentUser
from users import router as users_router
from daily_learning import router as daily_learning_router
from make_briefly import get_email_data, get_event_related_emails, EmailResponse, CalendarResponse
from make_briefless import generate_news_summary
from helpers import DEV

app = FastAPI()
app.include_router(users_router)
app.include_router(daily_learning_router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def load_or_save_pickle(file_name, data_function, *args):
    if os.path.exists(file_name):
        with open(file_name, 'rb') as f:
            return pickle.load(f)
    else:
        data = await data_function(*args)
        with open(file_name, 'wb') as f:
            pickle.dump(data, f)
        return data


async def get_user_header(authorization: str = Header(None)):
    if DEV >= 1:
        return CurrentUser(email="test", google_token="test")
    if authorization is None or not authorization:
        raise HTTPException(status_code=400, detail="Invalid or missing token")
    return await get_current_user(authorization.split(" ")[1])  # pass in jwt token


@app.get("/api/get-emails")
async def get_emails(user: CurrentUser = Depends(get_user_header)):
    if DEV >= 1:
        email_data: EmailResponse = await load_or_save_pickle('email_data.pickle', get_email_data)
    else:
        email_data = await get_email_data(token=user.google_token)
    return jsonable_encoder(email_data)


@app.get("/api/get-calendar")
async def get_calendar(user: CurrentUser = Depends(get_user_header)):
    if DEV >= 1:
        calendar_data: CalendarResponse = await load_or_save_pickle('calendar_events.pickle', get_event_related_emails)
    else:
        calendar_data = await get_event_related_emails(token=user.google_token, self_email=user.email)
    return jsonable_encoder(calendar_data)


class NewsRequest(BaseModel):
    clickedSummary: str


@app.post("/api/less-brief")
async def get_less_brief(request: NewsRequest):
    # news emails search the web
    briefless = await generate_news_summary(request.clickedSummary)
    return {"content": briefless}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
