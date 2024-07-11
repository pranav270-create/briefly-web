import { useEffect, useState, useCallback } from 'react';

import Footer from './Footer';
import GoogleLogin from './GoogleLogin';
import {baseUrl} from './env';
import AudioStreamer from './TextAndSpeech';
import SimpleText from './SimpleText';

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
  const [selectedCalendarId, setSelectedCalendarId] = useState<string | null>(null);
  const [selectedPersonalEmailId, setSelectedPersonalEmailId] = useState<string | null>(null);
  const [selectedNewsItemIds, setSelectedNewsItemIds] = useState<Set<string>>(new Set());
  const [lessBriefData, setLessBriefData] = useState<LessBriefData | null>(null);
  const [cachedLessBriefData, setCachedLessBriefData] = useState<CachedLessBriefData>({});
  const [isLoading, setIsLoading] = useState(false);

  async function fetchData() {
    setIsLoading(true);
    try {
      const [emailsResponse, calendarResponse] = await Promise.all([
        fetch(`${baseUrl}/get-emails`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('jwtToken')}`,
          },
        }),
        fetch(`${baseUrl}/get-calendar`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('jwtToken')}`,
          },
        }),
      ]);

      if (!emailsResponse.ok || !calendarResponse.ok) {
        throw new Error(`HTTP error! status: ${emailsResponse.status} ${calendarResponse.status}`);
      }

      const emailsData = await emailsResponse.json();
      const calendarData = await calendarResponse.json();
      console.log(emailsData);
      console.log(calendarData);

      setPersonalEmails(emailsData.personal_emails);
      setNewsEmails(emailsData.news_emails);
      setSpamEmails(emailsData.spam_emails);
      setCalendarEvents(calendarData.events);
      setIsLoading(false);
    } catch (error) {
      setIsLoading(false);
      console.error('Error fetching data:', error);
    }
  }

  const handleItemClick = useCallback(async (id: string, data: any, clickedSummary?: string) => {
    // classify the pr
    const isCalendar = 'start' in data;
    const isPersonalEmail = data.classification === 'personal';
    const isNewsItem = !isCalendar && !isPersonalEmail;

    // data ids
    if (isCalendar) {
      setSelectedCalendarId(prevId => prevId === id ? null : id);
    } else if (isPersonalEmail) {
      setSelectedPersonalEmailId(prevId => prevId === id ? null : id);
    } else if (isNewsItem) {
      setSelectedNewsItemIds(prevIds => {
        const newIds = new Set(prevIds);
        if (newIds.has(id)) {
          newIds.delete(id);
        } else {
          newIds.add(id);
        }
        return newIds;
      });
    }

    // Handle content based on item type
    if (!cachedLessBriefData[id]) {
      try {
        let content;
        if (isNewsItem) {
          // For news items, issue a POST request
          const response = await fetch(`${baseUrl}/less-brief`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ clickedSummary }),
          });
          if (!response.ok) {
            throw new Error('Failed to fetch less brief data');
          }
          content = await response.json();
        } else if (isPersonalEmail) {
          // For personal emails, use the data directly
          content = { content: data.body }; // Assuming 'data.body' contains the email content
        } else if (isCalendar) {
          // For calendar items, format the content
          content = {
            content: `
              Event: ${data.summary}
              When: ${data.start} - ${data.end}
              Where: ${data.location || 'No location specified'}
              Organizer: ${data.organizer}
              Attendees: ${data.attendees.join(', ')}

              Description:
              ${data.description}

              Context:
              ${data.context}
            `.trim()
          };
        }
        // Update the cache with the content
        setCachedLessBriefData(prev => ({ ...prev, [id]: content }));
      } catch (error) {
        console.error('Error handling item click:', error);
      }
    }
  }, []);

  const renderItem = useCallback((item: CalendarEvent | Email, index: number, type: 'calendar' | 'email') => {
    const id = `${type}-${index}`;
    const itemLessBriefData = cachedLessBriefData[id];
    const isCalendar = type === 'calendar';
    const isPersonalEmail = type === 'email' && (item as Email).classification === 'personal';
    const isNewsItem = type === 'email' && (item as Email).classification !== 'personal';
    
    const isSelected = isCalendar ? selectedCalendarId === id :
                       isPersonalEmail ? selectedPersonalEmailId === id :
                       selectedNewsItemIds.has(id);

    return (
      <li 
        key={id} 
        className={`p-4 transition-colors duration-200 rounded-lg ${(isCalendar || isPersonalEmail) ? 'cursor-pointer' : ''} ${isSelected ? 'bg-briefly_box' : (isCalendar || isPersonalEmail) ? 'hover:bg-briefly_box' : ''}`}
        onClick={() => (isCalendar || isPersonalEmail) ? handleItemClick(id, item) : null}
        >
        {isCalendar ? (
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
            {isSelected && itemLessBriefData && (
              <div className="mt-4 p-4 bg-briefly_box rounded-lg">
                <p className="text-sm text-sub_sub_grey whitespace-pre-wrap">{itemLessBriefData.content}</p>
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
                    onClick={(e) => {
                      e.stopPropagation();
                      handleItemClick(`${id}-${summaryIndex}`, item, summaryItem);
                    }}
                  >
                    <p className="text-sm text-sub_sub_grey">{summaryItem}</p>
                    {selectedNewsItemIds.has(`${id}-${summaryIndex}`) && cachedLessBriefData[`${id}-${summaryIndex}`] && (
                      <div className="mt-4 p-4 bg-briefly_box rounded-lg">
                        <p className="text-sm text-sub_sub_grey whitespace-pre-wrap">{cachedLessBriefData[`${id}-${summaryIndex}`].content}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p
              className="text-sm text-sub_sub_grey "
              onClick={() => isPersonalEmail ? handleItemClick(id, item) : null}
              >
                {(item as Email).summary}
            </p>
            )}
            {isPersonalEmail && isSelected && itemLessBriefData && (
              <div className="mt-4 p-4 bg-briefly_box rounded-lg">
                <p className="text-sm text-sub_sub_grey whitespace-pre-wrap">{itemLessBriefData.content}</p>
              </div>
            )}
          </>
        )}
      </li>
    );
  }, [selectedCalendarId, selectedPersonalEmailId, selectedNewsItemIds, cachedLessBriefData, handleItemClick]);

  return (
    <div className="bg-midjourney_navy flex flex-col min-h-screen text-white">
      <GoogleLogin />
      {localStorage.getItem('jwtToken') && (
        <button
          onClick={fetchData}
          style={{
            padding: '10px', // Adjust padding for circular shape
            width: '50px', // Fixed width for circle
            height: '50px', // Fixed height for circle
            border: 'none',
            borderRadius: '50%', // Make it circular
            cursor: 'pointer',
            fontSize: '16px',
            display: 'flex', // Use flex to center the text/icon
            alignItems: 'center', // Center vertically
            justifyContent: 'center', // Center horizontally
            position: 'absolute', // Position the button
            top: '0', // Top right corner
            right: '30px', // Top right corner
            ...(isLoading ? { animation: 'spin 1s linear infinite' } : {}), // Conditional animation
          }}
      >
        {isLoading ? '🔄' : '📥'}
      </button>
      )}
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
        <h2 className="text-3xl font-bold mb-6">daily learning</h2>
        {/* <AudioStreamer /> */}
        <SimpleText />
        <h2 className="text-3xl font-bold mb-6">calendar</h2>
        <ul className="space-y-2">
          {calendarEvents.map((event, index) => renderItem(event, index, 'calendar'))}
        </ul>
        <h2 className="text-3xl font-bold mb-6">personal</h2>
        <ul className="space-y-2">
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