import asyncio, os
from typing import List, Tuple
from pydantic import BaseModel, Field
from anthropic import AsyncAnthropic
from instructor import from_anthropic, Mode

from integrations.gmail import get_messages_since_yesterday, get_attendee_email_threads, GmailMessage
from integrations.google_calendar import get_today_events, CalendarEvent

DEBUG = 1
SELF_EMAIL = "markacastellano2@gmail.com"


class EmailResponse(BaseModel):
    personal_emails: List[GmailMessage]
    news_emails: List[GmailMessage]
    spam_emails: List[GmailMessage]


class NewsletterSummary(BaseModel):
    """
    A summary of a newsletter, represented as a comma-separated list containing key topics and their brief descriptions.
    """
    topic_summaries: List[str] = Field(description="A comma-separated list of brief summaries or key points for each main topic")


class CalendarResponse(BaseModel):
    events: List[CalendarEvent]


def anthropic_cost(usage):
    return (usage.input_tokens * 3 * 1e-6) + (usage.output_tokens * 15 * 1e-6) # sonnet pricing


async def summarize_thread(client, thread):
    thread_messages = [t['messages'][0] for t in thread]
    attendees = [t['attendees'] for t in thread]
    all_participants = [t['all_participants'] for t in thread]
    
    combined_content = "\n\n".join([
        f"Subject: {msg.subject}\nFrom: {msg.sender} <{msg.sender_email}>\nBody: {msg.body[:500]}..." 
        for msg in thread_messages
    ])
    
    prompt = f"""
    Summarize the following email thread concisely:

    {combined_content}

    Provide a brief summary that captures the main points and any important details.
    Focus on information relevant to the attendees listed above.
    """
    
    response = await client.messages.create(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
        temperature=0.0,
        model="claude-3-5-sonnet-20240620"
    )
    cost = anthropic_cost(response.usage)
    return response.content[0].text.strip(), cost


async def get_event_related_emails() -> CalendarResponse:
    """
    Get's emails related to todays events
    """
    client = AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    
    # Get today's events
    events: List[CalendarEvent] = get_today_events()
    
    total_cost = 0
    for event in events:
        attendees = event.attendees
        non_self_attendees = [attendee for attendee in attendees if attendee != SELF_EMAIL]
        
        thread_messages = get_attendee_email_threads(non_self_attendees)

        if thread_messages:
            # Summarize the thread
            summary, cost = await summarize_thread(client, thread_messages)
            event.context = summary
            total_cost += cost
                
    if DEBUG >= 1:
        print(f"\033[95mTotal Cost: ${total_cost:.5f}\033[0m", flush=True)
    
    return CalendarResponse(events=events)


async def classify_email(client, email: GmailMessage) -> Tuple[str, float]:
    """
    Classifies personal, news, and spam emails
    """
    prompt = f"""
    Classify the following email into one of the following categories:
    <categories>
    personal
    news
    spam
    </categories>

    personal emails are emails from individuals or emails directed to me. I am personally uninterested in emails that act as notifications.
    news emails are typically newsletters with news about what's going on in the world. 
    spam emails are often promotional emails that try to sell products, ask for donations, notify of sales, or notify terms of service changes 

    Here is the email:
    <email>
    From: {email.sender}
    Subject: {email.subject}
    Body: {email.body[:500]}...
    </email>
    """
    
    response = await client.messages.create(
        messages=[{"role":"user", "content": prompt}, {"role":"assistant", "content": "<category>"}],
        stop_sequences=["</category>"], 
        max_tokens=64, 
        temperature=0.0,
        model="claude-3-5-sonnet-20240620"
    )
    cost = anthropic_cost(response.usage)
    return response.content[0].text.strip(), cost


async def summarize_personal_email(client, email: GmailMessage) -> Tuple[str, int]:
    """
    Succinctly summarize personal emails
    """
    prompt = f"""
    You are a personal assistant, and I need help staying on top of my email inbox. 
    Summarize the following email concisely:

    <email>
    From: {email.sender}
    Subject: {email.subject}
    Body: {email.body}
    </email>

    Capture the central message the email is trying to convey. Keep the summary very short
    """
    response = await client.messages.create(
        messages=[{"role": "user", "content": prompt}, {"role":"assistant", "content": "<summary>"}],
        stop_sequences=["</summary>"],
        max_tokens=100,
        temperature=0.0,
        model="claude-3-5-sonnet-20240620"
    )
    cost = anthropic_cost(response.usage)
    return response.content[0].text.strip(), cost


async def summarize_news_email(client, email: GmailMessage) -> Tuple[NewsletterSummary, float]:
    """
    Summarize news emails
    """
    prompt = f"""
    Summarize the key topics in the following newsletter. Please respond invalid JSON.

    NewsLetter:
    From: {email.sender}
    Subject: {email.subject}
    Body: {email.body}
    """
    response_model, completion = await client.messages.create_with_completion(
        model="claude-3-5-sonnet-20240620",
        max_tokens = 1024,
        max_retries=0,
        messages=[{"role": "user", "content": prompt}],
        response_model=NewsletterSummary
    )
    cost = anthropic_cost(completion.usage)
    return response_model, cost


async def get_email_data() -> Tuple[List[GmailMessage], List[GmailMessage]]:
    """
    Gets emails from past day
    Classifies them as personal, news, spam
    Summarizes them
    """
    # get emails
    emails: List[GmailMessage] = get_messages_since_yesterday()
    
    # classify emails
    client = AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    classification_tasks = [classify_email(client, email) for email in emails]
    results = await asyncio.gather(*classification_tasks)
    classifications = [result[0] for result in results]
    total_cost = sum([result[1] for result in results])
    
    # save classification and filter
    personal, news, spam = [], [], []
    for email, classification in zip(emails, classifications):
        email.classification = classification
        if classification == "personal":
            personal.append(email)
        elif classification == "news":
            news.append(email)
        elif classification == "spam":
            spam.append(email)

    # Summarize personal emails
    personal_email_tasks = [summarize_personal_email(client, email) for email in personal]
    personal_email_results = await asyncio.gather(*personal_email_tasks)
    personal_summaries = [result[0] for result in personal_email_results]
    for email, summary in zip(personal, personal_summaries):
        email.summary = summary
    total_cost += sum([result[1] for result in personal_email_results])

    # Summarize news emails
    instructor_client = from_anthropic(client=AsyncAnthropic(), mode=Mode.ANTHROPIC_JSON)
    news_email_tasks = [summarize_news_email(instructor_client, email) for email in news]
    news_email_results = await asyncio.gather(*news_email_tasks)
    news_summaries: List[NewsletterSummary] = [result[0] for result in news_email_results]
    for email, summary in zip(news, news_summaries):
        email.summary = summary.topic_summaries
    total_cost += sum([result[1] for result in news_email_results])

    # printing
    if DEBUG >= 1:
        for i, email in enumerate(personal + news + spam):
            if email.classification == "personal":
                print(f"\033[92mEmail {i+1}: {email.classification}\033[0m", flush=True)
            elif email.classification == "news":
                print(f"\033[94mEmail {i+1}: {email.classification}\033[0m", flush=True)
            elif email.classification == "spam":
                print(f"\033[91mEmail {i+1}: {email.classification}\033[0m", flush=True)
            else:
                print(f"\033[93mEmail {i+1}: {email.classification}\033[0m", flush=True)
            print(f"From: {email.sender}", flush=True)
            print(f"Subject: {email.subject}", flush=True)
            print(f"Summary: {email.summary}", flush=True)
            print("---", flush=True)
        print(f"\033[95mTotal Cost: ${total_cost:.5f}\033[0m", flush=True)

    return EmailResponse(
        personal_emails=personal,
        news_emails=news,
        spam_emails=spam
    )


if __name__ == "__main__":
    asyncio.run(get_event_related_emails())