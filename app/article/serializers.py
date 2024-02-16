"""
Serializers for article APIs
"""
from rest_framework import serializers

from core.models import (
    Article
)
# from core.models import Tag

class ArticleSerializer(serializers.ModelSerializer):
    """Serializer for articles."""
    # Uncomment the following line if you decide to use the Tag model
    # tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Article
        fields = ['id', 'title', 'abstract', 'publication_date', 'authors']  # Add 'tags' to the fields list if using Tag model
        read_only_fields = ['id']

class ArticleDetailSerializer(ArticleSerializer):
    """Serializer for article detail view."""

    class Meta(ArticleSerializer.Meta):
        fields = ArticleSerializer.Meta.fields

    # Uncomment the following methods if you decide to use the Tag model
    # def _get_or_create_tags(self, tags, article):
    #     """Handle getting or creating tags as needed."""
    #     for tag in tags:
    #         tag_obj, created = Tag.objects.get_or_create(**tag)
    #         article.tags.add(tag_obj)

    def create(self, validated_data):
        """Create an article."""
        # tags = validated_data.pop('tags', [])
        article = Article.objects.create(**validated_data)
        # self._get_or_create_tags(tags, article)

        return article

    def update(self, instance, validated_data):
        """Update an article."""
        # tags = validated_data.pop('tags', None)
        # if tags is not None:
        #     instance.tags.clear()
        #     self._get_or_create_tags(tags, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
