import ProductGrid from "./ProductGrid";

export default function PopularSection({
  title,
  subtitle,
  products,
  isLoading,
  error,
  onBookClick,
  emptyMessage = "No recommendations available yet.",
}) {
  const sectionTitle = title || "Popular Recommendations";

  return (
    <section className="api-section">
      <div className="section-header">
        <h3>{sectionTitle}</h3>
        {subtitle && <p className="meta-text">{subtitle}</p>}
      </div>

      {isLoading && <p className="info-text">Loading popular recommendations...</p>}
      {error && <p className="search-error">{error}</p>}
      {!isLoading && !error && products.length === 0 && <p className="info-text">{emptyMessage}</p>}

      {!isLoading && !error && products.length > 0 && (
        <ProductGrid products={products} sectionTitle="" searchError="" onBookClick={onBookClick} />
      )}
    </section>
  );
}