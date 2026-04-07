import { useState } from "react";
import logo from "../assets/logo.png";
import { loginUser, registerUser, fetchMe } from "../services/api";

export default function AuthPage({ onLogin, onClose }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ full_name: "", phone: "", email: "", password: "" });
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isLogin = mode === "login";

  const clearMessage = () => { setMessage(""); setMessageType(""); };

  const onChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    if (message) clearMessage();
  };

  const switchMode = (nextMode) => {
    setMode(nextMode);
    clearMessage();
    setForm({ full_name: "", phone: "", email: "", password: "" });
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    clearMessage();
    setIsSubmitting(true);

    try {
      if (isLogin) {
        const { access_token } = await loginUser(form.email.trim(), form.password);
        const me = await fetchMe(access_token);
        onLogin(access_token, me);
        setMessage("Login successful");
        setMessageType("success");
        if (onClose) onClose();
      } else {
        await registerUser({
          email: form.email.trim(),
          password: form.password,
          full_name: form.full_name.trim(),
          phone: form.phone.trim(),
        });
        setMessage("Registration successful. Please login.");
        setMessageType("success");
        setMode("login");
        setForm({ full_name: "", phone: "", email: form.email, password: "" });
      }
    } catch (err) {
      setMessage(err.message);
      setMessageType("error");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div>
      <header className="header">
        <div className="logo">
          <img src={logo} alt="Rokomari" />
        </div>
        <div className="nav">
          {onClose ? (
            <button className="link-btn" type="button" onClick={onClose}>Close</button>
          ) : (
            <span>Become a Seller</span>
          )}
          <span>Sign in</span>
        </div>
      </header>

      <main className="page">
        <div className="card">
          <h2>{isLogin ? "Login" : "Create Account"}</h2>
          <p className="subtitle">
            {isLogin ? "Enter your email and password" : "Fill details to create account"}
          </p>

          <form onSubmit={onSubmit} className="form">
            {!isLogin && (
              <input type="text" name="full_name" placeholder="Enter your full name"
                value={form.full_name} onChange={onChange} required />
            )}
            {!isLogin && (
              <input type="text" name="phone" placeholder="Enter your phone number"
                value={form.phone} onChange={onChange} required />
            )}
            <input type="email" name="email" placeholder="Enter your email"
              value={form.email} onChange={onChange} required />
            <input type="password" name="password" placeholder="Enter your password"
              value={form.password} onChange={onChange} required />

            <div className="form-row">
              <label className="remember">
                <input type="checkbox" />
                <span>Remember me</span>
              </label>
              <button type="button" className="link-btn">Forgot password?</button>
            </div>

            <button className="primary-btn" disabled={isSubmitting}>
              {isSubmitting
                ? isLogin ? "Logging in..." : "Creating..."
                : isLogin ? "Login" : "Create Account"}
            </button>
          </form>

          {message && <p className={`message ${messageType}`}>{message}</p>}

          <p className="switch">
            {isLogin ? "No account?" : "Already have account?"}{" "}
            <button className="link-btn" onClick={() => switchMode(isLogin ? "register" : "login")}>
              {isLogin ? "Register" : "Login"}
            </button>
          </p>
        </div>
      </main>
    </div>
  );
}