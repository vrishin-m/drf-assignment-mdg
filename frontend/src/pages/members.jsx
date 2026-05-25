import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import api from '../api';

const ROLE_OPTIONS = [
  { label: 'Studio Admin', value: 'studio_admin' },
  { label: 'Project Lead', value: 'project_lead' },
  { label: 'Designer', value: 'designer' },
  { label: 'Writer', value: 'writer' },
  { label: 'Reviewer', value: 'reviewer' },
  { label: 'Client Viewer', value: 'client_viewer' },
];

export default function MembersView() {
  const { studioSlug, projectId } = useParams();
  const [members, setMembers] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [loadingMembers, setLoadingMembers] = useState(true);
  const [loadingTasks, setLoadingTasks] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchMembers = async () => {
      if (!studioSlug) return;
      try {
        const resp = await api.get(`/studios/${studioSlug}/members/`);
        setMembers(resp.data);
      } catch (err) {
        console.error('Error fetching members:', err);
        setError('Failed to load members.');
      } finally {
        setLoadingMembers(false);
      }
    };

    const fetchTasks = async () => {
      if (!studioSlug || !projectId) return;
      try {
        const resp = await api.get(`/studios/${studioSlug}/projects/${projectId}/tasks/`);
        setTasks(resp.data);
      } catch (err) {
        console.error('Error fetching tasks:', err);
        setError('Failed to load tasks.');
      } finally {
        setLoadingTasks(false);
      }
    };

    fetchMembers();
    fetchTasks();
  }, [studioSlug, projectId]);

  const handleRoleChange = async (userId, newRole) => {
    try {
      const resp = await api.patch(`/studios/${studioSlug}/members/${userId}/`, { role: newRole });
      setMembers(members.map(m => (m.user && String(m.user.id) === String(resp.data.user?.id) ? resp.data : m)));
    } catch (err) {
      console.error('Failed to update role:', err);
      setError('Failed to update role.');
    }
  };

  const handleAssignTask = async (taskId, memberUserId) => {
    const assignee = memberUserId ? memberUserId : null;
    try {
      const resp = await api.patch(`/studios/${studioSlug}/projects/${projectId}/tasks/${taskId}/`, { assignee });
      setTasks(tasks.map(t => (String(t.id) === String(taskId) ? resp.data : t)));
    } catch (err) {
      console.error('Failed to assign task:', err);
      setError('Failed to assign task.');
    }
  };

  const displayName = (member) => member?.user?.full_name || member?.user_name || member?.user?.email || 'Unknown';

  return (
    <div style={styles.page}>
      <h2 style={styles.mainTitle}>Manage Studio Members</h2>

      {error && <div style={{ color: 'red', marginBottom: 12 }}>{error}</div>}

      <div style={styles.splitLayout}>

        <div style={styles.panelCard}>
          <h3 style={styles.sectionTitle}>Team & Roles</h3>
          {loadingMembers ? (
            <p style={{ color: '#a0aec0' }}>Loading members...</p>
          ) : (
            <div style={styles.rosterList}>
              {members.map((member) => (
                <div key={member.user?.id || member.id} style={styles.memberCard}>
                  <div>
                    <strong style={styles.username}>@{displayName(member)}</strong>
                    <div style={styles.email}>{member.user?.email || member.user_email}</div>
                  </div>
                  <div>
                    <select
                      value={member.role || ''}
                      onChange={(e) => handleRoleChange(member.user?.id, e.target.value)}
                      style={styles.roleSelect}
                    >
                      {ROLE_OPTIONS.map((r) => (
                        <option key={r.value} value={r.value}>{r.label}</option>
                      ))}
                    </select>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div style={styles.panelCard}>
          <h3 style={styles.sectionTitle}>Task Assignments</h3>
          {loadingTasks ? (
            <p style={{ color: '#a0aec0' }}>Loading tasks...</p>
          ) : (
            <div style={styles.taskList}>
              {tasks.map((task) => {
                const assigned = String(task.assignee || '');
                const assignedMember = members.find((m) => String(m.user?.id) === assigned);
                return (
                  <div key={task.id} style={styles.taskCard}>
                    <div style={styles.taskTextInfo}>
                      <span style={styles.taskTitle}>{task.title}</span>
                      <div style={styles.assignmentStatus}>
                        Status:{' '}
                        {assignedMember ? (
                          <span style={{ color: '#2b6cb0', fontWeight: 'bold' }}>Assigned to @{displayName(assignedMember)}</span>
                        ) : (
                          <span style={{ color: '#c53030', fontWeight: 'bold' }}>Unassigned</span>
                        )}
                      </div>
                    </div>
                    <div>
                      <select
                        value={task.assignee || ''}
                        onChange={(e) => handleAssignTask(task.id, e.target.value)}
                        style={styles.assignSelect}
                      >
                        <option value="">-- Assign Owner --</option>
                        {members.map((m) => (
                          <option key={m.user?.id || m.id} value={m.user?.id}>{displayName(m)} ({m.role_display || m.role})</option>
                        ))}
                      </select>
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

const styles = {
  page: { padding: '100px 30px 40px 30px', fontFamily: 'sans-serif', maxWidth: '1200px', margin: '0 auto' },
  mainTitle: { margin: '0 0 24px 0', color: '#e4e4e4' },
  splitLayout: { display: 'flex', gap: '30px', flexWrap: 'wrap' },
  panelCard: { flex: '1', minWidth: '340px', backgroundColor: '#fff', padding: '24px', borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.05)', height: 'fit-content' },
  sectionTitle: { margin: '0 0 20px 0', fontSize: '15px', color: '#4a5568', textTransform: 'uppercase', letterSpacing: '0.5px' },
  rosterList: { display: 'flex', flexDirection: 'column', gap: '12px' },
  memberCard: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px', border: '1px solid #edf2f7', borderRadius: '6px', backgroundColor: '#f7fafc' },
  username: { color: '#2d3748', fontSize: '15px' },
  email: { color: '#718096', fontSize: '13px', marginTop: '2px' },
  roleSelect: { padding: '6px 10px', borderRadius: '6px', border: '1px solid #cbd5e1', backgroundColor: '#fff', fontSize: '13px', fontWeight: 'bold', color: '#4a5568', cursor: 'pointer' },
  taskList: { display: 'flex', flexDirection: 'column', gap: '12px' },
  taskCard: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px', border: '1px solid #edf2f7', borderRadius: '6px', backgroundColor: '#fff', boxShadow: '0 1px 2px rgba(0,0,0,0.02)' },
  taskTextInfo: { flex: 1, paddingRight: '15px' },
  taskTitle: { fontSize: '14px', fontWeight: '600', color: '#2d3748', display: 'block' },
  assignmentStatus: { fontSize: '12px', color: '#718096', marginTop: '4px' },
  assignSelect: { padding: '6px 10px', borderRadius: '6px', border: '1px solid #cbd5e1', backgroundColor: '#fff', fontSize: '13px', color: '#4a5568', cursor: 'pointer' }
};
