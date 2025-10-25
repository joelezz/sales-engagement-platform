import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';
import { contactsApi } from '../services/api';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';
import ContactList from './ContactList';
import ContactForm from './ContactForm';
import Header from './Header';
import './Dashboard.css';

function Dashboard() {
  const { logout } = useAuth();
  const [showContactForm, setShowContactForm] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const { data: contactsData, isLoading, refetch } = useQuery({
    queryKey: ['contacts', searchQuery],
    queryFn: () => searchQuery 
      ? contactsApi.search(searchQuery)
      : contactsApi.getAll(),
  });

  const contacts = contactsData?.data?.contacts || [];

  const handleContactCreated = () => {
    setShowContactForm(false);
    refetch();
  };

  // Keyboard shortcuts
  useKeyboardShortcuts([
    {
      key: 'n',
      ctrl: true,
      action: () => setShowContactForm(true)
    },
    {
      key: 'k',
      ctrl: true,
      action: () => {
        const searchInput = document.querySelector('.search-input');
        if (searchInput) {
          searchInput.focus();
        }
      }
    }
  ]);

  return (
    <div className="dashboard">
      <Header 
        onLogout={logout}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
      />
      
      <main className="dashboard-main">
        <div className="container">
          <div className="dashboard-header">
            <div className="dashboard-title-section">
              <h1 className="dashboard-title">Kontaktit</h1>
              <p className="dashboard-subtitle">
                Hallitse asiakaskontaktejasi ja seuraa vuorovaikutusta
              </p>
            </div>
            
            <div className="dashboard-actions">
              <button
                className="btn btn-primary"
                onClick={() => setShowContactForm(true)}
                title="Uusi kontakti (Ctrl+N)"
              >
                + Uusi kontakti
              </button>
              
              <div className="keyboard-shortcuts-hint">
                <span className="shortcut-hint">Ctrl+N: Uusi kontakti</span>
                <span className="shortcut-hint">Ctrl+K: Haku</span>
              </div>
            </div>
          </div>

          <div className="dashboard-stats">
            <div className="stat-card">
              <div className="stat-number">{contacts.length}</div>
              <div className="stat-label">Kontaktia yhteensä</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">{contacts.filter(c => c.phone).length}</div>
              <div className="stat-label">Puhelinnumerolla</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">{contacts.filter(c => c.email).length}</div>
              <div className="stat-label">Sähköpostilla</div>
            </div>
          </div>

          <div className="dashboard-content">
            {isLoading ? (
              <div className="loading-state">
                <div className="loading-spinner"></div>
                <p>Ladataan kontakteja...</p>
              </div>
            ) : (
              <ContactList contacts={contacts} onContactUpdate={refetch} />
            )}
          </div>
        </div>
      </main>

      {showContactForm && (
        <ContactForm
          onClose={() => setShowContactForm(false)}
          onContactCreated={handleContactCreated}
        />
      )}

      {/* Floating Action Button for mobile */}
      <button
        className="fab"
        onClick={() => setShowContactForm(true)}
        title="Lisää uusi kontakti"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <line x1="12" y1="5" x2="12" y2="19"></line>
          <line x1="5" y1="12" x2="19" y2="12"></line>
        </svg>
      </button>
    </div>
  );
}

export default Dashboard;