"""
URL mappings for the article app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from article import views  # Make sure to import your views from the article app

router = DefaultRouter()
router.register('articles', views.ArticleViewSet)  # Register ArticleViewSet with the router

app_name = 'article'

urlpatterns = [
    path('', include(router.urls)),
]
