import pandas as pd
import requests
import json
from sqlalchemy import create_engine
import clickhouse_connect


api_url = "https://dummyjson.com/products"

# try:

print(f"Mencoba mengambil data dari: {api_url}...")
response = requests.get(api_url, timeout=5)
response.raise_for_status()
raw_data = response.json()
print(f"Sukses ! Ditemukan {len(raw_data['products'])} data dari API")

# except Exception as e:
#     print(f" Gagal mengakses API: {e}")
#     print("Menggunakan file fallback lokal 'data_dummy.json'...")
#     with open("../data_dummy.json", "r", encoding="utf-8") as f:
#         raw_data = json.load(f)
#     print(f"Sukses memuat {len(raw_data['products'])} data dari file fallback.")

df = pd.DataFrame(raw_data['products'])
print(df.info())

filtered_df = df[["id","title","stock","category","price","rating"]]

print(filtered_df.info())
print(filtered_df.head(5))

df_rating = filtered_df[filtered_df["rating"] >= 4].copy()
print(df_rating.info())
print(df_rating.head(5))

df_final = df_rating.rename(columns={
    "id":"id_produk", 
    "title":"nama_produk",
    "stock":"stok",
    "category":"kategori",
    "price":"harga",
    "rating":"skor_rating"})

df_final['nama_produk'] = df_final['nama_produk'].str.upper()
print(df_final.head(6))
print(f"\nTotal baris siap di-load: {len(df_final)}")

print("\n--- Loading ke PostgreSQL ---")
pg_user = "vivi"
pg_password = "bootcamp123"
pg_host = "localhost"
pg_port = "5432"
pg_db = "nusacode_db"

pg_engine = create_engine(
    f"postgresql+psycopg2://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"
)

df_final.to_sql(
    "produk_rating",       
    con=pg_engine,
    if_exists="replace",   
    index=False
)
print(f"Sukses! {len(df_final)} baris masuk ke tabel 'produk_rating' di PostgreSQL.")

print("\n--- Loading ke ClickHouse ---")

ch_client = clickhouse_connect.get_client(
    host="localhost",
    port=8123,
    username="clickhousedev",
    password="adminpass123"
)
ch_client.command("""
CREATE TABLE IF NOT EXISTS produk_rating (
    id_produk Int64,
    nama_produk String,
    stok Int64,
    kategori String,
    harga Float64,
    skor_rating Float64
) ENGINE = MergeTree()
ORDER BY id_produk
""")

ch_client.insert_df("produk_rating", df_final)

print(f"Sukses! {len(df_final)} baris masuk ke tabel 'produk_rating' di ClickHouse.")