from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import ExtractMonth, ExtractDay
from datetime import date, timedelta
import calendar
import io

from .models import Book, BorrowRequest, Loan
from .models import Category
from .utils.exports import build_book_queryset, render_books_workbook


@staff_member_required
def admin_stats_api(request):
    data = {
        "basic": {
            "total_books": Book.objects.count(),
            "total_users": User.objects.filter(is_active=True).count(),
        },
        "requests": {
            "pending": BorrowRequest.objects.filter(
                status=BorrowRequest.Status.PENDING
            ).count(),
        },
        "loans": {
            "overdue": Loan.objects.filter(status=Loan.Status.OVERDUE).count(),
        },
    }
    return JsonResponse(data)


def _ago(dt):
    """Return a human-readable relative time like '5m ago'.

    Handles both naive and aware datetimes by converting naive values
    into the current timezone before subtraction.
    """
    if not dt:
        return "-"
    # Normalize dt to an aware datetime to avoid naive/aware subtraction errors
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    now = timezone.now()
    delta = now - dt
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return f"{seconds}s ago"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    return f"{days}d ago"


@staff_member_required
def admin_activity_api(request):
    activities = []

    recent_requests = BorrowRequest.objects.select_related("user").order_by(
        "-created_at"
    )[:5]
    for r in recent_requests:
        activities.append(
            {
                "timestamp": r.created_at,
                "message": f"Borrow request #{r.id} by {r.user}",
                "details": f"{r.items.count()} item(s) • Status: {r.status}",
                "ago": _ago(r.created_at),
            }
        )

    recent_books = Book.objects.order_by("-created_at")[:5]
    for b in recent_books:
        activities.append(
            {
                "timestamp": b.created_at,
                "message": f"New book: {b.title}",
                "details": f"Publisher: {b.publisher or '-'} • Year: {b.publish_year or '-'}",
                "ago": _ago(b.created_at),
            }
        )

    recent_loans = Loan.objects.select_related("book_item").order_by(
        "-created_at"
    )[:5]
    for loan in recent_loans:
        activities.append(
            {
                "timestamp": loan.created_at,
                "message": f"Loan #{loan.id} {loan.status}",
                "details": f"Item: {loan.book_item} • Due: {loan.due_date}",
                "ago": _ago(loan.created_at),
            }
        )

    # Sort mixed activities by timestamp desc and cap to 10
    activities.sort(
        key=lambda x: x.get("timestamp") or timezone.now(), reverse=True
    )
    activities = activities[:10]

    return JsonResponse({"activities": activities})


@staff_member_required
def admin_book_stats_api(request):
    """Return book-related statistics for charts (month/year scope).

    Query params:
    - period: 'month' (default) or 'year'
    - year: integer (defaults to current year)
    - month: 1-12 (required when period=month; defaults to current month)
    """
    now = timezone.now()
    period = (request.GET.get("period") or "month").lower()
    try:
        year = int(request.GET.get("year", now.year))
    except ValueError:
        year = now.year
    try:
        month = int(request.GET.get("month", now.month))
    except ValueError:
        month = now.month

    if period == "year":
        start = date(year, 1, 1)
        end = date(year + 1, 1, 1)
    else:
        # default to month
        month = max(1, min(12, month))
        start = date(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end = date(year, month, last_day) + timedelta(days=1)

    # Books per category (overall, not scoped to period)
    category_book_counts_qs = (
        Category.objects.annotate(total_books=Count("books", distinct=True))
        .values("id", "name", "total_books")
        .order_by("-total_books", "name")
    )
    category_book_counts = list(category_book_counts_qs)

    # Loans by category in the period
    loans_qs = (
        Loan.objects.filter(approved_from__gte=start, approved_from__lt=end)
        .values(
            "request_item__book__categories__id",
            "request_item__book__categories__name",
        )
        .annotate(total=Count("id"))
        .exclude(request_item__book__categories__id__isnull=True)
        .order_by("-total", "request_item__book__categories__name")
    )
    loans_by_category = [
        {
            "category_id": row["request_item__book__categories__id"],
            "category_name": row["request_item__book__categories__name"],
            "total": row["total"],
        }
        for row in loans_qs
    ]

    top_category = loans_by_category[0] if loans_by_category else None

    # Top books by loans in the period
    top_books_qs = (
        Loan.objects.filter(approved_from__gte=start, approved_from__lt=end)
        .values("request_item__book__id", "request_item__book__title")
        .annotate(total=Count("id"))
        .order_by("-total", "request_item__book__title")[:10]
    )
    top_books = [
        {
            "book_id": row["request_item__book__id"],
            "book_title": row["request_item__book__title"],
            "total": row["total"],
        }
        for row in top_books_qs
    ]

    # Time series: loans over time in selected period
    if period == "year":
        over_time_qs = (
            Loan.objects.filter(
                approved_from__gte=start, approved_from__lt=end
            )
            .annotate(month=ExtractMonth("approved_from"))
            .values("month")
            .annotate(total=Count("id"))
        )
        by_key = {row["month"]: row["total"] for row in over_time_qs}
        labels = [str(m) for m in range(1, 13)]
        values = [by_key.get(m, 0) for m in range(1, 13)]
        time_series = {
            "type": "by_month",
            "labels": labels,
            "values": values,
        }
    else:
        # month view: by day
        last_day = calendar.monthrange(year, month)[1]
        over_time_qs = (
            Loan.objects.filter(
                approved_from__gte=start, approved_from__lt=end
            )
            .annotate(day=ExtractDay("approved_from"))
            .values("day")
            .annotate(total=Count("id"))
        )
        by_key = {row["day"]: row["total"] for row in over_time_qs}
        labels = [str(d) for d in range(1, last_day + 1)]
        values = [by_key.get(d, 0) for d in range(1, last_day + 1)]
        time_series = {
            "type": "by_day",
            "labels": labels,
            "values": values,
        }

    # Top authors in the period
    top_authors_qs = (
        Loan.objects.filter(approved_from__gte=start, approved_from__lt=end)
        .values(
            "request_item__book__authors__id",
            "request_item__book__authors__name",
        )
        .annotate(total=Count("id"))
        .exclude(request_item__book__authors__id__isnull=True)
        .order_by("-total", "request_item__book__authors__name")[:10]
    )
    top_authors = [
        {
            "author_id": row["request_item__book__authors__id"],
            "author_name": row["request_item__book__authors__name"],
            "total": row["total"],
        }
        for row in top_authors_qs
    ]

    # Top publishers in the period
    top_publishers_qs = (
        Loan.objects.filter(approved_from__gte=start, approved_from__lt=end)
        .values(
            "request_item__book__publisher__id",
            "request_item__book__publisher__name",
        )
        .annotate(total=Count("id"))
        .exclude(request_item__book__publisher__id__isnull=True)
        .order_by("-total", "request_item__book__publisher__name")[:10]
    )
    top_publishers = [
        {
            "publisher_id": row["request_item__book__publisher__id"],
            "publisher_name": row["request_item__book__publisher__name"],
            "total": row["total"],
        }
        for row in top_publishers_qs
    ]

    # Loan status distribution in the period
    status_dist_qs = (
        Loan.objects.filter(approved_from__gte=start, approved_from__lt=end)
        .values("status")
        .annotate(total=Count("id"))
        .order_by("status")
    )
    status_distribution = [
        {"status": row["status"], "total": row["total"]}
        for row in status_dist_qs
    ]

    # Language distribution in the period
    language_dist_qs = (
        Loan.objects.filter(approved_from__gte=start, approved_from__lt=end)
        .values("request_item__book__language_code")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    language_distribution = [
        {
            "language": row["request_item__book__language_code"] or "Unknown",
            "total": row["total"],
        }
        for row in language_dist_qs
    ]

    data = {
        "period": {
            "type": "year" if period == "year" else "month",
            "year": year,
            "month": month if period != "year" else None,
            "start": start.isoformat(),
            "end_exclusive": end.isoformat(),
        },
        "category_book_counts": category_book_counts,
        "loans_by_category": loans_by_category,
        "top_category": top_category,
        "top_books": top_books,
        "time_series": time_series,
        "top_authors": top_authors,
        "top_publishers": top_publishers,
        "status_distribution": status_distribution,
        "language_distribution": language_distribution,
    }
    return JsonResponse(data)


@staff_member_required
def export_books_excel(request):
    """Xuất Excel danh sách sách theo tiêu chí tìm kiếm, có thể kèm sheet Items.

    Tham số GET:
    - Lọc: q, category_id, author_id, publisher_id, publish_year_from, publish_year_to,
            language, item_status, created_from, created_to, sort
    - columns: danh sách cột (phân tách bởi dấu phẩy); mặc định xem utils.exports.DEFAULT_BOOK_COLUMNS
    - include_items: 1/true để thêm sheet chi tiết bản sao (BookItems)
    - filename: tên file Excel (không kèm đuôi); mặc định books_export_YYYYMMDD_HHMMSS
    """
    include_items = (request.GET.get("include_items") or "").lower() in {
        "1",
        "true",
        "yes",
    }
    columns_param = (request.GET.get("columns") or "").strip()
    columns = (
        [c.strip() for c in columns_param.split(",") if c.strip()]
        if columns_param
        else None
    )

    # Build queryset & workbook
    qs = build_book_queryset(request.GET, include_items=include_items)
    wb = render_books_workbook(
        qs, columns=columns, include_items=include_items
    )

    # Serialize
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    ts = timezone.now().strftime("%Y%m%d_%H%M%S")
    base = (
        request.GET.get("filename") or f"books_export_{ts}"
    ).strip() or f"books_export_{ts}"
    resp = HttpResponse(
        buf.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = f'attachment; filename="{base}.xlsx"'
    return resp
