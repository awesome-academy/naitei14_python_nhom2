from django.contrib import admin
from django.contrib import messages
from django.utils import timezone
from django import forms
from django.utils.html import format_html
from django.urls import reverse
from django.db import models
from django.forms import Textarea
from django.contrib.admin.helpers import ActionForm
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.sessions.models import Session
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import (
    Author,
    Publisher,
    Category,
    Book,
    BookAuthor,
    BookCategory,
    BookItem,
    BorrowRequest,
    BorrowRequestItem,
)


# Custom Admin Site Configuration
admin.site.site_header = "Library Management System"
admin.site.site_title = "Library Admin"
admin.site.index_title = "Welcome to Library Management"


# Inline classes for better relationship management
class BookAuthorInline(admin.TabularInline):
    model = BookAuthor
    extra = 1
    autocomplete_fields = ["author"]


class BookCategoryInline(admin.TabularInline):
    model = BookCategory
    extra = 1
    autocomplete_fields = ["category"]


class BookItemInline(admin.TabularInline):
    model = BookItem
    extra = 1
    readonly_fields = ["created_at"]


class BorrowRequestItemInline(admin.TabularInline):
    model = BorrowRequestItem
    extra = 0
    autocomplete_fields = [
        "book",
    ]
    fields = ("book", "quantity")
    show_change_link = True


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "birth_date",
        "death_date",
        "books_count",
        "created_at",
    ]
    list_filter = ["birth_date", "death_date", "created_at"]
    search_fields = ["name", "biography"]
    readonly_fields = ["created_at"]
    date_hierarchy = "created_at"
    list_per_page = 25

    fieldsets = (
        ("Basic Information", {"fields": ("name", "biography")}),
        (
            "Dates",
            {
                "fields": ("birth_date", "death_date", "created_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def books_count(self, obj):
        count = obj.books.count()
        url = (
            reverse("admin:catalog_book_changelist")
            + f"?authors__id__exact={obj.id}"
        )
        return format_html('<a href="{}">{} books</a>', url, count)

    books_count.short_description = "Books"


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "founded_year",
        "website_link",
        "books_count",
        "created_at",
    ]
    list_filter = ["founded_year", "created_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at"]
    date_hierarchy = "created_at"
    list_per_page = 25
    fieldsets = (
        ("Basic Information", {"fields": ("name", "description")}),
        (
            "Additional Info",
            {
                "fields": ("founded_year", "website", "created_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def website_link(self, obj):
        if obj.website:
            return format_html(
                '<a href="{}" target="_blank">{}</a>', obj.website, obj.website
            )
        return "-"

    website_link.short_description = "Website"

    def books_count(self, obj):
        count = obj.books.count()
        url = (
            reverse("admin:catalog_book_changelist")
            + f"?publisher__id__exact={obj.id}"
        )
        return format_html('<a href="{}">{} books</a>', url, count)

    books_count.short_description = "Books"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "parent", "books_count", "children_count"]
    list_filter = ["parent"]
    search_fields = ["name", "description", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    list_per_page = 25

    fieldsets = (
        ("Basic Information", {"fields": ("name", "slug", "description")}),
        (
            "Hierarchy",
            {
                "fields": ("parent",),
            },
        ),
    )

    def books_count(self, obj):
        count = obj.books.count()
        url = (
            reverse("admin:catalog_book_changelist")
            + f"?categories__id__exact={obj.id}"
        )
        return format_html('<a href="{}">{} books</a>', url, count)

    books_count.short_description = "Books"

    def children_count(self, obj):
        count = obj.children.count()
        return f"{count} subcategories"

    children_count.short_description = "Subcategories"


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "publisher",
        "publish_year",
        "pages",
        "isbn13",
        "language_code",
        "items_count",
        "created_at",
    ]
    list_filter = [
        "publisher",
        "publish_year",
        "language_code",
        "created_at",
        "categories",
    ]
    search_fields = ["title", "description", "isbn13"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "created_at"
    list_per_page = 25
    autocomplete_fields = ["publisher"]
    inlines = [BookAuthorInline, BookCategoryInline, BookItemInline]

    fieldsets = (
        ("Basic Information", {"fields": ("title", "description", "isbn13")}),
        (
            "Publication Details",
            {
                "fields": (
                    "publisher",
                    "publish_year",
                    "pages",
                    "language_code",
                )
            },
        ),
        ("Media", {"fields": ("cover_url",), "classes": ("collapse",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    formfield_overrides = {
        models.TextField: {"widget": Textarea(attrs={"rows": 4, "cols": 80})},
    }

    def items_count(self, obj):
        # Return plain count; BookItem changelist is not exposed in admin
        return obj.items.count()

    items_count.short_description = "Items"


class BookAuthorAdmin(admin.ModelAdmin):
    list_display = ["book", "author", "author_order"]
    list_filter = ["author_order"]
    search_fields = ["book__title", "author__name"]
    autocomplete_fields = ["book", "author"]
    list_per_page = 25


class BookCategoryAdmin(admin.ModelAdmin):
    list_display = ["book", "category"]
    search_fields = ["book__title", "category__name"]
    autocomplete_fields = ["book", "category"]
    list_per_page = 25


class BookItemAdmin(admin.ModelAdmin):
    list_display = [
        "book_title",
        "barcode",
        "status_colored",
        "location_code",
        "created_at",
    ]
    list_filter = ["status", "location_code", "created_at"]
    search_fields = ["book__title", "barcode"]
    readonly_fields = ["created_at"]
    autocomplete_fields = ["book"]
    list_per_page = 25

    fieldsets = (
        ("Book Information", {"fields": ("book",)}),
        ("Item Details", {"fields": ("barcode", "status", "location_code")}),
        ("Timestamps", {"fields": ("created_at",), "classes": ("collapse",)}),
    )

    def book_title(self, obj):
        return obj.book.title

    book_title.short_description = "Book"

    def status_colored(self, obj):
        colors = {
            "AVAILABLE": "green",
            "RESERVED": "orange",
            "LOANED": "blue",
            "LOST": "red",
            "DAMAGED": "purple",
        }
        color = colors.get(obj.status, "black")
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_colored.short_description = "Status"


# =========================
#  USER MANAGEMENT (Activate/Deactivate)
# =========================


@admin.action(description="Activate selected users")
def activate_users(modeladmin, request, queryset):
    updated = queryset.update(is_active=True)
    messages.success(request, f"Activated {updated} user(s)")


@admin.action(description="Deactivate selected users")
def deactivate_users(modeladmin, request, queryset):
    # Prevent deactivating self
    qs = queryset.exclude(pk=request.user.pk)
    skipped = queryset.count() - qs.count()
    updated = qs.update(is_active=False)
    msg = f"Deactivated {updated} user(s)"
    if skipped:
        msg += f" (skipped {skipped} current user)"
    messages.success(request, msg)


class UserAdmin(DjangoUserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_active",
        "is_staff",
        "is_superuser",
        "last_login",
    )
    list_filter = (
        "is_active",
        "is_staff",
        "is_superuser",
        "date_joined",
        "last_login",
    )
    search_fields = ("username", "email", "first_name", "last_name")
    actions = [activate_users, deactivate_users]

    # Hide the password hash field on the change form, but keep the
    # built-in "Change password" object tool available.
    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        # Only alter the change form (obj is not None). Keep add form intact
        # so password1/password2 remain visible when creating users.
        if obj is None:
            return fieldsets

        cleaned = []
        for name, opts in fieldsets:
            fields = list(opts.get("fields", ()))
            # Remove the read-only 'password' field from display
            fields = [f for f in fields if f != "password"]
            if not fields:
                # Skip empty sections entirely
                continue
            new_opts = dict(opts)
            new_opts["fields"] = tuple(fields)
            cleaned.append((name, new_opts))
        return tuple(cleaned)


try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass
admin.site.register(User, UserAdmin)

# Unregister built-in models we don't want to show
for model in (Group, ContentType, Session):
    try:
        admin.site.unregister(model)
    except admin.sites.NotRegistered:
        pass


# =========================
#  BORROW REQUESTS & LOANS
# =========================


class RejectActionForm(ActionForm):
    rejection_reason = forms.CharField(
        required=False,
        label="Rejection reason",
        widget=forms.TextInput(
            attrs={
                "placeholder": 'Reason required when using "Reject selected"',
                "size": "40",
            }
        ),
    )


class OverdueRequestFilter(admin.SimpleListFilter):
    title = "Overdue (pending)"
    parameter_name = "overdue"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Overdue"),
            ("no", "Not overdue"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(
                status=BorrowRequest.Status.PENDING,
                requested_to__lt=timezone.now().date(),
            )
        if self.value() == "no":
            return queryset.exclude(
                status=BorrowRequest.Status.PENDING,
                requested_to__lt=timezone.now().date(),
            )
        return queryset


@admin.register(BorrowRequest)
class BorrowRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "requested_from",
        "requested_to",
        "status_colored",
        "items_count",
        "admin",
        "decision_at",
        "rejection_reason_short",
        "created_at",
    )
    list_filter = (
        "status",
        OverdueRequestFilter,
        "requested_from",
        "requested_to",
        "created_at",
    )
    search_fields = (
        "user__username",
        "user__email",
        "items__book__title",
        "rejection_reason",
    )
    autocomplete_fields = ["user", "admin"]
    inlines = [BorrowRequestItemInline]
    readonly_fields = ["created_at", "updated_at", "decision_at"]
    date_hierarchy = "created_at"
    list_per_page = 25
    actions = ["approve_selected", "reject_selected", "mark_selected_expired"]
    action_form = RejectActionForm
    formfield_overrides = {
        models.TextField: {"widget": Textarea(attrs={"rows": 3, "cols": 80})},
    }

    fieldsets = (
        ("Requester", {"fields": ("user",)}),
        ("Requested Period", {"fields": ("requested_from", "requested_to")}),
        (
            "Decision",
            {"fields": ("status", "admin", "decision_at", "rejection_reason")},
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    def items_count(self, obj):
        return obj.items.count()

    items_count.short_description = "Items"

    def status_colored(self, obj):
        color_map = {
            BorrowRequest.Status.PENDING: "orange",
            BorrowRequest.Status.APPROVED: "green",
            BorrowRequest.Status.REJECTED: "red",
            BorrowRequest.Status.CANCELLED: "gray",
            BorrowRequest.Status.EXPIRED: "purple",
        }
        return format_html(
            '<b><span style="color:{}">{}</span></b>',
            color_map.get(obj.status, "black"),
            obj.get_status_display(),
        )

    status_colored.short_description = "Status"

    def rejection_reason_short(self, obj):
        if not obj.rejection_reason:
            return "-"
        text = obj.rejection_reason.strip()
        return (text[:47] + "...") if len(text) > 50 else text

    rejection_reason_short.short_description = "Rejection Reason"
    rejection_reason_short.admin_order_field = "rejection_reason"

    @admin.action(description="Approve selected")
    def approve_selected(self, request, queryset):
        pending = queryset.filter(status=BorrowRequest.Status.PENDING)
        updated = pending.update(
            status=BorrowRequest.Status.APPROVED,
            decision_at=timezone.now(),
            admin=request.user,
            rejection_reason="",
        )
        messages.success(request, f"Approved {updated} request(s)")

    @admin.action(description="Reject selected")
    def reject_selected(self, request, queryset):
        reason = request.POST.get("rejection_reason", "").strip()
        if not reason:
            messages.error(
                request,
                "Please provide a rejection reason in the action bar before rejecting.",
            )
            return
        pending = queryset.filter(status=BorrowRequest.Status.PENDING)
        updated = pending.update(
            status=BorrowRequest.Status.REJECTED,
            decision_at=timezone.now(),
            admin=request.user,
            rejection_reason=reason,
        )
        messages.success(request, f"Rejected {updated} request(s)")

    @admin.action(
        description="Mark selected as expired (past to-date & pending)"
    )
    def mark_selected_expired(self, request, queryset):
        today = timezone.now().date()
        qs = queryset.filter(
            status=BorrowRequest.Status.PENDING, requested_to__lt=today
        )
        updated = qs.update(status=BorrowRequest.Status.EXPIRED)
        if updated:
            messages.success(
                request, f"Marked {updated} request(s) as expired"
            )
        else:
            messages.info(
                request, "No pending requests past their requested_to date"
            )


class BorrowRequestItemAdmin(admin.ModelAdmin):
    list_display = ("request", "book", "quantity")
    autocomplete_fields = ["request", "book"]
    search_fields = ["request__user__username", "book__title"]
    list_per_page = 25


class LoanAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "request",
        "request_item",
        "book_item",
        "approved_from",
        "due_date",
        "status_colored",
        "created_at",
    )
    list_filter = ("status", "approved_from", "due_date", "created_at")
    search_fields = ("book_item__barcode", "request__user__username")
    autocomplete_fields = ["request", "request_item", "book_item"]
    date_hierarchy = "approved_from"
    actions = ["mark_as_returned", "mark_overdue_due"]

    def status_colored(self, obj):
        colors = {
            "BORROWED": "blue",
            "RETURNED": "green",
            "OVERDUE": "red",
        }
        return format_html(
            '<span style="color:{}">{}</span>',
            colors.get(obj.status, "black"),
            obj.get_status_display(),
        )

    status_colored.short_description = "Status"

    @admin.action(description="Mark selected as returned")
    def mark_as_returned(self, request, queryset):
        updated = queryset.update(
            status="RETURNED", returned_at=timezone.now().date()
        )
        messages.success(request, f"Marked {updated} loan(s) as returned")

    @admin.action(description="Mark overdue where due_date passed")
    def mark_overdue_due(self, request, queryset):
        today = timezone.now().date()
        qs = queryset.filter(due_date__lt=today, status="BORROWED")
        updated = qs.update(status="OVERDUE")
        if updated:
            messages.success(request, f"Marked {updated} loan(s) as overdue")
        else:
            messages.info(request, "No borrowed loans past due date")


class MailQueueAdmin(admin.ModelAdmin):
    list_display = (
        "type",
        "to_user",
        "to_admin",
        "to_email",
        "status",
        "scheduled_at",
        "sent_at",
    )
    list_filter = ("type", "status", "scheduled_at", "sent_at")
    search_fields = (
        "subject",
        "to_email",
        "to_user__username",
        "to_admin__username",
    )
    readonly_fields = ("scheduled_at",)
