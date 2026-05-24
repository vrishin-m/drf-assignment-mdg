import { useState } from 'react';

export default function StudiosView() {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [isActive, setIsActive] = useState(true);

  const [studios, setStudios] = useState([
    { id: 1, name: 'hrhrV', slug: 'rhrhrhte', description: 'rhttrhrhrs.', is_active: true },
   
  ]);


  const handleCreateStudio = (e) => {
    e.preventDefault();
    if (!name.trim()) return;

    const generatedSlug = name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)+/g, '');

    const newStudio = {
      id: Date.now(), 
      name,
      slug: generatedSlug,
      description,
      is_active: isActive
    };

    //api ccall here

    setStudios([...studios, newStudio]);
    setName('');
    setDescription('');
    setIsActive(true);
  };


  const handleToggleActive = (id) => {
    setStudios(studios.map(studio => {
      if (studio.id === id) {
        const updatedStatus = !studio.is_active;
        
        //api call here

        return { ...studio, is_active: updatedStatus };
      }
      return studio;
    }));
  };

  return (
    <div style={styles.page}>
      <h2 style={styles.mainTitle}>Studio Workspaces</h2>
      
      <div style={styles.splitLayout}>
        <div style={styles.formCard}>
          <h3 style={styles.sectionTitle}>Make New Studio</h3>
          <form onSubmit={handleCreateStudio}>
            <div style={styles.formGroup}>
              <label style={styles.label}>Studio Name</label>
              <input 
                type="text" 
                placeholder="E.g., potato-studio" 
                value={name}
                onChange={(e) => setName(e.target.value)}
                style={styles.input}
                required
              />
            </div>

            <div style={styles.formGroup}>
              <label style={styles.label}>Description</label>
              <textarea 
                placeholder="is everything just a potato?" 
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                style={{ ...styles.input, minHeight: '90px', resize: 'none' }}
              />
            </div>

            <div style={{ ...styles.formGroup, flexDirection: 'row', alignItems: 'center', gap: '10px', cursor: 'pointer' }}>
              <input 
                type="checkbox" 
                id="isActiveCheck"
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
                style={{ width: '16px', height: '16px', cursor: 'pointer' }}
              />
              <label htmlFor="isActiveCheck" style={{ ...styles.label, marginBottom: 0, cursor: 'pointer' }}>
                Set Workspace as Active Immediately
              </label>
            </div>

            <button type="submit" style={styles.submitButton}>Initialize Studio</button>
          </form>
        </div>

 
        <div style={styles.directoryContainer}>
          <h3 style={styles.sectionTitle}>Active Directories ({studios.length})</h3>
          <div style={styles.grid}>
            {studios.map(studio => (
              <div key={studio.id} style={{ ...styles.studioCard, borderLeftColor: studio.is_active ? '#38a169' : '#e53e3e' }}>
                <div style={styles.cardHeader}>
                  <h4 style={styles.studioName}>{studio.name}</h4>
                  <span style={{
                    ...styles.statusBadge,
                    backgroundColor: studio.is_active ? '#e6fffa' : '#fff5f5',
                    color: studio.is_active ? '#234e52' : '#742a2a'
                  }}>
                    {studio.is_active ? ' Operational' : 'Dead'}
                  </span>
                </div>

                <div style={styles.slugDisplay}>URL Directory Slug: <code>/{studio.slug}</code></div>
                <p style={styles.studioDesc}>{studio.description || 'No description assigned.'}</p>
                
                <button 
                  type="button" 
                  onClick={() => handleToggleActive(studio.id)}
                  style={{
                    ...styles.toggleButton,
                    backgroundColor: studio.is_active ? '#fff5f5' : '#e6fffa',
                    color: studio.is_active ? '#c53030' : '#2f855a',
                    border: `1px solid ${studio.is_active ? '#feb2b2' : '#b2f5ea'}`
                  }}
                >
                  {studio.is_active ? 'Deactivate Studio' : 'Activate Studio'}
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

const styles = {
  page: { padding: '100px 30px 40px 30px', fontFamily: 'sans-serif', maxWidth: '1200px', margin: '0 auto' },
  mainTitle: { margin: '0 0 24px 0', color: '#e8e9eb' },
  splitLayout: { display: 'flex', gap: '30px', flexWrap: 'wrap' },
  formCard: { flex: '1', minWidth: '320px', backgroundColor: '#fff', padding: '24px', borderRadius: '8px', border: '1px solid #e2e8f0', height: 'fit-content', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' },
  directoryContainer: { flex: '2', minWidth: '450px' },
  sectionTitle: { margin: '0 0 16px 0', fontSize: '16px', color: '#4a5568', textTransform: 'uppercase', letterSpacing: '0.5px' },
  formGroup: { display: 'flex', flexDirection: 'column', marginBottom: '16px' },
  label: { fontSize: '13px', fontWeight: 'bold', color: '#4a5568', marginBottom: '6px' },
  input: { padding: '10px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px', outline: 'none' },
  submitButton: { width: '100%', padding: '12px', backgroundColor: '#3182ce', color: 'white', border: 'none', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer', fontSize: '14px', marginTop: '8px' },
  grid: { display: 'flex', flexDirection: 'column', gap: '16px' },
  studioCard: { backgroundColor: '#fff', padding: '20px', borderRadius: '8px', border: '1px solid #e2e8f0', borderLeftWidth: '5px', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' },
  cardHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '10px', marginBottom: '6px' },
  studioName: { margin: 0, fontSize: '18px', color: '#2d3748' },
  statusBadge: { fontSize: '12px', fontWeight: 'bold', padding: '4px 10px', borderRadius: '12px' },
  slugDisplay: { fontSize: '12px', color: '#718096', marginBottom: '12px' },
  studioDesc: { margin: '0 0 16px 0', fontSize: '14px', color: '#4a5568', lineHeight: '1.5' },
  toggleButton: { padding: '6px 14px', borderRadius: '6px', fontSize: '12px', fontWeight: 'bold', cursor: 'pointer', transition: 'all 0.15s' }
};