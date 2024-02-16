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

from core.models import Article
from article import serializers  # Make sure this points to your article serializers

@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'authors',
                OpenApiTypes.STR,
                description='Comma separated list of author IDs to filter',
            ),
            # Include other filters as required
        ]
    )
)
class ArticleViewSet(viewsets.ModelViewSet):
    """View for managing article APIs."""
    serializer_class = serializers.ArticleDetailSerializer  # Update with your ArticleDetailSerializer
    queryset = Article.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def _params_to_ints(self, qs):
        """Convert a list of strings to integers."""
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        """
        Retrieve articles with optional filtering by year, month, and authors.
        """
        queryset = super().get_queryset()
        year = self.request.query_params.get('year')
        month = self.request.query_params.get('month')
        authors = self.request.query_params.get('authors')

        # Filter by year if provided
        if year:
            queryset = queryset.filter(publication_date__year=year)

        # Filter by month if provided
        if month:
            queryset = queryset.filter(publication_date__month=month)

        # Filter by authors if provided
        if authors:
            author_ids = self._params_to_ints(authors)
            queryset = queryset.filter(authors__id__in=author_ids)

        return queryset.order_by('-publication_date', 'id').distinct()

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action == 'list':
            return serializers.ArticleSerializer  # Update with your ArticleSerializer for list view
        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new article."""
        serializer.save(authors=[self.request.user])  # Add the authenticated user as an author

# Add other ViewSets or views if needed
