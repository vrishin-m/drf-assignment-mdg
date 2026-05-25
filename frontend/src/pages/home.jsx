import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';

export default function HomeView() {
  const navigate = useNavigate();
  const [authMode, setAuthMode] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [username, setUsername] = useState('');
  const [message, setMessage] = useState('');
  const [isError, setIsError] = useState(false);

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setMessage('');
    setIsError(false);
    try {
      const response = await api.post('/auth/login/', {
        email: email,
        password: password,
      });
      localStorage.setItem('access_token', response.data.access);
      localStorage.setItem('refresh_token', response.data.refresh);
      navigate('/studios');
    } catch (err) {
      setIsError(true);
      setMessage('Invalid email or password.');
    }
  };

  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    setMessage('');
    setIsError(false);
    try {
      await api.post('/auth/register/', {
        email,
        password,
        full_name: username,
      });
      setMessage('Account created! Please log in.');
      setAuthMode('login');
    } catch (err) {
      setIsError(true);
      setMessage('Registration failed.');
    }
  };

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        
        <div style={styles.brandingHeader}>
          <h2 style={{ margin: '0 0 6px 0', color: '#1a202c' }}>Studio Workspace</h2>
          <p style={{ margin: 0, fontSize: '14px', color: '#718096' }}>Creative Production Portal</p>
        </div>

        {/* TABS */}
        <div style={styles.tabContainer}>
          <button 
            type="button"
            style={{ ...styles.tabButton, borderBottomColor: authMode === 'login' ? '#3182ce' : 'transparent', color: authMode === 'login' ? '#3182ce' : '#718096' }}
            onClick={() => setAuthMode('login')}
          >
            Sign In
          </button>
          <button 
            type="button"
            style={{ ...styles.tabButton, borderBottomColor: authMode === 'register' ? '#3182ce' : 'transparent', color: authMode === 'register' ? '#3182ce' : '#718096' }}
            onClick={() => setAuthMode('register')}
          >
            Register
          </button>
        </div>

        {message && (
          <div style={{ ...styles.alert, backgroundColor: isError ? '#fff5f5' : '#f0fff4', color: isError ? '#c53030' : '#2f855a' }}>
            {message}
          </div>
        )}


        {authMode === 'login' ? (
          <form onSubmit={handleLoginSubmit}>
            <div style={styles.formGroup}>
              <label style={styles.label}>Email Address</label>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} style={styles.input} required />
            </div>
            <div style={styles.formGroup}>
              <label style={styles.label}>Password</label>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} style={styles.input} required />
            </div>
            <button type="submit" style={styles.submitButton}>Sign Into Account</button>
          </form>
        ) : (
          <form onSubmit={handleRegisterSubmit}>
            <div style={styles.formGroup}>
              <label style={styles.label}>Username</label>
              <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} style={styles.input} required />
            </div>
            <div style={styles.formGroup}>
              <label style={styles.label}>Email Address</label>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} style={styles.input} required />
            </div>
            <div style={styles.formGroup}>
              <label style={styles.label}>Password</label>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} style={styles.input} required />
            </div>
            <button type="submit" style={{ ...styles.submitButton, backgroundColor: '#4a5568' }}>Register Account</button>
          </form>
        )}

      </div>
    </div>
  );
}

const styles = {
  page: { padding: '120px 20px 40px 20px', fontFamily: 'sans-serif', minHeight: 'calc(100vh - 160px)', display: 'flex', justifyContent: 'center', alignItems: 'center', backgroundColor: '#f7fafc' },
  card: { width: '100%', maxWidth: '400px', backgroundColor: '#ffffff', padding: '30px', borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)', display: 'block' },
  brandingHeader: { textAlign: 'center', marginBottom: '24px' },
  tabContainer: { display: 'flex', marginBottom: '24px', borderBottom: '1px solid #e2e8f0' },
  tabButton: { flex: 1, padding: '12px', background: 'none', border: 'none', borderBottom: '2px solid transparent', fontSize: '15px', fontWeight: 'bold', cursor: 'pointer' },
  formGroup: { display: 'flex', flexDirection: 'column', marginBottom: '16px' },
  label: { fontSize: '12px', fontWeight: 'bold', color: '#4a5568', marginBottom: '6px', textTransform: 'uppercase' },
  input: { padding: '10px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px', outline: 'none' },
  submitButton: { width: '100%', padding: '12px', backgroundColor: '#3182ce', color: 'white', border: 'none', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer', fontSize: '14px', marginTop: '10px' },
  alert: { padding: '12px', borderRadius: '6px', fontSize: '13px', marginBottom: '20px', textAlign: 'center' }
};