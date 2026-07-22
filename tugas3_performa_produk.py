import os
import sys
import logging
import pandas as pd
from sqlalchemy import create_engine

# =====================================================================
# 1. KONFIGURASI LOGGING
# =====================================================================
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    handlers=[
        logging.FileHandler("logs/tugas3_performa_produk.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

# =====================================================================
# 2. KONFIGURASI DATABASE
# Sesuaikan dengan docker-compose.yml kamu sendiri (bukan contoh mentor)
# =====================================================================
DB_USER = "vivi"
DB_PASS = "bootcamp123"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "nusacode_db"

DB_URI = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


# =====================================================================
# 3. FUNGSI: Performa Produk (Terlaris & Paling Menguntungkan)
# =====================================================================
def build_performa_produk(engine) -> pd.DataFrame:
    logging.info("Membaca data produk, order item, dan order...")

    items = pd.read_sql("SELECT * FROM public.fact_order_item", con=engine)
    orders = pd.read_sql("SELECT order_id, order_status FROM public.fact_order", con=engine)
    products = pd.read_sql("SELECT * FROM public.dim_product", con=engine)
    categories = pd.read_sql("SELECT * FROM public.dim_product_category", con=engine)

    # Filter order yang valid (bukan dibatalkan/tidak tersedia)
    cancel = ["canceled", "unavailable"]
    orders_valid = orders[~orders["order_status"].isin(cancel)]

    # Gabungkan item hanya dari order yang valid
    merged = items.merge(orders_valid[["order_id"]], on="order_id", how="inner")

    # Gabungkan dengan data produk & kategori
    merged = merged.merge(products, on="product_id", how="left")
    merged = merged.merge(categories, on="product_category_name", how="left")

    # Agregasi per produk
    grouped = merged.groupby(["product_id", "product_category_name"]).agg(
        total_terjual=("order_item_id", "count"),
        total_pendapatan=("price", "sum"),
        rata_rata_harga=("price", "mean"),
        total_ongkir=("freight_value", "sum"),
    ).reset_index()

    grouped["total_pendapatan"] = grouped["total_pendapatan"].round(2)
    grouped["rata_rata_harga"] = grouped["rata_rata_harga"].round(2)
    grouped["total_ongkir"] = grouped["total_ongkir"].round(2)

    grouped = grouped.sort_values("total_pendapatan", ascending=False).reset_index(drop=True)

    logging.info(f"Selesai. {len(grouped)} produk dianalisis.")
    return grouped


# =====================================================================
# 4. MAIN
# =====================================================================
if __name__ == "__main__":
    engine = create_engine(DB_URI)
    logging.info("Koneksi database berhasil.")

    df_produk = build_performa_produk(engine)

    print("\n=== TOP 20 PRODUK TERLARIS & PALING MENGUNTUNGKAN ===")
    print(df_produk.head(20))

    engine.dispose()
