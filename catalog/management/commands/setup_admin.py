from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.management import call_command
from catalog.models import Author, Publisher, Category, Book, BookItem
import random


class Command(BaseCommand):
    help = "Setup admin interface with sample data for testing"

    def add_arguments(self, parser):
        parser.add_argument(
            "--create-superuser",
            action="store_true",
            help="Create a superuser account",
        )
        parser.add_argument(
            "--username",
            type=str,
            default="admin",
            help="Superuser username (default: admin)",
        )
        parser.add_argument(
            "--email",
            type=str,
            default="admin@library.com",
            help="Superuser email (default: admin@library.com)",
        )
        parser.add_argument(
            "--password",
            type=str,
            default="admin123",
            help="Superuser password (default: admin123)",
        )
        parser.add_argument(
            "--sample-data",
            action="store_true",
            help="Create sample data for testing",
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("=== SETTING UP ADMIN INTERFACE ===")
        )

        # Create superuser if requested
        if options["create_superuser"]:
            username = options["username"]
            email = options["email"]
            password = options["password"]

            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(f"Superuser {username} already exists")
                )
            else:
                User.objects.create_superuser(
                    username=username, email=email, password=password
                )
                self.stdout.write(
                    self.style.SUCCESS(f"Created superuser: {username}")
                )
                self.stdout.write(f"  Email: {email}")
                self.stdout.write(f"  Password: {password}")

        # Create sample data if requested
        if options["sample_data"]:
            self.stdout.write(
                self.style.SUCCESS("\n=== CREATING SAMPLE DATA ===")
            )
            self.create_sample_data()

        # Run migrations to ensure everything is set up
        self.stdout.write(self.style.SUCCESS("\n=== RUNNING MIGRATIONS ==="))
        call_command("migrate", verbosity=0)

        self.stdout.write(self.style.SUCCESS("\n=== SETUP COMPLETE ==="))
        self.stdout.write("You can now access the admin interface at: /admin/")
        if options["create_superuser"]:
            self.stdout.write(
                f'Login with username: {options["username"]} and password: {options["password"]}'
            )

    def create_sample_data(self):
        # Create sample authors
        authors_data = [
            {
                "name": "J.K. Rowling",
                "biography": "British author, best known for the Harry Potter series",
            },
            {
                "name": "George R.R. Martin",
                "biography": "American novelist and short story writer",
            },
            {
                "name": "Stephen King",
                "biography": "American author of horror, supernatural fiction",
            },
            {
                "name": "Agatha Christie",
                "biography": "English writer known for detective novels",
            },
            {
                "name": "Isaac Asimov",
                "biography": "American writer and professor of biochemistry",
            },
        ]

        authors = []
        for author_data in authors_data:
            author, created = Author.objects.get_or_create(
                name=author_data["name"],
                defaults={"biography": author_data["biography"]},
            )
            authors.append(author)
            if created:
                self.stdout.write(f"  Created author: {author.name}")

        # Create sample publishers
        publishers_data = [
            {"name": "Penguin Random House", "founded_year": 2013},
            {"name": "HarperCollins", "founded_year": 1989},
            {"name": "Simon & Schuster", "founded_year": 1924},
            {"name": "Macmillan Publishers", "founded_year": 1843},
            {"name": "Hachette Book Group", "founded_year": 2006},
        ]

        publishers = []
        for pub_data in publishers_data:
            publisher, created = Publisher.objects.get_or_create(
                name=pub_data["name"],
                defaults={"founded_year": pub_data["founded_year"]},
            )
            publishers.append(publisher)
            if created:
                self.stdout.write(f"  Created publisher: {publisher.name}")

        # Create sample categories
        categories_data = [
            {"name": "Fiction", "slug": "fiction"},
            {"name": "Non-Fiction", "slug": "non-fiction"},
            {"name": "Science Fiction", "slug": "science-fiction"},
            {"name": "Mystery & Thriller", "slug": "mystery-thriller"},
            {"name": "Romance", "slug": "romance"},
            {"name": "Biography", "slug": "biography"},
            {"name": "History", "slug": "history"},
            {"name": "Technology", "slug": "technology"},
        ]

        categories = []
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data["name"], defaults={"slug": cat_data["slug"]}
            )
            categories.append(category)
            if created:
                self.stdout.write(f"  Created category: {category.name}")

        # Create sample books
        books_data = [
            {
                "title": "Harry Potter and the Philosopher's Stone",
                "description": "The first book in the Harry Potter series",
                "isbn13": "9780747532699",
                "publish_year": 1997,
                "pages": 223,
                "language_code": "en",
            },
            {
                "title": "A Game of Thrones",
                "description": "The first novel in A Song of Ice and Fire series",
                "isbn13": "9780553103540",
                "publish_year": 1996,
                "pages": 694,
                "language_code": "en",
            },
            {
                "title": "The Shining",
                "description": "Horror novel about a haunted hotel",
                "isbn13": "9780307743657",
                "publish_year": 1977,
                "pages": 447,
                "language_code": "en",
            },
            {
                "title": "Murder on the Orient Express",
                "description": "Detective novel featuring Hercule Poirot",
                "isbn13": "9780062693662",
                "publish_year": 1934,
                "pages": 256,
                "language_code": "en",
            },
            {
                "title": "Foundation",
                "description": "Science fiction novel about a galactic empire",
                "isbn13": "9780553293357",
                "publish_year": 1951,
                "pages": 244,
                "language_code": "en",
            },
        ]

        for i, book_data in enumerate(books_data):
            book, created = Book.objects.get_or_create(
                title=book_data["title"],
                defaults={**book_data, "publisher": random.choice(publishers)},
            )

            if created:
                self.stdout.write(f"  Created book: {book.title}")

                # Add author relationship
                book.authors.add(authors[i])

                # Add random categories
                book.categories.add(random.choice(categories))

                # Create book items
                for j in range(random.randint(2, 5)):
                    BookItem.objects.create(
                        book=book,
                        barcode=f"BK{book.id:04d}{j + 1:02d}",
                        status="AVAILABLE",
                        location_code=f"A{random.randint(1, 10)}-{random.randint(1, 20)}",
                    )

        self.stdout.write(
            self.style.SUCCESS("Sample data created successfully!")
        )
