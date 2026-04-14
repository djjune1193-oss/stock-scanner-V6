from django.urls import path
from . import views
from .views import sector_view, industry_detail_view, industry_rs_view, rs_alignment_dashboard, industry_detail_view_change
from .views import fundamentals_view

urlpatterns = [
    path("", views.home, name="home"),
    path("refresh-scanner/", views.refresh_scanner, name="refresh_scanner"),
    path('scanner/', views.scanner_view, name='scanner'),  # Scanner tab
    path('flat_bollinger/', views.flat_bollinger_view, name='flat_bollinger'), # flat_bollinger
    path("hot_ten_day/", views.hot_ten_day_view, name="hot_ten_day"),
    path("sector/", views.sector_view, name="sector"),
    path("industry_weekly/", views.industry_weekly_view, name="industry_weekly"),
    path("double-bottom/", views.double_bottom_view, name="double-bottom"),
    path("turtle_soup/", views.turtle_soup_view, name="turtle_soup"),
    path("momentum_strength/", views.calculate_momentum_strength, name="momentum_strength"),
    path("chart/<str:ticker>/", views.equity_chart, name="equity_chart"),
    path("sector-chart/", views.sector_ma_chart, name="sector_chart"),
    path("industry_ranking/", views.get_industry_ranking, name="industry_ranking"),
    path("equity_ranking/", views.get_equity_ranking, name="equity_ranking"),
    path("metrics/", views.metrics_view, name="metrics"),
    path("base_breakout/", views.base_breakout_scanner, name="base_breakout"),
    path("breakout_21/", views.breakout_21_view, name="breakout_21"),
    path("documentation/", views.documentation, name="documentation"),
    path("industry/<str:industry_name>/", industry_detail_view_change, name="industry_detail"),
    path("fundamentals/", fundamentals_view, name="fundamentals"),
    path("industry_rs/", industry_rs_view, name="industry_rs"),
    path("industry/rs/<path:industry_name>/", industry_detail_view, name="industry_detail_rs"),
    path("rs_alignment/",views.rs_alignment_dashboard,name="rs_alignment_dashboard"),
    path("sector_lbr/", views.sector_lbr_view, name="sector_lbr"),
    path("today/",views.industry_today_view,name="industry_today"),
    path("today/<str:industry_name>/",views.industry_today_detail,name="industry_today_detail"),
    path("ma_structure/",views.ma_structure_view,name="ma_structure"),
]
