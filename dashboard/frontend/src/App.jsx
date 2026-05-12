import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

function App() {
  const [repoUrl, setRepoUrl] = useState('https://github.com/mohabbadawy1/click');
  const [logs, setLogs] = useState([]);
  const [status, setStatus] = useState({ running: false, pr_url: null });
  const [ws, setWs] = useState(null);

  useEffect(() => {
    // Connect to WebSocket
    const websocket = new WebSocket('ws://localhost:8000/ws');
    
    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'log') {
        setLogs(prev => [...prev, data.message]);
      }
    };

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    setWs(websocket);

    return () => websocket.close();
  }, []);

  const runPipeline = async () => {
    try {
      const response = await axios.post(`${API_URL}/run?repo_url=${repoUrl}`);
      console.log('Pipeline started:', response.data);
      
      // Poll status
      const interval = setInterval(async () => {
        const statusResponse = await axios.get(`${API_URL}/status`);
        setStatus(statusResponse.data);
        if (!statusResponse.data.running) {
          clearInterval(interval);
        }
      }, 1000);
    } catch (error) {
      console.error('Error starting pipeline:', error);
    }
  };

  return (
    <div style={{ background: '#0a0a0a', color: '#fff', fontFamily: 'monospace', padding: '40px', minHeight: '100vh' }}>
      <h1 style={{ color: '#e8251a' }}>
        Code<span style={{ color: '#fff' }}>Sentinel</span>
      </h1>
      
      <div style={{ marginBottom: '20px' }}>
        <input
          type="text"
          value={repoUrl}
          onChange={(e) => setRepoUrl(e.target.value)}
          placeholder="Enter GitHub repo URL"
          style={{ width: '100%', padding: '10px', marginBottom: '10px', background: '#1a1a1a', color: '#fff', border: '1px solid #333' }}
        />
        <button
          onClick={runPipeline}
          disabled={status.running}
          style={{ padding: '10px 20px', background: '#e8251a', color: '#fff', border: 'none', cursor: 'pointer' }}
        >
          {status.running ? 'Running...' : 'Run Pipeline'}
        </button>
      </div>

      {status.pr_url && (
        <div style={{ color: '#0f0', marginBottom: '20px' }}>
          ✓ PR Created: <a href={status.pr_url} target="_blank" rel="noreferrer">{status.pr_url}</a>
        </div>
      )}

      <div style={{ background: '#1a1a1a', padding: '20px', borderRadius: '4px', maxHeight: '500px', overflow: 'auto' }}>
        <div style={{ fontSize: '12px', lineHeight: '1.5' }}>
          {logs.map((log, i) => (
            <div key={i}>{log}</div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default App;
