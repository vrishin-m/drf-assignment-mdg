import { useState, useEffect } from 'react';
import api from '../api';

export default function StudiosView() {
  const [studios, setStudios] = useState([]);
  const [studioName, setStudioName] = useState('');
  const [message, setMessage] = useState('');
  const [isError, setIsError] = useState(false);
  const [loading, setLoading] = useState(true);


  useEffect(() => {
    const fetchStudios = async () => {
      try {
        const response = await api.get('/studios/');

        setStudios(response.data);
        setLoading(false);
      } catch (err) {
        console.error("Error fetching studios:", err.response?.data);
        setIsError(true);
        setMessage('Failed to load studios. Make sure you are logged in.');
        setLoading(false);
      }
    };

    fetchStudios();
  }, []);


  const handleCreateStudio = async (e) => {
    e.preventDefault();
    setMessage('');
    setIsError(false);

    if (!studioName.trim()) return;

    try {
      const response = await api.post('/studios/', { name: studioName });


      setStudios([response.data, ...studios]);
      setStudioName(''); 
      setMessage(`Studio "${response.data.name}" created successfully!`);

    } catch (err) {
      console.error("Error creating studio:", err.response?.data);
      setIsError(true);
      setMessage(err.response?.data?.detail || 'Failed to create studio space.');
    }
  };

  return (
    <div style={styles.page}>
      <h2> Studio Workspace Hub</h2>
      <p style={{ color: '#718096', marginBottom: '30px' }}>Create studios and Manage them</p>

      {/* FEEDBACK STATUS BAR */}
      {message && (
        <div style={{ 
          ...styles.alert, 
          backgroundColor: isError ? '#fff5f5' : '#f0fff4', 
          color: isError ? '#c53030' : '#2f855a',
          border: `1px solid ${isError ? '#feb2b2' : '#c6f6d5'}`
        }}>
          {message}
        </div>
      )}

      {/* STUDIO ENVIRONMENT GENERATION FORM */}
      <form onSubmit={handleCreateStudio} style={styles.form}>
        <h4 style={{ margin: '0 0 12px 0', color: '#2d3748' }}>Initialize New Workspace</h4>
        <div style={{ display: 'flex', gap: '12px' }}>
          <input 
            type="text" 
            placeholder="E.g., potato tomato studio" 
            value={studioName}
            onChange={(e) => setStudioName(e.target.value)}
            style={styles.input}
            required
          />
          <button type="submit" style={styles.submitButton}>Launch Studio</button>
        </div>
      </form>

      {/* DISPLAY LOOP FOR RETRIEVED STUDIOS */}
      <h3>Active Workspaces</h3>
      {loading ? (
        <p style={{ color: '#a0aec0', fontStyle: 'italic' }}>Querying database...</p>
      ) : studios.length === 0 ? (
        <p style={{ color: '#a0aec0', fontStyle: 'italic' }}>No active studios found. make one!</p>
      ) : (
        <div style={styles.studioGrid}>
          {studios.map((studio) => (
            <div key={studio.id} style={styles.studioCard}>
              <div style={styles.avatar}>🎬</div>
              <div>
                <strong style={{ display: 'block', fontSize: '16px', color: '#1a202c' }}>{studio.name}</strong>
                <span style={{ fontSize: '12px', color: '#a0aec0' }}>ID: {studio.id}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const styles = {
  page: { padding: '100px 20px', fontFamily: 'sans-serif', maxWidth: '800px', margin: '0 auto' },
  form: { backgroundColor: '#fff', padding: '20px', borderRadius: '8px', border: '1px solid #e2e8f0', marginBottom: '30px', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' },
  input: { flex: 1, padding: '12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px', outline: 'none' },
  submitButton: { padding: '12px 24px', backgroundColor: '#3182ce', color: 'white', border: 'none', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer', fontSize: '14px' },
  studioGrid: { display: 'flex', flexDirection: 'column', gap: '12px' },
  studioCard: { display: 'flex', alignItems: 'center', gap: '16px', backgroundColor: '#fff', padding: '16px', borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 2px 4px rgba(0,0,0,0.02)' },
  avatar: { width: '40px', height: '40px', backgroundColor: '#ebf8ff', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '18px' },
  alert: { padding: '12px', borderRadius: '6px', fontSize: '14px', fontWeight: '500', marginBottom: '20px' }
};