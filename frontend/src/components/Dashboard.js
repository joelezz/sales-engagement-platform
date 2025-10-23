import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';
import { contactsApi } from '../services/api';
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
            
            <button
              className="btn btn-primary"
              onClick={() => setShowContactForm(true)}
            >
              + Uusi kontakti
            </button>
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
    </div>
  );
}

export default Dashboard;