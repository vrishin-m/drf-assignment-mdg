import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import api from '../api';

export default function CreateTask() {
  const { studioSlug, projectId } = useParams();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState('Medium');
  const [deadline, setDeadline] = useState('');
  

  const [tasks, setTasks] = useState([]);
  const [message, setMessage] = useState('');
  const [isError, setIsError] = useState(false);

  useEffect(() => {
    const fetchTasks = async () => {

      if (!studioSlug || !projectId) {
        console.warn("CreateTask mounting blocked: missing route parameters.");
        return;
      }
      
      try {
        const resp = await api.get(`studios/${studioSlug}/projects/${projectId}/tasks/`);
        setTasks(resp.data);
        setIsError(false);
      } catch (err) {
        console.error('Error fetching tasks from backend:', err);
        setIsError(true);
        setMessage('Could not load existing tasks from database.');
      }
    };
    
    fetchTasks();
  }, [studioSlug, projectId]);


  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim()) return;


    const payload = {
      title,
      description,
      priority: priority.toLowerCase(), 
    };
    if (deadline) payload.deadline = deadline;

    try {
      if (studioSlug && projectId) {
        
        const resp = await api.post(`studios/${studioSlug}/projects/${projectId}/tasks/`, payload);
        setTasks([resp.data, ...tasks]);
        setIsError(false);
        setMessage('Task created successfully!');
      } else {

        const newTask = { id: Date.now(), title, description, priority, deadline };
        setTasks([newTask, ...tasks]);
        setIsError(true);
        setMessage('Parameters missing! Local fallback container updated instead.');
      }
      

      setTitle('');
      setDescription('');
      setPriority('Medium');
      setDeadline('');
    } catch (err) {
      console.error('Failed to save task to backend database:', err);
      setIsError(true);
      setMessage('Failed to register task with database.');
    }
  };


  const getPriorityColor = (level) => {
    switch (level?.toLowerCase()) {
      case 'high':   return { bg: '#fed7d7', text: '#c53030' };
      case 'medium': return { bg: '#feebc8', text: '#c05621' }; 
      case 'low':    return { bg: '#e2e8f0', text: '#4a5568' }; 
      default:       return { bg: '#edf2f7', text: '#2d3748' };
    }
  };

  return (
    <div style={styles.page}>
      <h2 style={styles.header}>Create New Task</h2>
      
 
      {message && (
        <div style={{ 
          ...styles.alert, 
          backgroundColor: isError ? '#fff5f5' : '#e6fffa', 
          color: isError ? '#c53030' : '#234e52',
          border: `1px solid ${isError ? '#fed7d7' : '#b2f5ea'}`
        }}>
          {message}
        </div>
      )}
      
      <div style={styles.container}>

        <form onSubmit={handleSubmit} style={styles.form}>
          <div style={styles.formGroup}>
            <label style={styles.label}>Task Title</label>
            <input 
              type="text" 
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              style={styles.input}
              placeholder="What needs doing?"
              required
            />
          </div>

          <div style={styles.formGroup}>
            <label style={styles.label}>Description</label>
            <textarea 
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Add more details about this task allocation..."
              style={{ ...styles.input, minHeight: '80px', resize: 'vertical' }}
            />
          </div>

          <div style={styles.row}>
            <div style={styles.formGroup}>
              <label style={styles.label}>Priority Label</label>
              <select 
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                style={styles.input}
              >
                <option value="High">High</option>
                <option value="Medium">Medium</option>
                <option value="Low">Low</option>
              </select>
            </div>

            <div style={styles.formGroup}>
              <label style={styles.label}>Deadline Label</label>
              <input 
                type="date" 
                value={deadline}
                onChange={(e) => setDeadline(e.target.value)}
                style={styles.input}
              />
            </div>
          </div>

          <button type="submit" style={styles.submitButton}>
             Add Task to Workflow
          </button>
        </form>


        <div style={styles.feed}>
          <h3 style={styles.feedHeader}>Recent Studio Tasks ({tasks.length})</h3>
          
          {tasks.length === 0 ? (
            <p style={styles.emptyText}>No tasks in this project pipeline.</p>
          ) : (
            <div style={styles.taskList}>
              {tasks.map(task => {
                const colors = getPriorityColor(task.priority);
                return (
                  <div key={task.id || task.uuid} style={styles.taskCard}>
                    <h4 style={styles.taskTitle}>{task.title}</h4>
                    {task.description && <p style={styles.taskDesc}>{task.description}</p>}
                    
                    <div style={styles.labelRow}>
                      <span style={{
                        ...styles.pill, 
                        backgroundColor: colors.bg, 
                        color: colors.text,
                        textTransform: 'capitalize'
                      }}>
                        {task.priority} Priority
                      </span>
                      
                      {task.deadline && (
                        <span style={{
                          ...styles.pill, 
                          backgroundColor: '#ebf8ff', 
                          color: '#2b6cb0' 
                        }}>
                            Due: {task.deadline}
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ==========================================
// 🎨 ENHANCED STYLING INTERFACES
// ==========================================
const styles = {
  page: { padding: '100px 20px', fontFamily: 'sans-serif', maxWidth: '800px', margin: '0 auto' },
  header: { marginBottom: '20px', color: '#2d3748' },
  container: { display: 'flex', flexDirection: 'column', gap: '30px' },
  form: { backgroundColor: '#fff', padding: '24px', borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' },
  row: { display: 'flex', gap: '16px', flexWrap: 'wrap' },
  formGroup: { display: 'flex', flexDirection: 'column', marginBottom: '16px', flex: 1 },
  label: { fontSize: '12px', fontWeight: 'bold', color: '#4a5568', marginBottom: '8px', textTransform: 'uppercase' },
  input: { padding: '10px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px', outline: 'none', fontFamily: 'sans-serif' },
  submitButton: { width: '100%', padding: '12px', backgroundColor: '#3182ce', color: 'white', border: 'none', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer', marginTop: '10px', fontSize: '14px' },
  feed: { backgroundColor: '#f7fafc', padding: '24px', borderRadius: '8px', border: '1px solid #e2e8f0' },
  feedHeader: { margin: '0 0 16px 0', fontSize: '16px', color: '#2d3748', fontWeight: 'bold' },
  emptyText: { color: '#a0aec0', fontSize: '14px', fontStyle: 'italic' },
  taskList: { display: 'flex', flexDirection: 'column', gap: '12px' },
  taskCard: { backgroundColor: '#fff', padding: '16px', borderRadius: '6px', border: '1px solid #e2e8f0', boxShadow: '0 1px 2px rgba(0,0,0,0.02)' },
  taskTitle: { margin: '0 0 8px 0', fontSize: '16px', color: '#1a202c', fontWeight: '600' },
  taskDesc: { margin: '0 0 12px 0', fontSize: '14px', color: '#4a5568', lineHeight: '1.4' },
  labelRow: { display: 'flex', gap: '8px', flexWrap: 'wrap' },
  pill: { padding: '4px 10px', borderRadius: '16px', fontSize: '11px', fontWeight: '600', display: 'inline-block' },
  alert: { padding: '12px 16px', borderRadius: '6px', marginBottom: '5px', fontSize: '14px', fontWeight: '500' }
};