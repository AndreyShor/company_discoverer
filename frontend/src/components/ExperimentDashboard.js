import React, { useState } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import './ExperimentDashboard.css';

const ExperimentDashboard = () => {
  const [pipeline, setPipeline] = useState('rag');
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [thinking, setThinking] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;

    setMessages(prev => [...prev, { sender: 'User', text: input }]);
    const userInput = input;
    setInput('');
    setThinking(true);

    const endpoint = pipeline === 'rag' ? '/experiment/rag' : '/experiment/hyde';

    axios.post(`http://127.0.0.1:8000${endpoint}`, {
      model: 'gemma-3-4b-it',
      messages: [{ role: 'User', content: userInput }],
      temperature: 0.7
    })
    .then(response => {
      setMessages(prev => [...prev, { sender: 'System', text: response.data.message}]);
      setThinking(false);
    })
    .catch(error => {
      setMessages(prev => [...prev, { sender: 'System', text: 'Error: Unable to fetch response.' }]);
      setThinking(false);
    });
  };

  return (
    <div className="experiment-dashboard">
      <div className="stats-panel">
        <h3>Research Findings (1B vs 4B LLMs)</h3>
        <p>This dashboard replicates the environment used to evaluate RAG vs HyDE methodologies on compact open-weight models regarding Physics domains.</p>
        <div className="stat-cards">
          <div className="stat-card">
            <h4>RAG Impact</h4>
            <p>Reduces latency by up to <strong>17%</strong> across both models and virtually eliminates factual hallucinations.</p>
          </div>
          <div className="stat-card">
            <h4>HyDE Impact</h4>
            <p>Increases semantic relevance for complex queries, but adds a <strong>25-40%</strong> overhead in latency.</p>
          </div>
          <div className="stat-card">
            <h4>Scaling 1B → 4B</h4>
            <p>Scaling yields marginal throughput gains for RAG pipelines but heavily magnifies HyDE’s computational burden.</p>
          </div>
        </div>
      </div>

      <div className="experiment-chat-container">
        <div className="pipeline-selector">
          <label>Select active pipeline: </label>
          <select value={pipeline} onChange={(e) => setPipeline(e.target.value)}>
            <option value="rag">Retrieval-Augmented Generation (RAG)</option>
            <option value="hyde">Hypothetical Document Embeddings (HyDE)</option>
          </select>
        </div>

        <div className="chatbox-messages">
          {messages.map((msg, i) => (
            <div key={i} className={`message ${msg.sender === 'User' ? 'user' : 'bot'}`}>
              <strong>{msg.sender}:</strong>
              <ReactMarkdown>{msg.text}</ReactMarkdown>
            </div>
          ))}
          {thinking && <div className="message bot thinking">Processing request via {pipeline.toUpperCase()}...</div>}
        </div>

        <div className="chatbox-input">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Ask a technical physics question to test the system..."
          />
          <button onClick={handleSend}>Send</button>
        </div>
      </div>
    </div>
  );
};

export default ExperimentDashboard;
