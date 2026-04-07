export default function HistorySection({ searches, isLoading, error, isLoggedIn }) {
  return (
    <section className="api-section">
      <div className="section-header">
        <h3>Your Search History</h3>
      </div>

      {isLoading && <p className="info-text">Loading search history...</p>}
      {error && <p className="search-error">{error}</p>}

      {!isLoading && !error && (
        <div className="history-list">
          {isLoggedIn ? (
            searches.length > 0 ? (
              searches.map((item, index) => (
                <div className="history-card" key={`${item.query}-${index}`}>
                  <div className="history-query">{item.query}</div>
                  <div className="history-time">{item.timestamp}</div>
                </div>
              ))
            ) : (
              <p className="info-text">No search history found.</p>
            )
          ) : (
            <p className="info-text">Login to view your personalized search history.</p>
          )}
        </div>
      )}
    </section>
  );
}