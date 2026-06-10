from .run_scanner import run_scanner
from .build_double_bottom_signals import build_double_bottom_signals
from .run_finviz import run_finviz
from .run_top_news import fetch_top_headlines
from .run_ticker_news import run_ticker_news_job
from pathlib import Path
from django.conf import settings


def run_scanner_logic():
    print("Running scheduled scanner")
    run_scanner()
    print("double_bottom_started")
    build_double_bottom_signals()
    print("double_bottom_completed")


def run_finviz_cron():
    run_finviz()

from .run_premarket import run_premarket_scan


def premarket_scanner():
    run_premarket_scan()


def run_top_news():
    fetch_top_headlines()

def run_ticker_news():
    run_ticker_news_job()
