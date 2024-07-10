import sys
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from typing import List, Optional

sys.path.append("..")
from integrations.auth import get_google_api_service
from helpers import DEBUG


class CalendarEvent(BaseModel):
    summary: str
    creator: str = Field(default="No creator")
    organizer: str = Field(default="No organizer")
    attendees: List[str] = Field(default_factory=list)
    start: datetime
    end: datetime
    description: Optional[str] = Field(default="No description")
    location: Optional[str] = Field(default="No location")
    context: str = Field(default="")


def get_today_events(token: Optional[str] = None, days_before=2, days_after=0):
    service = get_google_api_service("calendar", "v3", token)

    # Get the start and end of the desired date range
    today = datetime.now().date()
    start_date = today - timedelta(days=days_before)
    end_date = today + timedelta(
        days=days_after + 1
    )  # Add 1 to include the full last day

    start = datetime.combine(start_date, datetime.min.time()).isoformat() + "Z"
    end = datetime.combine(end_date, datetime.min.time()).isoformat() + "Z"

    # Retrieve all calendars
    calendar_list = service.calendarList().list().execute()

    today_events: List[CalendarEvent] = []
    for calendar_entry in calendar_list.get('items', []):
        events_result = (
            service.events()
            .list(
                calendarId=calendar_entry['id'],
                timeMin=start,
                timeMax=end,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            end = event["end"].get("dateTime", event["end"].get("date"))
            today_events.append(
                CalendarEvent(
                    summary=event["summary"],
                    creator=event.get("creator").get("email", ""),
                    organizer=event.get("organizer").get("email", ""),
                    attendees=[
                        attendee.get("email", "") for attendee in event.get("attendees", [])
                    ],
                    start=start,
                    end=end,
                    description=event.get("description", ""),
                    location=event.get("location", ""),
                )
            )

    # events_result = (
    #     service.events()
    #     .list(
    #         calendarId="primary",
    #         timeMin=start,
    #         timeMax=end,
    #         singleEvents=True,
    #         orderBy="startTime",
    #     )
    #     .execute()
    # )
    # events = events_result.get("items", [])

    # today_events: List[CalendarEvent] = []
    # for event in events:
    #     start = event["start"].get("dateTime", event["start"].get("date"))
    #     end = event["end"].get("dateTime", event["end"].get("date"))
    #     today_events.append(
    #         CalendarEvent(
    #             summary=event["summary"],
    #             creator=event.get("creator").get("email", ""),
    #             organizer=event.get("organizer").get("email", ""),
    #             attendees=[
    #                 attendee.get("email", "") for attendee in event.get("attendees", [])
    #             ],
    #             start=start,
    #             end=end,
    #             description=event.get("description", ""),
    #             location=event.get("location", ""),
    #         )
    #     )

    if DEBUG >= 1:
        print(f"Found {len(events)} events for today.", flush=True)
        for event in today_events:
            print(f"Summary: {event.summary}", flush=True)
            print(f"Creator: {event.creator}", flush=True)
            print(f"Organizer: {event.organizer}", flush=True)
            print(f"Attendees: {event.attendees}", flush=True)
            print(f"Start: {event.start}", flush=True)
            print(f"End: {event.end}", flush=True)
            print(f"Description: {event.description}", flush=True)
            print(f"Location: {event.location}", flush=True)
            print("---", flush=True)

    return today_events


if __name__ == "__main__":
    events = get_today_events()
