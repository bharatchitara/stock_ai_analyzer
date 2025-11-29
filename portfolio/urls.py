from django.urls import path
from . import views

app_name = 'portfolio'

urlpatterns = [
    path('', views.portfolio_dashboard, name='dashboard'),
    path('add-holding/', views.add_holding, name='add_holding'),
    path('remove-holding/<int:holding_id>/', views.remove_holding, name='remove_holding'),
    path('update-holding/<int:holding_id>/', views.update_holding, name='update_holding'),
    path('holding/<int:holding_id>/', views.holding_detail, name='holding_detail'),
    path('analytics/', views.portfolio_analytics, name='analytics'),
    path('search-stocks/', views.search_stocks, name='search_stocks'),
    path('import/', views.import_portfolio, name='import_portfolio'),
    path('import/summary/', views.import_summary, name='import_summary'),
    path('import/sample-csv/', views.download_sample_csv, name='download_sample_csv'),
    path('refresh-prices/', views.refresh_stock_prices, name='refresh_prices'),
    path('analyze/', views.analyze_portfolio, name='analyze_portfolio'),
    path('analysis-results/', views.analysis_results, name='analysis_results'),
]