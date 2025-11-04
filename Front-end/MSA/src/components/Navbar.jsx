import { NavLink } from 'react-router-dom';
import './Navbar.css';

const Navbar = () => {
  return (
    <nav className="navbar">
      <div className="navbar-container">
        <div className="navbar-logo">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
            <polyline points="7.5 4.21 12 6.81 16.5 4.21"></polyline>
            <polyline points="7.5 19.79 7.5 14.6 3 12"></polyline>
            <polyline points="21 12 16.5 14.6 16.5 19.79"></polyline>
            <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
            <line x1="12" y1="22.08" x2="12" y2="12"></line>
          </svg>
          <span>Mine Safety AI</span>
        </div>

        <ul className="navbar-links">
          <li>
            <NavLink to="/" className={({ isActive }) => isActive ? 'active' : ''}>
              Home
            </NavLink>
          </li>
          <li>
            <NavLink to="/alerts" className={({ isActive }) => isActive ? 'active' : ''}>
              Critical Alerts
            </NavLink>
          </li>
          <li>
            <NavLink to="/warnings" className={({ isActive }) => isActive ? 'active' : ''}>
              Warnings
            </NavLink>
          </li>
          <li>
            <NavLink to="/analysis" className={({ isActive }) => isActive ? 'active' : ''}>
              Analysis
            </NavLink>
          </li>
          <li>
            <NavLink to="/preventive" className={({ isActive }) => isActive ? 'active' : ''}>
              Preventive Measures
            </NavLink>
          </li>
        </ul>

        <div className="navbar-status">
          <span className="status-dot"></span>
          <span>Monitoring</span>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
