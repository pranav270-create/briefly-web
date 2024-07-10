from io import BytesIO
import os
import asyncio
import base64
import json
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
import anthropic
from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel


router = APIRouter()
elvenlabs_client = ElevenLabs(api_key=os.environ.get("ELEVENLABS_API_KEY"))
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


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


@router.post("/api/anthropic_speech")
async def get_anthropic(request: BaseRequest):
    query = request.query
    return EventSourceResponse(stream_data_speech(query), media_type="text/event-stream")


@router.post("/api/anthropic")
async def get_anthropic(request: BaseRequest):
    query = request.query
    return EventSourceResponse(stream_data(query), media_type="text/event-stream")
