
  
    
    
    
        
         


        
  

  insert into `public`.`silver_dim_products__dbt_backup`
        ("product_id", "product_category_name", "product_category_english", "product_name_lenght", "product_description_lenght", "product_photos_qty", "product_weight_g", "product_length_cm", "product_height_cm", "product_width_cm")

-- ============================================================================
-- Silver Model: silver_dim_products
-- Deskripsi    : Menggabungkan data produk dengan terjemahan kategori
--                (Portugis -> Inggris).
-- ============================================================================

WITH source_product AS (
    SELECT * FROM `public`.`dim_product`
),

source_category AS (
    SELECT * FROM `public`.`dim_product_category`
),

joined AS (
    SELECT
        p.product_id,
        p.product_category_name,
        COALESCE(c.product_category_name_english, 'unknown') AS product_category_english,
        p.product_name_lenght,
        p.product_description_lenght,
        p.product_photos_qty,
        p.product_weight_g,
        p.product_length_cm,
        p.product_height_cm,
        p.product_width_cm
    FROM source_product p
    LEFT JOIN source_category c
        ON p.product_category_name = c.product_category_name
)

SELECT * FROM joined
  