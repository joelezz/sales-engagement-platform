import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { activitiesApi } from '../services/api';
import ActivityForm from './ActivityForm';
import './ActivitiesTimeline.css';

function ActivitiesTimeline() {
  const [showActivityForm, setShowActivityForm] = useState(false);
  const [filterType, setFilterType] = useState('all');
  const [dateRange, setDateRange] = useState('week');

  const { data: activitiesData, isLoading, refetch } = useQuery({
    queryKey: ['activities', filterType, dateRange],
    queryFn: () => activitiesApi.getAll({
      type: filterType !== 'all' ? filterType : undefined,
      date_range: dateRange,
    }),
  });

  const activities = activitiesData?.data?.activities || [];

  const handleActivityCreated = () => {
    setShowActivityForm(false);
    refetch();
  };

  const getActivityIcon = (type) => {
    switch (type) {
      case 'call':
        return (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
          </svg>
        );
      case 'email':
        return (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
            <polyline points="22,6 12,13 2,6"></polyline>
          </svg>
        );
      case 'sms':
        return (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          </svg>
        );
      case 'note':
        return (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14,2 14,8 20,8"></polyline>
            <line x1="16" y1="13" x2="8" y2="13"></line>
            <line x1="16" y1="17" x2="8" y2="17"></line>
          </svg>
        );
      case 'meeting':
        return (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
            <line x1="16" y1="2" x2="16" y2="6"></line>
            <line x1="8" y1="2" x2="8" y2="6"></line>
            <line x1="3" y1="10" x2="21" y2="10"></line>
          </svg>
        );
      default:
        return (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"></circle>
            <polyline points="12,6 12,12 16,14"></polyline>
          </svg>
        );
    }
  };

  const getActivityTypeColor = (type) => {
    switch (type) {
      case 'call': return 'var(--color-success)';
      case 'email': return 'var(--color-primary)';
      case 'sms': return 'var(--color-warning)';
      case 'note': return 'var(--color-secondary)';
      case 'meeting': return '#8b5cf6';
      default: return 'var(--color-text-muted)';
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 1) {
      return `Tänään ${date.toLocaleTimeString('fi-FI', { hour: '2-digit', minute: '2-digit' })}`;
    } else if (diffDays === 2) {
      return `Eilen ${date.toLocaleTimeString('fi-FI', { hour: '2-digit', minute: '2-digit' })}`;
    } else if (diffDays <= 7) {
      return `${diffDays - 1} päivää sitten`;
    } else {
      return date.toLocaleDateString('fi-FI', {
        day: 'numeric',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit',
      });
    }
  };

  const getActivityTypeLabel = (type) => {
    switch (type) {
      case 'call': return 'Puhelu';
      case 'email': return 'Sähköposti';
      case 'sms': return 'Tekstiviesti';
      case 'note': return 'Muistiinpano';
      case 'meeting': return 'Tapaaminen';
      default: return 'Toiminta';
    }
  };

  const groupActivitiesByDate = (activities) => {
    const groups = {};
    activities.forEach(activity => {
      const date = new Date(activity.created_at).toDateString();
      if (!groups[date]) {
        groups[date] = [];
      }
      groups[date].push(activity);
    });
    return groups;
  };

  const activityGroups = groupActivitiesByDate(activities);

  return (
    <div className="activities-timeline">
      <div className="container">
        <div className="activities-header">
          <div className="activities-title-section">
            <h1 className="activities-title">Aktiviteettien aikajana</h1>
            <p className="activities-subtitle">
              Seuraa kaikkia asiakasinteraktioita yhdestä paikasta
            </p>
          </div>
          
          <button
            className="btn btn-primary"
            onClick={() => setShowActivityForm(true)}
          >
            + Uusi aktiviteetti
          </button>
        </div>

        <div className="activities-filters">
          <div className="filter-group">
            <label className="filter-label">Tyyppi:</label>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="filter-select"
            >
              <option value="all">Kaikki</option>
              <option value="call">Puhelut</option>
              <option value="email">Sähköpostit</option>
              <option value="sms">Tekstiviestit</option>
              <option value="note">Muistiinpanot</option>
              <option value="meeting">Tapaamiset</option>
            </select>
          </div>

          <div className="filter-group">
            <label className="filter-label">Aikaväli:</label>
            <select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
              className="filter-select"
            >
              <option value="day">Tänään</option>
              <option value="week">Tämä viikko</option>
              <option value="month">Tämä kuukausi</option>
              <option value="quarter">Tämä neljännes</option>
              <option value="all">Kaikki</option>
            </select>
          </div>
        </div>

        <div className="activities-content">
          {isLoading ? (
            <div className="loading-state">
              <div className="loading-spinner"></div>
              <p>Ladataan aktiviteetteja...</p>
            </div>
          ) : Object.keys(activityGroups).length > 0 ? (
            <div className="timeline">
              {Object.entries(activityGroups).map(([date, dayActivities]) => (
                <div key={date} className="timeline-day">
                  <div className="timeline-date">
                    <h3 className="date-header">
                      {new Date(date).toLocaleDateString('fi-FI', {
                        weekday: 'long',
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                      })}
                    </h3>
                    <div className="activity-count">
                      {dayActivities.length} aktiviteettia
                    </div>
                  </div>

                  <div className="timeline-activities">
                    {dayActivities.map((activity, index) => (
                      <div key={activity.id} className="timeline-item">
                        <div className="timeline-connector">
                          <div 
                            className="timeline-dot"
                            style={{ backgroundColor: getActivityTypeColor(activity.type) }}
                          >
                            {getActivityIcon(activity.type)}
                          </div>
                          {index < dayActivities.length - 1 && <div className="timeline-line"></div>}
                        </div>

                        <div className="activity-card">
                          <div className="activity-header">
                            <div className="activity-type-badge" style={{ backgroundColor: getActivityTypeColor(activity.type) }}>
                              {getActivityTypeLabel(activity.type)}
                            </div>
                            <div className="activity-time">
                              {formatDate(activity.created_at)}
                            </div>
                          </div>

                          <div className="activity-content">
                            <h4 className="activity-title">
                              {activity.payload?.title || `${getActivityTypeLabel(activity.type)} - ${activity.contact?.full_name || 'Tuntematon kontakti'}`}
                            </h4>
                            
                            {activity.payload?.description && (
                              <p className="activity-description">
                                {activity.payload.description}
                              </p>
                            )}

                            {activity.payload?.content && (
                              <p className="activity-description">
                                {activity.payload.content}
                              </p>
                            )}

                            <div className="activity-meta">
                              {activity.contact && (
                                <span className="activity-contact">
                                  Kontakti: {activity.contact.full_name}
                                </span>
                              )}
                              
                              {activity.payload?.duration && (
                                <span className="activity-duration">
                                  Kesto: {activity.payload.duration}
                                </span>
                              )}

                              {activity.payload?.tags && activity.payload.tags.length > 0 && (
                                <div className="activity-tags">
                                  {activity.payload.tags.map((tag, tagIndex) => (
                                    <span key={tagIndex} className="activity-tag">
                                      {tag}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <div className="empty-icon">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
                  <circle cx="12" cy="12" r="10"></circle>
                  <polyline points="12,6 12,12 16,14"></polyline>
                </svg>
              </div>
              <h3 className="empty-title">Ei aktiviteetteja</h3>
              <p className="empty-description">
                Aloita lisäämällä ensimmäinen aktiviteettisi
              </p>
            </div>
          )}
        </div>
      </div>

      {showActivityForm && (
        <ActivityForm
          onClose={() => setShowActivityForm(false)}
          onActivityCreated={handleActivityCreated}
        />
      )}
    </div>
  );
}

export default ActivitiesTimeline;