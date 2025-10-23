import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Header.css';

function Header({ onLogout, searchQuery, onSearchChange }) {
  const location = useLocation();

  return (
    <header className="header">
      <div className="container">
        <div className="header-content">
          <div className="header-left">
            <Link to="/dashboard" className="header-logo">
              Sales Engagement
            </Link>
            
            <nav className="header-nav">
              <Link 
                to="/dashboard" 
                className={`nav-link ${location.pathname === '/dashboard' ? 'active' : ''}`}
              >
                Kontaktit
              </Link>
              <Link 
                to="/activities" 
                className={`nav-link ${location.pathname === '/activities' ? 'active' : ''}`}
              >
                Aikajana
              </Link>
            </nav>
          </div>
          
          <div className="header-center">
            <div className="search-container">
              <input
                type="text"
                placeholder="Hae kontakteja..."
                value={searchQuery}
                onChange={(e) => onSearchChange(e.target.value)}
                className="search-input"
              />
              <div className="search-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="11" cy="11" r="8"></circle>
                  <path d="m21 21-4.35-4.35"></path>
                </svg>
              </div>
            </div>
          </div>
          
          <div className="header-right">
            <button className="btn btn-secondary btn-sm" onClick={onLogout}>
              Kirjaudu ulos
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;