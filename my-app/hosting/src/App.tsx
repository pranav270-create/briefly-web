import { useEffect, useState } from 'react';
import Footer from './Footer';

const baseUrl: string = 'https://briefly-backend-krnivdrwhq-uk.a.run.app';

interface Email {
  subject: string;
  sender: string;
  summary: string;
}

interface AttendeeEmail {
  attendee: string;
  summary: string;
}

interface CalendarEvent {
  event: string;
  start: string;
  end: string;
  attendee_summaries: AttendeeEmail[];
}

export default function Home() {
  const [personalEmails, setPersonalEmails] = useState<Email[]>([]);
  const [newsEmails, setNewsEmails] = useState<Email[]>([]);
  //@ts-ignore
  const [spamEmails, setSpamEmails] = useState<Email[]>([]);
  const [calendarEvents, setCalendarEvents] = useState<CalendarEvent[]>([]);
  //@ts-ignore
  const [isLoading, setIsLoading] = useState(true);
  //@ts-ignore
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setIsLoading(true);
        setError(null);
        const [emailsResponse, calendarResponse] = await Promise.all([
          fetch(`${baseUrl}/api/get-emails`),
          fetch(`${baseUrl}/api/get-calendar`),
        ]);

        if (!emailsResponse.ok || !calendarResponse.ok) {
          // return some sort of error page
          console.log('not found');
        }

        const emailsData = await emailsResponse.json();
        const calendarData = await calendarResponse.json();

        setPersonalEmails(emailsData.personal_emails);
        setNewsEmails(emailsData.news_emails);
        setSpamEmails(emailsData.spam_emails);
        setCalendarEvents(calendarData.events);
      } catch (error) {
        console.error('Error fetching data:', error);
        setError('Failed to fetch data. Please try again later.');
      } finally {
        setIsLoading(false);
      }
    }

    fetchData();
  }, []);


  return (
    <div className="bg-midjourney_navy flex flex-col min-h-screen text-white">
      <main className="flex-grow container mx-auto px-4 py-8">
        <div className="bg-briefly_box p-6 mb-8 rounded-lg shadow-lg flex justify-center items-center">
          <pre className="text-white font-mono text-sm">
{` _          _       __ _       
| |        (_)     / _| |      
| |__  _ __ _  ___| |_| |_   _ 
| '_ \\| '__| |/ _ \\  _| | | | |
| |_) | |  | |  __/ | | | |_| |
|_.__/|_|  |_|\\___|_| |_|\\__, |
                          __/ |
                         |___/ `}
          </pre>
        </div>
        <h2 className="text-3xl font-bold mb-6">personal</h2>
        <ul className="space-y-2">
          {calendarEvents.map((event, index) => (
            <li key={index} className="p-4">
              <p className="text-md font-semibold text-main_white">{event.event}</p>
              {event.attendee_summaries && event.attendee_summaries.length > 0 && (
                <div>
                  <ul className="list-disc list-inside">
                    {event.attendee_summaries.map((summary, idx) => (
                      <li key={idx} className="ml-4">
                        <span className="font-medium">{summary.attendee}:</span> {summary.summary}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </li>
          ))}
          {personalEmails && personalEmails.map((email, index) => (
            <li key={index} className="p-4">
              <p className="text-md font-semibold text-main_white">{email.sender}</p>
              <p className="text-md text-sub_grey">{email.subject}</p>
              <p className="text-sm text-sub_sub_grey">{email.summary}</p>
            </li>
          ))}
        </ul>
        <div className="mt-8"></div>

        <h2 className="text-3xl font-bold mb-6">news</h2>
        <ul className="space-y-2">
          {newsEmails && newsEmails.map((email, index) => (
            <li key={index} className="p-4">
              <p className="text-md font-semibold text-main_white">{email.sender}</p>
              <p className="text-md text-sub_grey">{email.subject}</p>
              <p className="text-sm text-sub_sub_grey">{email.summary}</p>
            </li>
          ))}
        </ul>
      </main>
      <Footer />
    </div>
  );
}