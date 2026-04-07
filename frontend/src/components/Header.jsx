import logo from "../assets/logo.png";

export default function Header({ user, searchQuery, setSearchQuery, onSearch, isSearching, onLogout }) {
  return (
    <>
      <header className="header home-header">
        <div className="logo">
          <img src={logo} alt="Rokomari" />
        </div>

        <form className="search-bar" onSubmit={onSearch}>
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
          <button className="link-btn" onClick={onLogout}>Logout</button>
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