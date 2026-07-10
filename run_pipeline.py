# run_pipeline.py — Usage: python run_pipeline.py
import subprocess, sys, os, logging, time

BASE = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE, "pipeline.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

SCRIPTS = [
    ("data/raw/generate_data.py",                   "1/5  Generating synthetic dataset"),
    ("python/eda/01_eda_preprocessing.py",           "2/5  EDA & preprocessing"),
    ("python/segmentation/02_rfm_segmentation.py",  "3/5  RFM customer segmentation"),
    ("python/churn/03_churn_analysis.py",            "4/5  Churn prediction model"),
    ("python/forecasting/04_revenue_forecasting.py", "5/5  Revenue forecasting"),
]

def run_step(rel_path, label):
    abs_path = os.path.join(BASE, rel_path)
    log.info("START  %s", label)
    t0 = time.monotonic()

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"

    result = subprocess.run(
        [sys.executable, abs_path],
        capture_output=True, text=True, encoding="utf-8", env=env,
    )
    elapsed = time.monotonic() - t0

    if result.stdout.strip():
        for line in result.stdout.strip().splitlines():
            log.debug("  [stdout] %s", line)
    if result.stderr.strip():
        for line in result.stderr.strip().splitlines():
            log.warning("  [stderr] %s", line)

    if result.returncode != 0:
        log.error("FAILED %s  (exit code %d, %.1fs)", label, result.returncode, elapsed)
        raise RuntimeError(f"Pipeline aborted at step: {rel_path}")

    log.info("DONE   %s  (%.1fs)", label, elapsed)

def main():
    log.info("=" * 55)
    log.info("E-Commerce Analytics Pipeline — starting")
    log.info("=" * 55)

    t0 = time.monotonic()
    for rel, label in SCRIPTS:
        try:
            run_step(rel, label)
        except RuntimeError as exc:
            log.critical("%s", exc)
            sys.exit(1)

    log.info("=" * 55)
    log.info("Pipeline complete in %.1fs", time.monotonic() - t0)
    log.info("-> Open dashboard/dashboard.html in your browser")
    log.info("=" * 55)

if __name__ == "__main__":
    main()