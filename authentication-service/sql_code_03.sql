-- Normalize product taxonomy and metadata so filters are reliable.

-- 1) Infer product_type from product_name keywords.
WITH classified AS (
    SELECT
        product_id,
        CASE
            WHEN product_name ~* '(usb|wireless|bluetooth|keyboard|mouse|monitor|webcam|charger|speaker|headphone|earbud|router|printer|ssd|hard drive|power bank|smart watch|tv stick|microphone|projector|scanner|tracker|camera|docking|soundbar|gimbal|torch|humidifier|media player|range extender|charging dock|barcode)' THEN 'ELECTRONICS'
            WHEN product_name ~* '(book|textbook|guide|handbook|fundamentals|concepts|introduction to|theory of|workbook|literature|novel|poetry|economics|finance|accounting|sociology|philosophy|programming|algorithms|mathematics|history|statistics|communication|ethics|research|physics|marketing|linguistics)' THEN 'BOOK'
            WHEN product_name ~* '(gift|hamper|bouquet|card|candle|trophy|frame|teddy|chocolate|anniversary|surprise|rose|memory|photo|mug|voucher|keychain|decorative|celebration|love)' THEN 'GIFT'
            WHEN product_name ~* '(notebook|pen|marker|folder|sticky|diary|highlighter|binder|paper|stapler|tray|file|register|journal|planner|desk|drawer|storage|organizer|pouch|basket|bin|holder|whiteboard|duster|clip|memo|calendar|caddy|rack|cabinet|shelf|wallet|pad|scissors|tape|stationery)' THEN 'STATIONERY'
            ELSE 'OTHER'
        END AS inferred_type
    FROM products
)
UPDATE products p
SET product_type = c.inferred_type
FROM classified c
WHERE p.product_id = c.product_id
  AND p.product_type <> c.inferred_type;

-- 2) Align category_id with normalized product_type.
WITH category_map AS (
    SELECT
        MAX(CASE WHEN lower(category_name) = 'books' THEN category_id END) AS books_id,
        MAX(CASE WHEN lower(category_name) = 'stationery' THEN category_id END) AS stationery_id,
        MAX(CASE WHEN lower(category_name) = 'electronics' THEN category_id END) AS electronics_id,
        MAX(CASE WHEN lower(category_name) = 'gift items' THEN category_id END) AS gift_id,
        MAX(CASE WHEN lower(category_name) = 'other' THEN category_id END) AS other_id
    FROM categories
)
UPDATE products p
SET category_id = CASE p.product_type
    WHEN 'BOOK' THEN cm.books_id
    WHEN 'STATIONERY' THEN cm.stationery_id
    WHEN 'ELECTRONICS' THEN cm.electronics_id
    WHEN 'GIFT' THEN cm.gift_id
    ELSE cm.other_id
END
FROM category_map cm
WHERE (
    CASE p.product_type
        WHEN 'BOOK' THEN cm.books_id
        WHEN 'STATIONERY' THEN cm.stationery_id
        WHEN 'ELECTRONICS' THEN cm.electronics_id
        WHEN 'GIFT' THEN cm.gift_id
        ELSE cm.other_id
    END
) IS NOT NULL
AND p.category_id <> (
    CASE p.product_type
        WHEN 'BOOK' THEN cm.books_id
        WHEN 'STATIONERY' THEN cm.stationery_id
        WHEN 'ELECTRONICS' THEN cm.electronics_id
        WHEN 'GIFT' THEN cm.gift_id
        ELSE cm.other_id
    END
);

-- 3) Keep book_details only for books.
DELETE FROM book_details bd
USING products p
WHERE p.product_id = bd.product_id
  AND p.product_type <> 'BOOK';

-- 4) Upsert usable book metadata instead of dummy Author <id> values.
INSERT INTO book_details (product_id, isbn, author, publisher, language, num_pages, edition)
SELECT
    p.product_id,
    COALESCE(NULLIF(bd.isbn, ''), 'ISBN' || p.product_id::text) AS isbn,
    CASE
        WHEN bd.author IS NOT NULL AND bd.author !~ '^Author [0-9]+$' THEN bd.author
        WHEN p.product_name ~* '(algorithms|data structures|theory of computation|formal languages|operating systems|compiler|database|microprocessor|network|cyber security|digital logic|object oriented|software engineering)' THEN 'Tech Faculty Editorial Board'
        WHEN p.product_name ~* '(history|literature|poetry|english|linguistics|philosophy|sociology|communication|writing)' THEN 'Humanities Editorial Board'
        WHEN p.product_name ~* '(economics|finance|accounting|marketing|business)' THEN 'Business Studies Editorial Board'
        ELSE COALESCE(NULLIF(p.brand, ''), 'Rokomari') || ' Publications'
    END AS author,
    CASE
        WHEN bd.publisher IS NOT NULL AND bd.publisher !~ '^Publisher [0-9]+$' THEN bd.publisher
        WHEN p.product_name ~* '(algorithms|data structures|theory|operating systems|network|cyber security|software|programming|database|microprocessor)' THEN 'TechPress'
        WHEN p.product_name ~* '(history|literature|poetry|english|linguistics|writing|philosophy|sociology)' THEN 'Literary House'
        WHEN p.product_name ~* '(economics|finance|accounting|marketing|business)' THEN 'Business Insight Press'
        ELSE 'Rokomari Books'
    END AS publisher,
    COALESCE(NULLIF(bd.language, ''), 'English') AS language,
    COALESCE(bd.num_pages, 160 + (p.product_id % 340)) AS num_pages,
    COALESCE(NULLIF(bd.edition, ''), ((p.product_id % 5) + 1)::text || 'th') AS edition
FROM products p
LEFT JOIN book_details bd ON bd.product_id = p.product_id
WHERE p.product_type = 'BOOK'
ON CONFLICT (product_id) DO UPDATE
SET
    isbn = EXCLUDED.isbn,
    author = EXCLUDED.author,
    publisher = EXCLUDED.publisher,
    language = EXCLUDED.language,
    num_pages = EXCLUDED.num_pages,
    edition = EXCLUDED.edition;

-- 5) Helpful indexes for filtering/sorting.
CREATE INDEX IF NOT EXISTS idx_products_price ON products (price);
CREATE INDEX IF NOT EXISTS idx_products_type_price ON products (product_type, price);
CREATE INDEX IF NOT EXISTS idx_products_brand_lower ON products ((lower(brand)));
CREATE INDEX IF NOT EXISTS idx_book_details_author_lower ON book_details ((lower(author)));
CREATE INDEX IF NOT EXISTS idx_book_details_publisher_lower ON book_details ((lower(publisher)));
