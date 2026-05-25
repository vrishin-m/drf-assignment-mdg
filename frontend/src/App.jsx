import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';

import HomeView from './pages/home.jsx';
import CreateTaskView from './pages/createtask.jsx';
import OrganizeView from './pages/board.jsx';
import MembersView from './pages/members.jsx';
import StudiosView from './pages/studios.jsx';




         
function Navbar() {
  const [activeStudio, setActiveStudio] = useState('');
  const [projectId, setProjectId] = useState('');
  const location = useLocation();
  
  useEffect(() => {
    const storedSlug = localStorage.getItem('current_studio_slug');
    const storedProjectId = localStorage.getItem('current_project_id');
    if (storedSlug && storedSlug !== 'null' && storedSlug !== 'undefined') {
      setActiveStudio(storedSlug);
    } else {
      setActiveStudio('');
    }
    if (storedProjectId && storedProjectId !== 'null' && storedProjectId !== 'undefined') {
      setProjectId(storedProjectId);
    } else {
      setProjectId('00000000-0000-0000-0000-000000000000');
    }
  

  }, [location]);

  return (
    <nav style={navStyle}>
      <div style={{ color: '#fff', fontWeight: 'bold' }}> Studio App</div>
      <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
        <Link to="/" style={linkStyle}>Home / Login</Link>
        <Link to="/studios" style={linkStyle}>Studios</Link>

        {activeStudio ? (
          <>
            <Link to={`/studios/${activeStudio}/projects/${projectId}/create-task/`} style={linkStyle}>Create Task</Link>
            <Link to={`/studios/${activeStudio}/projects/${projectId}/organize/`} style={linkStyle}>Organize Tasks</Link>
            <Link to={`/studios/${activeStudio}/projects/${projectId}/members/`} style={linkStyle}>Manage Members</Link>
            
            <span >Current Studio: {activeStudio}</span>
          </>   
        ) : (
          <span >Go to "Studios" and select or create one</span>
        )}
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <Routes>

        <Route path="/" element={<HomeView />} />
        <Route path="/studios/:studioSlug/projects/:projectId/create-task"  element={<CreateTaskView />} />
        <Route path="/studios/:studioSlug/projects/:projectId/organize" element={<OrganizeView />} />
        <Route path="/studios/:studioSlug/projects/:projectId/members"  element={<MembersView />} />
        <Route path="/studios" element={<StudiosView />} />
         

      </Routes>
    </BrowserRouter>
  );
}


const navStyle = { position: 'fixed', top: 0, left: 0, right: 0, height: '60px', backgroundColor: '#1a202c', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 30px', zIndex: 1000, fontFamily: 'sans-serif' };
const linkStyle = { color: '#cbd5e0', textDecoration: 'none', fontSize: '14px' };