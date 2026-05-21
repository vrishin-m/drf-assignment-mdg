import { useEffect, useState } from 'react';
import api from './api';

function App() {
  const [message, setMessage] = useState('Loading...');

  useEffect(() => {
    api.get('test/')
      .then(response => {
        setMessage(response.data.message);
      })
      .catch(error => {
        console.error("Error fetching data:", error);
        setMessage('Failed to connect to backend.');
      });
  }, []);

  return (
    <div style={{ padding: '40px', fontFamily: 'sans-serif', textAlign: 'center' }}>
      <h1>Creative Studio Workflow</h1>
      <p style={{ fontSize: '1.2rem', color: '#4A5568' }}>
        Backend Status: <strong>{message}</strong>
      </p>
    </div>
  );
}

export default App;