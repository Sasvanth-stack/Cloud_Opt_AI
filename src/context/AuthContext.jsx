import React, { createContext, useContext, useState } from 'react';

const AuthContext = createContext(null);

export const ROLES = {
  ADMIN: 'ADMIN',
  DEVOPS_ENGINEER: 'DEVOPS_ENGINEER',
  FINOPS_ANALYST: 'FINOPS_ANALYST',
  SRE_OPERATIONS: 'SRE_OPERATIONS',
  VIEWER_MANAGER: 'VIEWER_MANAGER'
};

const DEFAULT_USER = {
  id: 1,
  username: 'Admin',
  full_name: 'CloudOpt Operator',
  email: 'operator@cloudopt.ai',
  role: 'ADMIN',
  is_active: true
};

export function AuthProvider({ children }) {
  const [user] = useState(DEFAULT_USER);

  // Full operational permissions for cloud optimization dashboard
  const permissions = {
    canApprove: true,
    canDismiss: true,
    canModifyResources: true,
    canManageAlerts: true,
    canRunOptimization: true,
    canExportReports: true,
  };

  const value = {
    user,
    role: 'ADMIN',
    isAuthenticated: true,
    isLoading: false,
    permissions,
    login: async () => ({ status: 'success', user: DEFAULT_USER }),
    register: async () => ({ status: 'success', user: DEFAULT_USER }),
    logout: async () => {},
    forgotPassword: async () => ({ status: 'success' }),
    resetPassword: async () => ({ status: 'success' }),
    checkAuthStatus: async () => DEFAULT_USER
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
