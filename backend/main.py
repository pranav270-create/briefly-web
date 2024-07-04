from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from daily_data import get_email_data, get_event_related_emails, EmailResponse, CalendarResponse

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Token(BaseModel):
    idToken: str

@app.post('/api/token')
async def api_get_google_service(token: Token):
    try:
        token = token.idToken
        print(token, flush=True)
        return jsonable_encoder({"status": "success"})
    except Exception as e:
        return jsonable_encoder({"status": "error", "message": str(e)})


@app.post("/api/get-emails")
async def get_emails(token: Token):
    email_data: EmailResponse = await get_email_data(token.idToken)
    return jsonable_encoder(email_data)


@app.post("/api/get-calendar")
async def get_calendar(token: Token):
    calendar_data: CalendarResponse = await get_event_related_emails(token.idToken, "pranaviyer2@gmail.com")
    return jsonable_encoder(calendar_data)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
