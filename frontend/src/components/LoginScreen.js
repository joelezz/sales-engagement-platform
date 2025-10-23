import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Navigate } from 'react-router-dom';
import './LoginScreen.css';

function LoginScreen() {
  const { login, register, isAuthenticated } = useAuth();
  const [isLoginMode, setIsLoginMode] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    companyName: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (isAuthenticated) {
    return <Navigate to="/dashboard" />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      let result;
      if (isLoginMode) {
        result = await login(formData.email, formData.password);
      } else {
        result = await register(formData.email, formData.password, formData.companyName);
        if (result.success) {
          // Auto-login after successful registration
          result = await login(formData.email, formData.password);
        }
      }

      if (!result.success) {
        setError(result.error);
      }
    } catch (err) {
      setError('An unexpected error occurred');
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
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1 className="login-title">Sales Engagement Platform</h1>
          <p className="login-subtitle">
            {isLoginMode ? 'Kirjaudu sisään tilillesi' : 'Luo uusi tili'}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

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
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password" className="form-label">
              Salasana
            </label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleInputChange}
              className="input-field"
              placeholder="Salasana"
              required
            />
          </div>

          {!isLoginMode && (
            <div className="form-group">
              <label htmlFor="companyName" className="form-label">
                Yrityksen nimi
              </label>
              <input
                type="text"
                id="companyName"
                name="companyName"
                value={formData.companyName}
                onChange={handleInputChange}
                className="input-field"
                placeholder="Yrityksen nimi"
                required
              />
            </div>
          )}

          <button
            type="submit"
            className="btn btn-primary btn-lg w-full"
            disabled={loading}
          >
            {loading ? 'Ladataan...' : (isLoginMode ? 'Kirjaudu sisään' : 'Rekisteröidy')}
          </button>
        </form>

        <div className="login-footer">
          <button
            type="button"
            className="link-button"
            onClick={() => {
              setIsLoginMode(!isLoginMode);
              setError('');
              setFormData({ email: '', password: '', companyName: '' });
            }}
          >
            {isLoginMode 
              ? 'Eikö sinulla ole tiliä? Rekisteröidy tästä' 
              : 'Onko sinulla jo tili? Kirjaudu sisään'
            }
          </button>
        </div>
      </div>
    </div>
  );
}

export default LoginScreen;