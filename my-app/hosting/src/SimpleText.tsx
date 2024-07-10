import React, { useState, useEffect, useRef } from 'react';
import { fetchEventSource } from '@microsoft/fetch-event-source';

import baseUrl from './env';

const SimpleText = () => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [recognition, setRecognition] = useState(null);
  const [answer, setAnswer] = useState('');
  const eventSource = useRef(null);

  useEffect(() => {
    if ('webkitSpeechRecognition' in window) {
      const recognitionInstance = new window.webkitSpeechRecognition();
      recognitionInstance.continuous = true;
      recognitionInstance.interimResults = true;

      recognitionInstance.onresult = (event) => {
        const current = event.resultIndex;
        const transcript = event.results[current][0].transcript;
        setTranscript(transcript);
      };

      recognitionInstance.onerror = (event) => {
        console.error('Speech recognition error', event.error);
      };

      setRecognition(recognitionInstance);
    } else {
      console.log('Speech recognition not supported');
    }
  }, []);

  const startListening = () => {
    if (recognition) {
      recognition.start();
      setIsListening(true);
      setAnswer(''); // Clear previous answer
    }
  };

  const stopListening = async () => {
    if (recognition) {
      recognition.stop();
      setIsListening(false);
      
      // Send transcript to Anthropic API
      await sendToAnthropicAPI(transcript);
    }
  };

  const handleEvent = async (data: any) => {
    const answer = data.answer;
    setAnswer((prevAnswer) => prevAnswer + answer);
  }

  const sendToAnthropicAPI = async (question: string) => {
    eventSource.current = await fetchEventSource(`${baseUrl}/anthropic`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: question }),
        onopen: (res) => {
            if (res.ok && res.status === 200) {
                console.log("Connection made ", res);
            } else if (res.status >= 400 && res.status < 500 && res.status !== 429) {
                console.log("Client-side error ", res);
            }
        },
        onmessage: (event) => {
            console.log("Message received from server", event);
            if (!event.data) return;
            handleEvent(JSON.parse(event.data));
        },
        onclose: () => { console.log("Connection closed by the server"); },
        onerror: (err) => { console.log("There was an error from server", err); },
    });
  };

  return (
    <div>
      <button onClick={isListening ? stopListening : startListening}>
        {isListening ? '⏹️' : '🎙️'}
      </button>
      <p>Your question: {transcript}</p>
      {answer && <p>Answer: {answer}</p>}
    </div>
  );
};

export default SimpleText;