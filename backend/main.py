import pickle, os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from fastapi import HTTPException, Header, Depends
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from typing import Union
import anthropic
from io import BytesIO
import asyncio
import base64
import json
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs

from users import router, get_current_user, CurrentUser
from integrations.google_calendar import CalendarEvent
from integrations.gmail import GmailMessage
from make_briefly import get_email_data, get_event_related_emails, EmailResponse, CalendarResponse
from make_briefless import generate_news_summary, generate_calendar_event_details
from helpers import DEV

app = FastAPI()
app.include_router(router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
elvenlabs_client = ElevenLabs(api_key=os.environ.get("ELEVENLABS_API_KEY"))


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


class BaseRequest(BaseModel):
    query: str


class BaseAnswer(BaseModel):
    answer: str


class AudioAnswer(BaseModel):
    text: str
    audio: str


async def stream_data(query: str):
    with client.messages.stream(
            max_tokens=1024,
            temperature=0.0,
            messages=[{"role": "user", "content": query}],
            model="claude-3-5-sonnet-20240620") as stream:
        for text in stream.text_stream:
            yield json.dumps(jsonable_encoder(BaseAnswer(answer=text)))


async def stream_data_speech(query: str):
    try:
        full_text = ""
        accumulated_text = ""  # To accumulate text
        last_time = asyncio.get_event_loop().time()  # Get the current event loop time

        with client.messages.stream(
            max_tokens=1024,
            temperature=0.0,
            messages=[{"role": "user", "content": query}],
            model="claude-3-5-sonnet-20240620"
        ) as stream:
            for text in stream.text_stream:
                print(f"Streaming: {text}", end="", flush=True)
                full_text += text
                accumulated_text += text  # Accumulate text

                current_time = asyncio.get_event_loop().time()
                if current_time - last_time >= 2:  # Check if 2 seconds have passed
                    last_time = current_time  # Reset the last time

                    # Generate audio for the accumulated text
                    response = elvenlabs_client.text_to_speech.convert(
                        voice_id="pNInz6obpgDQGcFmaJgB",  # Adam pre-made voice
                        optimize_streaming_latency="2",
                        output_format="mp3_22050_32",
                        text=accumulated_text,  # Use accumulated text
                        model_id="eleven_turbo_v2",
                        voice_settings=VoiceSettings(
                            stability=0.0,
                            similarity_boost=1.0,
                            style=0.0,
                            use_speaker_boost=True,
                        ),
                    )
                    # Create a BytesIO object to hold the audio data in memory
                    audio_stream = BytesIO()

                    # Write each chunk of audio data to the stream
                    for chunk in response:
                        if chunk:
                            audio_stream.write(chunk)

                    # Reset stream position to the beginning
                    audio_stream.seek(0)
                    audio_data = base64.b64encode(audio_stream.read()).decode('utf-8')

                    # Yield both text and audio
                    yield json.dumps(jsonable_encoder(AudioAnswer(text=accumulated_text, audio=audio_data)))

                    accumulated_text = ""  # Reset accumulated text for the next batch
                    await asyncio.sleep(3)  # Wait for 2 seconds before processing the next batch

    except Exception as e:
        print(f"Error in stream_data: {str(e)}")
        yield f"data: {{'error': '{str(e)}'}}\n\n"


@app.post("/api/anthropic_speech")
async def get_anthropic(request: BaseRequest):
    query = request.query
    return EventSourceResponse(stream_data_speech(query), media_type="text/event-stream")


@app.post("/api/anthropic")
async def get_anthropic(request: BaseRequest):
    query = request.query
    return EventSourceResponse(stream_data(query), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
