import { useEffect, useState } from "react";
import Header from "../components/Header";
import ProductGrid from "../components/ProductGrid";
import { fetchSearchFilters, searchProducts } from "../services/api";

const DEFAULT_FILTERS = {
  minPrice: "",
  maxPrice: "",
  productType: "",
  brand: "",
  author: "",
  publisher: "",
  sortBy: "relevance",
  sortOrder: "desc",
};

export default function SearchPage({ user, searchQuery, token, onLogout, onRequestLogin, onBackToHome, onBookClick }) {
  const [products, setProducts] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState("");
  const [inputQuery, setInputQuery] = useState(searchQuery);
  const [activeQuery, setActiveQuery] = useState(searchQuery);
  const [searchMeta, setSearchMeta] = useState(null);
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [filterOptions, setFilterOptions] = useState({
    product_types: [],
    brands: [],
    authors: [],
    publishers: [],
    price_range: { min: null, max: null },
  });

  useEffect(() => {
    setInputQuery(searchQuery);
    setActiveQuery(searchQuery);
  }, [searchQuery]);

  useEffect(() => {
    const loadFilters = async () => {
      try {
        const data = await fetchSearchFilters(token);
        setFilterOptions({
          product_types: data.product_types || [],
          brands: data.brands || [],
          authors: data.authors || [],
          publishers: data.publishers || [],
          price_range: data.price_range || { min: null, max: null },
        });
      } catch (err) {
        if (err.status === 401) {
          onLogout();
          return;
        }
      }
    };

    loadFilters();
  }, [token, onLogout]);

  const buildSearchOptions = (activeFilters) => ({
    limit: 12,
    threshold: 0.1,
    minPrice: activeFilters.minPrice === "" ? undefined : Number(activeFilters.minPrice),
    maxPrice: activeFilters.maxPrice === "" ? undefined : Number(activeFilters.maxPrice),
    productTypes: activeFilters.productType || undefined,
    brand: activeFilters.brand.trim() || undefined,
    author: activeFilters.author.trim() || undefined,
    publisher: activeFilters.publisher.trim() || undefined,
    sortBy: activeFilters.sortBy,
    sortOrder: activeFilters.sortOrder,
  });

  useEffect(() => {
    if (searchQuery) {
      performSearch(searchQuery, filters);
    }
  }, [searchQuery]);

  const performSearch = async (q, activeFilters = filters) => {
    setIsSearching(true);
    setSearchError("");
    try {
      const data = await searchProducts(q, token, buildSearchOptions(activeFilters));
      setActiveQuery(q);
      setSearchMeta({
        source: data.source,
        count: data.count,
        sort: data.sort,
      });

      const mapped = (data.results || []).map((item) => ({
        id: item.id,
        title: item.name,
        author: item.author || item.brand || "Unknown",
        publisher: item.publisher,
        category: item.category || item.product_type,
        productType: item.product_type,
        isbn: item.isbn,
        language: item.language,
        pages: item.pages,
        edition: item.edition,
        price: item.price != null ? `৳${item.price}` : "N/A",
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
    performSearch(q, filters);
  };

  const handleApplyFilters = (e) => {
    e.preventDefault();
    const q = inputQuery.trim() || activeQuery.trim();
    if (!q) return;
    performSearch(q, filters);
  };

  const handleResetFilters = () => {
    setFilters(DEFAULT_FILTERS);
    const q = inputQuery.trim() || activeQuery.trim();
    if (!q) return;
    performSearch(q, DEFAULT_FILTERS);
  };

  const minHint = filterOptions.price_range?.min;
  const maxHint = filterOptions.price_range?.max;

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
            <p>Showing results for "{activeQuery}"</p>
            {searchMeta && (
              <p className="meta-text">
                Source: {searchMeta.source} | Results: {searchMeta.count} | Sort: {searchMeta.sort?.by} ({searchMeta.sort?.order})
              </p>
            )}
            <button className="link-btn" onClick={onBackToHome}>Back to Home</button>
          </div>
        </section>

        <section className="filter-panel">
          <form onSubmit={handleApplyFilters}>
            <div className="filter-grid">
              <label>
                Min Price
                <input
                  type="number"
                  min="0"
                  value={filters.minPrice}
                  onChange={(e) => setFilters((prev) => ({ ...prev, minPrice: e.target.value }))}
                  placeholder={minHint != null ? String(Math.floor(minHint)) : "0"}
                />
              </label>

              <label>
                Max Price
                <input
                  type="number"
                  min="0"
                  value={filters.maxPrice}
                  onChange={(e) => setFilters((prev) => ({ ...prev, maxPrice: e.target.value }))}
                  placeholder={maxHint != null ? String(Math.ceil(maxHint)) : "1000"}
                />
              </label>

              <label>
                Product Type
                <select
                  value={filters.productType}
                  onChange={(e) => setFilters((prev) => ({ ...prev, productType: e.target.value }))}
                >
                  <option value="">All</option>
                  {(filterOptions.product_types || []).map((type) => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
              </label>

              <label>
                Brand
                <input
                  type="text"
                  list="brand-options"
                  value={filters.brand}
                  onChange={(e) => setFilters((prev) => ({ ...prev, brand: e.target.value }))}
                  placeholder="e.g. Brand 2"
                />
              </label>

              <label>
                Author
                <input
                  type="text"
                  list="author-options"
                  value={filters.author}
                  onChange={(e) => setFilters((prev) => ({ ...prev, author: e.target.value }))}
                  placeholder="Filter by author"
                />
              </label>

              <label>
                Publisher
                <input
                  type="text"
                  list="publisher-options"
                  value={filters.publisher}
                  onChange={(e) => setFilters((prev) => ({ ...prev, publisher: e.target.value }))}
                  placeholder="Filter by publisher"
                />
              </label>

              <label>
                Sort By
                <select
                  value={filters.sortBy}
                  onChange={(e) => setFilters((prev) => ({ ...prev, sortBy: e.target.value }))}
                >
                  <option value="relevance">Relevance</option>
                  <option value="price">Price</option>
                  <option value="name">Name</option>
                </select>
              </label>

              <label>
                Sort Order
                <select
                  value={filters.sortOrder}
                  onChange={(e) => setFilters((prev) => ({ ...prev, sortOrder: e.target.value }))}
                >
                  <option value="desc">Descending</option>
                  <option value="asc">Ascending</option>
                </select>
              </label>
            </div>

            <div className="filter-actions">
              <button className="search-btn" type="submit" disabled={isSearching}>
                {isSearching ? "Applying..." : "Apply Filters"}
              </button>
              <button className="link-btn" type="button" onClick={handleResetFilters}>
                Reset Filters
              </button>
            </div>
          </form>

          <datalist id="author-options">
            {(filterOptions.authors || []).map((name) => (
              <option key={name} value={name} />
            ))}
          </datalist>

          <datalist id="publisher-options">
            {(filterOptions.publishers || []).map((name) => (
              <option key={name} value={name} />
            ))}
          </datalist>

          <datalist id="brand-options">
            {(filterOptions.brands || []).map((name) => (
              <option key={name} value={name} />
            ))}
          </datalist>
        </section>

        <ProductGrid products={products} sectionTitle={`Search Results for "${activeQuery}"`} searchError={searchError} onBookClick={onBookClick} />
      </main>
    </div>
  );
}