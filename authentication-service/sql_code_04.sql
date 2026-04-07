-- One-time visit rebalance migration.
-- Goal:
-- 1) Advanced Academic Writing -> 0 visits
-- 2) Introduction to Algorithms -> 3000 visits
-- 3) Ensure this script runs only once using a migration marker.

CREATE TABLE IF NOT EXISTS bootstrap_migration_history (
    migration_key VARCHAR(120) PRIMARY KEY,
    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Remove visits for Introduction to Algorithms.
DELETE FROM product_visits
WHERE product_id = (
    SELECT product_id
    FROM products
    WHERE lower(product_name) = 'introduction to algorithms'
    ORDER BY product_id
    LIMIT 1
)
AND NOT EXISTS (
    SELECT 1
    FROM bootstrap_migration_history
    WHERE migration_key = 'sql_code_04_visit_rebalance_v1'
);

-- Remove visits for Advanced Academic Writing.
DELETE FROM product_visits
WHERE product_id = (
    SELECT product_id
    FROM products
    WHERE lower(product_name) = 'advanced academic writing'
    ORDER BY product_id
    LIMIT 1
)
AND NOT EXISTS (
    SELECT 1
    FROM bootstrap_migration_history
    WHERE migration_key = 'sql_code_04_visit_rebalance_v1'
);

-- Remove pre-existing outlier products at 3000+ visits so Introduction to Algorithms is top.
DELETE FROM product_visits
WHERE product_id IN (
    SELECT v.product_id
    FROM product_visits v
    GROUP BY v.product_id
    HAVING COUNT(*) >= 3000
       AND v.product_id <> (
           SELECT product_id
           FROM products
           WHERE lower(product_name) = 'introduction to algorithms'
           ORDER BY product_id
           LIMIT 1
       )
)
AND NOT EXISTS (
    SELECT 1
    FROM bootstrap_migration_history
    WHERE migration_key = 'sql_code_04_visit_rebalance_v1'
);

-- Seed exactly 3000 visits for Introduction to Algorithms.
INSERT INTO product_visits (user_id, product_id, visited_at)
SELECT
    up.user_id,
    p.product_id,
    CURRENT_TIMESTAMP - (g.i || ' seconds')::interval
FROM generate_series(1, 3000) AS g(i)
CROSS JOIN (
    SELECT product_id
    FROM products
    WHERE lower(product_name) = 'introduction to algorithms'
    ORDER BY product_id
    LIMIT 1
) AS p
CROSS JOIN (
    SELECT COUNT(*) AS user_count
    FROM users
) AS uc
JOIN (
    SELECT user_id, ROW_NUMBER() OVER (ORDER BY user_id) AS rn
    FROM users
) AS up
    ON up.rn = ((g.i - 1) % uc.user_count) + 1
WHERE uc.user_count > 0
AND NOT EXISTS (
    SELECT 1
    FROM bootstrap_migration_history
    WHERE migration_key = 'sql_code_04_visit_rebalance_v1'
);

-- Mark migration as applied (one-time gate).
INSERT INTO bootstrap_migration_history (migration_key)
SELECT 'sql_code_04_visit_rebalance_v1'
WHERE NOT EXISTS (
    SELECT 1
    FROM bootstrap_migration_history
    WHERE migration_key = 'sql_code_04_visit_rebalance_v1'
);
