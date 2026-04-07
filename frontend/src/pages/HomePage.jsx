import { useEffect, useState } from "react";
import Header from "../components/Header";
import ProductGrid from "../components/ProductGrid";
import PopularSection from "../components/PopularSection";
import TrendingSection from "../components/TrendingSection";
import HistorySection from "../components/HistorySection";
import {
  fetchPopularRecommendations,
  fetchPersonalizedRecommendations,

  fetchTrendingSearches,
  fetchSearchHistory,
} from "../services/api";

export default function HomePage({ user, token, onLogout, onRequestLogin, onSearch, onBookClick }) {
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState("");

  const [genericProducts, setGenericProducts] = useState([]);
  const [genericError, setGenericError] = useState("");
  const [isLoadingGeneric, setIsLoadingGeneric] = useState(false);

  const [personalizedProducts, setPersonalizedProducts] = useState([]);
  const [personalizedError, setPersonalizedError] = useState("");
  const [isLoadingPersonalized, setIsLoadingPersonalized] = useState(false);
  const [preferredTypes, setPreferredTypes] = useState([]);

  const [recommendedProducts, setRecommendedProducts] = useState([]);
  const [recommendedError, setRecommendedError] = useState("");
  const [isLoadingRecommended, setIsLoadingRecommended] = useState(false);

  const [trendingSearches, setTrendingSearches] = useState([]);
  const [trendingError, setTrendingError] = useState("");
  const [isLoadingTrending, setIsLoadingTrending] = useState(false);

  const [searchHistory, setSearchHistory] = useState([]);
  const [historyError, setHistoryError] = useState("");
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  const [currentBanner, setCurrentBanner] = useState(0);

  const banners = [
    "https://rokbucket.rokomari.io/banner/DESKTOPe463d458-4443-485e-b9de-384ecb8d0ce2.webp",
    "https://rokbucket.rokomari.io/banner/DESKTOP56335902-dbf4-48f6-b80e-84acd1b67d4f.webp"
  ];

  


  const mapRecommendationProducts = (items) =>
    (items || []).map((item) => ({
      id: item.id,
      title: item.name || "Unnamed Product",
      author: item.author || "Unknown Author",
      category: item.category || item.product_type || "Unknown Category",
      price: item.price != null ? `৳${item.price}` : "N/A",
      image: item.image_url || "/src/assets/books/atomic-habits.jpg",
      visitCount: item.visit_count ?? 0,
      searchCount: item.search_count ?? 0,
      popularityScore: item.popularity_score ?? null,
    }));

  const loadGenericRecommendations = async () => {
    setIsLoadingGeneric(true);
    setGenericError("");
    try {
      const data = await fetchPopularRecommendations();
      setGenericProducts(mapRecommendationProducts(data.results));
    } catch (err) {
      setGenericError(err.message);
    } finally {
      setIsLoadingGeneric(false);
    }
  };

  const loadPersonalizedRecommendations = async () => {
    if (!token) {
      setPersonalizedProducts([]);
      setPreferredTypes([]);
      setPersonalizedError("");
      return;
    }

    setIsLoadingPersonalized(true);
    setPersonalizedError("");
    try {
      const data = await fetchPersonalizedRecommendations(token);
      setPreferredTypes(data.preferred_types || []);
      setPersonalizedProducts(mapRecommendationProducts(data.results));
    } catch (err) {
      if (err.status === 401) {
        onLogout();
        return;
      }
      setPersonalizedError(err.message);
    } finally {
      setIsLoadingPersonalized(false);
    }
  };

  const loadRecommended = async () => {
    setIsLoadingRecommended(true);
    setRecommendedError("");
    try {
      const data = user && token
        ? await fetchPersonalizedRecommendations(token, 6)
        : await fetchPopularRecommendations();
      setRecommendedProducts(
        (data.results || []).map((item) => ({
          id: item.id,
          title: item.name || "Unnamed Product",
          author: item.author || "Unknown Author",
          category: item.category || "Unknown Category",
          price: item.price != null ? `৳${item.price}` : "N/A",
          image: item.image_url || "/src/assets/books/atomic-habits.jpg",
          visitCount: item.visit_count ?? 0,
        }))
      );
    } catch (err) {
      if (err.status === 401) {
        onLogout();
        return;
      }
      setPersonalizedError(err.message);
    } finally {
      setIsLoadingPersonalized(false);
    }
  };

  const loadTrending = async () => {
    setIsLoadingTrending(true);
    setTrendingError("");
    try {
      const data = await fetchTrendingSearches();
      setTrendingSearches(data.trending_searches || []);
    } catch (err) {
      setTrendingError(err.message);
    } finally {
      setIsLoadingTrending(false);
    }
  };

  const loadHistory = async () => {
    if (!token) return;
    setIsLoadingHistory(true);
    setHistoryError("");
    try {
      const data = await fetchSearchHistory(token);
      setSearchHistory(data.searches || []);
    } catch (err) {
      setHistoryError(err.message);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    const q = searchQuery.trim();
    if (!q) return;

    onSearch(q); // Navigate to search page
  };

  useEffect(() => {
    loadGenericRecommendations();
    loadTrending();
  }, []);

  useEffect(() => {
    if (!token) {
      setSearchHistory([]);
      setPersonalizedProducts([]);
      setPreferredTypes([]);
      return;
    }

    loadHistory();
    loadPersonalizedRecommendations();
  }, [token]);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentBanner((prev) => (prev + 1) % banners.length);
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const heroTitle = user ? `Welcome back, ${user.full_name || "Reader"}` : "Welcome to Rokomari";
  const heroSubtext = user
    ? "Browse books, search products, and enjoy your personalized homepage."
    : "Browse popular books, trending searches, and login to personalize your recommendations.";

  return (
    <div>
      <Header
        user={user}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        onSearch={handleSearch}
        isSearching={isSearching}
        onLogout={onLogout}
        onRequestLogin={onRequestLogin}
        onGoHome={() => {}} // No-op on home page
      />

      {/* Banner Section */}
      <section className="banner-section">
        <div className="banner-container">
          <img
            src={banners[currentBanner]}
            alt={`Rokomari Banner ${currentBanner + 1}`}
            className="banner-image"
          />
        </div>
      </section>

      <main className="home-page">
        <section className="hero-banner">
          <div>
            <h2>{heroTitle}</h2>
            <p>{heroSubtext}</p>
            {!user && (
              <button className="primary-btn" type="button" onClick={onRequestLogin}>
                Login to personalize
              </button>
            )}
          </div>
        </section>

        <ProductGrid
            products={recommendedProducts}
            sectionTitle={user ? "Recommended for You" : "Popular Books"}
            searchError={recommendedError}
            onBookClick={onBookClick}
        />

        {/* 🔥 ONLY show these when NOT searching */}
        {!isSearching && (
          <>
            <PopularSection
              title="Generic Recommendations"
              subtitle="Popular across all users based on both visits and searches."
              products={genericProducts}
              isLoading={isLoadingGeneric}
              error={genericError}
              emptyMessage="No global recommendation data yet."
              onBookClick={onBookClick}
            />

            <PopularSection
              title="Personalized Recommendations"
              subtitle={
                user
                  ? (
                      preferredTypes.length > 0
                        ? `Based on your top interaction types: ${preferredTypes.join(", ")}`
                        : "Based on your search and visit behavior."
                    )
                  : "Login to get recommendations tailored to your activity."
              }
              products={personalizedProducts}
              isLoading={isLoadingPersonalized}
              error={personalizedError}
              emptyMessage={
                user
                  ? "No personalized signals yet. Browse and search a bit to personalize this section."
                  : "Login to see personalized recommendations."
              }
              onBookClick={onBookClick}
            />
            <TrendingSection
              searches={trendingSearches}
              isLoading={isLoadingTrending}
              error={trendingError}
            />
            <HistorySection
              searches={searchHistory}
              isLoading={isLoadingHistory}
              error={historyError}
              isLoggedIn={!!user}
            />
          </>
        )}
        </main>
    </div>
  );
}