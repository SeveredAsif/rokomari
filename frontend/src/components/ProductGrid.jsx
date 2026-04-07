export default function ProductGrid({ products, sectionTitle, searchError, onBookClick }) {
  return (
    <section className="search-section">
      <div className="section-header">
        <h3>{sectionTitle}</h3>
      </div>

      {searchError && <p className="search-error">{searchError}</p>}

      {products.length > 0 ? (
        <section className="product-grid">
          {products.map((item) => {
            const authorLine = [item.author, item.publisher].filter(Boolean).join(" | ");

            return (
              <div
                className="product-card"
                key={item.id}
                onClick={() => onBookClick && onBookClick(item)}
                style={{ cursor: "pointer" }}
                role="button"
                tabIndex={0}
              >
                <div className="product-thumb">
                  <img src={item.image} alt={item.title} />
                </div>
                <h4>{item.title}</h4>
                <p>{authorLine || item.author || "Unknown"}</p>
                {item.category && <p className="meta-text">{item.category}</p>}
                <strong className="product-price">{item.price}</strong>
              </div>
            );
          })}
        </section>
      ) : (
        <p className="info-text">No products found.</p>
      )}
    </section>
  );
}