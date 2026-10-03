import { useEffect, useState } from 'react';
import { fetchItems, recommendOutfits } from './api/client';
import { ClothingDetailsModal } from './components/ClothingDetailsModal';
import { Dashboard } from './components/Dashboard';
import { UploadClothingModal } from './components/UploadClothingModal';
import { useWardrobe } from './hooks/useWardrobe';
import type { AIRecommendation, ClothingItem } from './types';
import { AuthProvider } from './auth/AuthContext';
import { useAuth } from './auth/useAuth';
import { LandingPage, LoginPage, RegisterPage } from './auth/PublicPages';
import './App.css';

const occasionOptions = ['Everyday', 'Work', 'Office', 'University', 'Formal event', 'Party', 'Date', 'Wedding', 'Travel', 'Workout'];
const styleOptions = ['Minimal', 'Casual', 'Smart casual', 'Formal', 'Streetwear', 'Elegant', 'Vintage', 'Sporty', 'Bohemian'];

function RecommendationImages({ recommendation }: { recommendation: AIRecommendation }) {
  const [compositionFailed, setCompositionFailed] = useState(false);
  if (recommendation.composition_url && !compositionFailed) {
    return (
      <img
        src={recommendation.composition_url}
        alt={`${recommendation.title} outfit composition`}
        className="ai-composition-image"
        onError={() => setCompositionFailed(true)}
      />
    );
  }
  return (
    <div className="ai-card-images">
      {recommendation.items.map((item) => (
        <img key={item.id} src={item.secure_url} alt={item.name} />
      ))}
    </div>
  );
}

function WardrobeDashboard() {
  const { user, logout } = useAuth();
  const wardrobe = useWardrobe();
  const [uploadOpen, setUploadOpen] = useState(false);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [aiMessage, setAiMessage] = useState<string | null>('Ready to style your wardrobe.');
  const [aiError, setAiError] = useState<string | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiRecommendations, setAiRecommendations] = useState<AIRecommendation[]>([]);
  const [aiRequest, setAiRequest] = useState({
    occasion: 'Work',
    preferred_style: 'Smart casual',
    preferred_colours: '',
    avoid_colours: '',
    season: '',
  });

  useEffect(() => {
    if (!notice) return;
    const timer = window.setTimeout(() => setNotice(null), 4200);
    return () => window.clearTimeout(timer);
  }, [notice]);

  function handleCreated(item: ClothingItem) {
    setUploadOpen(false);
    setNotice(`${item.name} is in your wardrobe.`);
    wardrobe.showNewest(item.id);
  }

  function handleUpdated(item: ClothingItem) {
    setNotice(`${item.name} was updated.`);
    wardrobe.refresh();
  }

  function handleDeleted() {
    setSelectedId(null);
    setNotice('Piece removed from your wardrobe.');
    const currentPage = wardrobe.pageData;
    if (currentPage && currentPage.items.length === 1 && wardrobe.query.page > 1) {
      wardrobe.updateQuery({ page: wardrobe.query.page - 1 });
      return;
    }
    wardrobe.refresh();
  }

  async function handleGenerateOutfits() {
    setAiLoading(true);
    setAiError(null);
    setAiMessage('Looking through your wardrobe...');
    try {
      const allItems = await fetchItems({
        q: '',
        category: '',
        colour: '',
        pattern: '',
        style: '',
        occasion: '',
        sort: 'recent',
        page: 1,
        pageSize: 60,
      });
      if (!allItems.items.length) {
        setAiRecommendations([]);
        setAiError('Add more clothing pieces to receive outfit recommendations.');
        return;
      }
      const response = await recommendOutfits({
        occasion: aiRequest.occasion || undefined,
        preferred_style: aiRequest.preferred_style || undefined,
        preferred_colours: aiRequest.preferred_colours.split(',').map((entry) => entry.trim()).filter(Boolean),
        avoid_colours: aiRequest.avoid_colours.split(',').map((entry) => entry.trim()).filter(Boolean),
        season: aiRequest.season || undefined,
      });
      setAiRecommendations(response.recommendations ?? []);
      if (response.warning) {
        setAiError(response.warning);
      } else {
        setAiMessage('Finding colour combinations...');
      }
    } catch (error) {
      setAiRecommendations([]);
      setAiError(error instanceof Error ? error.message : 'AI styling is unavailable right now.');
    } finally {
      setAiLoading(false);
    }
  }

  const cloudinaryReady = wardrobe.health?.cloudinary_configured ?? true;
  const hasWardrobeItems = (wardrobe.stats?.total_items ?? 0) > 0;

  return (
    <div className="app">
      <header className="site-header">
        <div>
          <p className="wordmark">WardrobeAI</p>
          <p className="tagline">Your wardrobe. Your style. One intelligent closet.</p>
        </div>
        <nav className="app-nav" aria-label="Dashboard navigation">
          <a href="#dashboard">Dashboard</a>
          <a href="#wardrobe">My Wardrobe</a>
          <a href="#stylist">AI Stylist</a>
        </nav>
        <div className="account-controls">
          <span>{user?.name}</span>
          <button
            type="button"
            className="button secondary"
            onClick={async () => {
              try {
                await logout();
                window.location.assign('/');
              } catch {
                setNotice('Could not end this session. Please try again.');
              }
            }}
          >
            Log out
          </button>
        </div>
      </header>

      {notice && (
        <div className="notice" role="status">
          {notice}
        </div>
      )}

      {wardrobe.health && !cloudinaryReady && (
        <p className="banner" role="status">
          Cloudinary is not configured. Add your cloud name, API key, and API secret to{' '}
          <code>backend/.env</code> before uploading photographs. Existing wardrobe records still
          load.
        </p>
      )}

      <main id="dashboard" className={hasWardrobeItems ? 'has-wardrobe' : 'empty-wardrobe'}>
        <section className="ai-panel" id="stylist">
          <div className="ai-panel-header">
            <div>
              <p className="eyebrow">AI Stylist</p>
              <h2>Style suggestions for your wardrobe</h2>
            </div>
            <button type="button" className="button secondary" onClick={handleGenerateOutfits} disabled={aiLoading || wardrobe.loading || !hasWardrobeItems}>
              {aiLoading ? 'Styling…' : 'Generate outfits'}
            </button>
          </div>

          <p className="ai-status">{hasWardrobeItems ? 'Rule-based recommendation engine powered by wardrobe data and Cloudinary image intelligence.' : 'Add your first clothing item to unlock personal outfit suggestions.'}</p>

          {hasWardrobeItems && <div className="ai-form-grid">
            <label className="field">
              <span>Occasion</span>
              <select value={aiRequest.occasion} onChange={(event) => setAiRequest((current) => ({ ...current, occasion: event.target.value }))}>
                {occasionOptions.map((option) => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>Style</span>
              <select value={aiRequest.preferred_style} onChange={(event) => setAiRequest((current) => ({ ...current, preferred_style: event.target.value }))}>
                {styleOptions.map((option) => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>Preferred colours</span>
              <input value={aiRequest.preferred_colours} onChange={(event) => setAiRequest((current) => ({ ...current, preferred_colours: event.target.value }))} placeholder="White, Blue" />
            </label>

            <label className="field">
              <span>Avoid colours</span>
              <input value={aiRequest.avoid_colours} onChange={(event) => setAiRequest((current) => ({ ...current, avoid_colours: event.target.value }))} placeholder="Neon" />
            </label>

            <label className="field field-wide">
              <span>Season</span>
              <input value={aiRequest.season} onChange={(event) => setAiRequest((current) => ({ ...current, season: event.target.value }))} placeholder="Summer" />
            </label>
          </div>}

          {aiLoading && <p className="ai-status">Looking through your wardrobe…</p>}
          {aiMessage && !aiLoading && <p className="ai-status">{aiMessage}</p>}
          {aiError && <p className="form-error" role="alert">{aiError}</p>}

          {aiRecommendations.length > 0 && (
            <div className="ai-results">
              {aiRecommendations.map((recommendation) => (
                <article
                  key={`${recommendation.title}-${recommendation.occasion}-${recommendation.items.map((item) => item.id).join('-')}`}
                  className="ai-card"
                >
                  <div className="ai-card-header">
                    <div>
                      <h3>{recommendation.title}</h3>
                      <span>{recommendation.occasion} • {recommendation.style}</span>
                    </div>
                    <strong>{Math.round(recommendation.compatibility_score)}%</strong>
                  </div>
                  <RecommendationImages recommendation={recommendation} />
                  <p>{recommendation.description}</p>
                  <div className="ai-card-meta">
                    <p><strong>Why it works:</strong> {recommendation.reasoning}</p>
                    <ul>
                      {recommendation.styling_tips.map((tip) => <li key={tip}>{tip}</li>)}
                    </ul>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>

        <Dashboard
          id="wardrobe"
          userName={user?.name}
          cld={wardrobe.cld}
          loading={wardrobe.loading}
          error={wardrobe.error}
          stats={wardrobe.stats}
          pageData={wardrobe.pageData}
          query={wardrobe.query}
          search={wardrobe.search}
          highlightId={wardrobe.highlightId}
          onRetry={wardrobe.refresh}
          onSearch={wardrobe.updateSearch}
          onQueryChange={wardrobe.updateQuery}
          onClearFilters={wardrobe.clearFilters}
          onSelect={setSelectedId}
          onUpload={() => setUploadOpen(true)}
        />
      </main>

      {uploadOpen && (
        <UploadClothingModal onClose={() => setUploadOpen(false)} onCreated={handleCreated} />
      )}
      {selectedId !== null && (
        <ClothingDetailsModal
          key={selectedId}
          itemId={selectedId}
          cld={wardrobe.cld}
          onClose={() => setSelectedId(null)}
          onUpdated={handleUpdated}
          onDeleted={handleDeleted}
        />
      )}
    </div>
  );
}

function AppContent() {
  const { user, loading } = useAuth();
  const path = window.location.pathname;

  useEffect(() => {
    if (!loading && path === '/app' && !user) window.location.replace('/login');
    if (!loading && user && (path === '/login' || path === '/register')) window.location.replace('/app');
  }, [loading, path, user]);

  if (loading) return <div className="app-loading" role="status">Opening your wardrobe…</div>;
  if (path === '/login') return user ? null : <LoginPage />;
  if (path === '/register') return user ? null : <RegisterPage />;
  if (path === '/app') return user ? <WardrobeDashboard /> : null;
  return <LandingPage />;
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
