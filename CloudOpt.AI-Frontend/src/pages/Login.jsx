import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  Cloud, 
  Lock, 
  User, 
  AlertCircle, 
  CheckCircle2, 
  ArrowRight, 
  RefreshCw
} from 'lucide-react';

export default function Login({ onSwitchToSignUp, onSwitchToForgotPassword, initialSuccessMessage }) {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState(
    location.state?.message || initialSuccessMessage || ''
  );

  useEffect(() => {
    if (location.state?.message) {
      setSuccessMessage(location.state.message);
    } else if (initialSuccessMessage) {
      setSuccessMessage(initialSuccessMessage);
    }
  }, [location.state, initialSuccessMessage]);

  const goToSignUp = () => {
    if (onSwitchToSignUp) onSwitchToSignUp();
    navigate('/signup');
  };

  const goToForgotPassword = () => {
    if (onSwitchToForgotPassword) onSwitchToForgotPassword();
    navigate('/forgot-password');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!identifier.trim() || !password) {
      setErrorMessage('Please enter both your email/username and password.');
      return;
    }

    setErrorMessage('');
    setSuccessMessage('');
    setIsSubmitting(true);

    try {
      await login(identifier.trim(), password);
      // Requirement 5: On successful login, navigate to /dashboard
      navigate('/dashboard', { replace: true });
    } catch (err) {
      // Requirement 6: On failed login, stay on /login and show error
      const serverMsg = err.data?.message || err.message || 'Invalid username/email or password.';
      setErrorMessage(serverMsg);
    } finally {
      setIsSubmitting(false);
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
      <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: '56px',
          height: '56px',
          borderRadius: '16px',
          background: 'linear-gradient(135deg, #2563EB 0%, #06B6D4 100%)',
          color: '#fff',
          boxShadow: '0 0 25px rgba(56, 189, 248, 0.45)',
          marginBottom: '1rem'
        }}>
          <Cloud size={32} />
        </div>
        <h1 style={{
          fontSize: '2.1rem',
          fontWeight: 800,
          letterSpacing: '-0.03em',
          margin: 0,
          color: '#fff'
        }}>
          CloudOpt<span style={{ color: 'var(--primary-light)' }}>.AI</span>
        </h1>
        <p style={{
          fontSize: '0.92rem',
          color: 'var(--text-secondary)',
          marginTop: '0.4rem',
          maxWidth: '460px'
        }}>
          Intelligent Cloud Resource Optimization & FinOps Management
        </p>
      </div>

      {/* Main Login Card */}
      <div style={{
        width: '100%',
        maxWidth: '440px',
        background: 'var(--bg-card)',
        border: '1px solid var(--border-medium)',
        borderRadius: 'var(--radius-lg)',
        padding: '2.25rem',
        boxShadow: 'var(--shadow-lg), 0 0 40px rgba(0, 0, 0, 0.4)',
        position: 'relative'
      }}>
        <div style={{ marginBottom: '1.75rem' }}>
          <h2 style={{ fontSize: '1.35rem', fontWeight: 700, margin: '0 0 0.35rem 0', color: '#fff' }}>
            Sign In
          </h2>
          <p style={{ fontSize: '0.86rem', color: 'var(--text-muted)', margin: 0 }}>
            Enter your credentials to access your optimization workspace.
          </p>
        </div>

        {/* Success Alert */}
        {successMessage && (
          <div style={{
            background: 'var(--success-bg)',
            border: '1px solid var(--success-border)',
            borderRadius: 'var(--radius-md)',
            padding: '0.75rem 1rem',
            color: '#86EFAC',
            fontSize: '0.85rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.65rem',
            marginBottom: '1.25rem'
          }}>
            <CheckCircle2 size={18} color="var(--success)" style={{ flexShrink: 0 }} />
            <span>{successMessage}</span>
          </div>
        )}

        {/* Error Alert */}
        {errorMessage && (
          <div style={{
            background: 'var(--danger-bg)',
            border: '1px solid var(--danger-border)',
            borderRadius: 'var(--radius-md)',
            padding: '0.85rem 1rem',
            color: '#FCA5A5',
            fontSize: '0.85rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.65rem',
            marginBottom: '1.25rem'
          }}>
            <AlertCircle size={18} color="var(--danger)" style={{ flexShrink: 0 }} />
            <span style={{ fontWeight: 500 }}>{errorMessage}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Email or Username */}
          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{
              display: 'block',
              fontSize: '0.82rem',
              fontWeight: 600,
              color: 'var(--text-secondary)',
              marginBottom: '0.5rem'
            }}>
              Email or Username
            </label>
            <div style={{ position: 'relative' }}>
              <User size={17} color="var(--text-muted)" style={{
                position: 'absolute',
                left: '12px',
                top: '50%',
                transform: 'translateY(-50%)'
              }} />
              <input
                type="text"
                value={identifier}
                onChange={(e) => {
                  setIdentifier(e.target.value);
                  if (errorMessage) setErrorMessage('');
                }}
                placeholder="Enter email or username"
                style={{
                  width: '100%',
                  padding: '0.7rem 0.85rem 0.7rem 2.4rem',
                  backgroundColor: 'var(--bg-subtle)',
                  border: '1px solid var(--border-medium)',
                  borderRadius: 'var(--radius-md)',
                  color: 'var(--text-main)',
                  fontSize: '0.9rem',
                  fontFamily: 'var(--font-sans)',
                  outline: 'none',
                  transition: 'border-color 0.2s ease'
                }}
                onFocus={(e) => e.target.style.borderColor = 'var(--primary-light)'}
                onBlur={(e) => e.target.style.borderColor = 'var(--border-medium)'}
                required
                autoComplete="username"
              />
            </div>
          </div>

          {/* Password Field */}
          <div style={{ marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
              <label style={{
                fontSize: '0.82rem',
                fontWeight: 600,
                color: 'var(--text-secondary)'
              }}>
                Password
              </label>
              <button
                type="button"
                onClick={goToForgotPassword}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--primary-light)',
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                  padding: 0,
                  fontWeight: 600
                }}
              >
                Forgot Password?
              </button>
            </div>
            <div style={{ position: 'relative' }}>
              <Lock size={17} color="var(--text-muted)" style={{
                position: 'absolute',
                left: '12px',
                top: '50%',
                transform: 'translateY(-50%)'
              }} />
              <input
                type="password"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (errorMessage) setErrorMessage('');
                }}
                placeholder="••••••••••••"
                style={{
                  width: '100%',
                  padding: '0.7rem 0.85rem 0.7rem 2.4rem',
                  backgroundColor: 'var(--bg-subtle)',
                  border: '1px solid var(--border-medium)',
                  borderRadius: 'var(--radius-md)',
                  color: 'var(--text-main)',
                  fontSize: '0.9rem',
                  fontFamily: 'var(--font-sans)',
                  outline: 'none',
                  transition: 'border-color 0.2s ease'
                }}
                onFocus={(e) => e.target.style.borderColor = 'var(--primary-light)'}
                onBlur={(e) => e.target.style.borderColor = 'var(--border-medium)'}
                required
                autoComplete="current-password"
              />
            </div>
          </div>

          {/* Sign In Button */}
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
                <span>Signing in...</span>
              </>
            ) : (
              <>
                <span>Sign In</span>
                <ArrowRight size={18} />
              </>
            )}
          </button>
        </form>

        {/* Footer: Sign Up */}
        <div style={{
          marginTop: '1.75rem',
          paddingTop: '1.25rem',
          borderTop: '1px solid var(--border-subtle)',
          textAlign: 'center',
          fontSize: '0.88rem',
          color: 'var(--text-secondary)'
        }}>
          <span>Don't have an account? </span>
          <button
            type="button"
            onClick={goToSignUp}
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
            Sign Up
          </button>
        </div>
      </div>
    </div>
  );
}
