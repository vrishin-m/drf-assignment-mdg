import { useState } from 'react';

export default function MembersView() {
  const [members, setMembers] = useState([
    { id: 101, username: 'hrhrhrh', email: 'seegegege@studio.com', role: 'Producer' },
    { id: 102, username: 'arhrhx', email: 'jtjtx@studio.com', role: 'Designer' },
    
  ]);


  const [tasks, setTasks] = useState([
    { id: 1, title: 'eat a potato', assigned_to: null },
    { id: 2, title: 'plant a potato', assigned_to: 102 },
    { id: 3, title: 'cook a potato', assigned_to: 101 },
  ]);

  const availableRoles = ['Admin', 'Producer', 'Designer', 'Editor'];

  const handleRoleChange = (memberId, newRole) => {
   
    // api call goes here
    setMembers(members.map(m => m.id === memberId ? { ...m, role: newRole } : m));
  };


  const handleAssignTask = (taskId, memberId) => {
    const targetMemberId = memberId ? parseInt(memberId) : null;

    // api call here
    setTasks(tasks.map(t => t.id === taskId ? { ...t, assigned_to: targetMemberId } : t));
  };

  return (
    <div style={styles.page}>
      <h2 style={styles.mainTitle}>Manage Studio Members</h2>

      <div style={styles.splitLayout}>

        <div style={styles.panelCard}>
          <h3 style={styles.sectionTitle}>Team  & Roles</h3>
          <div style={styles.rosterList}>
            {members.map(member => (
              <div key={member.id} style={styles.memberCard}>
                <div>
                  <strong style={styles.username}>@{member.username}</strong>
                  <div style={styles.email}>{member.email}</div>
                </div>
                <div>
                  <select
                    value={member.role}
                    onChange={(e) => handleRoleChange(member.id, e.target.value)}
                    style={styles.roleSelect}
                  >
                    {availableRoles.map(role => (
                      <option key={role} value={role}>{role}</option>
                    ))}
                  </select>
                </div>
              </div>
            ))}
          </div>
        </div>


        <div style={styles.panelCard}>
          <h3 style={styles.sectionTitle}> Task Assignments</h3>
          <div style={styles.taskList}>
            {tasks.map(task => (
              <div key={task.id} style={styles.taskCard}>
                <div style={styles.taskTextInfo}>
                  <span style={styles.taskTitle}>{task.title}</span>
                  <div style={styles.assignmentStatus}>
                    Status:{' '}
                    {task.assigned_to ? (
                      <span style={{ color: '#2b6cb0', fontWeight: 'bold' }}>
                        Assigned to @{members.find(m => m.id === task.assigned_to)?.username}
                      </span>
                    ) : (
                      <span style={{ color: '#c53030', fontWeight: 'bold' }}>Unassigned</span>
                    )}
                  </div>
                </div>
                <div>
                  <select
                    value={task.assigned_to || ''}
                    onChange={(e) => handleAssignTask(task.id, e.target.value)}
                    style={styles.assignSelect}
                  >
                    <option value="">-- Assign Owner --</option>
                    {members.map(m => (
                      <option key={m.id} value={m.id}>
                        @{m.username} ({m.role})
                      </option>
                    ))}
                  </select>
                </div>
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