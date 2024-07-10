import React, { useState, useEffect, useRef } from 'react';
import { fetchEventSource } from '@microsoft/fetch-event-source';

import baseUrl from './env';

const AudioStreamer = () => {
    const [answer, setAnswer] = useState('');
    const [audioQueue, setAudioQueue] = useState<string[]>([]);
    const [isPlaying, setIsPlaying] = useState(false);
    const eventSource = useRef(null);

    const [isListening, setIsListening] = useState(false);
    const [transcript, setTranscript] = useState('');
    const [recognition, setRecognition] = useState(null);
  
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
        await startStreaming(transcript);
      }
    };

    const handleEvent = (data: any) => {
        const text = data.text;
        const audio = data.audio;
        setAnswer((prevAnswer) => prevAnswer + text);
        setAudioQueue((prevQueue) => [...prevQueue, audio]);
    };

    useEffect(() => {
      // This function ensures that audio playback starts only if there's audio in the queue and nothing is currently playing.
      const startPlayback = () => {
          if (audioQueue.length > 0 && !isPlaying) {
              playNextAudio();
          }
      };
  
      // Call startPlayback when the component mounts and whenever audioQueue or isPlaying changes.
      startPlayback();
  
      return () => {
          // Implement any necessary cleanup here, such as stopping current audio playback if needed.
      };
    }, [audioQueue, isPlaying]); // Depend on audioQueue and isPlaying to re-evaluate when they change.
  
    const playNextAudio = () => {
      if (audioQueue.length === 0) {
          setIsPlaying(false); // Ensure isPlaying is set to false when the queue is empty.
          return;
      }
  
      setIsPlaying(true);
      const audioData = atob(audioQueue[0]); // Decode the first audio in the queue.
      const audioBlob = new Blob([new Uint8Array(audioData.split('').map(char => char.charCodeAt(0)))], { type: 'audio/mpeg' });
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
  
      audio.onended = () => {
          setAudioQueue((prevQueue) => prevQueue.slice(1)); // Remove the first audio from the queue.
          setIsPlaying(false); // Set isPlaying to false to allow the next audio to play.
      };
  
      audio.play().then(() => {
          setIsPlaying(true); // Ensure isPlaying is true while the audio is playing.
      }).catch((error) => {
          console.error("Error playing audio:", error);
          setIsPlaying(false); // Handle play error by setting isPlaying to false.
      });
  };

    const startStreaming = async (question: string) => {
      eventSource.current = await fetchEventSource(`${baseUrl}/anthropic_speech`, {
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

export default AudioStreamer;