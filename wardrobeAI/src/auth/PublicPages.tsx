import { useState, type FormEvent, type ReactNode } from 'react';
import { ApiError } from '../api/client';
import { useAuth } from './useAuth';
import './PublicPages.css';

const features = [
  {
    number: '01',
    title: 'Your Digital Wardrobe',
    text: 'Bring your entire wardrobe into one intelligent digital closet. Upload your clothes, organise them, and access everything in one place.',
  },
  {
    number: '02',
    title: 'AI Clothing Recognition',
    text: 'Upload a clothing photograph and let WardrobeAI identify visual attributes such as category, colour, and pattern.',
  },
  {
    number: '03',
    title: 'Your Personal AI Stylist',
    text: 'Discover outfit combinations using the clothes you already own.',
  },
  {
    number: '04',
    title: 'Smart Outfit Recommendations',
    text: 'Get outfit suggestions based on occasion, style preferences, colours, and your existing wardrobe.',
  },
  {
    number: '05',
    title: 'Visual Outfit Composition',
    text: 'See your selected clothing pieces together through visually organised outfit compositions.',
  },
  {
    number: '06',
    title: 'Make More of Your Wardrobe',
    text: 'Rediscover what you own, explore new combinations, and reduce the need to buy unnecessary clothing.',
  },
];

export function LandingPage() {
  const { user } = useAuth();
  const startHref = user ? '/app' : '/register';
  return (
    <div className="public-site">
      <header className="public-nav">
        <a className="public-brand" href="/" aria-label="WardrobeAI home">Wardrobe<span>AI</span></a>
        <nav className="public-links" aria-label="Main navigation">
          <a href="/">Home</a>
          <a href="#features">Features</a>
          <a href="#how-it-works">How it works</a>
        </nav>
        <div className="public-actions">
          {user ? <a className="nav-signin" href="/app">My wardrobe</a> : <a className="nav-signin" href="/login">Sign in</a>}
          <a className="nav-register" href={startHref}>{user ? 'Open wardrobe' : 'Register'}</a>
        </div>
      </header>

      <main>
        <section className="landing-hero">
          <img
            className="hero-photo"
            src="https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=2200&q=85"
            alt="Friends exploring a clothing collection"
          />
          <div className="hero-copy">
            <p className="hero-eyebrow">A considered way to get dressed</p>
            <h1>Your wardrobe,<br />reimagined with AI.</h1>
            <p>Meet your personal AI stylist. Digitise your wardrobe, discover new outfit combinations, and make the most of the clothes you already own.</p>
            <div className="hero-actions">
              <a className="button button-light" href={startHref}>Start Creating Outfits <span aria-hidden="true">↗</span></a>
              {!user && <a className="hero-signin" href="/login">Sign in</a>}
            </div>
          </div>
          <p className="hero-caption">Less guesswork. More you.</p>
        </section>

        <section className="feature-section" id="features">
          <div className="section-intro">
            <p className="section-kicker">The wardrobe, made intelligent</p>
            <h2>Everything you own.<br /><em>More ways to wear it.</em></h2>
          </div>
          <div className="feature-list">
            {features.map((feature) => (
              <article className="feature-row" key={feature.number}>
                <span className="feature-number">{feature.number}</span>
                <h3>{feature.title}</h3>
                <p>{feature.text}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="how-section" id="how-it-works">
          <div className="how-heading">
            <p className="section-kicker">A simpler morning starts here</p>
            <h2>Three steps to a wardrobe<br /><em>that works harder.</em></h2>
          </div>
          <ol className="steps-list">
            <li><span>01</span><strong>Upload your wardrobe</strong><p>Add the clothes you reach for, one photograph at a time.</p></li>
            <li><span>02</span><strong>Let WardrobeAI organise</strong><p>Keep your pieces searchable by what they are and how you wear them.</p></li>
            <li><span>03</span><strong>Discover new combinations</strong><p>Find personal outfit ideas from the pieces already in your closet.</p></li>
          </ol>
        </section>

        <section className="final-cta">
          <p className="section-kicker">Your next look is closer than you think</p>
          <h2>Your next favourite outfit is<br />already in your wardrobe.</h2>
          <p>Create your digital closet and let WardrobeAI help you discover new possibilities.</p>
          <a className="button button-dark" href={startHref}>Get Started <span aria-hidden="true">↗</span></a>
        </section>
      </main>

      <footer className="public-footer">
        <div className="footer-brand"><a className="public-brand" href="/">Wardrobe<span>AI</span></a><p>Your wardrobe. Your style. One intelligent closet.</p></div>
        <nav aria-label="Footer navigation"><a href="/">Home</a><a href="#features">Features</a><a href="/login">Sign in</a><a href="/register">Register</a></nav>
        <small>© {new Date().getFullYear()} WardrobeAI</small>
      </footer>
    </div>
  );
}

function AuthFrame({ children, mode }: { children: ReactNode; mode: 'login' | 'register' }) {
  return (
    <main className="auth-page">
      <a className="public-brand auth-brand" href="/">Wardrobe<span>AI</span></a>
      <div className="auth-layout">
        <div className="auth-photo" role="img" aria-label="A thoughtfully arranged clothing wardrobe">
          <div><p className="section-kicker">A more personal way to get dressed</p><h1>Your closet,<br /><em>with a point of view.</em></h1></div>
        </div>
        <section className="auth-form-wrap">{children}</section>
      </div>
      <a className="auth-back" href="/">← Back to home</a>
      <span className="auth-mode" aria-hidden="true">{mode === 'login' ? 'WELCOME BACK' : 'YOUR WARDROBE, REIMAGINED'}</span>
    </main>
  );
}

function readableAuthError(error: unknown) {
  if (error instanceof ApiError) {
    if (error.status === 409) return 'An account with this email already exists. Sign in or use another email.';
    if (error.status === 401) return 'Invalid email or password.';
    if (error.status === 429) return 'Too many attempts. Please wait a moment and try again.';
    if (error.fields && Object.keys(error.fields).length) return Object.values(error.fields).join(' ');
    return error.message;
  }
  return error instanceof Error ? error.message : 'Something went wrong. Please try again.';
}

export function LoginPage() {
  const { login, loading, csrfReady } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError('');
    if (!email.trim() || !/^\S+@\S+\.\S+$/.test(email.trim())) { setError('Enter a valid email address.'); return; }
    if (!password) { setError('Enter your password.'); return; }
    setSubmitting(true);
    try { await login(email.trim(), password); window.location.assign('/app'); }
    catch (reason) { setError(readableAuthError(reason)); setSubmitting(false); }
  }

  if (loading) return <AuthFrame mode="login"><p className="auth-loading">Preparing your sign in…</p></AuthFrame>;
  return (
    <AuthFrame mode="login">
      <p className="section-kicker">Welcome back</p>
      <h2>Sign in to your wardrobe.</h2>
      <p className="auth-subtitle">Your pieces and personal outfit ideas are waiting.</p>
      <form className="auth-form" onSubmit={submit} noValidate>
        <label><span>Email address</span><input type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} /></label>
        <label><span>Password</span><span className="password-control"><input type={showPassword ? 'text' : 'password'} autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)} /><button type="button" onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? 'Hide password' : 'Show password'}>{showPassword ? 'Hide' : 'Show'}</button></span></label>
        {error && <p className="auth-error" role="alert">{error}</p>}
        <button className="button button-dark auth-submit" type="submit" disabled={submitting || !csrfReady}>{submitting ? 'Signing in…' : 'Sign In'}</button>
      </form>
      <p className="auth-switch">New to WardrobeAI? <a href="/register">Create an account</a></p>
    </AuthFrame>
  );
}

export function RegisterPage() {
  const { register, loading, csrfReady } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError('');
    if (!name.trim()) { setError('Enter your full name.'); return; }
    if (!/^\S+@\S+\.\S+$/.test(email.trim())) { setError('Enter a valid email address.'); return; }
    if (password.length < 12) { setError('Use a password with at least 12 characters.'); return; }
    const strength = [/[a-z]/.test(password), /[A-Z]/.test(password), /\d/.test(password), /[^A-Za-z0-9]/.test(password)].filter(Boolean).length;
    if (strength < 3) { setError('Use at least three of lowercase, uppercase, number, and symbol.'); return; }
    if (password !== confirmPassword) { setError('Passwords do not match.'); return; }
    setSubmitting(true);
    try { await register(name.trim(), email.trim(), password, confirmPassword); window.location.assign('/app'); }
    catch (reason) { setError(readableAuthError(reason)); setSubmitting(false); }
  }

  if (loading) return <AuthFrame mode="register"><p className="auth-loading">Preparing your account…</p></AuthFrame>;
  return (
    <AuthFrame mode="register">
      <p className="section-kicker">Make room for more possibilities</p>
      <h2>Create your account.</h2>
      <p className="auth-subtitle">Start with a wardrobe that's yours alone.</p>
      <form className="auth-form" onSubmit={submit} noValidate>
        <label><span>Full name</span><input type="text" autoComplete="name" maxLength={120} required value={name} onChange={(event) => setName(event.target.value)} /></label>
        <label><span>Email address</span><input type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} /></label>
        <label><span>Password <small>12+ characters</small></span><span className="password-control"><input type={showPassword ? 'text' : 'password'} autoComplete="new-password" minLength={12} required value={password} onChange={(event) => setPassword(event.target.value)} /><button type="button" onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? 'Hide password' : 'Show password'}>{showPassword ? 'Hide' : 'Show'}</button></span></label>
        <label><span>Confirm password</span><input type={showPassword ? 'text' : 'password'} autoComplete="new-password" required value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} /></label>
        {error && <p className="auth-error" role="alert">{error}</p>}
        <button className="button button-dark auth-submit" type="submit" disabled={submitting || !csrfReady}>{submitting ? 'Creating account…' : 'Create Account'}</button>
      </form>
      <p className="auth-switch">Already have an account? <a href="/login">Sign in</a></p>
    </AuthFrame>
  );
}
