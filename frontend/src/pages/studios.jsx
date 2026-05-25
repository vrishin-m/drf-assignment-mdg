import { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom'; 
import api from '../api';

export default function StudiosView() {
  const navigate = useNavigate(); 
  const [studios, setStudios] = useState([]);
  const [studioName, setStudioName] = useState('');
  const [message, setMessage] = useState('');
  const [isError, setIsError] = useState(false);
  const [loading, setLoading] = useState(true);
  const [activeStudioSlug, setActiveStudioSlug] = useState(
    localStorage.getItem('current_studio_slug') || ''
  );


  useEffect(() => {
    const fetchStudios = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const response = await axios.get('http://127.0.0.1:8000/api/studios/', {
          headers: { Authorization: `Bearer ${token}` }
        });
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


const handleSelectStudio = async (studio) => {
  localStorage.setItem('current_studio_slug', studio.slug);
  setActiveStudioSlug(studio.slug);

  try {
    const response = await api.get(`studios/${studio.slug}/projects/`);
    const projectsList = Array.isArray(response.data) ? response.data : response.data.results || [];

    if (projectsList.length > 0) {
      const realProjectId = projectsList[0].id;
      localStorage.setItem('current_project_id', realProjectId);
      navigate(`/studios/${studio.slug}/projects/${realProjectId}/organize`);
    } else {
      console.log(" Studio empty. Silently initializing backend project container...");
      
      const createResponse = await api.post(`studios/${studio.slug}/projects/`, {
        name: "Default Potato",
        description: "boil em mash em stick em in a stew."
      });

      const newProjectId = createResponse.data.id;
      localStorage.setItem('current_project_id', newProjectId);
      navigate(`/studios/${studio.slug}/projects/${newProjectId}/organize`);
    }
  } catch (err) {
    console.error("Failed to sync project workspace context:", err);
    const fallbackUUID = crypto.randomUUID();
    localStorage.setItem('current_project_id', fallbackUUID);
    navigate(`/studios/${studio.slug}/projects/${fallbackUUID}/organize`);
  }
};



  const handleCreateStudio = async (e) => {
    e.preventDefault();
    setMessage('');
    setIsError(false);

    if (!studioName.trim()) return;

    try {
      const token = localStorage.getItem('access_token');
      

      const generatedSlug = studioName
        .toLowerCase()
        .trim()
        .replace(/[^\w\s-]/g, '')
        .replace(/[\s_-]+/g, '-')
        .replace(/^-+|-+$/g, '');

      const response = await axios.post('http://127.0.0.1:8000/api/studios/', 
        { 
          name: studioName,
          slug: generatedSlug 
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setStudios([response.data, ...studios]);
      setStudioName(''); 
      setMessage(`Studio "${response.data.name}" created successfully!`);

    } catch (err) {
      console.error("Error creating studio:", err.response?.data);
      setIsError(true);
      setMessage(err.response?.data?.slug?.[0] || 'Failed to create studio space.');
    }
  };

  return (
    <div style={styles.page}>
      <h2> Studio Workspace Hub</h2>
      <p style={{ color: '#718096', marginBottom: '30px' }}>Select an active studio workspace so that you can use the taskboard and manage members.</p>

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


      <form onSubmit={handleCreateStudio} style={styles.form}>
        <h4 style={{ margin: '0 0 12px 0', color: '#2d3748' }}>Initialize New Workspace</h4>
        <div style={{ display: 'flex', gap: '12px' }}>
          <input 
            type="text" 
            placeholder="tomato potato studio" 
            value={studioName}
            onChange={(e) => setStudioName(e.target.value)}
            style={styles.input}
            required
          />
          <button type="submit" style={styles.submitButton}>Launch Studio</button>
        </div>
      </form>


      <h3>Available Workspaces</h3>
      {loading ? (
        <p style={{ color: '#a0aec0', fontStyle: 'italic' }}>Querying database...</p>
      ) : studios.length === 0 ? (
        <p style={{ color: '#a0aec0', fontStyle: 'italic' }}>No active studios found. Create one above!</p>
      ) : (
        <div style={styles.studioGrid}>
          {studios.map((studio) => {
            const isActive = studio.slug === activeStudioSlug;
            
            return (
              <div 
                key={studio.id} 
                style={{ 
                  ...styles.studioCard, 
                  borderColor: isActive ? '#3182ce' : '#e2e8f0',
                  backgroundColor: isActive ? '#f7fafc' : '#fff',
                  boxShadow: isActive ? '0 0 0 2px #ebf8ff' : '0 2px 4px rgba(0,0,0,0.02)'
                }}
              >
             
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <strong style={{ fontSize: '16px', color: '#1a202c' }}>{studio.name}</strong>
                    {isActive && <span style={styles.activeBadge}>Active</span>}
                  </div>
                  <span style={{ fontSize: '12px', color: '#a0aec0' }}>Slug: {studio.slug}</span>
                </div>
                
                <button 
                  type="button" 
                  onClick={() => handleSelectStudio(studio)}
                  style={{
                    ...styles.selectButton,
                    backgroundColor: isActive ? '#4a5568' : '#3182ce'
                  }}
                >
                  {isActive ? 'Workspace Active' : 'Enter Workspace'}
                </button>
              </div>
            );
          })}
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
  studioCard: { display: 'flex', alignItems: 'center', gap: '16px', padding: '16px', borderRadius: '8px', border: '1px solid', transition: 'all 0.2s ease' },
  avatar: { width: '40px', height: '40px', backgroundColor: '#ebf8ff', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '18px' },
  selectButton: { padding: '8px 16px', color: 'white', border: 'none', borderRadius: '6px', fontSize: '13px', fontWeight: 'bold', cursor: 'pointer', transition: 'background-color 0.1s' },
  activeBadge: { fontSize: '11px', backgroundColor: '#c6f6d5', color: '#22543d', padding: '2px 8px', borderRadius: '12px', fontWeight: 'bold' },
  alert: { padding: '12px', borderRadius: '6px', fontSize: '14px', fontWeight: '500', marginBottom: '20px' }
};