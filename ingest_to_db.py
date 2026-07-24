import os
import sys
import logging
from posixpath import split
from sqlalchemy import create_engine, text
import pandas as pd

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format = "%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    handlers = [
        logging.FileHandler("logs/ingest_to_db.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

DB_USER = "vivi"
DB_PASS = "bootcamp123"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "nusacode_db"

DB_URI = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

#DEFINISI TABLE CSV

DATASET_MAP = [
    ("dim_customer", "olist_customers_dataset.csv", "public.dim_customer", "DIM"),
    ("dim_geolocation", "olist_geolocation_dataset.csv", "public.dim_geolocation", "DIM"),
    ("dim_product", "olist_products_dataset.csv", "public.dim_product", "DIM"),
    ("dim_product_category", "product_category_name_translation.csv", "public.dim_product_category", "DIM"),
    ("dim_seller", "olist_sellers_dataset.csv", "public.dim_seller", "DIM"),
    ("fact_order", "olist_orders_dataset.csv", "public.fact_order", "FACT"),
    ("fact_order_item", "olist_order_items_dataset.csv", "public.fact_order_item", "FACT"),
    ("fact_order_payment", "olist_order_payments_dataset.csv", "public.fact_order_payment", "FACT"),
    ("fact_order_review", "olist_order_reviews_dataset.csv", "public.fact_order_review", "FACT")
]

ARCHIVE_DIR = os.path.join(os.path.dirname(__file__), "archive")

def drop_table_if_exists(engine, table_name: str):
    with engine.connect() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE;"))
        logging.info(f"Tabel {table_name} berhasil dihapus jika sudah ada")
        conn.commit()
        logging.info(f"Tabel {table_name} berhasil dihapus jika sudah ada")


def ingest_cvs_to_postgres():
    logging.info("===== Memulai proses ingest data ke PostgreSQL =====")

    try:
        engine = create_engine(DB_URI)
        logging.info(f"Sukses terhubung ke Database: {DB_HOST}")
    except Exception as e:
        logging.error(f"Gagal terhubung ke Database: {e}")
        raise

    os.makedirs(ARCHIVE_DIR, exist_ok=True)

    for label, csv_file, table_name, table_type in DATASET_MAP:
        csv_path = os.path.join(ARCHIVE_DIR, csv_file)
        logging.info(f"[START] Memproses file: {csv_file} ...")

        try:
            df = pd.read_csv(csv_path)
            logging.info(f"berhasil memuat {len(df)} baris dari data {csv_file}")

            drop_table_if_exists(engine, table_name)

            logging.info(f"Memulai proses ingest data ke tabel {table_name} ...")

            df.to_sql(
                name=table_name.split(".")[1],
                con=engine,
                schema=table_name.split(".")[0],
                index=False,
                chunksize=100,
                method='multi',
                if_exists='replace', 
            )
                
            logging.info(f"[DONE] Berhasil memuat data ke tabel {table_name} ...")

        except Exception as e:
            logging.error(f"gagal memuat {csv_file}: {e}")
            continue    


if __name__ == "__main__":
    ingest_cvs_to_postgres()    
