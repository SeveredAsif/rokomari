export default function TrendingSection({ searches, isLoading, error }) {
  return (
    <section className="api-section">
      <div className="section-header">
        <h3>Trending Searches</h3>
      </div>

      {isLoading && <p className="info-text">Loading trending searches...</p>}
      {error && <p className="search-error">{error}</p>}

      {!isLoading && !error && (
        <div className="trending-list">
          {searches.length > 0 ? (
            searches.map((item, index) => (
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
  );
}