import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import '../styles/navbar.css';

function Navbar() {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
    navigate('/');
  };

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/home" className="navbar-logo">
          AI Travel
        </Link>
        <div className="navbar-links">
          <Link to="/locations" className="nav-link">Locations</Link>
          <Link to="/hotels" className="nav-link">Hotels</Link>
          <Link to="/plans" className="nav-link">Plans</Link>
          <Link to="/bookings" className="nav-link">Your Bookings</Link>
          <Link to="/booked-visits" className="nav-link">Booked Visits</Link>
          <Link to="/chatbot" className="nav-link">AI Assistant</Link>
          <button onClick={handleLogout} className="nav-button">Logout</button>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
