import { useState } from "react";
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

        <div className="search-bar">
          <input type="text" placeholder="Search by title, author or keyword" />
          <button className="search-btn">Search</button>
        </div>

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
          <h3>Popular Books</h3>
        </section>

        <section className="product-grid">
          {mockProducts.map((item) => (
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