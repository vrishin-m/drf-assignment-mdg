import { useState } from 'react';

export default function HomeView() {
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

    if (!email || !password) {
      setIsError(true);
      setMessage('Please fill out all fields.');
      return;
    }

    //API CALL TO BACKEND GOES HERE

   

 
  };

  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    setMessage('');
    setIsError(false);

    if (!email || !password || !username) {
      setIsError(true);
      setMessage('Please fill out all fields.');
      return;
    }

    //API CALL TO BACKEND GOES HERE

    setMessage(`account created. now sign in!`)
    setAuthMode('login');
  };

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <div style={styles.brandingHeader}>
          <h2 style={{ margin: '0 0 6px 0', color: "#000000"}}>Studio App</h2>
          <p style={{ margin: 0, fontSize: '14px', color: '#718096' }}>Creative Production Portal</p>
        </div>

  
        <div style={styles.tabContainer}>
          <button 
            style={{ ...styles.tabButton, borderBottomColor: authMode === 'login' ? '#3182ce' : 'transparent', color: authMode === 'login' ? '#3182ce' : '#718096' }}
            onClick={() => { setAuthMode('login'); setMessage(''); }}
          >
            Sign In
          </button>
          <button 
            style={{ ...styles.tabButton, borderBottomColor: authMode === 'register' ? '#3182ce' : 'transparent', color: authMode === 'register' ? '#3182ce' : '#718096' }}
            onClick={() => { setAuthMode('register'); setMessage(''); }}
          >
            Register
          </button>
        </div>


        {message && (
          <div style={{ 
            ...styles.alert, 
            backgroundColor: isError ? '#fff5fff5' : '#f0fff4', 
            color: isError ? '#c53030' : '#2f855a',
            border: `1px solid ${isError ? '#feb2b2' : '#c6f6d5'}`
          }}>
            {message}
          </div>
        )}


        {authMode === 'login' ? (
          <form onSubmit={handleLoginSubmit}>
            <div style={styles.formGroup}>
              <label style={styles.label}>Email Address</label>
              <input 
                type="email" 
                placeholder="name@studio.com" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                style={styles.input}
                required
              />
            </div>
            <div style={styles.formGroup}>
              <label style={styles.label}>Password</label>
              <input 
                type="password" 
                placeholder="••••••••" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                style={styles.input}
                required
              />
            </div>
            <button type="submit" style={styles.submitButton}>Sign Into Account</button>
          </form>
        ) : (
          <form onSubmit={handleRegisterSubmit}>
            <div style={styles.formGroup}>
              <label style={styles.label}>Choose Username</label>
              <input 
                type="text" 
                placeholder="creative_director" 
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                style={styles.input}
                required
              />
            </div>
            <div style={styles.formGroup}>
              <label style={styles.label}>Email Address</label>
              <input 
                type="email" 
                placeholder="name@studio.com" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                style={styles.input}
                required
              />
            </div>
            <div style={styles.formGroup}>
              <label style={styles.label}>Secure Password</label>
              <input 
                type="password" 
                placeholder="••••••••" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                style={styles.input}
                required
              />
            </div>
            <button type="submit" style={{ ...styles.submitButton, backgroundColor: '#4a5568' }}>Register Member Account</button>
          </form>
        )}
      </div>
    </div>
  );
}

const styles = {
  page: { padding: '120px 20px 40px 20px', fontFamily: 'sans-serif', minHeight: 'calc(100vh - 160px)', display: 'flex', justifyContent: 'center', alignItems: 'center', backgroundColor: '#f7fafc' },
  card: { width: '100%', maxWidth: '400px', backgroundColor: '#fff', padding: '30px', borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)' },
  brandingHeader: { textAlign: 'center', marginBottom: '24px' },
  tabContainer: { display: 'flex', marginBottom: '24px', borderBottom: '1px solid #e2e8f0' },
  tabButton: { flex: 1, padding: '12px', background: 'none', border: 'none', borderBottom: '2px solid transparent', fontSize: '15px', fontWeight: 'bold', cursor: 'pointer', transition: 'all 0.2s' },
  formGroup: { display: 'flex', flexDirection: 'column', marginBottom: '16px' },
  label: { fontSize: '12px', fontWeight: 'bold', color: '#4a5568', marginBottom: '6px', textTransform: 'uppercase' },
  input: { padding: '10px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px', outline: 'none' },
  submitButton: { width: '100%', padding: '12px', backgroundColor: '#3182ce', color: 'white', border: 'none', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer', fontSize: '14px', marginTop: '10px', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' },
  alert: { padding: '12px', borderRadius: '6px', fontSize: '13px', fontWeight: '500', marginBottom: '20px', textAlign: 'center' }
};