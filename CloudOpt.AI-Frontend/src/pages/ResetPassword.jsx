import React, { useState } from 'react';
import { useNavigate, useParams, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  Cloud, 
  Lock, 
  AlertCircle, 
  CheckCircle2, 
  ArrowRight, 
  RefreshCw,
  KeyRound
} from 'lucide-react';

export default function ResetPassword({ uid: propUid, token: propToken, onSwitchToLogin }) {
  const navigate = useNavigate();
  const routeParams = useParams();
  const location = useLocation();
  const searchParams = new URLSearchParams(location.search);

  const effectiveUid = propUid || routeParams.uid || searchParams.get('uid') || '';
  const effectiveToken = propToken || routeParams.token || searchParams.get('token') || '';

  const { resetPassword } = useAuth();
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const goToLogin = (msg = '') => {
    const finalMsg = msg || 'Password reset successfully. Please sign in.';
    if (onSwitchToLogin) onSwitchToLogin(finalMsg);
    navigate('/login', { state: { message: finalMsg } });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!newPassword) {
      setErrorMessage('Please enter your new password.');
      return;
    }

    if (newPassword.length < 8) {
      setErrorMessage('Password must be at least 8 characters long.');
      return;
    }

    if (newPassword !== confirmPassword) {
      setErrorMessage('Passwords do not match.');
      return;
    }

    if (!effectiveUid || !effectiveToken) {
      setErrorMessage('Missing or invalid password reset token. Please request a new link.');
      return;
    }

    setErrorMessage('');
    setIsSubmitting(true);

    try {
      const response = await resetPassword(effectiveUid, effectiveToken, newPassword, confirmPassword);
      setSuccessMessage(
        response?.message || 'Password has been reset successfully. Please sign in.'
      );
    } catch (err) {
      setErrorMessage(err.data?.message || err.message || 'Failed to reset password. The link may have expired.');
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
          Secure Password Reset
        </p>
      </div>

      {/* Main Card */}
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
        <div style={{ marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.35rem', fontWeight: 700, margin: '0 0 0.35rem 0', color: '#fff' }}>
            Set New Password
          </h2>
          <p style={{ fontSize: '0.86rem', color: 'var(--text-muted)', margin: 0 }}>
            Enter your new password below to update your PostgreSQL credentials.
          </p>
        </div>

        {/* Success Alert */}
        {successMessage ? (
          <div>
            <div style={{
              background: 'var(--success-bg)',
              border: '1px solid var(--success-border)',
              borderRadius: 'var(--radius-md)',
              padding: '1rem',
              color: '#86EFAC',
              fontSize: '0.88rem',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '0.65rem',
              marginBottom: '1.5rem'
            }}>
              <CheckCircle2 size={20} color="var(--success)" style={{ flexShrink: 0, marginTop: '2px' }} />
              <div>
                <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Password Updated</div>
                <div style={{ fontSize: '0.84rem', color: '#D1FAE5' }}>{successMessage}</div>
              </div>
            </div>

            <button
              type="button"
              className="btn btn-primary"
              onClick={() => goToLogin(successMessage)}
              style={{
                width: '100%',
                padding: '0.8rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.5rem',
                fontWeight: 700
              }}
            >
              <span>Sign In with New Password</span>
              <ArrowRight size={17} />
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
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

            {/* New Password */}
            <div style={{ marginBottom: '1.25rem' }}>
              <label style={{
                display: 'block',
                fontSize: '0.82rem',
                fontWeight: 600,
                color: 'var(--text-secondary)',
                marginBottom: '0.5rem'
              }}>
                New Password
              </label>
              <div style={{ position: 'relative' }}>
                <Lock size={17} color="var(--text-muted)" style={{
                  position: 'absolute',
                  left: '12px',
                  top: '50%',
                  transform: 'translateY(-50%)'
                }} />
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => {
                    setNewPassword(e.target.value);
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
                    outline: 'none',
                    transition: 'border-color 0.2s ease'
                  }}
                  onFocus={(e) => e.target.style.borderColor = 'var(--primary-light)'}
                  onBlur={(e) => e.target.style.borderColor = 'var(--border-medium)'}
                  required
                  autoComplete="new-password"
                />
              </div>
            </div>

            {/* Confirm Password */}
            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{
                display: 'block',
                fontSize: '0.82rem',
                fontWeight: 600,
                color: 'var(--text-secondary)',
                marginBottom: '0.5rem'
              }}>
                Confirm New Password
              </label>
              <div style={{ position: 'relative' }}>
                <Lock size={17} color="var(--text-muted)" style={{
                  position: 'absolute',
                  left: '12px',
                  top: '50%',
                  transform: 'translateY(-50%)'
                }} />
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => {
                    setConfirmPassword(e.target.value);
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
                    outline: 'none',
                    transition: 'border-color 0.2s ease'
                  }}
                  onFocus={(e) => e.target.style.borderColor = 'var(--primary-light)'}
                  onBlur={(e) => e.target.style.borderColor = 'var(--border-medium)'}
                  required
                  autoComplete="new-password"
                />
              </div>
            </div>

            {/* Reset Password Button */}
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
                  <span>Updating Password...</span>
                </>
              ) : (
                <>
                  <KeyRound size={17} />
                  <span>Update Password</span>
                </>
              )}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
