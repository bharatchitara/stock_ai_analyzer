from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('news/', views.news_list, name='news_list'),
    path('news/<int:news_id>/', views.news_detail, name='news_detail'),
    path('recommendations/', views.recommendations_list, name='recommendations'),
    path('watchlist/', views.watchlist, name='watchlist'),
    path('trading-signals/', views.trading_signals, name='trading_signals'),
    
    # API endpoints
    path('api/sentiment-chart/', views.sentiment_chart_data, name='sentiment_chart_data'),
    path('api/recommendation-chart/', views.recommendation_chart_data, name='recommendation_chart_data'),
    path('api/news-timeline/', views.news_timeline_data, name='news_timeline_data'),
    path('api/run-news-collection/', views.run_news_collection, name='run_news_collection'),
    path('api/check-collection-status/', views.check_collection_status, name='check_collection_status'),
]