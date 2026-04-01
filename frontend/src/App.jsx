import { useState } from "react";

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

  const onChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setMode("login");
    setMessage("");
  };

  const onSubmit = async (event) => {
    event.preventDefault();
    setMessage("");

    const email = form.email.trim();
    const password = form.password;

    try {
      if (isLogin) {
        const loginResp = await fetch("/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password })
        });

        if (!loginResp.ok) {
          const err = await loginResp.json().catch(() => ({ detail: "Login failed" }));
          throw new Error(err.detail || "Login failed");
        }

        const loginData = await loginResp.json();
        const newToken = loginData.access_token;

        localStorage.setItem("token", newToken);
        setToken(newToken);

        const meResp = await fetch("/auth/me", {
          headers: { Authorization: `Bearer ${newToken}` }
        });

        if (!meResp.ok) {
          throw new Error("Could not load profile");
        }

        const me = await meResp.json();
        localStorage.setItem("user", JSON.stringify(me));
        setUser(me);
      } else {
        const registerResp = await fetch("/auth/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email,
            password,
            full_name: form.full_name.trim(),
            phone: form.phone.trim()
          })
        });

        if (!registerResp.ok) {
          const err = await registerResp.json().catch(() => ({ detail: "Register failed" }));
          throw new Error(err.detail || "Register failed");
        }

        setMessage("Registration successful. Please login.");
        setMode("login");
      }
    } catch (error) {
      setMessage(error.message || "Request failed");
    }
  };

  if (token && user) {
    return (
      <div>
        <p>Logged in{user.email ? ` as ${user.email}` : ""}</p>
        <h1>Welcome to Rokomari</h1>
        <button onClick={logout}>Logout</button>
      </div>
    );
  }

  return (
    <div>
      <h2>{isLogin ? "Login" : "Register"}</h2>
      <form onSubmit={onSubmit}>
        {!isLogin ? (
          <input
            name="full_name"
            placeholder="Full name"
            required
            value={form.full_name}
            onChange={onChange}
          />
        ) : null}

        {!isLogin ? (
          <input
            name="phone"
            placeholder="Phone"
            required
            value={form.phone}
            onChange={onChange}
          />
        ) : null}

        <input
          name="email"
          type="email"
          placeholder="Email"
          required
          value={form.email}
          onChange={onChange}
        />

        <input
          name="password"
          type="password"
          placeholder="Password"
          required
          value={form.password}
          onChange={onChange}
        />

        <button type="submit">{isLogin ? "Login" : "Register"}</button>
      </form>

      <button onClick={() => setMode(isLogin ? "register" : "login")}>
        Switch to {isLogin ? "Register" : "Login"}
      </button>

      <p>{message}</p>
    </div>
  );
}
