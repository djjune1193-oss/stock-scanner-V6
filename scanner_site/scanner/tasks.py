from .run_scanner import run_scanner
from .build_double_bottom_signals import build_double_bottom_signals
from .run_finviz import run_finviz
def run_scanner_logic():
    print("Running scheduled scanner")
    run_scanner()
    print("double_bottom_started")
    build_double_bottom_signals()
    print( "double_bottom_completed") 



def run_finviz_cron():
    run_finviz()
