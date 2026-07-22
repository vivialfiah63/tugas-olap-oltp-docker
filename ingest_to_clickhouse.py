import os
import sys
import logging
import pandas as pd
import clickhouse_connect

# =====================================================================
# 1. KONFIGURASI LOGGING
# =====================================================================
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    handlers=[
        logging.FileHandler("logs/ingest_to_clickhouse.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

# =====================================================================
# 2. KONFIGURASI CLICKHOUSE
# Sesuaikan dengan docker-compose.yml kamu sendiri kalau beda
# =====================================================================
CH_HOST = "localhost"
CH_PORT = 8123
CH_USER = "clickhousedev"
CH_PASS = "adminpass123"
CH_DATABASE = "public"

# =====================================================================
# 3. DEFINISI TABLE CSV
# (sama seperti DATASET_MAP di ingest_to_db.py, target: database 'public' di ClickHouse)
# =====================================================================
DATASET_MAP = [
    ("dim_customer", "olist_customers_dataset.csv"),
    ("dim_geolocation", "olist_geolocation_dataset.csv"),
    ("dim_product", "olist_products_dataset.csv"),
    ("dim_product_category", "product_category_name_translation.csv"),
    ("dim_seller", "olist_sellers_dataset.csv"),
    ("fact_order", "olist_orders_dataset.csv"),
    ("fact_order_item", "olist_order_items_dataset.csv"),
    ("fact_order_payment", "olist_order_payments_dataset.csv"),
    ("fact_order_review", "olist_order_reviews_dataset.csv"),
]

ARCHIVE_DIR = os.path.join(os.path.dirname(__file__), "..", "pertemuan 3", "archive")


# =====================================================================
# 4. FUNGSI BANTU: mapping tipe data pandas -> tipe ClickHouse
# =====================================================================
def map_dtype_to_clickhouse(dtype) -> str:
    dtype_str = str(dtype)
    if "int" in dtype_str:
        return "Nullable(Int64)"
    elif "float" in dtype_str:
        return "Nullable(Float64)"
    else:
        return "Nullable(String)"


def build_create_table_sql(table_name: str, df: pd.DataFrame) -> str:
    columns_sql = []
    for col, dtype in df.dtypes.items():
        ch_type = map_dtype_to_clickhouse(dtype)
        columns_sql.append(f'"{col}" {ch_type}')

    columns_def = ",\n    ".join(columns_sql)

    return f"""
    CREATE TABLE IF NOT EXISTS {CH_DATABASE}.{table_name}
    (
        {columns_def}
    )
    ENGINE = MergeTree()
    ORDER BY tuple()
    """


# =====================================================================
# 5. PIPELINE UTAMA
# =====================================================================
def ingest_csv_to_clickhouse():
    logging.info("===== Memulai proses ingest data ke ClickHouse =====")

    try:
        client = clickhouse_connect.get_client(
            host=CH_HOST,
            port=CH_PORT,
            username=CH_USER,
            password=CH_PASS,
        )
        logging.info(f"Sukses terhubung ke ClickHouse: {CH_HOST}")
    except Exception as e:
        logging.error(f"Gagal terhubung ke ClickHouse: {e}")
        raise

    # Bikin database 'public' kalau belum ada
    client.command(f"CREATE DATABASE IF NOT EXISTS {CH_DATABASE}")
    logging.info(f"Database '{CH_DATABASE}' siap.")

    for table_name, csv_file in DATASET_MAP:
        csv_path = os.path.join(ARCHIVE_DIR, csv_file)
        logging.info(f"[START] Memproses file: {csv_file} ...")

        try:
            df = pd.read_csv(csv_path)
            logging.info(f"Berhasil memuat {len(df)} baris dari {csv_file}")

            # ClickHouse tidak suka NaN campur tipe -> ganti NaN jadi None
            df = df.where(pd.notnull(df), None)

            # Drop tabel lama kalau ada, lalu bikin ulang sesuai skema CSV
            client.command(f"DROP TABLE IF EXISTS {CH_DATABASE}.{table_name}")
            create_sql = build_create_table_sql(table_name, df)
            client.command(create_sql)

            # Insert data
            client.insert_df(f"{CH_DATABASE}.{table_name}", df)

            logging.info(f"[DONE] {len(df)} baris masuk ke tabel {CH_DATABASE}.{table_name}")

        except Exception as e:
            logging.error(f"Gagal memuat {csv_file}: {e}")
            continue

    logging.info("===== Selesai proses ingest ke ClickHouse =====")


if __name__ == "__main__":
    ingest_csv_to_clickhouse()
