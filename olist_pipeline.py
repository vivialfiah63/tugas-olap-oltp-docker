import subprocess
import sys
from prefect import flow, task, serve
from prefect.client.schemas.schedules import CronSchedule
from prefect.logging import get_run_logger

# =====================================================================
# SESUAIKAN PATH INI dengan lokasi file di komputer kamu
# =====================================================================
PYTHON_EXE = sys.executable

PATH_INGEST_POSTGRES = r"C:\Nusacode\pertemuan 3\ingest_to_db.py"
PATH_INGEST_CLICKHOUSE = r"C:\Nusacode\pertemuan4\ingest_to_clickhouse.py"
PATH_DBT_PROJECT = r"C:\Nusacode\pertemuan4\olist_analytics"


# =====================================================================
# TASK 1: Extract + Load ke OLTP (Postgres)
# =====================================================================
@task(name="extract-load-postgres", retries=1, retry_delay_seconds=10)
def extract_load_postgres():
    logger = get_run_logger()
    logger.info("Menjalankan ingest CSV -> PostgreSQL ...")

    result = subprocess.run(
        [PYTHON_EXE, PATH_INGEST_POSTGRES],
        capture_output=True,
        text=True
    )

    logger.info(result.stdout)
    if result.returncode != 0:
        logger.error(result.stderr)
        raise Exception("Gagal ingest ke PostgreSQL")

    logger.info("Selesai ingest ke PostgreSQL.")


# =====================================================================
# TASK 2: Load raw data ke OLAP (ClickHouse) - bronze layer
# =====================================================================
@task(name="load-clickhouse-raw", retries=1, retry_delay_seconds=10)
def load_clickhouse_raw():
    logger = get_run_logger()
    logger.info("Menjalankan ingest CSV -> ClickHouse (raw) ...")

    result = subprocess.run(
        [PYTHON_EXE, PATH_INGEST_CLICKHOUSE],
        capture_output=True,
        text=True
    )

    logger.info(result.stdout)
    if result.returncode != 0:
        logger.error(result.stderr)
        raise Exception("Gagal ingest ke ClickHouse")

    logger.info("Selesai ingest ke ClickHouse.")


# =====================================================================
# TASK 3: Transform pakai dbt (silver -> gold)
# =====================================================================
@task(name="dbt-transform", retries=1, retry_delay_seconds=10)
def run_dbt_transform():
    logger = get_run_logger()
    logger.info("Menjalankan dbt run (silver + gold) ...")

    result = subprocess.run(
        ["dbt", "run"],
        cwd=PATH_DBT_PROJECT,
        capture_output=True,
        text=True,
        shell=True
    )

    logger.info(result.stdout)
    if result.returncode != 0:
        logger.error(result.stderr)
        raise Exception("Gagal menjalankan dbt run")

    logger.info("Selesai menjalankan dbt transform.")


# =====================================================================
# FLOW UTAMA: menyatukan semua tahap ETL/ELT
# =====================================================================
@flow(name="olist-etl-elt-pipeline", log_prints=True)
def olist_pipeline():
    print("===== MEMULAI PIPELINE OLIST =====")

    extract_load_postgres()
    load_clickhouse_raw()
    run_dbt_transform()

    print("===== PIPELINE SELESAI =====")


# =====================================================================
# DEPLOY DENGAN SCHEDULE (bagian wajib: scheduling/orchestration)
# =====================================================================
if __name__ == "__main__":
    # Jadwal: setiap hari jam 02:00 pagi waktu Jakarta
    # Format cron: menit jam tanggal bulan hari -> "0 2 * * *" = jam 02:00 tiap hari
    SCHEDULE = [CronSchedule(cron="*/10 * * * *", timezone="Asia/Jakarta")]

    serve(
        olist_pipeline.to_deployment(
            name="olist-etl-elt-scheduled",
            schedules=SCHEDULE
        )
    )
