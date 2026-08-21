import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  Cloud, 
  Lock, 
  User, 
  Mail, 
  AlertCircle, 
  ArrowRight, 
  RefreshCw, 
  UserPlus,
  LogIn
} from 'lucide-react';

export default function SignUp({ onSwitchToLogin }) {
  const navigate = useNavigate();
  const { register } = useAuth();
  
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    username: '',
    password: '',
    confirmPassword: ''
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [errorCode, setErrorCode] = useState('');
  const [fieldErrors, setFieldErrors] = useState({});

  const goToLogin = (msg = '') => {
    if (onSwitchToLogin) {
      onSwitchToLogin(msg);
    }
    navigate('/login', { state: msg ? { message: msg } : undefined });
  };

  const validateForm = () => {
    const errors = {};
    const { fullName, email, username, password, confirmPassword } = formData;

    if (!fullName.trim()) {
      errors.fullName = 'Full name is required.';
    }

    if (!email.trim()) {
      errors.email = 'Email address is required.';
    } else {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(email.trim())) {
        errors.email = 'Please enter a valid email address.';
      }
    }

    if (!username.trim()) {
      errors.username = 'Username is required.';
    } else if (username.trim().length < 3) {
      errors.username = 'Username must be at least 3 characters long.';
    }

    if (!password) {
      errors.password = 'Password is required.';
    } else if (password.length < 8) {
      errors.password = 'Password must be at least 8 characters long.';
    }

    if (!confirmPassword) {
      errors.confirmPassword = 'Please confirm your password.';
    } else if (password !== confirmPassword) {
      errors.confirmPassword = 'Passwords do not match.';
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    setErrorCode('');

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      const payload = {
        full_name: formData.fullName.trim(),
        email: formData.email.trim(),
        username: formData.username.trim(),
        password: formData.password,
        confirm_password: formData.confirmPassword
      };

      await register(payload);
      // Registration creates the Django PostgreSQL user and authenticates session immediately.
      // Navigate directly to /dashboard as requested in requirement 4
      navigate('/dashboard', { replace: true });
    } catch (err) {
      const code = err.data?.code || '';
      setErrorCode(code);

      let msg = err.data?.message || err.message || 'Registration failed. Please check your details.';
      if (code === 'EMAIL_EXISTS' || msg.toLowerCase().includes('email already exists')) {
        msg = 'An account with this email already exists. Please sign in.';
        setErrorCode('EMAIL_EXISTS');
      } else if (code === 'USERNAME_EXISTS' || msg.toLowerCase().includes('username already exists')) {
        msg = 'A user with that username already exists. Please choose another username or sign in.';
        setErrorCode('USERNAME_EXISTS');
      }

      setErrorMessage(msg);
      if (err.data?.field) {
        setFieldErrors(prev => ({
          ...prev,
          [err.data.field === 'full_name' ? 'fullName' : err.data.field === 'confirm_password' ? 'confirmPassword' : err.data.field]: msg
        }));
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (fieldErrors[field]) {
      setFieldErrors(prev => ({ ...prev, [field]: null }));
    }
    if (errorMessage) {
      setErrorMessage('');
      setErrorCode('');
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: 'var(--bg-main)',
      backgroundImage: 'radial-gradient(ellipse 80% 50% at 50% -20%, rgba(14, 165, 233, 0.15), transparent 70%), radial-gradient(ellipse 60% 40% at 80% 100%, rgba(99, 102, 241, 0.1), transparent 60%)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '2rem 1rem',
      fontFamily: 'var(--font-sans)',
      color: 'var(--text-main)'
    }}>
      {/* Brand Header */}
      <div style={{ textAlign: 'center', marginBottom: '1.75rem' }}>
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: '52px',
          height: '52px',
          borderRadius: '14px',
          background: 'linear-gradient(135deg, #2563EB 0%, #06B6D4 100%)',
          color: '#fff',
          boxShadow: '0 0 25px rgba(56, 189, 248, 0.45)',
          marginBottom: '0.85rem'
        }}>
          <Cloud size={28} />
        </div>
        <h1 style={{
          fontSize: '1.9rem',
          fontWeight: 800,
          letterSpacing: '-0.03em',
          margin: 0,
          color: '#fff'
        }}>
          CloudOpt<span style={{ color: 'var(--primary-light)' }}>.AI</span>
        </h1>
        <p style={{
          fontSize: '0.88rem',
          color: 'var(--text-secondary)',
          marginTop: '0.35rem',
          maxWidth: '460px'
        }}>
          Create your account to start optimizing cloud infrastructure
        </p>
      </div>

      {/* Main Registration Card */}
      <div style={{
        width: '100%',
        maxWidth: '480px',
        background: 'var(--bg-card)',
        border: '1px solid var(--border-medium)',
        borderRadius: 'var(--radius-lg)',
        padding: '2.25rem',
        boxShadow: 'var(--shadow-lg), 0 0 40px rgba(0, 0, 0, 0.4)',
        position: 'relative'
      }}>
        <div style={{ marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: '0 0 0.35rem 0', color: '#fff' }}>
            Create Account
          </h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: 0 }}>
            Enter your details below to register your CloudOpt.AI workspace.
          </p>
        </div>

        {/* Error Alert */}
        {errorMessage && (
          <div style={{
            background: 'var(--danger-bg)',
            border: '1px solid var(--danger-border)',
            borderRadius: 'var(--radius-md)',
            padding: '0.85rem 1rem',
            color: '#FCA5A5',
            fontSize: '0.85rem',
            marginBottom: '1.25rem'
          }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.65rem' }}>
              <AlertCircle size={18} color="var(--danger)" style={{ flexShrink: 0, marginTop: '2px' }} />
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600 }}>{errorMessage}</div>
                {errorCode === 'EMAIL_EXISTS' && (
                  <div style={{ marginTop: '0.6rem' }}>
                    <button
                      type="button"
                      onClick={() => goToLogin()}
                      className="btn btn-secondary btn-sm"
                      style={{
                        padding: '0.35rem 0.75rem',
                        fontSize: '0.8rem',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.35rem',
                        color: 'var(--primary-light)',
                        borderColor: 'rgba(56, 189, 248, 0.4)',
                        backgroundColor: 'rgba(14, 165, 233, 0.1)',
                        cursor: 'pointer'
                      }}
                    >
                      <LogIn size={13} />
                      <span>Sign In Now</span>
                    </button>
                  </div>
                )}
                {errorCode === 'USERNAME_EXISTS' && (
                  <div style={{ marginTop: '0.6rem' }}>
                    <button
                      type="button"
                      onClick={() => goToLogin()}
                      className="btn btn-secondary btn-sm"
                      style={{
                        padding: '0.35rem 0.75rem',
                        fontSize: '0.8rem',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.35rem',
                        color: 'var(--primary-light)',
                        borderColor: 'rgba(56, 189, 248, 0.4)',
                        backgroundColor: 'rgba(14, 165, 233, 0.1)',
                        cursor: 'pointer'
                      }}
                    >
                      <LogIn size={13} />
                      <span>Go to Sign In</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Full Name */}
          <div style={{ marginBottom: '1rem' }}>
            <label style={{
              display: 'block',
              fontSize: '0.82rem',
              fontWeight: 600,
              color: 'var(--text-secondary)',
              marginBottom: '0.4rem'
            }}>
              Full Name
            </label>
            <div style={{ position: 'relative' }}>
              <User size={16} color="var(--text-muted)" style={{
                position: 'absolute',
                left: '12px',
                top: '50%',
                transform: 'translateY(-50%)'
              }} />
              <input
                type="text"
                value={formData.fullName}
                onChange={(e) => handleChange('fullName', e.target.value)}
                placeholder="e.g. Alex Morgan"
                style={{
                  width: '100%',
                  padding: '0.65rem 0.85rem 0.65rem 2.4rem',
                  backgroundColor: 'var(--bg-subtle)',
                  border: `1px solid ${fieldErrors.fullName ? 'var(--danger)' : 'var(--border-medium)'}`,
                  borderRadius: 'var(--radius-md)',
                  color: 'var(--text-main)',
                  fontSize: '0.88rem',
                  outline: 'none'
                }}
                required
                autoComplete="name"
              />
            </div>
            {fieldErrors.fullName && (
              <span style={{ fontSize: '0.75rem', color: 'var(--danger)', marginTop: '0.25rem', display: 'block' }}>
                {fieldErrors.fullName}
              </span>
            )}
          </div>

          {/* Email Address */}
          <div style={{ marginBottom: '1rem' }}>
            <label style={{
              display: 'block',
              fontSize: '0.82rem',
              fontWeight: 600,
              color: 'var(--text-secondary)',
              marginBottom: '0.4rem'
            }}>
              Email Address
            </label>
            <div style={{ position: 'relative' }}>
              <Mail size={16} color="var(--text-muted)" style={{
                position: 'absolute',
                left: '12px',
                top: '50%',
                transform: 'translateY(-50%)'
              }} />
              <input
                type="email"
                value={formData.email}
                onChange={(e) => handleChange('email', e.target.value)}
                placeholder="alex@company.com"
                style={{
                  width: '100%',
                  padding: '0.65rem 0.85rem 0.65rem 2.4rem',
                  backgroundColor: 'var(--bg-subtle)',
                  border: `1px solid ${fieldErrors.email ? 'var(--danger)' : 'var(--border-medium)'}`,
                  borderRadius: 'var(--radius-md)',
                  color: 'var(--text-main)',
                  fontSize: '0.88rem',
                  outline: 'none'
                }}
                required
                autoComplete="email"
              />
            </div>
            {fieldErrors.email && (
              <span style={{ fontSize: '0.75rem', color: 'var(--danger)', marginTop: '0.25rem', display: 'block' }}>
                {fieldErrors.email}
              </span>
            )}
          </div>

          {/* Username */}
          <div style={{ marginBottom: '1rem' }}>
            <label style={{
              display: 'block',
              fontSize: '0.82rem',
              fontWeight: 600,
              color: 'var(--text-secondary)',
              marginBottom: '0.4rem'
            }}>
              Username
            </label>
            <div style={{ position: 'relative' }}>
              <UserPlus size={16} color="var(--text-muted)" style={{
                position: 'absolute',
                left: '12px',
                top: '50%',
                transform: 'translateY(-50%)'
              }} />
              <input
                type="text"
                value={formData.username}
                onChange={(e) => handleChange('username', e.target.value)}
                placeholder="alex_dev"
                style={{
                  width: '100%',
                  padding: '0.65rem 0.85rem 0.65rem 2.4rem',
                  backgroundColor: 'var(--bg-subtle)',
                  border: `1px solid ${fieldErrors.username ? 'var(--danger)' : 'var(--border-medium)'}`,
                  borderRadius: 'var(--radius-md)',
                  color: 'var(--text-main)',
                  fontSize: '0.88rem',
                  outline: 'none'
                }}
                required
                autoComplete="username"
              />
            </div>
            {fieldErrors.username && (
              <span style={{ fontSize: '0.75rem', color: 'var(--danger)', marginTop: '0.25rem', display: 'block' }}>
                {fieldErrors.username}
              </span>
            )}
          </div>

          {/* Password & Confirm Password */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginBottom: '1.5rem' }}>
            <div>
              <label style={{
                display: 'block',
                fontSize: '0.82rem',
                fontWeight: 600,
                color: 'var(--text-secondary)',
                marginBottom: '0.4rem'
              }}>
                Password
              </label>
              <div style={{ position: 'relative' }}>
                <Lock size={15} color="var(--text-muted)" style={{
                  position: 'absolute',
                  left: '10px',
                  top: '50%',
                  transform: 'translateY(-50%)'
                }} />
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => handleChange('password', e.target.value)}
                  placeholder="••••••••"
                  style={{
                    width: '100%',
                    padding: '0.65rem 0.75rem 0.65rem 2.2rem',
                    backgroundColor: 'var(--bg-subtle)',
                    border: `1px solid ${fieldErrors.password ? 'var(--danger)' : 'var(--border-medium)'}`,
                    borderRadius: 'var(--radius-md)',
                    color: 'var(--text-main)',
                    fontSize: '0.88rem',
                    outline: 'none'
                  }}
                  required
                  autoComplete="new-password"
                />
              </div>
            </div>

            <div>
              <label style={{
                display: 'block',
                fontSize: '0.82rem',
                fontWeight: 600,
                color: 'var(--text-secondary)',
                marginBottom: '0.4rem'
              }}>
                Confirm Password
              </label>
              <div style={{ position: 'relative' }}>
                <Lock size={15} color="var(--text-muted)" style={{
                  position: 'absolute',
                  left: '10px',
                  top: '50%',
                  transform: 'translateY(-50%)'
                }} />
                <input
                  type="password"
                  value={formData.confirmPassword}
                  onChange={(e) => handleChange('confirmPassword', e.target.value)}
                  placeholder="••••••••"
                  style={{
                    width: '100%',
                    padding: '0.65rem 0.75rem 0.65rem 2.2rem',
                    backgroundColor: 'var(--bg-subtle)',
                    border: `1px solid ${fieldErrors.confirmPassword ? 'var(--danger)' : 'var(--border-medium)'}`,
                    borderRadius: 'var(--radius-md)',
                    color: 'var(--text-main)',
                    fontSize: '0.88rem',
                    outline: 'none'
                  }}
                  required
                  autoComplete="new-password"
                />
              </div>
            </div>
          </div>

          {(fieldErrors.password || fieldErrors.confirmPassword) && (
            <div style={{ fontSize: '0.75rem', color: 'var(--danger)', marginBottom: '1rem' }}>
              {fieldErrors.password || fieldErrors.confirmPassword}
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isSubmitting}
            className="btn btn-primary"
            style={{
              width: '100%',
              padding: '0.8rem',
              fontSize: '0.95rem',
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem',
              opacity: isSubmitting ? 0.7 : 1,
              cursor: isSubmitting ? 'not-allowed' : 'pointer'
            }}
          >
            {isSubmitting ? (
              <>
                <RefreshCw size={18} className="spin-animation" />
                <span>Creating Account...</span>
              </>
            ) : (
              <>
                <span>Create Account</span>
                <ArrowRight size={18} />
              </>
            )}
          </button>
        </form>

        {/* Footer: Already have an account? */}
        <div style={{
          marginTop: '1.75rem',
          paddingTop: '1.25rem',
          borderTop: '1px solid var(--border-subtle)',
          textAlign: 'center',
          fontSize: '0.88rem',
          color: 'var(--text-secondary)'
        }}>
          <span>Already have an account? </span>
          <button
            type="button"
            onClick={() => goToLogin()}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--primary-light)',
              fontWeight: 700,
              cursor: 'pointer',
              padding: 0,
              textDecoration: 'underline'
            }}
          >
            Sign In
          </button>
        </div>
      </div>
    </div>
  );
}
