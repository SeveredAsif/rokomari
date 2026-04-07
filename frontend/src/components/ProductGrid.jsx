export default function PopularSection({ products, isLoading, error }) {
  return (
    <section className="api-section">
      <div className="section-header">
        <h3>Popular Recommendations (API)</h3>
      </div>

      {isLoading && <p className="info-text">Loading API recommendations...</p>}
      {error && <p className="search-error">{error}</p>}

      {!isLoading && !error && (
        <section className="product-grid">
          {products.length > 0 ? (
            products.map((item) => (
              <div className="product-card" key={`api-${item.id}`}>
                <div className="product-thumb">
                  <img src={item.image} alt={item.title} />
                </div>
                <h4>{item.title}</h4>
                <p>{item.author}</p>
                <strong className="product-price">{item.price}</strong>
                <p className="meta-text">{item.category}</p>
                <p className="meta-text">Visits: {item.visitCount}</p>
              </div>
            ))
          ) : (
            <p className="info-text">No API recommendations found.</p>
          )}
        </section>
      )}
    </section>
  );
}