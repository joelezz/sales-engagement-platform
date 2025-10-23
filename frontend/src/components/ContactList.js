import React from 'react';
import { useNavigate } from 'react-router-dom';
import './ContactList.css';

function ContactList({ contacts, onContactUpdate }) {
  const navigate = useNavigate();

  const handleContactClick = (contactId) => {
    navigate(`/contacts/${contactId}`);
  };

  const formatPhone = (phone) => {
    if (!phone) return '-';
    return phone;
  };

  const getInitials = (firstname, lastname) => {
    return `${firstname?.charAt(0) || ''}${lastname?.charAt(0) || ''}`.toUpperCase();
  };

  const getCompanyFromMetadata = (metadata) => {
    return metadata?.company || '-';
  };

  if (!contacts || contacts.length === 0) {
    return (
      <div className="contact-list-empty">
        <div className="empty-state">
          <div className="empty-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
              <circle cx="9" cy="7" r="4"></circle>
              <path d="M22 21v-2a4 4 0 0 0-3-3.87"></path>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
            </svg>
          </div>
          <h3 className="empty-title">Ei kontakteja</h3>
          <p className="empty-description">
            Aloita lisäämällä ensimmäinen kontaktisi
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="contact-list">
      <div className="contact-list-header">
        <div className="contact-count">
          {contacts.length} kontaktia
        </div>
      </div>
      
      <div className="contact-grid">
        {contacts.map((contact) => (
          <div
            key={contact.id}
            className="contact-card"
            onClick={() => handleContactClick(contact.id)}
          >
            <div className="contact-avatar">
              {getInitials(contact.firstname, contact.lastname)}
            </div>
            
            <div className="contact-info">
              <h3 className="contact-name">
                {contact.firstname} {contact.lastname}
              </h3>
              
              <div className="contact-details">
                <div className="contact-detail">
                  <span className="contact-label">Yritys:</span>
                  <span className="contact-value">
                    {getCompanyFromMetadata(contact.contact_metadata)}
                  </span>
                </div>
                
                <div className="contact-detail">
                  <span className="contact-label">Sähköposti:</span>
                  <span className="contact-value">
                    {contact.email || '-'}
                  </span>
                </div>
                
                <div className="contact-detail">
                  <span className="contact-label">Puhelin:</span>
                  <span className="contact-value">
                    {formatPhone(contact.phone)}
                  </span>
                </div>
              </div>
            </div>
            
            <div className="contact-actions">
              <button
                className="contact-action-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  // Handle call action
                }}
                title="Soita"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
                </svg>
              </button>
              
              <button
                className="contact-action-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  // Handle email action
                }}
                title="Lähetä sähköposti"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                  <polyline points="22,6 12,13 2,6"></polyline>
                </svg>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default ContactList;