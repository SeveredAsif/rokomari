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
  discountMin: "",
  discountMax: "",
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
        if (err.status === 401 && token) {
          onLogout();
          return;
        }
        // anonymous users can still search even if filters are unavailable.
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

  useEffect(() => {
    if (!activeQuery?.trim()) return;
    const timeout = setTimeout(() => {
      performSearch(activeQuery, filters);
    }, 250);

    return () => clearTimeout(timeout);
  }, [filters, activeQuery]);

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
        onBookClick={onBookClick} // 🔥 ADD THIS
        enableSuggestions={false}
      />

      <div className="search-page-layout">
        {/* Left Sidebar - Filters */}
        <aside className="filter-sidebar">
          <h3>Search Controls</h3>
          <div className="filter-section">
            <h4>Sort</h4>
            <div className="filter-fields">
              <label>
                Sort By
                <select
                  value={filters.sortBy}
                  onChange={(e) => setFilters((prev) => ({ ...prev, sortBy: e.target.value }))}
                >
                  <option value="relevance">Relevance</option>
                  <option value="best_seller">Best Seller</option>
                  <option value="new_released">New Released</option>
                  <option value="price_low_high">Price - Low to High</option>
                  <option value="price_high_low">Price - High to Low</option>
                  <option value="discount_low_high">Discount - Low to High</option>
                  <option value="discount_high_low">Discount - High to Low</option>
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
          </div>

          <div className="filter-section">
            <h4>Filters</h4>
            <div className="filter-fields">

              <label>
                Price Range: ৳{filters.minPrice || minHint || 0} - ৳{filters.maxPrice || maxHint || 10000}
              </label>
              <div className="range-inputs">
                <input
                  type="range"
                  min={minHint || 0}
                  max={maxHint || 10000}
                  value={filters.minPrice || minHint || 0}
                  onChange={(e) => setFilters((prev) => ({ ...prev, minPrice: e.target.value }))}
                  className="range-slider"
                />
                <input
                  type="range"
                  min={minHint || 0}
                  max={maxHint || 10000}
                  value={filters.maxPrice || maxHint || 10000}
                  onChange={(e) => setFilters((prev) => ({ ...prev, maxPrice: e.target.value }))}
                  className="range-slider"
                />
              </div>

              <label>
                Discount Range: {filters.discountMin || 0}% - {filters.discountMax || 100}%
              </label>
              <div className="range-inputs">
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={filters.discountMin || 0}
                  onChange={(e) => setFilters((prev) => ({ ...prev, discountMin: e.target.value }))}
                  className="range-slider"
                />
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={filters.discountMax || 100}
                  onChange={(e) => setFilters((prev) => ({ ...prev, discountMax: e.target.value }))}
                  className="range-slider"
                />
              </div>

              <fieldset className="filter-checkboxes">
                <legend>Type</legend>
                <input
                  type="text"
                  placeholder="Type product type..."
                  list="type-options"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      const value = e.target.value.trim();
                      if (value && !filters.productType.split(",").includes(value)) {
                        const types = filters.productType.split(",").filter(t => t);
                        setFilters((prev) => ({ ...prev, productType: [...types, value].join(",") }));
                        e.target.value = "";
                      }
                    }
                  }}
                />
                <div className="filter-choice-row">
                  {(filterOptions.product_types || []).slice(0, 8).map((type) => (
                    <button
                      key={type}
                      type="button"
                      className={filters.productType.split(",").includes(type) ? "filter-chip selected" : "filter-chip"}
                      onClick={() => {
                        const types = filters.productType.split(",").filter(t => t);
                        if (types.includes(type)) {
                          setFilters((prev) => ({ ...prev, productType: types.filter(t => t !== type).join(",") }));
                        } else {
                          setFilters((prev) => ({ ...prev, productType: [...types, type].join(",") }));
                        }
                      }}
                    >
                      {type}
                    </button>
                  ))}
                </div>
                <div className="filter-tags">
                  {filters.productType.split(",").filter(t => t).map((type) => (
                    <span key={type} className="filter-tag">
                      {type}
                      <button
                        type="button"
                        onClick={() => {
                          const types = filters.productType.split(",").filter(t => t && t !== type);
                          setFilters((prev) => ({ ...prev, productType: types.join(",") }));
                        }}
                      >
                        ✕
                      </button>
                    </span>
                  ))}
                </div>
              </fieldset>

              <fieldset className="filter-checkboxes">
                <legend>Authors</legend>
                <input
                  type="text"
                  placeholder="Type author name..."
                  list="author-options"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      const value = e.target.value.trim();
                      if (value && !filters.author.split(",").includes(value)) {
                        const authors = filters.author.split(",").filter(a => a);
                        setFilters((prev) => ({ ...prev, author: [...authors, value].join(",") }));
                        e.target.value = "";
                      }
                    }
                  }}
                />
                <div className="filter-choice-row">
                  {(filterOptions.authors || []).slice(0, 8).map((author) => (
                    <button
                      key={author}
                      type="button"
                      className={filters.author.split(",").includes(author) ? "filter-chip selected" : "filter-chip"}
                      onClick={() => {
                        const authors = filters.author.split(",").filter(a => a);
                        if (authors.includes(author)) {
                          setFilters((prev) => ({ ...prev, author: authors.filter(a => a !== author).join(",") }));
                        } else {
                          setFilters((prev) => ({ ...prev, author: [...authors, author].join(",") }));
                        }
                      }}
                    >
                      {author}
                    </button>
                  ))}
                </div>
                <div className="filter-tags">
                  {filters.author.split(",").filter(a => a).map((author) => (
                    <span key={author} className="filter-tag">
                      {author}
                      <button
                        type="button"
                        onClick={() => {
                          const authors = filters.author.split(",").filter(a => a && a !== author);
                          setFilters((prev) => ({ ...prev, author: authors.join(",") }));
                        }}
                      >
                        ✕
                      </button>
                    </span>
                  ))}
                </div>
              </fieldset>

              <fieldset className="filter-checkboxes">
                <legend>Publishers</legend>
                <input
                  type="text"
                  placeholder="Type publisher name..."
                  list="publisher-options"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      const value = e.target.value.trim();
                      if (value && !filters.publisher.split(",").includes(value)) {
                        const publishers = filters.publisher.split(",").filter(p => p);
                        setFilters((prev) => ({ ...prev, publisher: [...publishers, value].join(",") }));
                        e.target.value = "";
                      }
                    }
                  }}
                />
                <div className="filter-choice-row">
                  {(filterOptions.publishers || []).slice(0, 8).map((publisher) => (
                    <button
                      key={publisher}
                      type="button"
                      className={filters.publisher.split(",").includes(publisher) ? "filter-chip selected" : "filter-chip"}
                      onClick={() => {
                        const publishers = filters.publisher.split(",").filter(p => p);
                        if (publishers.includes(publisher)) {
                          setFilters((prev) => ({ ...prev, publisher: publishers.filter(p => p !== publisher).join(",") }));
                        } else {
                          setFilters((prev) => ({ ...prev, publisher: [...publishers, publisher].join(",") }));
                        }
                      }}
                    >
                      {publisher}
                    </button>
                  ))}
                </div>
                <div className="filter-tags">
                  {filters.publisher.split(",").filter(p => p).map((publisher) => (
                    <span key={publisher} className="filter-tag">
                      {publisher}
                      <button
                        type="button"
                        onClick={() => {
                          const publishers = filters.publisher.split(",").filter(p => p && p !== publisher);
                          setFilters((prev) => ({ ...prev, publisher: publishers.join(",") }));
                        }}
                      >
                        ✕
                      </button>
                    </span>
                  ))}
                </div>
              </fieldset>
            </div>
          </div>

          <datalist id="type-options">
            {(filterOptions.product_types || []).map((type) => (
              <option key={type} value={type} />
            ))}
          </datalist>

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
        </aside>

        {/* Right Content - Results */}
        <main className="search-results-main">
          <section className="hero-banner">
            <div>
              <h2>Search Results</h2>
              <p>Showing results for "{activeQuery}"</p>
              {searchMeta && (
                <p className="meta-text">
                  Results: {searchMeta.count} | Source: {searchMeta.source} | Sort: {searchMeta.sort?.by} ({searchMeta.sort?.order})
                </p>
              )}
              <button className="link-btn" onClick={onBackToHome}>Back to Home</button>
            </div>
          </section>

          <ProductGrid products={products} sectionTitle={`Search Results for "${activeQuery}"`} searchError={searchError} onBookClick={onBookClick} />
        </main>
      </div>
    </div>
  );
}