"use client";

import { useEffect, useState, useCallback } from 'react';
import Footer from './Footer';

interface Email {
  id: string;
  threadId: string;
  labels: string[];
  snippet: string;
  subject: string;
  sender: string;
  sender_email: string;
  body: string;
  date: string;
  classification: string | null;
  summary: string | string[];
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

interface LessBriefData {
  content: string;
}

interface CachedLessBriefData {
  [key: string]: LessBriefData;
}


export default function Home() {
  const [personalEmails, setPersonalEmails] = useState<Email[]>([]);
  const [newsEmails, setNewsEmails] = useState<Email[]>([]);
  const [spamEmails, setSpamEmails] = useState<Email[]>([]);
  const [calendarEvents, setCalendarEvents] = useState<CalendarEvent[]>([]);
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const [lessBriefData, setLessBriefData] = useState<LessBriefData | null>(null);
  const [cachedLessBriefData, setCachedLessBriefData] = useState<CachedLessBriefData>({});

  useEffect(() => {
    async function fetchData() {
      try {
        const [emailsResponse, calendarResponse] = await Promise.all([
          fetch('http://localhost:8000/api/get-emails'),
          fetch('http://localhost:8000/api/get-calendar')
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
        console.error('Error fetching data:', error);
      } 
    }

    fetchData();
  }, []);

  const handleItemClick = useCallback(async (id: string, data: any) => {
    setSelectedItemId(id);
    if (!cachedLessBriefData[id]) {
    //   setLessBriefData(cachedLessBriefData[id]);
    // } else {
      try {
        const response = await fetch('http://localhost:8000/api/less-brief', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(data),
        });
        if (!response.ok) {
          throw new Error('Failed to fetch less brief data');
        }
        const lessBriefData: LessBriefData = await response.json();
        setLessBriefData(lessBriefData);
      } catch (error) {
        console.error('Error fetching less brief data:', error);
      }
    }
  }, [cachedLessBriefData]);

  const renderItem = useCallback((item: CalendarEvent | Email, index: number, type: 'calendar' | 'email') => {
    const id = `${type}-${index}`;
    const itemLessBriefData = cachedLessBriefData[id];
    return (
      <li 
        key={id} 
        className={`p-4 transition-colors duration-200 rounded-lg ${(type === 'calendar' || (type === 'email' && (item as Email).classification === 'personal')) ? 'cursor-pointer' : ''} ${selectedItemId === id ? 'bg-briefly_box' : (type === 'calendar' || (type === 'email' && (item as Email).classification === 'personal')) ? 'hover:bg-briefly_box' : ''}`}
        onClick={() => type === 'calendar' ? handleItemClick(id, item) : null}
        >
        {type === 'calendar' ? (
          // Render calendar event
          <>
            <p className="text-md font-semibold text-main_white">{(item as CalendarEvent).summary}</p>
            <p className="text-sm text-sub_grey mb-1">
              {new Date((item as CalendarEvent).start).toLocaleString()} - {new Date((item as CalendarEvent).end).toLocaleString()}
            </p>
            {(item as CalendarEvent).location && (
              <p className="text-sm text-sub_grey mb-1">
                <span className="font-medium">Location:</span> {(item as CalendarEvent).location}
              </p>
            )}
            {(item as CalendarEvent).context && (
              <div className="mt-2">
                <p className="text-sm font-medium text-sub_grey mb-1">Context:</p>
                <p className="text-sm text-sub_sub_grey whitespace-pre-wrap">{(item as CalendarEvent).context}</p>
              </div>
            )}
          </>
        ) : (
          // Render email
          <>
            <p className="text-md font-semibold text-main_white">{(item as Email).sender}</p>
            <p className="text-md text-sub_grey">{(item as Email).subject}</p>
            {Array.isArray((item as Email).summary) ? (
              <div className="space-y-1">
                {(item as Email).summary.map((summaryItem: string, summaryIndex: number) => (
                  <div 
                    key={summaryIndex}
                    className="py-1.5 -ml-4 pl-4  bg-midjourney_navy rounded cursor-pointer hover:bg-briefly_box transition-colors duration-200"
                    onClick={() => handleItemClick(`${id}-${summaryIndex}`, { ...item, summary: summaryItem })}
                  >
                    <p className="text-sm text-sub_sub_grey">{summaryItem}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p
              className="text-sm text-sub_sub_grey "
              onClick={() => handleItemClick(id, item)}
              >
                {(item as Email).summary}
            </p>
            )}
          </>
        )}
        {selectedItemId === id && lessBriefData && (
          <div className="mt-4 p-4 bg-briefly_box rounded-lg">
            <p className="text-sm text-sub_sub_grey whitespace-pre-wrap">{lessBriefData.content}</p>
          </div>
        )}
        {itemLessBriefData && (
          <div className={`mt-4 p-4 bg-briefly_box rounded-lg ${selectedItemId === id ? '' : 'opacity-50'}`}>
            <p className="text-sm text-sub_sub_grey whitespace-pre-wrap">{itemLessBriefData.content}</p>
          </div>
        )}
      </li>
    );
  }, [selectedItemId, lessBriefData, handleItemClick]);


  return (
    <div className="bg-midjourney_navy flex flex-col min-h-screen text-white">
      <header className="bg-midjourney_navy w-full flex-shrink-0" style={{ height: '40px' }}>
        <div className="w-full h-full">&nbsp;</div>
      </header>
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
          {calendarEvents.map((event, index) => renderItem(event, index, 'calendar'))}
          {personalEmails.map((email, index) => renderItem(email, index, 'email'))}
        </ul>
        <div className="mt-8"></div>
        <h2 className="text-3xl font-bold mb-6">news</h2>
        <ul className="space-y-2">
          {newsEmails.map((email, index) => renderItem(email, index, 'email'))}
        </ul>
      </main>
      <Footer />
    </div>
  );
}