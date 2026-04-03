import { useState } from "react";
import "./App.css";
import logo from "./assets/logo.png";

export default function App() {
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem("user");
    return raw ? JSON.parse(raw) : null;
  });

  const [mode, setMode] = useState("login");
  const [message, setMessage] = useState("");

  const [form, setForm] = useState({
    full_name: "",
    phone: "",
    email: "",
    password: ""
  });

  const isLogin = mode === "login";

  const onChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("token");
    localStorage.removeItem("user");
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    setMessage("");

    try {
      if (isLogin) {
        const res = await fetch("/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: form.email,
            password: form.password
          })
        });

        if (!res.ok) throw new Error("Login failed");

        const data = await res.json();
        localStorage.setItem("token", data.access_token);
        setToken(data.access_token);

        const me = await fetch("/auth/me", {
          headers: {
            Authorization: `Bearer ${data.access_token}`
          }
        });

        const userData = await me.json();
        localStorage.setItem("user", JSON.stringify(userData));
        setUser(userData);
      } else {
        const res = await fetch("/auth/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(form)
        });

        if (!res.ok) throw new Error("Register failed");

        setMessage("Registration successful. Please login.");
        setMode("login");
      }
    } catch (err) {
      setMessage(err.message);
    }
  };

  if (token && user) {
    return (
      <div>
        <div className="header">
          <div className="logo">
              <img src={logo} alt="rokomari" />
          </div>
        </div>

        <div className="page">
          <div className="card">
            <h2>Welcome {user.email}</h2>
            <button className="primary-btn" onClick={logout}>
              Logout
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="header">
        <div className="logo">
            <img src={logo} alt="rokomari" />
        </div>
        <div className="nav">
          <span>Become a Seller</span>
          <span>Sign in</span>
        </div>
      </div>

      <div className="page">
        <div className="card">
          <h2>{isLogin ? "Login" : "Create Account"}</h2>
          <p className="subtitle">
            {isLogin
              ? "Enter your email and password to continue"
              : "Fill in the details to create your account"}
          </p>
          <form onSubmit={onSubmit} className="form">
            {!isLogin && (
              <input
                name="full_name"
                placeholder="Full name"
                value={form.full_name}
                onChange={onChange}
                required
              />
            )}

            {!isLogin && (
              <input
                name="phone"
                placeholder="Phone"
                value={form.phone}
                onChange={onChange}
                required
              />
            )}

            <input
              name="email"
              placeholder="Enter your email"
              value={form.email}
              onChange={onChange}
              required
            />

            <input
              name="password"
              type="password"
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

              <button type="button" className="link">
                Forgot password?
              </button>
            </div>

            <button className="primary-btn">
              {isLogin ? "Login to Account" : "Create Account"}
            </button>
          </form>

          {message && <p className="error">{message}</p>}

          <p className="switch">
            {isLogin ? "No account?" : "Already have account?"}
            <button
              className="link"
              onClick={() => {
                setMode(isLogin ? "register" : "login");
                setMessage("");
              }}
            >
              {isLogin ? " Register" : " Login"}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}