import ProductGrid from "./ProductGrid";

export default function PopularSection({ products, isLoading, error, onBookClick }) {
  return (
    <section className="api-section">
      <div className="section-header">
        <h3>Popular Recommendations (API)</h3>
      </div>

      {isLoading && <p className="info-text">Loading popular recommendations...</p>}
      {error && <p className="search-error">{error}</p>}

      {!isLoading && !error && (
        <ProductGrid products={products} sectionTitle="" searchError="" onBookClick={onBookClick} />
      )}
    </section>
  );
}