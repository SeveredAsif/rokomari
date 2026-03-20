INSERT INTO users (full_name, email, phone, password_hash)
SELECT 
    'User ' || i,
    'user' || i || '@mail.com',
    '017' || LPAD(i::text, 8, '0'),
    'hash' || i
FROM generate_series(1, 1000) AS i;



INSERT INTO admins (user_id)
SELECT user_id FROM users WHERE user_id <= 10;


INSERT INTO products (product_name, category_id, price, stock_qty, brand, product_type)
SELECT 
    'Product ' || i,
    (RANDOM()*4 + 1)::INT,
    ROUND((RANDOM()*1000 + 50)::numeric, 2),
    (RANDOM()*100)::INT,
    'Brand ' || ((i % 10) + 1),
    (ARRAY['BOOK','STATIONERY','ELECTRONICS','GIFT','OTHER'])[floor(random()*5 + 1)]
FROM generate_series(1, 1000) AS i;



INSERT INTO book_details (product_id, isbn, author, publisher, language, num_pages, edition)
SELECT 
    product_id,
    'ISBN' || product_id,
    'Author ' || product_id,
    'Publisher ' || product_id,
    'English',
    (RANDOM()*500 + 100)::INT,
    (floor(random()*5)+1) || 'th'
FROM products
WHERE product_type = 'BOOK'
LIMIT 200;



INSERT INTO electronics_details (product_id, model_no, warranty_months)
SELECT 
    product_id,
    'Model-' || product_id,
    (RANDOM()*24 + 6)::INT
FROM products
WHERE product_type = 'ELECTRONICS'
LIMIT 200;


INSERT INTO search_history (user_id, searched_keyword)
SELECT 
    (RANDOM()*999 + 1)::INT,
    'keyword_' || i
FROM generate_series(1, 2000) AS i;


INSERT INTO product_visits (user_id, product_id)
SELECT 
    (RANDOM()*999 + 1)::INT,
    (RANDOM()*999 + 1)::INT
FROM generate_series(1, 3000);


INSERT INTO addresses (user_id, recipient_name, phone, address_line, city, area, postal_code)
SELECT 
    user_id,
    'User ' || user_id,
    '017' || LPAD(user_id::text, 8, '0'),
    'Address Line ' || user_id,
    'City ' || ((user_id % 5)+1),
    'Area ' || ((user_id % 10)+1),
    '1000' || user_id
FROM users;


INSERT INTO cart (user_id)
SELECT user_id FROM users;


INSERT INTO cart_items (cart_id, product_id, quantity)
SELECT 
    (RANDOM()*999 + 1)::INT,
    (RANDOM()*999 + 1)::INT,
    (RANDOM()*5 + 1)::INT
FROM generate_series(1, 3000);



INSERT INTO orders (user_id, address_id, total_amount, shipping_charge, discount_amount, order_status)
SELECT 
    (RANDOM()*999 + 1)::INT,
    (RANDOM()*999 + 1)::INT,
    ROUND((RANDOM()*5000 + 100)::numeric, 2),
    ROUND((RANDOM()*100)::numeric, 2),
    ROUND((RANDOM()*50)::numeric, 2),
    (ARRAY['PENDING','CONFIRMED','PACKED','SHIPPED','DELIVERED'])[floor(random()*5 + 1)]
FROM generate_series(1, 1000);



INSERT INTO order_items (order_id, product_id, quantity)
SELECT 
    (RANDOM()*999 + 1)::INT,
    (RANDOM()*999 + 1)::INT,
    (RANDOM()*3 + 1)::INT
FROM generate_series(1, 3000);



INSERT INTO payments (order_id, payment_method, payment_status, transaction_id, paid_at)
SELECT 
    order_id,
    (ARRAY['COD','BKASH','NAGAD','CARD'])[floor(random()*4 + 1)],
    (ARRAY['UNPAID','PAID','FAILED'])[floor(random()*3 + 1)],
    'TXN' || order_id,
    CURRENT_TIMESTAMP
FROM orders;



INSERT INTO order_status_history (order_id, status, note)
SELECT 
    (RANDOM()*999 + 1)::INT,
    (ARRAY['PENDING','CONFIRMED','PACKED','SHIPPED','DELIVERED'])[floor(random()*5 + 1)],
    'Auto update'
FROM generate_series(1, 2000);

