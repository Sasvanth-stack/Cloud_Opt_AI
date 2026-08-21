import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export const ROLES = {
  ADMIN: 'ADMIN',
  DEVOPS_ENGINEER: 'DEVOPS_ENGINEER',
  FINOPS_ANALYST: 'FINOPS_ANALYST',
  SRE_OPERATIONS: 'SRE_OPERATIONS',
  VIEWER_MANAGER: 'VIEWER_MANAGER'
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Equal access model: All authenticated users have full access to all features
  const permissions = {
    canApprove: true,
    canDismiss: true,
    canManageUsers: true,
    canViewAuditLogs: true,
    canModifyResources: true,
    canManageAlerts: true,
    canRunOptimization: true,
    canExportReports: true,
  };

  const checkAuthStatus = useCallback(async () => {
    try {
      setIsLoading(true);
      const currentUser = await api.getCurrentUser();
      if (currentUser && currentUser.username) {
        setUser(currentUser);
        return currentUser;
      } else {
        setUser(null);
        return null;
      }
    } catch {
      setUser(null);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuthStatus();
  }, [checkAuthStatus]);

  const login = async (identifier, password) => {
    const response = await api.login(identifier, password);
    if (response && (response.status === 'success' || response.user)) {
      const loggedUser = response.user || response.data?.user;
      setUser(loggedUser);
      return response;
    }
    throw new Error(response?.message || 'Login failed');
  };

  const register = async (userData) => {
    const response = await api.register(userData);
    if (response && (response.status === 'success' || response.user)) {
      const newUser = response.user || response.data?.user;
      setUser(newUser);
      return response;
    }
    throw new Error(response?.message || 'Registration failed');
  };

  const logout = async () => {
    try {
      await api.logout();
    } finally {
      setUser(null);
    }
  };

  const forgotPassword = async (email) => {
    return await api.forgotPassword(email);
  };

  const resetPassword = async (uid, token, newPassword, confirmPassword) => {
    return await api.resetPassword(uid, token, newPassword, confirmPassword);
  };

  const value = {
    user,
    isAuthenticated: Boolean(user),
    isLoading,
    permissions,
    login,
    register,
    logout,
    forgotPassword,
    resetPassword,
    checkAuthStatus
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

