import pickle, os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from fastapi import HTTPException, Header, Depends
from pydantic import BaseModel
from typing import Union

from integrations.google_calendar import CalendarEvent
from integrations.gmail import GmailMessage
from make_briefly import get_email_data, get_event_related_emails, EmailResponse, CalendarResponse
from make_briefless import generate_news_summary, generate_calendar_event_details
from helpers import DEV

app = FastAPI()

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

async def get_token_header(authorization: str = Header(None)):
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=400, detail="Invalid or missing token")
    return authorization.split(" ")[1]

@app.get("/api/get-emails")
async def get_emails(token: str = Depends(get_token_header)):
    if DEV >= 1:
        email_data: EmailResponse = await load_or_save_pickle('email_data.pickle', get_email_data)
    else:
        email_data = await get_email_data(token=token)
    return jsonable_encoder(email_data)


@app.get("/api/get-calendar")
async def get_calendar(token: str = Depends(get_token_header)):
    if DEV >= 1:
        calendar_data: CalendarResponse = await load_or_save_pickle('calendar_events.pickle', get_event_related_emails)
    else:
        calendar_data = await get_event_related_emails(token=token)
    return jsonable_encoder(calendar_data)

class NewsRequest(BaseModel):
    clickedSummary: str

LessBriefRequest = Union[GmailMessage, CalendarEvent, NewsRequest]

@app.post("/api/less-brief")
async def get_less_brief(request: LessBriefRequest):
    if isinstance(request, GmailMessage):
        # personal emails expose the entire body
        if request.classification == 'personal':
            return {"content": request.body}
        
    # news emails search the web
    elif isinstance(request, NewsRequest):
        if DEV >= 1:
            briefless = await load_or_save_pickle('briefless_news.pickle', generate_news_summary, request.clickedSummary)
        else:
            briefless = await generate_news_summary(request.clickedSummary)
        return {"content": briefless}
        
    # calendar events expose more data
    elif isinstance(request, CalendarEvent):
        return {"content": generate_calendar_event_details(request)}

    else:
        raise HTTPException(status_code=400, detail="Invalid input data")

class AccessToken(BaseModel):
    access_token: str

@app.post("/api/token")
async def login(token: AccessToken):
    if token.access_token:
        print("Access token provided", flush=True)
        return {"status": "success"}
    else:
        print("No access token provided", flush=True)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)