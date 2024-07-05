import pickle, os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from fastapi import HTTPException

from integrations.google_calendar import CalendarEvent
from integrations.gmail import GmailMessage
from make_briefly import get_email_data, get_event_related_emails, EmailResponse, CalendarResponse
from make_briefless import generate_news_summary, generate_calendar_event_details

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def load_or_save_pickle(file_name, data_function):
    if os.path.exists(file_name):
        with open(file_name, 'rb') as f:
            return pickle.load(f)
    else:
        data = await data_function()
        with open(file_name, 'wb') as f:
            pickle.dump(data, f)
        return data


@app.get("/api/get-emails")
async def get_emails():
    email_data: EmailResponse = await load_or_save_pickle('email_data.pickle', get_email_data)
    return jsonable_encoder(email_data)


@app.get("/api/get-calendar")
async def get_calendar():
    calendar_data: CalendarResponse = await load_or_save_pickle('calendar_events.pickle', get_event_related_emails)
    return jsonable_encoder(calendar_data)


LessBriefRequest = GmailMessage | CalendarEvent

@app.post("/api/less-brief")
async def get_less_brief(request: LessBriefRequest):
    if isinstance(request, GmailMessage):
        # personal emails expose the entire body
        if request.classification == 'personal':
            return {"content": request.body}
        
        # news emails search the web
        elif request.classification == "news":
            return {"content": ""} #generate_news_summary(request.body)}
        
    # calendar events expose more data
    elif isinstance(request, CalendarEvent):
        return {"content": generate_calendar_event_details(request)}

    else:
        raise HTTPException(status_code=400, detail="Invalid input data")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)