from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from catalog.models import (
    Author,
    Publisher,
    Category,
    Book,
    BookItem,
    BorrowRequest,
    Loan,
)


class Command(BaseCommand):
    help = "Generate admin dashboard statistics"

    def handle(self, *args, **options):
        stats = {}

        # Basic counts
        stats["total_books"] = Book.objects.count()
        stats["total_authors"] = Author.objects.count()
        stats["total_publishers"] = Publisher.objects.count()
        stats["total_categories"] = Category.objects.count()
        stats["total_book_items"] = BookItem.objects.count()
        stats["total_users"] = User.objects.filter(is_active=True).count()

        # Book items by status
        stats["available_items"] = BookItem.objects.filter(
            status="AVAILABLE"
        ).count()
        stats["loaned_items"] = BookItem.objects.filter(
            status="LOANED"
        ).count()
        stats["reserved_items"] = BookItem.objects.filter(
            status="RESERVED"
        ).count()
        stats["damaged_items"] = BookItem.objects.filter(
            status="DAMAGED"
        ).count()
        stats["lost_items"] = BookItem.objects.filter(status="LOST").count()

        # Borrow requests by status
        stats["pending_requests"] = BorrowRequest.objects.filter(
            status="PENDING"
        ).count()
        stats["approved_requests"] = BorrowRequest.objects.filter(
            status="APPROVED"
        ).count()
        stats["rejected_requests"] = BorrowRequest.objects.filter(
            status="REJECTED"
        ).count()

        # Loans by status
        stats["active_loans"] = Loan.objects.filter(status="BORROWED").count()
        stats["overdue_loans"] = Loan.objects.filter(status="OVERDUE").count()
        stats["returned_loans"] = Loan.objects.filter(
            status="RETURNED"
        ).count()

        # Recent activity (last 30 days)
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        stats["new_books_30d"] = Book.objects.filter(
            created_at__gte=thirty_days_ago
        ).count()
        stats["new_requests_30d"] = BorrowRequest.objects.filter(
            created_at__gte=thirty_days_ago
        ).count()
        stats["new_users_30d"] = User.objects.filter(
            date_joined__gte=thirty_days_ago
        ).count()

        # Popular books (most borrowed)
        popular_books = (
            Book.objects.filter(requested_items__request__status="APPROVED")
            .distinct()
            .order_by("-requested_items__quantity")[:5]
        )

        # Output statistics
        self.stdout.write(
            self.style.SUCCESS("=== LIBRARY MANAGEMENT STATISTICS ===")
        )
        self.stdout.write(f'Total Books: {stats["total_books"]}')
        self.stdout.write(f'Total Authors: {stats["total_authors"]}')
        self.stdout.write(f'Total Publishers: {stats["total_publishers"]}')
        self.stdout.write(f'Total Categories: {stats["total_categories"]}')
        self.stdout.write(f'Total Book Items: {stats["total_book_items"]}')
        self.stdout.write(f'Active Users: {stats["total_users"]}')

        self.stdout.write(self.style.SUCCESS("\n=== BOOK ITEM STATUS ==="))
        self.stdout.write(f'Available: {stats["available_items"]}')
        self.stdout.write(f'Loaned: {stats["loaned_items"]}')
        self.stdout.write(f'Reserved: {stats["reserved_items"]}')
        self.stdout.write(f'Damaged: {stats["damaged_items"]}')
        self.stdout.write(f'Lost: {stats["lost_items"]}')

        self.stdout.write(self.style.SUCCESS("\n=== BORROW REQUESTS ==="))
        self.stdout.write(f'Pending: {stats["pending_requests"]}')
        self.stdout.write(f'Approved: {stats["approved_requests"]}')
        self.stdout.write(f'Rejected: {stats["rejected_requests"]}')

        self.stdout.write(self.style.SUCCESS("\n=== LOANS ==="))
        self.stdout.write(f'Active: {stats["active_loans"]}')
        self.stdout.write(f'Overdue: {stats["overdue_loans"]}')
        self.stdout.write(f'Returned: {stats["returned_loans"]}')

        self.stdout.write(
            self.style.SUCCESS("\n=== RECENT ACTIVITY (30 days) ===")
        )
        self.stdout.write(f'New Books: {stats["new_books_30d"]}')
        self.stdout.write(f'New Requests: {stats["new_requests_30d"]}')
        self.stdout.write(f'New Users: {stats["new_users_30d"]}')

        self.stdout.write(self.style.SUCCESS("\n=== POPULAR BOOKS ==="))
        for i, book in enumerate(popular_books, 1):
            authors_list = list(book.authors.all())
            authors_str = ", ".join(author.name for author in authors_list)
            self.stdout.write(f"{i}. {book.title} by {authors_str}")

        if not popular_books:
            self.stdout.write("No popular books data available yet.")

        self.stdout.write(
            self.style.SUCCESS("Statistics completed successfully!")
        )
