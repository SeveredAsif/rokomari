import { useState } from "react";
import "./App.css";
import { useAuth } from "./hooks/useAuth";
import AuthPage from "./pages/AuthPage";
import HomePage from "./pages/HomePage";
import SearchPage from "./pages/SearchPage";

export default function App() {
  const { token, user, login, logout } = useAuth();

  const [showAuth, setShowAuth] = useState(false);

  // 🔥 NEW
  const [page, setPage] = useState("home");
  const [searchQuery, setSearchQuery] = useState("");

  const handleLoginRequest = () => setShowAuth(true);
  const handleCloseAuth = () => setShowAuth(false);

  const handleLogin = (access_token, me) => {
    login(access_token, me);
    setShowAuth(false);
  };

  // 🔥 HANDLE SEARCH NAVIGATION
  const handleSearch = (q) => {
    setSearchQuery(q);
    setPage("search");
  };

  const handleBackToHome = () => {
    setPage("home");
  };

  // 🔐 Auth page
  if (showAuth && !user) {
    return <AuthPage onLogin={handleLogin} onClose={handleCloseAuth} />;
  }

  // 🔍 Search page
  if (page === "search") {
    return (
      <SearchPage
        searchQuery={searchQuery}
        token={token}
        onLogout={logout}
        onBackToHome={handleBackToHome}
      />
    );
  }

  // 🏠 Home page
  return (
    <HomePage
      user={user}
      token={token}
      onLogout={logout}
      onRequestLogin={handleLoginRequest}
      onSearch={handleSearch} // 🔥 IMPORTANT
    />
  );
}