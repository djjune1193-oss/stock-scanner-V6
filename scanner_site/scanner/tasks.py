from .run_scanner import run_scanner
from .build_double_bottom_signals import build_double_bottom_signals
def run_scanner_logic():
    print("Running scheduled scanner")
    run_scanner()
    build_double_bottom_signals()
    print( "double_bottom_completed") 
