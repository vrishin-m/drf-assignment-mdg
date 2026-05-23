import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';


import HomeView from './pages/home.jsx';
import CreateTaskView from './pages/createtask.jsx';
import OrganizeView from './pages/board.jsx';
import MembersView from './pages/members.jsx';

function Navbar() {
  return (
    <nav style={navStyle}>
      <div style={{ color: '#fff', fontWeight: 'bold' }}> Studio App</div>
      <div style={{ display: 'flex', gap: '20px' }}>
        <Link to="/" style={linkStyle}>Home / Login</Link>
        <Link to="/create-task" style={linkStyle}> Create Task</Link>
        <Link to="/organize" style={linkStyle}> Organize Tasks</Link>
        <Link to="/members" style={linkStyle}> Manage Members</Link>
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
        <Route path="/create-task" element={<CreateTaskView />} />
        <Route path="/organize" element={<OrganizeView />} />
        <Route path="/members" element={<MembersView />} />
      </Routes>
    </BrowserRouter>
  );
}


const navStyle = { position: 'fixed', top: 0, left: 0, right: 0, height: '60px', backgroundColor: '#1a202c', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 30px', zIndex: 1000, fontFamily: 'sans-serif' };
const linkStyle = { color: '#cbd5e0', textDecoration: 'none', fontSize: '14px' };