import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Header.css';

function Header({ onLogout, searchQuery, onSearchChange }) {
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <header className="header">
      <div className="container">
        <div className="header-content">
          <div className="header-left">
            <Link to="/dashboard" className="header-logo">
              Sales Engagement
            </Link>
            
            <button 
              className="mobile-menu-toggle"
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="3" y1="6" x2="21" y2="6"></line>
                <line x1="3" y1="12" x2="21" y2="12"></line>
                <line x1="3" y1="18" x2="21" y2="18"></line>
              </svg>
            </button>
            
            <nav className={`header-nav ${isMobileMenuOpen ? 'mobile-open' : ''}`}>
              <Link 
                to="/dashboard" 
                className={`nav-link ${location.pathname === '/dashboard' ? 'active' : ''}`}
                onClick={() => setIsMobileMenuOpen(false)}
              >
                Kontaktit
              </Link>
              <Link 
                to="/activities" 
                className={`nav-link ${location.pathname === '/activities' ? 'active' : ''}`}
                onClick={() => setIsMobileMenuOpen(false)}
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
                value={searchQuery || ''}
                onChange={(e) => onSearchChange && onSearchChange(e.target.value)}
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
            <button 
              className="btn btn-secondary btn-sm" 
              onClick={() => {
                onLogout();
                setIsMobileMenuOpen(false);
              }}
            >
              Kirjaudu ulos
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;