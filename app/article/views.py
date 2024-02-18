"""
Views for the article APIs.
"""
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)
from rest_framework import viewsets, mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model

from core.models import Article, Author, Tag
from article import serializers  # Make sure this points to your article serializers

User = get_user_model()

@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter('year', OpenApiTypes.INT, description='Year to filter'),
            OpenApiParameter('month', OpenApiTypes.INT, description='Month to filter'),
            OpenApiParameter('authors', OpenApiTypes.STR, description='Comma separated list of author IDs to filter'),
            OpenApiParameter('tags', OpenApiTypes.STR, description='Comma separated list of tag names to filter'),
            # OpenApiParameter('keyword', OpenApiTypes.STR, description='Keyword to search in title and abstract'),
            # Add other parameters as needed
        ]
    )
)
class ArticleViewSet(viewsets.ModelViewSet):
    """View for managing article APIs."""
    serializer_class = serializers.ArticleDetailSerializer
    queryset = Article.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def _params_to_ints(self, qs):
        """Convert a list of strings to integers."""
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        queryset = super().get_queryset()
        year = self.request.query_params.get('year')
        month = self.request.query_params.get('month')
        author_names = self.request.query_params.get('authors')
        tag_names = self.request.query_params.get('tags')

        # Filter by year if provided
        if year:
            queryset = queryset.filter(publication_date__year=year)

        # Filter by month if provided
        if month:
            queryset = queryset.filter(publication_date__month=month)

        # Filter by authors if provided
        if author_names:
            author_names = author_names.split(',')
            queryset = queryset.filter(authors__name__in=author_names)

        # Filter by tags if provided
        if tag_names:
            tag_names = tag_names.split(',')
            queryset = queryset.filter(tags__name__in=tag_names)

        return queryset.distinct().order_by('-publication_date')

    def perform_create(self, serializer):
        author_names = self.request.data.get('author_names', [])
        if not isinstance(author_names, list):
            author_names = [author_names]

        existing_authors = []
        for author_name in author_names:
            # Create author if not exists
            author_obj, created = Author.objects.get_or_create(name=author_name)
            existing_authors.append(author_obj)

        serializer.save()
        serializer.instance.authors.set(existing_authors)
        serializer.save(createdBy=self.request.user)