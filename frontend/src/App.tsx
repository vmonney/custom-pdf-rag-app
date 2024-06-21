import React, { useState } from 'react';
import './App.css';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import ReactMarkdown from 'react-markdown';

interface Message {
  message: string;
  isUser: boolean;
  sources?: string[];
}

function App() {
  const [inputValue, setInputValue] = useState("")
  const [messages, setMessages] = useState<Message[]>([]);

  const setPartialMessage = (chunk: string, sources: string[] = []) => {
    setMessages(prevMessages => {
      // Check if there are any messages already
      if (prevMessages.length === 0) {
        return [{ message: chunk, isUser: false, sources }];
      }
  
      // Check if the last message is from the user
      let lastMessage = prevMessages[prevMessages.length - 1];
      if (lastMessage.isUser) {
        return [...prevMessages, { message: chunk, isUser: false, sources }];
      }
  
      // If the last message is not from the user, append the chunk to the last message
      return [
        ...prevMessages.slice(0, -1),
        {
          ...lastMessage,
          message: lastMessage.message + chunk,
          sources: lastMessage.sources ? [...lastMessage.sources, ...sources] : sources,
        }
      ];
    });
  }
  

  function handleReceiveMessage(data: string) {
    let parsedData = JSON.parse(data);
  
    if (parsedData.answer || parsedData.anwser) {
      const content = parsedData.answer ? parsedData.answer.content : parsedData.anwser.content;
      setPartialMessage(content);
    }
  
    if (parsedData.docs) {
      setPartialMessage("", parsedData.docs.map((doc: any) => doc.metadata.source))
    }
  }
  
  const handleSendMessage = async (message: string) => {
    setInputValue("")
    
    setMessages(prevMessages => [...prevMessages, {message, isUser: true}]);

    await fetchEventSource(`${process.env.REACT_APP_BACKEND_URL}/rag/stream`, {
      method: 'POST',
      openWhenHidden: true,
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        input: {
          question: message,
        }
      }),
      onmessage(event) {
        console.log('Event from server:', event); // Log server events
        if (event.event === "data") {
          handleReceiveMessage(event.data);
        }
      },
      onerror(error) {
        console.error('Error in fetchEventSource:', error); // Log errors
      }
    });
  };


  const handleKeyPress = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      handleSendMessage(inputValue.trim())
    }
  }

  function formatSource(source: string) {
    return source.split("/").pop() || "";
  }
  
  return (
    <div className="min-h-screen bg-gray-900 flex flex-col text-white">
      <header className='bg-gradient-to-r from-teal-700 to-gray-700 text-center p-6 shadow-lg'>
        <h1 className="text-3xl font-bold">Ton assistant Bon à Savoir !</h1>
      </header>
      <main className='flex-grow container mx-auto p-6 flex flex-col'>
        <div className='flex-grow bg-gray-800 shadow-lg rounded-lg overflow-hidden'>
          <div className='border-b border-gray-700 p-6'>
            {messages.map((msg, index) => (
              <div key={index} 
                  className={`p-4 my-4 rounded-lg ml-auto ${msg.isUser ? 'bg-gray-700' : 'bg-gray-900'}`}>
                <ReactMarkdown>{msg.message}</ReactMarkdown>         
                {!msg.isUser && (
                  <div className="text-xs mt-4">
                    <hr className='border-gray-600 mb-4'></hr>
                    {msg.sources?.map((source, index) => (
                      <div>
                        <a
                          target="_blank"
                          download
                          href={`${process.env.REACT_APP_BACKEND_URL}/rag/static/${encodeURI(formatSource(source))}`}
                          rel="noreferrer"
                        >{formatSource(source)}</a>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
          <div className='p-6 bg-gray-800'>
            <textarea
              className='form-textarea w-full p-4 border rounded-lg text-white bg-gray-900 border-gray-600 resize-none h-auto'
              placeholder='Posez votre question ici...'
              onKeyUp={handleKeyPress}
              onChange={(e) => setInputValue(e.target.value)}
              value={inputValue}
            ></textarea>
            <button className='mt-4 bg-teal-600 hover:bg-teal-700 text-white font-bold py-2 px-6 rounded-lg transition-all duration-200'
            onClick={() => handleSendMessage(inputValue.trim())}>
              Envoyer
            </button>
          </div>
        </div>
      </main>
      <footer className="bg-gradient-to-r from-teal-700 to-gray-700 text-center p-6 text-xs shadow-lg">
        <p>*AI Agents can make mistakes. Consider checking important information.</p>
        <p>All training data derived from bon à savoir magazine.</p>
        <p className="mt-4">© 2024 Monney Valentin</p>
      </footer>
    </div>
  );
}

export default App;
