import { useState } from "react";
import "./App.css";
import { useAuth } from "./hooks/useAuth";
import AuthPage from "./pages/AuthPage";
import HomePage from "./pages/HomePage";
import SearchPage from "./pages/SearchPage";
import BookDetailPage from "./pages/BookDetailPage";

export default function App() {
  const { token, user, login, logout } = useAuth();

  const [showAuth, setShowAuth] = useState(false);
  const [page, setPage] = useState("home");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedBook, setSelectedBook] = useState(null);
  const [sourcePageBeforeBook, setSourcePageBeforeBook] = useState("home");

  const handleLoginRequest = () => setShowAuth(true);
  const handleCloseAuth = () => setShowAuth(false);

  const handleLogin = (access_token, me) => {
    login(access_token, me);
    setShowAuth(false);
  };

  const handleSearch = (q) => {
    setSearchQuery(q);
    setPage("search");
  };

  const handleBackToHome = () => {
    setPage("home");
  };

  const handleBookClick = (book) => {
    setSelectedBook(book);
    setSourcePageBeforeBook(page);
    setPage("book-detail");
  };

  const handleBackFromBook = () => {
    setPage(sourcePageBeforeBook);
    setSelectedBook(null);
  };

  // 🔐 Auth page
  if (showAuth && !user) {
    return <AuthPage onLogin={handleLogin} onClose={handleCloseAuth} />;
  }

  // 📖 Book detail page
  if (page === "book-detail") {
    return (
      <BookDetailPage
        book={selectedBook}
        user={user}
        token={token}
        onLogout={logout}
        onRequestLogin={handleLoginRequest}
        onGoBack={handleBackFromBook}
      />
    );
  }

  // 🔍 Search page
  if (page === "search") {
    return (
      <SearchPage
        user={user}
        searchQuery={searchQuery}
        token={token}
        onLogout={logout}
        onRequestLogin={handleLoginRequest}
        onBackToHome={handleBackToHome}
        onBookClick={handleBookClick}
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
      onSearch={handleSearch}
      onBookClick={handleBookClick}
    />
  );
}
