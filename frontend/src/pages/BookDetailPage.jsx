import { useEffect, useState } from "react";
import Header from "../components/Header";
import { recordProductVisit } from "../services/api";

export default function BookDetailPage({
  book,
  user,
  token,
  searchQuery,
  setSearchQuery,
  onSearch,
  isSearching,
  onLogout,
  onRequestLogin,
  onGoHome,
  onGoBack,
}) {
  const [actionMessage, setActionMessage] = useState("");
  const [actionType, setActionType] = useState("success");

  const showActionMessage = (message, type = "success") => {
    setActionMessage(message);
    setActionType(type);
    window.setTimeout(() => setActionMessage(""), 3000);
  };

  const handleAddToCart = () => {
    if (!token) {
      onRequestLogin();
      return;
    }
    showActionMessage("Added to cart successfully", "success");
  };

  const handleAddToWishlist = () => {
    if (!token) {
      onRequestLogin();
      return;
    }
    showActionMessage("Added to wishlist successfully", "success");
  };

  useEffect(() => {
    if (!token || !book?.id) {
      return;
    }

    recordProductVisit(book.id, token).catch((err) => {
      if (err?.status === 401) {
        onLogout();
      }
    });
  }, [book?.id, token, onLogout]);

  if (!book) {
    return <div className="page"><p>Book not found</p></div>;
  }

  return (
    <div>
      <Header
        user={user}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        onSearch={onSearch}
        isSearching={isSearching}
        onLogout={onLogout}
        onRequestLogin={onRequestLogin}
        onGoHome={onGoHome}
        enableSuggestions={false}
      />

      <div className="home-page">
        {actionMessage && (
          <div className={`toast ${actionType}`}>
            {actionMessage}
          </div>
        )}

        {/* Back button */}
        <button className="link-btn" onClick={onGoBack} style={{ marginBottom: "16px", fontSize: "14px" }}>
          ← Back
        </button>

        {/* Main detail card */}
        <div className="product-card" style={{ display: "flex", gap: "32px", padding: "28px" }}>

          {/* Book cover */}
          <div className="product-thumb" style={{ width: "200px", height: "280px", flexShrink: 0 }}>
            <img src={book.image} alt={book.title} />
          </div>

          {/* Book info */}
          <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "12px" }}>
            <h2 style={{ margin: 0 }}>{book.title}</h2>

            {book.author && (
              <p style={{ margin: 0, color: "#6b7280", fontSize: "15px" }}>
                by <span style={{ color: "#16a34a", fontWeight: 600 }}>{book.author}</span>
              </p>
            )}

            {book.category && (
              <p className="meta-text"><strong>Category:</strong> {book.category}</p>
            )}

            <p className="product-price">{book.price}</p>

            {book.visitCount && (
              <p className="meta-text">👁 {book.visitCount} people viewed this</p>
            )}

            <div style={{ display: "flex", gap: "12px", marginTop: "8px", flexWrap: "wrap" }}>
              <button className="primary-btn" style={{ flex: 1, marginTop: 0 }} onClick={handleAddToCart}>
                🛒 Add to Cart
              </button>
              <button
                className="primary-btn"
                style={{ flex: 1, marginTop: 0, background: "white", color: "#22c55e", border: "1px solid #22c55e" }}
                onClick={handleAddToWishlist}
              >
                ♡ Wishlist
              </button>
            </div>
          </div>
        </div>

        {/* Description */}
        <div className="product-card" style={{ marginTop: "20px", padding: "24px" }}>
          <div className="section-header">
            <h3>About this book</h3>
          </div>
          <p className="info-text" style={{ lineHeight: "1.8", margin: 0 }}>
            {book.description || "No description available for this book."}
          </p>
        </div>

        {/* Book details table */}
        <div className="product-card" style={{ marginTop: "20px", padding: "24px" }}>
          <div className="section-header">
            <h3>Book details</h3>
          </div>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "14px" }}>
            <tbody>
              {[
                ["Category",   book.category],
                ["Author",     book.author],
                ["Publisher",  book.publisher],
                ["ISBN",       book.isbn],
                ["Pages",      book.pages],
                ["Language",   book.language],
                ["Edition",    book.edition],
                ["Popularity", book.visitCount ? `${book.visitCount} visits` : null],
              ]
                .filter(([, val]) => val)
                .map(([label, val]) => (
                  <tr key={label} style={{ borderBottom: "1px solid #f3f4f6" }}>
                    <td style={{ padding: "10px 0", color: "#6b7280", width: "40%" }}>{label}</td>
                    <td style={{ padding: "10px 0", fontWeight: 600, color: "#111827" }}>{val}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>

      </div>
    </div>
  );
}