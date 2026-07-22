-- ============================================================
-- TUGAS 3: Query SQL - Performa Produk, Seller, dan Review
-- Dataset: Olist E-commerce (public schema)
-- ============================================================


-- ============================================================
-- 1. PERFORMA PRODUK (Terlaris & Paling Menguntungkan)
-- ============================================================
-- Catatan: status order yang dibatalkan/tidak tersedia dikeluarkan,
-- konsisten dengan filter yang dipakai di gold_pandas_transform.py

SELECT
    p.product_id,
    pc.product_category_name AS kategori,
    COUNT(oi.order_item_id)      AS total_terjual,
    SUM(oi.price)                AS total_pendapatan,
    ROUND(AVG(oi.price), 2)      AS rata_rata_harga,
    SUM(oi.freight_value)        AS total_ongkir
FROM public.fact_order_item oi
JOIN public.fact_order o
    ON oi.order_id = o.order_id
JOIN public.dim_product p
    ON oi.product_id = p.product_id
LEFT JOIN public.dim_product_category pc
    ON p.product_category_name = pc.product_category_name
WHERE o.order_status NOT IN ('canceled', 'unavailable')
GROUP BY p.product_id, pc.product_category_name
ORDER BY total_pendapatan DESC
LIMIT 20;


-- ============================================================
-- 2. PERFORMA SELLER / PENJUAL
-- ============================================================

SELECT
    s.seller_id,
    s.seller_city,
    s.seller_state,
    COUNT(DISTINCT oi.order_id)   AS total_order,
    COUNT(oi.order_item_id)       AS total_item_terjual,
    SUM(oi.price)                 AS total_pendapatan,
    ROUND(AVG(oi.price), 2)       AS rata_rata_harga_per_item,
    SUM(oi.freight_value)         AS total_ongkir
FROM public.fact_order_item oi
JOIN public.fact_order o
    ON oi.order_id = o.order_id
JOIN public.dim_seller s
    ON oi.seller_id = s.seller_id
WHERE o.order_status NOT IN ('canceled', 'unavailable')
GROUP BY s.seller_id, s.seller_city, s.seller_state
ORDER BY total_pendapatan DESC
LIMIT 20;


-- ============================================================
-- 3. ANALISIS REVIEW / KEPUASAN PELANGGAN
-- ============================================================
-- Ringkasan skor review + kaitannya dengan ketepatan waktu pengiriman

SELECT
    r.review_score,
    COUNT(*) AS jumlah_review,
    ROUND(
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2
    ) AS persentase,
    ROUND(AVG(
        EXTRACT(EPOCH FROM (o.order_delivered_customer_date - o.order_estimated_delivery_date)) / 86400
    ), 2) AS rata_rata_selisih_hari_pengiriman
FROM public.fact_order_review r
JOIN public.fact_order o
    ON r.order_id = o.order_id
WHERE o.order_status NOT IN ('canceled', 'unavailable')
GROUP BY r.review_score
ORDER BY r.review_score DESC;
