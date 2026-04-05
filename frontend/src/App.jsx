import { useEffect, useState } from "react";
import "./App.css";
import logo from "./assets/logo.png";

async function getErrorMessage(response, fallbackMessage) {
  try {
    const data = await response.json();
    return data.detail || data.message || fallbackMessage;
  } catch {
    return fallbackMessage;
  }
}

export default function App() {
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem("user");
    return raw ? JSON.parse(raw) : null;
  });

    const [searchQuery, setSearchQuery] = useState("");
  const [products, setProducts] = useState([
    {
      id: 1,
      title: "Atomic Habits",
      author: "James Clear",
      price: "৳450",
      image: "/src/assets/books/atomic-habits.jpg",
    },
    {
      id: 2,
      title: "Deep Work",
      author: "Cal Newport",
      price: "৳390",
      image: "/src/assets/books/deep-work.jpg",
    },
    {
      id: 3,
      title: "The Psychology of Money",
      author: "Morgan Housel",
      price: "৳520",
      image: "/src/assets/books/psychology-money.jpg",
    },
    {
      id: 4,
      title: "Clean Code",
      author: "Robert C. Martin",
      price: "৳610",
      image: "/src/assets/books/clean-code.jpg",
    },
    {
      id: 5,
      title: "Steal Like An Artist",
      author: "Austin Kleon",
      price: "৳350",
      image: "/src/assets/books/steal-like-an-artist.jpg",
    },
    {
      id: 6,
      title: "Men are from Mars, Women are from Venus",
      author: "John Gray",
      price: "৳480",
      image: "/src/assets/books/mars-venus.jpg",
    },
  ]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState("");
  const [sectionTitle, setSectionTitle] = useState("Popular Books");
  const [apiPopularProducts, setApiPopularProducts] = useState([]);
  const [popularError, setPopularError] = useState("");
  const [isLoadingPopular, setIsLoadingPopular] = useState(false);
  const [trendingSearches, setTrendingSearches] = useState([]);
  const [trendingError, setTrendingError] = useState("");
  const [isLoadingTrending, setIsLoadingTrending] = useState(false);
  const [searchHistory, setSearchHistory] = useState([]);
  const [historyError, setHistoryError] = useState("");
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);  

  const [mode, setMode] = useState("login");
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [form, setForm] = useState({
    full_name: "",
    phone: "",
    email: "",
    password: "",
  });

  const isLogin = mode === "login";

  const clearMessage = () => {
    setMessage("");
    setMessageType("");
  };

  const onChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    if (message) clearMessage();
  };

  const switchMode = (nextMode) => {
    setMode(nextMode);
    clearMessage();
    setForm({
      full_name: "",
      phone: "",
      email: "",
      password: "",
    });
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.clear();
    clearMessage();
    setMode("login");
  };

  const fetchPopularRecommendations = async () => {
  setIsLoadingPopular(true);
  setPopularError("");

    try {
      const response = await fetch("/recommendation/recommendations/popular?limit=6");

      if (!response.ok) {
        throw new Error(await getErrorMessage(response, "Failed to load popular recommendations"));
      }

      const data = await response.json();

      const mappedPopular = (data.results || []).map((item) => ({
        id: item.id,
        title: item.name || "Unnamed Product",
        author: item.author || "Unknown Author",
        category: item.category || "Unknown Category",
        price: item.price != null ? `৳${item.price}` : "N/A",
        image: item.image_url || "/src/assets/books/atomic-habits.jpg",
        visitCount: item.visit_count ?? 0,
      }));

      setApiPopularProducts(mappedPopular);
    } catch (error) {
      setPopularError(error.message || "Failed to load popular recommendations");
    } finally {
      setIsLoadingPopular(false);
    }
  };

  const fetchTrendingSearches = async () => {
    setIsLoadingTrending(true);
    setTrendingError("");

    try {
      const response = await fetch("/productsearch/search/trending?limit=8");

      if (!response.ok) {
        throw new Error(await getErrorMessage(response, "Failed to load trending searches"));
      }

      const data = await response.json();
      setTrendingSearches(data.trending_searches || []);
    } catch (error) {
      setTrendingError(error.message || "Failed to load trending searches");
    } finally {
      setIsLoadingTrending(false);
    }
  };  

  const fetchSearchHistory = async () => {
    if (!token) return;

    setIsLoadingHistory(true);
    setHistoryError("");

    try {
      const response = await fetch("/productsearch/search/history?limit=8", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(await getErrorMessage(response, "Failed to load search history"));
      }

      const data = await response.json();
      setSearchHistory(data.searches || []);
    } catch (error) {
      setHistoryError(error.message || "Failed to load search history");
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const handleSearch = async (e) => {
  e.preventDefault();

  const q = searchQuery.trim();
  if (!q) return;

  setIsSearching(true);
  setSearchError("");

  try {
    const storedToken = localStorage.getItem("token");

    const response = await fetch(
      `/productsearch/search?q=${encodeURIComponent(q)}&limit=12&threshold=0.1`,
      {
        headers: {
          Authorization: `Bearer ${storedToken}`,
        },
      }
    );

    if (!response.ok) {
      const errorText = await getErrorMessage(response, "Search failed");

      if (response.status === 401) {
        logout();
        throw new Error("Session expired. Please login again.");
      } 

      throw new Error(errorText);
    }

    const data = await response.json();

    const mappedProducts = (data.results || []).map((item) => ({
      id: item.id,
      title: item.name,
      author: item.author,
      price: `৳${item.price}`,
      image: item.image_url || "/src/assets/books/atomic-habits.jpg",
    }));

    setProducts(mappedProducts);
    setSectionTitle(`Search Results for "${q}"`);

    if (mappedProducts.length === 0) {
      setSearchError("No products found for this search.");
      }
    } catch (error) {
      setSearchError(error.message || "Search failed");
    } finally {
      setIsSearching(false);
    }

    fetchSearchHistory();
    fetchTrendingSearches();
  };

  useEffect(() => {
    if (token && user) {
      fetchPopularRecommendations();
      fetchTrendingSearches();
      fetchSearchHistory();
    }
  }, [token, user]);

  const onSubmit = async (e) => {
    e.preventDefault();
    clearMessage();
    setIsSubmitting(true);

    const email = form.email.trim();
    const password = form.password;

    try {
      if (isLogin) {
        const loginResp = await fetch("/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        });

        if (!loginResp.ok) {
          throw new Error(await getErrorMessage(loginResp, "Login failed"));
        }

        const { access_token } = await loginResp.json();
        localStorage.setItem("token", access_token);
        setToken(access_token);

        const meResp = await fetch("/auth/me", {
          headers: { Authorization: `Bearer ${access_token}` },
        });

        if (!meResp.ok) {
          throw new Error(await getErrorMessage(meResp, "Failed to fetch user"));
        }

        const me = await meResp.json();
        localStorage.setItem("user", JSON.stringify(me));
        setUser(me);

        setMessage("Login successful");
        setMessageType("success");
      } else {
        const registerResp = await fetch("/auth/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email,
            password,
            full_name: form.full_name.trim(),
            phone: form.phone.trim(),
          }),
        });

        if (!registerResp.ok) {
          throw new Error(await getErrorMessage(registerResp, "Register failed"));
        }

        setMessage("Registration successful. Please login.");
        setMessageType("success");

        setMode("login");
        setForm({
          full_name: "",
          phone: "",
          email,
          password: "",
        });
      }
    } catch (err) {
      setMessage(err.message);
      setMessageType("error");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Logged-in view
  if (token && user) {
  const mockProducts = [
    {
      id: 1,
      title: "Atomic Habits",
      author: "James Clear",
      price: "৳450",
      image: "/src/assets/books/atomic-habits.jpg",
    },
    {
      id: 2,
      title: "Deep Work",
      author: "Cal Newport",
      price: "৳390",
      image: "/src/assets/books/deep-work.jpg",
    },
    {
      id: 3,
      title: "The Psychology of Money",
      author: "Morgan Housel",
      price: "৳520",
      image: "/src/assets/books/psychology-money.jpg",
    },
    {
      id: 4,
      title: "Clean Code",
      author: "Robert C. Martin",
      price: "৳610",
      image: "/src/assets/books/clean-code.jpg",
    },
    {
      id: 5,
      title: "Steal Like An Artist",
      author: "Austin Kleon",
      price: "৳350",
      image: "/src/assets/books/steal-like-an-artist.jpg",
    },
    {
      id: 6,
      title: "Men are from Mars, Women are from Venus",
      author: "John Gray",
      price: "৳480",
      image: "/src/assets/books/mars-venus.jpg",
    },
  ];

  return (
    <div>
      <header className="header home-header">
        <div className="logo">
          <img src={logo} alt="Rokomari" />
        </div>

        <form className="search-bar" onSubmit={handleSearch}>
          <input
            type="text"
            placeholder="Search by title, author or keyword"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <button className="search-btn" type="submit" disabled={isSearching}>
            {isSearching ? "Searching..." : "Search"}
          </button>
        </form>

        <div className="nav">
          <span>{user.full_name || user.email}</span>
          <button className="link-btn" onClick={logout}>Logout</button>
        </div>
      </header>

      <div className="category-bar">
        <span>Books</span>
        <span>Electronics</span>
        <span>Stationery</span>
        <span>Kids Zone</span>
        <span>Islamic Books</span>
      </div>

      <main className="home-page">
        <section className="hero-banner">
          <div>
            <h2>Welcome back, {user.full_name || "Reader"}</h2>
            <p>Browse books, search products, and discover recommendations.</p>
          </div>
        </section>

        <section className="section-header">
          <h3>{sectionTitle}</h3>
        </section>

        {searchError && <p className="search-error">{searchError}</p>}

        <section className="product-grid">
          {products.map((item) => (
            <div className="product-card" key={item.id}>
              <div className="product-thumb">
                 <img src={item.image} alt={item.title} />
              </div>
              <h4>{item.title}</h4>
              <p>{item.author}</p>
              <strong className="product-price">{item.price}</strong>
            </div>
          ))}
        </section>

        <section className="api-section">
          <div className="section-header">
            <h3>Popular Recommendations (API)</h3>
          </div>

          {isLoadingPopular && <p className="info-text">Loading API recommendations...</p>}
          {popularError && <p className="search-error">{popularError}</p>}

          {!isLoadingPopular && !popularError && (
            <section className="product-grid">
              {apiPopularProducts.length > 0 ? (
                apiPopularProducts.map((item) => (
                  <div className="product-card" key={`api-${item.id}`}>
                    <div className="product-thumb">
                      <img src={item.image} alt={item.title} />
                    </div>
                    <h4>{item.title}</h4>
                    <p>{item.author}</p>
                    <strong className="product-price">{item.price}</strong>
                    <p className="meta-text">{item.category}</p>
                    <p className="meta-text">Visits: {item.visitCount}</p>
                  </div>
                ))
              ) : (
                <p className="info-text">No API recommendations found.</p>
              )}
            </section>
          )}
        </section>

        <section className="api-section">
          <div className="section-header">
            <h3>Trending Searches</h3>
          </div>

          {isLoadingTrending && <p className="info-text">Loading trending searches...</p>}
          {trendingError && <p className="search-error">{trendingError}</p>}

          {!isLoadingTrending && !trendingError && (
            <div className="trending-list">
              {trendingSearches.length > 0 ? (
                trendingSearches.map((item, index) => (
                  <div className="trending-chip" key={`${item.query}-${index}`}>
                    <span className="trending-query">{item.query}</span>
                    <span className="trending-count">{item.search_count}</span>
                  </div>
                ))
              ) : (
                <p className="info-text">No trending searches found.</p>
              )}
            </div>
          )}
        </section>

        <section className="api-section">
          <div className="section-header">
            <h3>Your Search History</h3>
          </div>

          {isLoadingHistory && <p className="info-text">Loading search history...</p>}
          {historyError && <p className="search-error">{historyError}</p>}

          {!isLoadingHistory && !historyError && (
            <div className="history-list">
              {searchHistory.length > 0 ? (
                searchHistory.map((item, index) => (
                  <div className="history-card" key={`${item.query}-${index}`}>
                    <div className="history-query">{item.query}</div>
                    <div className="history-time">{item.timestamp}</div>
                  </div>
                ))
              ) : (
                <p className="info-text">No search history found.</p>
              )}
            </div>
          )}
        </section>                

      </main>
    </div>
  );
}

  // Auth form
  return (
    <div>
      <header className="header">
        <div className="logo">
          <img src={logo} alt="Rokomari" />
        </div>

        <div className="nav">
          <span>Become a Seller</span>
          <span>Sign in</span>
        </div>
      </header>

      <main className="page">
        <div className="card">
          <h2>{isLogin ? "Login" : "Create Account"}</h2>

          <p className="subtitle">
            {isLogin
              ? "Enter your email and password"
              : "Fill details to create account"}
          </p>

          <form onSubmit={onSubmit} className="form">
            {!isLogin && (
              <input
                type="text"
                name="full_name"
                placeholder="Enter your full name"
                value={form.full_name}
                onChange={onChange}
                required
              />
            )}

            {!isLogin && (
              <input
                type="text"
                name="phone"
                placeholder="Enter your phone number"
                value={form.phone}
                onChange={onChange}
                required
              />
            )}

            <input
              type="email"
              name="email"
              placeholder="Enter your email"
              value={form.email}
              onChange={onChange}
              required
            />

            <input
              type="password"
              name="password"
              placeholder="Enter your password"
              value={form.password}
              onChange={onChange}
              required
            />

            <div className="form-row">
              <label className="remember">
                <input type="checkbox" />
                <span>Remember me</span>
              </label>

              <button type="button" className="link-btn">
                Forgot password?
              </button>
            </div>

            <button className="primary-btn" disabled={isSubmitting}>
              {isSubmitting
                ? isLogin
                  ? "Logging in..."
                  : "Creating..."
                : isLogin
                ? "Login"
                : "Create Account"}
            </button>
          </form>

          {message && (
            <p className={`message ${messageType}`}>
              {message}
            </p>
          )}

          <p className="switch">
            {isLogin ? "No account?" : "Already have account?"}{" "}
            <button
              className="link-btn"
              onClick={() => switchMode(isLogin ? "register" : "login")}
            >
              {isLogin ? "Register" : "Login"}
            </button>
          </p>
        </div>
      </main>
    </div>
  );
}