import inspect
import random
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Article, Author, Tag, User
from article.serializers import ArticleSerializer

from datetime import date, timedelta

ARTICLES_URL = reverse('article:article-list')


def test_log(response, serializer, user=None):
    # Get the name of the calling test method
    calling_test_method = inspect.stack()[1].function
    print(f"\n- - - - - Logging for Test: {calling_test_method} - - - - -\n")

    # Print current user if given
    if user:
        print(f"\nCurrent user is: {user.name}\n")

    # Debug for article retrieval
    print("\n\n- - - - -Current view of the db- - - - -\n\n")
    for article in Article.objects.all():
        print(f"Article: {article.title}, Authors: {[author.name for author in article.authors.all()]}")

    if response:
        print("\n\n- - - - -Response data- - - - -\n\n")
        print(response.data)
    if serializer:
        print("\n\n- - - - -Serializer data- - - - -\n\n")
        print(serializer.data)

def create_test_users():
    users = [
        get_user_model().objects.create_user(
            email='spiderman@example.com',
            password='testpass123',
            name='Peter Parker'
        ),
        get_user_model().objects.create_user(
            email='ironman@example.com',
            password='testpass456',
            name='Tony Stark'
        ),
    ]
    return users

def create_test_articles(users):
    number_of_articles = 4
    dates = [date.today() - timedelta(days=i) for i in range(number_of_articles)]
    titles = ["Article Title " + str(i+1) for i in range(number_of_articles)]
    abstracts = ["Abstract " + str(i+1) for i in range(number_of_articles)]
    author_names = ["Author " + str(i+1) for i in range(number_of_articles)]

    for i in range(number_of_articles):
        user = random.choice(users)

        # Correct field name for referencing the user
        article = Article.objects.create(
            title=titles[i],
            abstract=abstracts[i],
            publication_date=dates[i],
            createdBy=user
        )

        for name in author_names:
            author, created = Author.objects.get_or_create(name=name)
            if random.choice([True, False]):
                article.authors.add(author)

def create_article(user, **params):
    """
    Create and return a sample article, associating it with the specified user.
    The function also handles optional authors and tags passed in params.
    :param user: User object or user ID who is creating the article
    :param params: Article parameters like title, abstract, authors, tags, etc.
    """
    # Extract authors and tags from params if they exist
    authors = params.pop('authors', [])
    tags = params.pop('tags', [])

    # Create the article
    defaults = {
        'title': 'Sample Article Title',
        'abstract': 'Sample abstract of the article.',
        'publication_date': timezone.now().date(),
        'createdBy': user
    }
    defaults.update(params)

    article = Article.objects.create(**defaults)

    # Associate the provided authors with the article
    for author_id in authors:
        author, created = Author.objects.get_or_create(id=author_id)
        article.authors.add(author)

    # Associate the provided tags with the article
    for tag_id in tags:
        tag, created = Tag.objects.get_or_create(id=tag_id)
        article.tags.add(tag)

    return article

class PublicArticleAPITests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to access the API."""
        response = self.client.get(ARTICLES_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateArticleApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        users = create_test_users()
        create_test_articles(users)
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

        response = self.client.get(ARTICLES_URL)
        articles = Article.objects.all().order_by('-publication_date', 'id').distinct()
        serializer = ArticleSerializer(articles, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_retrieve_articles_one_author(self):
        """Test retrieving a list of articles filtered by a specific author."""
        # Create an author
        author1 = Author.objects.create(name='Steven Rogers')

        # Create an article by the author
        create_article(user=self.user, authors=[author1.id])

        # Perform a filter by the author
        response = self.client.get(ARTICLES_URL, {'authors': author1.name})

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Fetch articles from the database that match the filter criteria
        articles = Article.objects.filter(authors=author1).order_by('-publication_date', 'id').distinct()

        # Check if the count of articles is correct
        self.assertEqual(len(response.data), len(articles))

        # Check if the returned articles are correct
        response_article_ids = {article_data['id'] for article_data in response.data}
        db_article_ids = {str(article.id) for article in articles}
        self.assertTrue(response_article_ids.issubset(db_article_ids))



    def test_retrieve_articles_multiple_authors(self):
        """Test retrieving a list of articles with multiple authors."""
        # Create two new authors
        author1 = Author.objects.create(name='Steven Rogers')
        author2 = Author.objects.create(name='Wade Wilson')

        # Creating an article with a single author
        create_article(user=self.user, authors=[author1.id], title="Single Author Article", abstract="An abstract.")

        # Creating an article with multiple authors
        create_article(user=self.user, authors=[author1.id, author2.id], title="Multiple Authors Article", abstract="Another abstract.")

        # Perform a filter by the common author (e.g., author1)
        response = self.client.get(ARTICLES_URL, {'authors': author1.name})

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Fetch articles from the database that match the filter criteria
        articles = Article.objects.filter(authors=author1).order_by('-publication_date', 'id').distinct()

        # Check if the count of articles is correct
        self.assertEqual(len(response.data), len(articles))

        # Check if the returned articles are correct
        response_article_ids = {article_data['id'] for article_data in response.data}
        db_article_ids = {str(article.id) for article in articles}
        self.assertTrue(response_article_ids.issubset(db_article_ids))

    def test_create_article_with_tags(self):
        """Test creating an article with tags."""
        tags = ['Tech', 'Innovation']
        payload = {
            'title': 'Tech Trends',
            'abstract': 'Article about upcoming technology trends.',
            'publication_date': timezone.now().date().isoformat(),
            'tags': [{'name': tag} for tag in tags],
            'author_names': [self.user.name],
        }
        response = self.client.post(ARTICLES_URL, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        article = Article.objects.get(id=response.data['id'])
        article_tags = [tag.name for tag in article.tags.all()]

        test_log(response, ArticleSerializer(article), self.user)

        self.assertEqual(article.title, "Tech Trends")

        # Modify the assertion to compare the tag names correctly
        response_tags = [tag_dict['name'] for tag_dict in response.data['tags']]
        self.assertEqual(sorted(article_tags), sorted(response_tags))


