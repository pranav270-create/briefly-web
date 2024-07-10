import httpx
import asyncio
from pydantic import BaseModel


async def send_parse_request(local: bool, request):
    route = "http://localhost:8080/api/less-brief" if local else "https://briefly-backend-krnivdrwhq-uk.a.run.app/api/less-brief"
    async with httpx.AsyncClient(timeout=3600.0) as client:
        response = await client.post(route, json=request.model_dump())
        response.raise_for_status()


class NewsRequest(BaseModel):
    clickedSummary: str


if __name__ == '__main__':
    summary = "SpaceX launches new satellite constellation for global internet coverage"
    request = NewsRequest(clickedSummary=summary)
    asyncio.run(send_parse_request(True, request))
