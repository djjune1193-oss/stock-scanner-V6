from django.urls import path
from . import views
from .views import sector_view, industry_detail_view, industry_rs_view, rs_alignment_dashboard, industry_detail_view_change
from .views import fundamentals_view

from django.contrib.auth import views as auth_views

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
    path("stochastic_short/", views.stochastic_short_view, name="stochastic_short"),
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
    path("rs_alignment/",views.rs_alignment_dashboard,name="rs_alignment"),
    path("sector_lbr/", views.sector_lbr_view, name="sector_lbr"),
    path("today/",views.industry_today_view,name="industry_today"),
    path("today/<str:industry_name>/",views.industry_today_detail,name="industry_today_detail"),
    path("ma_structure/",views.ma_structure_view,name="ma_structure"),
    path('keltner_scan/', views.keltner_scan, name='keltner_scan'),
    path("futures/", views.futures_view, name="futures"),
    path("fib_scan/", views.fib_retracement_scan, name="fib_scan"),
    path('industry_dashboard/',views.industry_dashboard,name='industry_dashboard'),
    path("login/",auth_views.LoginView.as_view(template_name="auth/login.html"),name="login"),
    path("logout/",auth_views.LogoutView.as_view(),name="logout"),
    path("signup/",views.signup_view,name="signup"),
    path("verify-email/", views.verify_email, name="verify_email"),
    path("resend-code/", views.resend_code, name="resend_code"),
    path("forgot-password/", views.forgot_password, name="forgot_password"),
    path("reset-password-verify/", views.reset_password_verify, name="reset_password_verify"),
    path("new-password/", views.new_password, name="new_password"),
    
]
