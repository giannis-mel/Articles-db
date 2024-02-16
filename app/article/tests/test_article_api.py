from django.utils import timezone
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Article, User
from article.serializers import ArticleSerializer

ARTICLES_URL = reverse('article:article-list')

def create_article(user, **params):
    """Create and return a sample article, associating it with the given user as an author."""
    defaults = {
        'title': 'Sample Article Title',
        'abstract': 'Sample abstract of the article.',
        'publication_date': timezone.now().date(),
    }
    defaults.update(params)

    # Create the article instance
    article = Article.objects.create(**defaults)

    # Add the provided user as an author of the article
    article.authors.add(user)

    return article


class PublicArticleAPITests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to access the API."""
        res = self.client.get(ARTICLES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateArticleApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='superman@example.com',
            password='testpass123',
            name='Clark Kent'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_articles(self):
        """Test retrieving a list of articles."""
        create_article(user=self.user)
        create_article(user=self.user)

        res = self.client.get(ARTICLES_URL)
        articles = Article.objects.all().order_by('-publication_date', 'id').distinct()
        serializer = ArticleSerializer(articles, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_articles_one_author(self):
        """Test retrieving a list of articles filtered by a specific author."""
        # Create another user and an article by this user
        other_user = get_user_model().objects.create_user(
            email='hulk@example.com',
            password='testpass1234',
            name='Bruce Banner'
        )
        create_article(user=other_user)

        # Create an article by the original user
        create_article(user=self.user)

        # Request articles by the original user
        res = self.client.get(ARTICLES_URL, {'authors': self.user.id})

        # Get articles from the database that match the filter criteria
        articles = Article.objects.filter(authors=self.user).order_by('-publication_date', 'id').distinct()
        serializer = ArticleSerializer(articles, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), len(serializer.data))  # Validate the count of articles


        # Debug for article retrieval
        # for article in Article.objects.all():
        #     print(f"Article: {article.title}, Authors: {[author.name for author in article.authors.all()]}")
        # print(res.data)
        # print(serializer.data)

        self.assertEqual(res.data, serializer.data)


