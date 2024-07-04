import { useEffect, useState } from 'react';
import { GoogleOAuthProvider } from '@react-oauth/google';

import GoogleSignIn from './GoogleLogin';
import Footer from './Footer.tsx';
import './App.css';

const baseUrl: string = 'https://briefly-backend-krnivdrwhq-uk.a.run.app';
// const baseUrl: string = 'http://localhost:8000';

interface Email {
  subject: string;
  sender: string;
  summary: string;
}

interface CalendarEvent {
  summary: string;
  creator: string;
  organizer: string;
  attendees: string[];
  start: string;
  end: string;
  description: string;
  location: string;
  context: string;
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
  
  const handleLoginSuccess = async (idToken: string) => {
    try {
      localStorage.setItem('id_token', idToken);
      // Send the ID token to your backend
      const response = await fetch(`${baseUrl}/api/token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ id_token: idToken }),
      });

      if (response.ok) {
        console.log('Backend authentication successful');
      } else {
        console.error('Backend authentication failed');
      }

      const requestOptions = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ idToken: idToken }),
      };

      const [emailsResponse, calendarResponse] = await Promise.all([
        fetch(`${baseUrl}/api/get-emails`, requestOptions),
        fetch(`${baseUrl}/api/get-calendar`, requestOptions),
      ]);

      if (!emailsResponse.ok || !calendarResponse.ok) {
        throw new Error(`HTTP error! status: ${emailsResponse.status} ${calendarResponse.status}`);
      }

      const emailsData = await emailsResponse.json();
      const calendarData = await calendarResponse.json();

      setPersonalEmails(emailsData.personal_emails);
      setNewsEmails(emailsData.news_emails);
      setSpamEmails(emailsData.spam_emails);
      setCalendarEvents(calendarData.events);
    } catch (error) {
      console.error('Error during authentication:', error);
    }
  };

  return (
    <GoogleOAuthProvider clientId="673278476323-gd8p0jcn0lspqs3e8n9civolog1n1b55.apps.googleusercontent.com">
      <div className="main_container">
            <GoogleSignIn onLoginSuccess={handleLoginSuccess} />
        <main className="flex_container">
          <div className="briefly_shadow">
            <pre className="mono_text">
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
          <div className="text_content">
            <h2 className="h2_text">personal</h2>
            <ul className="ul_text">
              {calendarEvents && calendarEvents.map((event, index) => (
                <li key={index} className="p4">
                  <p className="p_text">{event.summary}</p>
                  <p className="p_text">
                    {new Date(event.start).toLocaleString()} - {new Date(event.end).toLocaleString()}
                  </p>
                  {event.location && (
                    <p className="p_text">
                      <span className="font-medium">Location:</span> {event.location}
                    </p>
                  )}
                  {event.attendees && event.attendees.length > 0 && (
                    <div className="mb-2">
                      <p className="p_text">Attendees:</p>
                      <ul className="list_disc">
                        {event.attendees.map((attendee, idx) => (
                          <li key={idx} className="text-sm text-sub_sub_grey ml-4">{attendee}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {event.context && (
                    <div className="mt-2">
                      <p className="text-sm font-medium text-sub_grey mb-1">Context:</p>
                      <p className="text-sm text-sub_sub_grey whitespace-pre-wrap">{event.context}</p>
                    </div>
                  )}
                </li>
              ))}
              {personalEmails && personalEmails.map((email, index) => (
                <li key={index} className="p4">
                  <p className="md_text">{email.sender}</p>
                  <p className="md_text">{email.subject}</p>
                  <p className="sm_text">{email.summary}</p>
                </li>
              ))}
            </ul>
            <div className="mt_8"></div>

            <h2 className="mb_6">news</h2>
            <ul className="space-y-2">
              {newsEmails && newsEmails.map((email, index) => (
                <li key={index} className="p4">
                  <p className="md_text">{email.sender}</p>
                  <p className="md_text">{email.subject}</p>
                  <p className="sm_text">{email.summary}</p>
                </li>
              ))}
            </ul>
          </div>
        </main>
        <Footer />
      </div>
    </GoogleOAuthProvider>
  );
}