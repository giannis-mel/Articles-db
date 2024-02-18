"""
Serializers for article APIs
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from core.models import (
    Article,
    Tag,
    Author
)

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['name']

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['name']


class ArticleSerializer(serializers.ModelSerializer):
    authors = AuthorSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, required=False)
    created_by = serializers.ReadOnlyField(source='createdBy.name')

    class Meta:
        model = Article
        fields = ['id', 'title', 'abstract', 'publication_date', 'authors', 'tags', 'created_by']
        read_only_fields = ['id', 'created_by']


class ArticleDetailSerializer(ArticleSerializer):
    """Serializer for article detail view."""

    class Meta(ArticleSerializer.Meta):
        fields = ArticleSerializer.Meta.fields

    def _get_or_create_tags(self, tags, article):
        """Handle getting or creating tags as needed."""
        for tag_name in tags:
            tag_obj, created = Tag.objects.get_or_create(name=tag_name)
            article.tags.add(tag_obj)

    def _get_or_create_authors(self, author_names, article):
        """Handle getting or creating authors as needed."""
        for author_name in author_names:
            author_obj, created = Author.objects.get_or_create(name=author_name)
            article.authors.add(author_obj)

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        author_names = validated_data.pop('authors', [])
        created_by = self.context['request'].user  # Get the user from the request context
        article = Article.objects.create(**validated_data, createdBy=created_by)
        self._get_or_create_tags(tags, article)
        self._get_or_create_authors(author_names, article)
        return article

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        author_names = validated_data.pop('authors', None)
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)
        if author_names is not None:
            instance.authors.clear()
            self._get_or_create_authors(author_names, instance)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance