import { useEffect, useState } from "react";
import Header from "../components/Header";
import ProductGrid from "../components/ProductGrid";
import { searchProducts } from "../services/api";

export default function SearchPage({ user, searchQuery, token, onLogout, onRequestLogin, onBackToHome }) {
  const [products, setProducts] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState("");
  const [inputQuery, setInputQuery] = useState(searchQuery);

  useEffect(() => {
    if (searchQuery) {
      performSearch(searchQuery);
    }
  }, [searchQuery]);

  const performSearch = async (q) => {
    setIsSearching(true);
    setSearchError("");
    try {
      const data = await searchProducts(q, token);
      const mapped = (data.results || []).map((item) => ({
        id: item.id,
        title: item.name,
        author: item.author,
        price: `৳${item.price}`,
        image: item.image_url || "/src/assets/books/atomic-habits.jpg",
      }));
      setProducts(mapped);
      if (mapped.length === 0) setSearchError("No products found for this search.");
    } catch (err) {
      if (err.status === 401) onLogout();
      setSearchError(err.message);
    } finally {
      setIsSearching(false);
    }
  };

  const handleNewSearch = (e) => {
    e.preventDefault();
    const q = inputQuery.trim();
    if (!q) return;
    performSearch(q);
  };

  return (
    <div>
      <Header
        user={user}
        searchQuery={inputQuery}
        setSearchQuery={setInputQuery}
        onSearch={handleNewSearch}
        isSearching={isSearching}
        onLogout={onLogout}
        onRequestLogin={onRequestLogin}
        onGoHome={onBackToHome}
      />

      <main className="home-page">
        <section className="hero-banner">
          <div>
            <h2>Search Results</h2>
            <p>Showing results for "{searchQuery}"</p>
            <button className="link-btn" onClick={onBackToHome}>Back to Home</button>
          </div>
        </section>

        <ProductGrid products={products} sectionTitle={`Search Results for "${searchQuery}"`} searchError={searchError} />
      </main>
    </div>
  );
}