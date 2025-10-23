import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { activitiesApi, contactsApi } from '../services/api';
import './ActivityForm.css';

function ActivityForm({ onClose, onActivityCreated, activity = null }) {
  const isEditing = !!activity;
  const [formData, setFormData] = useState({
    type: activity?.type || 'note',
    contact_id: activity?.contact_id || '',
    title: activity?.payload?.title || '',
    description: activity?.payload?.description || '',
    content: activity?.payload?.content || '',
    duration: activity?.payload?.duration || '',
    tags: activity?.payload?.tags?.join(', ') || '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Fetch contacts for selection
  const { data: contactsData } = useQuery({
    queryKey: ['contacts'],
    queryFn: () => contactsApi.getAll(),
  });

  const contacts = contactsData?.data?.contacts || [];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const activityData = {
        type: formData.type,
        contact_id: parseInt(formData.contact_id),
        payload: {
          title: formData.title || null,
          description: formData.description || null,
          content: formData.content || null,
          duration: formData.duration || null,
          tags: formData.tags ? formData.tags.split(',').map(tag => tag.trim()).filter(tag => tag) : [],
        },
      };

      await activitiesApi.create(activityData);
      onActivityCreated();
    } catch (err) {
      console.error('Error saving activity:', err);
      setError(err.response?.data?.message || 'Virhe tallentaessa aktiviteettia');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const getActivityTypeLabel = (type) => {
    switch (type) {
      case 'call': return 'Puhelu';
      case 'email': return 'Sähköposti';
      case 'sms': return 'Tekstiviesti';
      case 'note': return 'Muistiinpano';
      case 'meeting': return 'Tapaaminen';
      default: return 'Muu';
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content activity-form-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">
            {isEditing ? 'Muokkaa aktiviteettia' : 'Uusi aktiviteetti'}
          </h2>
          <button className="modal-close" onClick={onClose}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="activity-form">
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="type" className="form-label">
                Aktiviteetin tyyppi *
              </label>
              <select
                id="type"
                name="type"
                value={formData.type}
                onChange={handleInputChange}
                className="input-field"
                required
              >
                <option value="note">Muistiinpano</option>
                <option value="call">Puhelu</option>
                <option value="email">Sähköposti</option>
                <option value="sms">Tekstiviesti</option>
                <option value="meeting">Tapaaminen</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="contact_id" className="form-label">
                Kontakti *
              </label>
              <select
                id="contact_id"
                name="contact_id"
                value={formData.contact_id}
                onChange={handleInputChange}
                className="input-field"
                required
              >
                <option value="">Valitse kontakti</option>
                {contacts.map((contact) => (
                  <option key={contact.id} value={contact.id}>
                    {contact.firstname} {contact.lastname}
                    {contact.contact_metadata?.company && ` - ${contact.contact_metadata.company}`}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="title" className="form-label">
              Otsikko
            </label>
            <input
              type="text"
              id="title"
              name="title"
              value={formData.title}
              onChange={handleInputChange}
              className="input-field"
              placeholder={`${getActivityTypeLabel(formData.type)} - ${new Date().toLocaleDateString('fi-FI')}`}
            />
          </div>

          {formData.type === 'note' ? (
            <div className="form-group">
              <label htmlFor="content" className="form-label">
                Sisältö *
              </label>
              <textarea
                id="content"
                name="content"
                value={formData.content}
                onChange={handleInputChange}
                className="input-field textarea-field"
                rows="4"
                placeholder="Kirjoita muistiinpanosi tähän..."
                required
              />
            </div>
          ) : (
            <div className="form-group">
              <label htmlFor="description" className="form-label">
                Kuvaus
              </label>
              <textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                className="input-field textarea-field"
                rows="3"
                placeholder="Kuvaa aktiviteettia..."
              />
            </div>
          )}

          <div className="form-row">
            {(formData.type === 'call' || formData.type === 'meeting') && (
              <div className="form-group">
                <label htmlFor="duration" className="form-label">
                  Kesto
                </label>
                <input
                  type="text"
                  id="duration"
                  name="duration"
                  value={formData.duration}
                  onChange={handleInputChange}
                  className="input-field"
                  placeholder="esim. 15 min, 1h 30min"
                />
              </div>
            )}

            <div className="form-group">
              <label htmlFor="tags" className="form-label">
                Tunnisteet
              </label>
              <input
                type="text"
                id="tags"
                name="tags"
                value={formData.tags}
                onChange={handleInputChange}
                className="input-field"
                placeholder="tärkeä, seuranta, myynti (pilkulla erotettu)"
              />
            </div>
          </div>

          <div className="form-actions">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onClose}
              disabled={loading}
            >
              Peruuta
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
            >
              {loading ? 'Tallennetaan...' : (isEditing ? 'Tallenna muutokset' : 'Luo aktiviteetti')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default ActivityForm;