import logo from "../assets/logo.png";
import { useEffect, useRef, useState } from "react";
import { searchProducts } from "../services/api";

export default function Header({
  user,
  searchQuery,
  setSearchQuery,
  onSearch,
  isSearching,
  onLogout,
  onRequestLogin,
  onGoHome,
  onBookClick, // 🔥 IMPORTANT
}) {
  const [suggestions, setSuggestions] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [loading, setLoading] = useState(false);
  const [disableDropdown, setDisableDropdown] = useState(false);

  const debounceRef = useRef(null);
  const containerRef = useRef(null);

  // 🔥 AUTOCOMPLETE
  useEffect(() => {
    if (!searchQuery.trim() || disableDropdown){
      setSuggestions([]);
      setShowDropdown(false);
      return;
    }

    clearTimeout(debounceRef.current);

    debounceRef.current = setTimeout(async () => {
      try {
        setLoading(true);

        const res = await searchProducts(searchQuery, null, {
          limit: 5,
        });

        setSuggestions(res.results || []);
        setShowDropdown(true);
      } catch (err) {
        console.error("Autocomplete error:", err);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => clearTimeout(debounceRef.current);
  }, [searchQuery]);

  // 🔥 CLICK OUTSIDE
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setShowDropdown(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <>
      <header className="header home-header">
        {/* LOGO */}
        <div className="logo" onClick={onGoHome} style={{ cursor: "pointer" }}>
          <img src={logo} alt="Rokomari" />
        </div>

        {/* SEARCH */}
        <div className="search-container" ref={containerRef}>
          <form
            className="search-bar"
            onSubmit={(e) => {
              e.preventDefault();

              setDisableDropdown(true);   // 🔥 STOP reopening
              setShowDropdown(false);

              // 🔥 normal search page
              onSearch(e);

              // 🔥 clear input after
              setTimeout(() => {
                setSearchQuery("");
                setDisableDropdown(false); 
              }, 200);
            }}
          >
            <input
              type="text"
              placeholder="Search by title, author or keyword"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onFocus={() => suggestions.length && setShowDropdown(true)}
            />

            <button
              type="submit"
              className="search-btn"
              disabled={isSearching}
            >
              {isSearching ? "Searching..." : "Search"}
            </button>
          </form>

          {/* DROPDOWN */}
          {showDropdown && (
            <div className="search-dropdown">
              {loading ? (
                <div className="dropdown-item">Loading...</div>
              ) : suggestions.length === 0 ? (
                <div className="dropdown-item">No results</div>
              ) : (
                suggestions.map((item) => (
                  <div
                    key={item.id}
                    className="dropdown-item rich"
                    onClick={() => {
                    setDisableDropdown(true);   // 🔥 prevent reopen
                      // 🔥 NAVIGATE TO DETAIL PAGE
                      onBookClick({
                        id: item.id,
                        title: item.name,
                        author: item.author || item.brand || "Unknown",
                        publisher: item.publisher,
                        category: item.category || item.product_type,
                        price:
                          item.price != null ? `৳${item.price}` : "N/A",
                        image:
                          item.image_url || "/placeholder.jpg",
                      });
                      setShowDropdown(false);

                      setTimeout(() => {
                        setSearchQuery("");
                        setDisableDropdown(false);
                      }, 200);
                    }}
                  >
                    <img
                      src={item.image_url || "/placeholder.jpg"}
                      alt=""
                    />

                    <div>
                      <div className="title">{item.name}</div>

                      <div className="meta">
                        {item.author ||
                          item.brand ||
                          item.publisher ||
                          ""}
                      </div>

                      {item.price && (
                        <div className="price">৳{item.price}</div>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        {/* NAV */}
        <div className="nav">
          {user ? (
            <>
              <span>{user.full_name || user.email}</span>
              <button className="link-btn" onClick={onLogout}>
                Logout
              </button>
            </>
          ) : (
            <button className="primary-btn" onClick={onRequestLogin}>
              Login
            </button>
          )}
        </div>
      </header>

      <div className="category-bar">
        <span>Books</span>
        <span>Electronics</span>
        <span>Stationery</span>
        <span>Kids Zone</span>
        <span>Islamic Books</span>
      </div>
    </>
  );
}