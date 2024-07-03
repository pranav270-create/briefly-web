import asyncio, os
from typing import List, Tuple
from pydantic import BaseModel
from anthropic import AsyncAnthropic
from integrations.gmail import get_messages_since_yesterday, get_attendee_email_threads, GmailMessage
from integrations.google_calendar import get_today_events

DEBUG = 1
SELF_EMAIL = "markacastellano2@gmail.com"


class EmailResponse(BaseModel):
    personal_emails: List[GmailMessage]
    news_emails: List[GmailMessage]
    spam_emails: List[GmailMessage]


def anthropic_cost(usage):
    return (usage.input_tokens * 3 * 1e-6) + (usage.output_tokens * 15 * 1e-6) # sonnet pricing


async def summarize_thread(client, thread_messages):
    combined_content = "\n\n".join([f"Subject: {msg.subject}\nFrom: {msg.sender}\nBody: {msg.body[:500]}..." for msg in thread_messages])
    prompt = f"""
    Summarize the following email thread concisely:

    {combined_content}

    Provide a brief summary that captures the main points and any important details.
    """
    
    response = await client.messages.create(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
        temperature=0.0,
        model="claude-3-5-sonnet-20240620"
    )
    cost = anthropic_cost(response.usage)
    return response.content[0].text.strip(), cost


async def get_event_related_emails():
    """
    Get's emails related to todays events
    """
    client = AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    
    # Get today's events
    events = await get_today_events()
    
    event_summaries = []
    total_cost = 0
    for event in events:
        attendees = event['attendees']
        non_self_attendees = [attendee for attendee in attendees if attendee != SELF_EMAIL]
        
        event_summary = {
            'event': event['summary'],
            'start': event['start'],
            'end': event['end'],
            'attendee_summaries': []
        }


        for attendee in non_self_attendees:
            # Get email threads for the attendee
            thread_messages = get_attendee_email_threads(attendee)
            
            if thread_messages:
                # Summarize the thread
                summary, cost = await summarize_thread(client, thread_messages)
                event_summary['attendee_summaries'].append({
                    'attendee': attendee,
                    'summary': summary
                })
                total_cost += cost
        
        event_summaries.append(event_summary)
        
    if DEBUG >= 1:
        print(f"\033[95mTotal Cost: ${total_cost:.5f}\033[0m", flush=True)
    
    return event_summaries


async def classify_email(client, email: GmailMessage) -> Tuple[str, int]:
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


async def summarize_email(client, email: GmailMessage) -> Tuple[str, int]:
    """
    Summarizes personal and news emails
    """
    prompt = f"""
    You are a personal assistant, and I need help staying on top of my email inbox. 
    Summarize the following email concisely:

    <email>
    From: {email.sender}
    Subject: {email.subject}
    Body: {email.body}
    </email>

    Capture the main points and any important details.
    """
    if email.classification == "personal":
        prompt += f"\nThis is a personal email, so keep the summary very short."
        max_tokens = 128
    elif email.classification == "news":
        prompt += f"\nThis email is news, so your description of each newsworthy item should be concise so I can quickly know what's throughout the newsletter."
        max_tokens = 768

    response = await client.messages.create(
        messages=[{"role": "user", "content": prompt}, {"role":"assistant", "content": "<summary>"}],
        stop_sequences=["</summary>"],
        max_tokens=max_tokens,
        temperature=0.0,
        model="claude-3-5-sonnet-20240620"
    )
    cost = anthropic_cost(response.usage)
    return response.content[0].text.strip(), cost


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

    # Summarize useful emails
    useful_emails: List[GmailMessage] = personal + news
    summary_tasks = [summarize_email(client, email) for email in useful_emails]
    results = await asyncio.gather(*summary_tasks)
    summaries = [result[0] for result in results]
    total_cost += sum([result[1] for result in results])

    # save summaries
    for email, summary in zip(useful_emails, summaries):
        email.summary = summary

    # printing
    if DEBUG >= 1:
        for i, email in enumerate(useful_emails + spam):
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
    asyncio.run(get_email_data())