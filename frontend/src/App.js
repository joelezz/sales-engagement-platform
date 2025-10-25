import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { NotificationProvider } from './contexts/NotificationContext';
import LoginScreen from './components/LoginScreen';
import Dashboard from './components/Dashboard';
import ContactDetails from './components/ContactDetails';
import ActivitiesTimeline from './components/ActivitiesTimeline';
import './index.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? children : <Navigate to="/login" />;
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <NotificationProvider>
        <AuthProvider>
          <Router>
            <div className="App">
              <Routes>
                <Route path="/login" element={<LoginScreen />} />
                <Route 
                  path="/dashboard" 
                  element={
                    <ProtectedRoute>
                      <Dashboard />
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/contacts/:id" 
                  element={
                    <ProtectedRoute>
                      <ContactDetails />
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/activities" 
                  element={
                    <ProtectedRoute>
                      <ActivitiesTimeline />
                    </ProtectedRoute>
                  } 
                />
                <Route path="/" element={<Navigate to="/dashboard" />} />
              </Routes>
            </div>
          </Router>
        </AuthProvider>
      </NotificationProvider>
    </QueryClientProvider>
  );
}

export default App;