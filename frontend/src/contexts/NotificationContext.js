import React, { createContext, useContext, useState } from 'react';
import Notification from '../components/Notification';

const NotificationContext = createContext();

export function useNotification() {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
}

export function NotificationProvider({ children }) {
  const [notifications, setNotifications] = useState([]);

  const addNotification = (message, type = 'info', duration = 5000) => {
    const id = Date.now() + Math.random();
    const notification = { id, message, type, duration };
    
    setNotifications(prev => [...prev, notification]);
    
    return id;
  };

  const removeNotification = (id) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
  };

  const showSuccess = (message, duration) => addNotification(message, 'success', duration);
  const showError = (message, duration) => addNotification(message, 'error', duration);
  const showWarning = (message, duration) => addNotification(message, 'warning', duration);
  const showInfo = (message, duration) => addNotification(message, 'info', duration);

  return (
    <NotificationContext.Provider value={{
      addNotification,
      removeNotification,
      showSuccess,
      showError,
      showWarning,
      showInfo
    }}>
      {children}
      
      {/* Render notifications */}
      <div className="notification-container">
        {notifications.map((notification, index) => (
          <div 
            key={notification.id} 
            style={{ 
              position: 'fixed',
              top: `${20 + (index * 80)}px`,
              right: '20px',
              zIndex: 1000 + index
            }}
          >
            <Notification
              message={notification.message}
              type={notification.type}
              duration={notification.duration}
              onClose={() => removeNotification(notification.id)}
            />
          </div>
        ))}
      </div>
    </NotificationContext.Provider>
  );
}