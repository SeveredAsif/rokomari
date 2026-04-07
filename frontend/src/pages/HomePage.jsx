import { useEffect, useState } from "react";
import Header from "../components/Header";
import ProductGrid from "../components/ProductGrid";
import PopularSection from "../components/PopularSection";
import TrendingSection from "../components/TrendingSection";
import HistorySection from "../components/HistorySection";
import {
  fetchPopularRecommendations,
  fetchTrendingSearches,
  fetchSearchHistory,
  searchProducts,
} from "../services/api";

const DEFAULT_PRODUCTS = [
  { id: 1, title: "Atomic Habits", author: "James Clear", price: "৳450", image: "/src/assets/books/atomic-habits.jpg" },
  { id: 2, title: "Deep Work", author: "Cal Newport", price: "৳390", image: "/src/assets/books/deep-work.jpg" },
  { id: 3, title: "The Psychology of Money", author: "Morgan Housel", price: "৳520", image: "/src/assets/books/psychology-money.jpg" },
  { id: 4, title: "Clean Code", author: "Robert C. Martin", price: "৳610", image: "/src/assets/books/clean-code.jpg" },
  { id: 5, title: "Steal Like An Artist", author: "Austin Kleon", price: "৳350", image: "/src/assets/books/steal-like-an-artist.jpg" },
  { id: 6, title: "Men are from Mars, Women are from Venus", author: "John Gray", price: "৳480", image: "/src/assets/books/mars-venus.jpg" },
];

export default function HomePage({ user, token, onLogout, onRequestLogin, onSearch, onBookClick }) {
  const [searchQuery, setSearchQuery] = useState("");
  const [products, setProducts] = useState(DEFAULT_PRODUCTS);
  const [sectionTitle, setSectionTitle] = useState("Popular Books");
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState("");

  const [popularProducts, setPopularProducts] = useState([]);
  const [popularError, setPopularError] = useState("");
  const [isLoadingPopular, setIsLoadingPopular] = useState(false);

  const [trendingSearches, setTrendingSearches] = useState([]);
  const [trendingError, setTrendingError] = useState("");
  const [isLoadingTrending, setIsLoadingTrending] = useState(false);

  const [searchHistory, setSearchHistory] = useState([]);
  const [historyError, setHistoryError] = useState("");
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  const loadPopular = async () => {
    setIsLoadingPopular(true);
    setPopularError("");
    try {
      const data = await fetchPopularRecommendations();
      setPopularProducts(
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
      setPopularError(err.message);
    } finally {
      setIsLoadingPopular(false);
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
    loadPopular();
    loadTrending();
    loadHistory();
  }, []);

  useEffect(() => {
    if (!token) {
      setSearchHistory([]);
    }
  }, [token]);

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
            products={products}
            sectionTitle={sectionTitle}
            searchError={searchError}
            onBookClick={onBookClick}
        />

        {/* 🔥 ONLY show these when NOT searching */}
        {sectionTitle === "Popular Books" && (
          <>
            <PopularSection
              products={popularProducts}
              isLoading={isLoadingPopular}
              error={popularError}
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