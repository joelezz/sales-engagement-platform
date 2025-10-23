import React, { useState } from 'react';
import { contactsApi } from '../services/api';
import './ContactForm.css';

function ContactForm({ onClose, onContactCreated, contact = null }) {
  const isEditing = !!contact;
  const [formData, setFormData] = useState({
    firstname: contact?.firstname || '',
    lastname: contact?.lastname || '',
    email: contact?.email || '',
    phone: contact?.phone || '',
    company: contact?.contact_metadata?.company || '',
    position: contact?.contact_metadata?.position || '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const contactData = {
        firstname: formData.firstname,
        lastname: formData.lastname,
        email: formData.email || null,
        phone: formData.phone || null,
        contact_metadata: {
          company: formData.company || null,
          position: formData.position || null,
        },
      };

      if (isEditing) {
        await contactsApi.update(contact.id, contactData);
      } else {
        await contactsApi.create(contactData);
      }

      onContactCreated();
    } catch (err) {
      console.error('Error saving contact:', err);
      setError(err.response?.data?.message || 'Virhe tallentaessa kontaktia');
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

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">
            {isEditing ? 'Muokkaa kontaktia' : 'Uusi kontakti'}
          </h2>
          <button className="modal-close" onClick={onClose}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="contact-form">
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="firstname" className="form-label">
                Etunimi *
              </label>
              <input
                type="text"
                id="firstname"
                name="firstname"
                value={formData.firstname}
                onChange={handleInputChange}
                className="input-field"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="lastname" className="form-label">
                Sukunimi *
              </label>
              <input
                type="text"
                id="lastname"
                name="lastname"
                value={formData.lastname}
                onChange={handleInputChange}
                className="input-field"
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="email" className="form-label">
              Sähköposti
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              className="input-field"
              placeholder="anna@yritys.fi"
            />
          </div>

          <div className="form-group">
            <label htmlFor="phone" className="form-label">
              Puhelinnumero
            </label>
            <input
              type="tel"
              id="phone"
              name="phone"
              value={formData.phone}
              onChange={handleInputChange}
              className="input-field"
              placeholder="+358 40 123 4567"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="company" className="form-label">
                Yritys
              </label>
              <input
                type="text"
                id="company"
                name="company"
                value={formData.company}
                onChange={handleInputChange}
                className="input-field"
                placeholder="Yrityksen nimi"
              />
            </div>

            <div className="form-group">
              <label htmlFor="position" className="form-label">
                Asema
              </label>
              <input
                type="text"
                id="position"
                name="position"
                value={formData.position}
                onChange={handleInputChange}
                className="input-field"
                placeholder="Toimitusjohtaja"
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
              {loading ? 'Tallennetaan...' : (isEditing ? 'Tallenna muutokset' : 'Luo kontakti')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default ContactForm;