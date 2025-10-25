import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { contactsApi, activitiesApi, callsApi } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { useNotification } from '../contexts/NotificationContext';
import ContactForm from './ContactForm';
import Header from './Header';


function ContactDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { logout } = useAuth();
  const { showSuccess, showError } = useNotification();
  const [showEditForm, setShowEditForm] = useState(false);
  const [isCallInProgress, setIsCallInProgress] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const { data: contact, isLoading: contactLoading, refetch: refetchContact } = useQuery({
    queryKey: ['contact', id],
    queryFn: () => contactsApi.getById(id),
  });

  const { data: activitiesData, isLoading: activitiesLoading } = useQuery({
    queryKey: ['activities', id],
    queryFn: () => activitiesApi.getByContact(id),
  });

  const contactData = contact?.data;
  const activities = activitiesData?.data?.activities || [];

  const handleContactUpdated = () => {
    setShowEditForm(false);
    refetchContact();
  };

  const handleCall = async () => {
    if (!contactData.phone) {
      showError('Kontaktilla ei ole puhelinnumeroa!');
      return;
    }

    setIsCallInProgress(true);
    try {
      const response = await callsApi.initiate({
        contact_id: parseInt(id),
        phone_number: contactData.phone,
        call_type: 'outbound'
      });

      if (response.data) {
        showSuccess(`Soitto aloitettu numeroon ${contactData.phone}`);
        // Päivitä aktiviteetit kun puhelu on aloitettu
        setTimeout(() => {
          window.location.reload(); // Yksinkertainen tapa päivittää aktiviteetit
        }, 2000);
      }
    } catch (error) {
      console.error('Soiton aloitus epäonnistui:', error);
      let errorMessage = 'Soiton aloitus epäonnistui. Tarkista Twilio-asetukset.';
      
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.response?.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error.message) {
        errorMessage = `Verkkovirhe: ${error.message}`;
      }
      
      showError(errorMessage);
    } finally {
      setIsCallInProgress(false);
    }
  };

  const getInitials = (firstname, lastname) => {
    return `${firstname?.charAt(0) || ''}${lastname?.charAt(0) || ''}`.toUpperCase();
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('fi-FI', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getActivityIcon = (type) => {
    switch (type) {
      case 'call':
        return (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
          </svg>
        );
      case 'email':
        return (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
            <polyline points="22,6 12,13 2,6"></polyline>
          </svg>
        );
      case 'note':
        return (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14,2 14,8 20,8"></polyline>
            <line x1="16" y1="13" x2="8" y2="13"></line>
            <line x1="16" y1="17" x2="8" y2="17"></line>
            <polyline points="10,9 9,9 8,9"></polyline>
          </svg>
        );
      default:
        return (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"></circle>
            <polyline points="12,6 12,12 16,14"></polyline>
          </svg>
        );
    }
  };

  if (contactLoading) {
    return (
      <div className="contact-details-loading">
        <div className="loading-spinner"></div>
        <p>Ladataan kontaktin tietoja...</p>
      </div>
    );
  }

  if (!contactData) {
    return (
      <div className="contact-details-error">
        <h2>Kontaktia ei löytynyt</h2>
        <button className="btn btn-primary" onClick={() => navigate('/dashboard')}>
          Takaisin kontaktilistaan
        </button>
      </div>
    );
  }

  return (
    <div className="contact-details">
      <Header 
        onLogout={logout}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
      />
      
      <div className="container">
        <div className="contact-details-header">
          <div className="breadcrumb">
            <button 
              className="breadcrumb-link"
              onClick={() => navigate('/dashboard')}
            >
              Kontaktit
            </button>
            <span className="breadcrumb-separator">/</span>
            <span className="breadcrumb-current">
              {contactData ? `${contactData.firstname} ${contactData.lastname}` : 'Ladataan...'}
            </span>
          </div>
          
          <div className="contact-details-actions">
            <button 
              className="btn btn-secondary"
              onClick={() => setShowEditForm(true)}
            >
              Muokkaa
            </button>
            <button 
              className="btn btn-primary"
              onClick={handleCall}
              disabled={!contactData.phone || isCallInProgress}
            >
              {isCallInProgress ? (
                <>
                  <div className="loading-spinner-small"></div>
                  Soittaa...
                </>
              ) : (
                <>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
                  </svg>
                  Soita
                </>
              )}
            </button>
          </div>
        </div>

        <div className="contact-details-content">
          <div className="contact-details-main">
            <div className="contact-header">
              <div className="contact-avatar-large">
                {getInitials(contactData.firstname, contactData.lastname)}
              </div>
              
              <div className="contact-header-info">
                <h1 className="contact-name">
                  {contactData.firstname} {contactData.lastname}
                </h1>
                
                <div className="contact-meta">
                  {contactData.contact_metadata?.position && (
                    <span className="contact-position">
                      {contactData.contact_metadata.position}
                    </span>
                  )}
                  {contactData.contact_metadata?.company && (
                    <span className="contact-company">
                      {contactData.contact_metadata.company}
                    </span>
                  )}
                </div>
              </div>
            </div>

            <div className="contact-info-grid">
              <div className="contact-info-item">
                <div className="contact-info-label">Sähköposti</div>
                <div className="contact-info-value">
                  {contactData.email ? (
                    <a href={`mailto:${contactData.email}`} className="contact-link">
                      {contactData.email}
                    </a>
                  ) : (
                    <span className="contact-empty">Ei sähköpostia</span>
                  )}
                </div>
              </div>

              <div className="contact-info-item">
                <div className="contact-info-label">Puhelinnumero</div>
                <div className="contact-info-value">
                  {contactData.phone ? (
                    <div className="phone-actions">
                      <span className="phone-number">{contactData.phone}</span>
                      <button 
                        className="phone-call-btn"
                        onClick={handleCall}
                        disabled={isCallInProgress}
                        title="Soita VoIP:lla"
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
                        </svg>
                      </button>
                    </div>
                  ) : (
                    <span className="contact-empty">Ei puhelinnumeroa</span>
                  )}
                </div>
              </div>

              <div className="contact-info-item">
                <div className="contact-info-label">Luotu</div>
                <div className="contact-info-value">
                  {formatDate(contactData.created_at)}
                </div>
              </div>

              <div className="contact-info-item">
                <div className="contact-info-label">Päivitetty</div>
                <div className="contact-info-value">
                  {formatDate(contactData.updated_at)}
                </div>
              </div>
            </div>
          </div>

          <div className="contact-details-sidebar">
            <div className="activities-section">
              <h3 className="activities-title">Toiminta</h3>
              
              {activitiesLoading ? (
                <div className="activities-loading">
                  <div className="loading-spinner"></div>
                </div>
              ) : activities.length > 0 ? (
                <div className="activities-list">
                  {activities.map((activity) => (
                    <div key={activity.id} className="activity-item">
                      <div className="activity-icon">
                        {getActivityIcon(activity.type)}
                      </div>
                      <div className="activity-content">
                        <div className="activity-title">
                          {activity.payload?.title || activity.type}
                        </div>
                        <div className="activity-description">
                          {activity.payload?.description || activity.payload?.content}
                        </div>
                        <div className="activity-date">
                          {formatDate(activity.created_at)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="activities-empty">
                  <p>Ei toimintaa vielä</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {showEditForm && (
        <ContactForm
          contact={contactData}
          onClose={() => setShowEditForm(false)}
          onContactCreated={handleContactUpdated}
        />
      )}
    </div>
  );
}

export default ContactDetails;