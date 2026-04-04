import { useState, useEffect, useRef } from 'react';
import { Link, NavLink } from 'react-router-dom';
import { useAuthStore } from '../../stores/auth';
import { track } from '../../analytics';
import * as api from '../../api/client';
import { staticUrl } from '../../config';

const RESEND_COOLDOWN_MS = 60 * 60 * 1000; // 1 hour
const STORAGE_KEY = 'lastVerificationEmailSent';

function Header() {
  const { user, isAuthenticated, isLoading, logout } = useAuthStore();
  const [verificationSent, setVerificationSent] = useState(false);
  const [sendingVerification, setSendingVerification] = useState(false);
  const [cooldownRemaining, setCooldownRemaining] = useState(0);
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Check for existing cooldown on mount and when user changes
  useEffect(() => {
    const checkCooldown = () => {
      const lastSent = localStorage.getItem(STORAGE_KEY);
      if (lastSent) {
        const elapsed = Date.now() - parseInt(lastSent, 10);
        if (elapsed < RESEND_COOLDOWN_MS) {
          setCooldownRemaining(Math.ceil((RESEND_COOLDOWN_MS - elapsed) / 60000));
          setVerificationSent(true);
        } else {
          localStorage.removeItem(STORAGE_KEY);
          setCooldownRemaining(0);
          setVerificationSent(false);
        }
      }
    };

    checkCooldown();
    const interval = setInterval(checkCooldown, 60000); // Update every minute
    return () => clearInterval(interval);
  }, [user?.email]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };

    if (showDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [showDropdown]);

  const handle退出登录 = async () => {
    track('退出登录');
    setShowDropdown(false);
    await logout();
  };

  const handleResendVerification = async () => {
    if (!user?.email || sendingVerification || verificationSent) return;

    track('Resend Verification Email');
    setSendingVerification(true);
    try {
      await api.requestVerificationEmail(user.email);
      localStorage.setItem(STORAGE_KEY, Date.now().toString());
      setVerificationSent(true);
      setCooldownRemaining(60);
    } finally {
      setSendingVerification(false);
    }
  };

  const showVerificationBanner = isAuthenticated && user && !user.isVerified && user.email;

  const getButtonText = () => {
    if (sendingVerification) return '发送中...';
    if (verificationSent) {
      return cooldownRemaining > 0
        ? `剩余 ${cooldownRemaining}m`
        : '已发送';
    }
    return '重新发送验证邮件';
  };

  return (
    <>
      {showVerificationBanner && (
        <div className="verification-banner" role="alert">
          <span>请先验证你的邮箱地址。</span>
          <button
            className="btn-link"
            onClick={handleResendVerification}
            disabled={sendingVerification || verificationSent}
          >
            {getButtonText()}
          </button>
        </div>
      )}
      <header className="header">
        <div className="header-content">
          <div className="logo-group">
            <Link to="/" className="logo">
              <span className="logo-img"><img src={staticUrl('logo.png')} alt="" /></span>
              <span className="logo-text">Real-time-chess-battle</span>
            </Link>
            <a href="https://amplitude.com" target="_blank" rel="noopener noreferrer" className="header-amp" onClick={() => track('Click Amplitude Link')}>
              <span className="header-amp-text">Powered by</span>
              <span className="header-amp-img"><img src={staticUrl('amplitude.png')} alt="Amplitude" /></span>
            </a>
          </div>
          <div className="header-right">
            <nav className="nav">
              <NavLink to="/" end className={({ isActive }) => isActive ? 'nav-link-active' : ''}>Home</NavLink>
              <NavLink to="/lobbies" className={({ isActive }) => isActive ? 'nav-link-active' : ''}>Lobbies</NavLink>
              <NavLink to="/campaign" className={({ isActive }) => isActive ? 'nav-link-active' : ''}>战役</NavLink>
              <NavLink to="/watch" className={({ isActive }) => isActive ? 'nav-link-active' : ''}>观战</NavLink>
              <a href="https://www.reddit.com/r/xiangqi/" target="_blank" rel="noopener noreferrer" className="nav-secondary" onClick={() => track('Click Reddit Link')}>Reddit</a>
              <NavLink to="/about" className={({ isActive }) => `nav-secondary ${isActive ? 'nav-link-active' : ''}`}>关于</NavLink>
              <NavLink to="/privacy" className={({ isActive }) => `nav-secondary ${isActive ? 'nav-link-active' : ''}`}>隐私</NavLink>
              {!isLoading && !isAuthenticated && (
                <NavLink to="/login" className={({ isActive }) => `nav-secondary ${isActive ? 'nav-link-active' : ''}`} onClick={() => track('Click 登录')}>登录</NavLink>
              )}
            </nav>

            {isLoading ? (
              <span className="user-loading">...</span>
            ) : isAuthenticated && user ? (
              /* Authenticated: 个人资料 pic with dropdown containing 个人资料, 退出登录, and secondary links */
              <div className="header-menu-wrapper" ref={dropdownRef}>
                <button
                  className="profile-pic-button"
                  onClick={() => { if (!showDropdown) track('Click 个人资料 Pic'); setShowDropdown(!showDropdown); }}
                  aria-expanded={showDropdown}
                >
                  <div className="profile-pic">
                    <img src={user.pictureUrl || staticUrl('default-profile.jpg')} alt={user.username} />
                  </div>
                </button>
                {showDropdown && (
                  <div className="header-dropdown">
                    <div className="header-dropdown-option">
                      <Link to="/profile" onClick={() => setShowDropdown(false)}>个人资料</Link>
                    </div>
                    <div className="header-dropdown-option">
                      <button onClick={handle退出登录}>退出登录</button>
                    </div>
                    <div className="header-dropdown-secondary">
                      <div className="header-dropdown-divider"></div>
                      <div className="header-dropdown-option">
                        <a href="https://www.reddit.com/r/xiangqi/" target="_blank" rel="noopener noreferrer" onClick={() => { track('Click Reddit Link'); setShowDropdown(false); }}>Reddit</a>
                      </div>
                      <div className="header-dropdown-option">
                        <Link to="/about" onClick={() => setShowDropdown(false)}>关于</Link>
                      </div>
                      <div className="header-dropdown-option">
                        <Link to="/privacy" onClick={() => setShowDropdown(false)}>隐私</Link>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              /* Unauthenticated mobile: hamburger with 登录 + secondary links */
              <div className="header-menu-wrapper mobile-only" ref={dropdownRef}>
                <button
                  className="hamburger-button"
                  onClick={() => setShowDropdown(!showDropdown)}
                  aria-expanded={showDropdown}
                  aria-label="Menu"
                >
                  <span className="hamburger-icon">
                    <span></span>
                    <span></span>
                    <span></span>
                  </span>
                </button>
                {showDropdown && (
                  <div className="header-dropdown">
                    <div className="header-dropdown-option">
                      <Link to="/login" onClick={() => setShowDropdown(false)}>登录</Link>
                    </div>
                    <div className="header-dropdown-divider"></div>
                    <div className="header-dropdown-option">
                      <a href="https://www.reddit.com/r/xiangqi/" target="_blank" rel="noopener noreferrer" onClick={() => { track('Click Reddit Link'); setShowDropdown(false); }}>Reddit</a>
                    </div>
                    <div className="header-dropdown-option">
                      <Link to="/about" onClick={() => setShowDropdown(false)}>关于</Link>
                    </div>
                    <div className="header-dropdown-option">
                      <Link to="/privacy" onClick={() => setShowDropdown(false)}>隐私</Link>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </header>
    </>
  );
}

export default Header;
