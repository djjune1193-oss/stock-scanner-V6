from pathlib import Path
from scanner.run_scanner import run_scanner
from scanner.build_double_bottom_signals import build_double_bottom_signals

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PATH = BASE_DIR / "scanner" / "data" / "all_data.parquet"
DATA_PATH.parent.mkdir(parents=True, exist_ok=True)  # ensure folder exists

def run_full_scan():
    print("Running full scanner...")
    run_scanner()  # pass path to scanner if needed

    print("Running double bottom signals...")
    build_double_bottom_signals()

    print("Full scan + signals complete!")
