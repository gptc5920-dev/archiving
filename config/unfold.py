from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.urls import reverse

from records.models import College, Course, Student, StudentDocument


def environment_callback(request):
    if settings.DEBUG:
        return ["Development", "info"]

    return ["Production", "danger"]


def active_users_badge(request):
    return get_user_model().objects.filter(is_active=True).count()


def students_badge(request):
    return Student.objects.count()


def colleges_badge(request):
    return College.objects.count()


def courses_badge(request):
    return Course.objects.count()


def documents_badge(request):
    return StudentDocument.objects.count()


def profile_link(request):
    if request.user.is_authenticated:
        return reverse("admin:accounts_user_change", args=[request.user.pk])

    return reverse("admin:index")


def dashboard_callback(request, context):
    User = get_user_model()
    total_colleges = College.objects.count()
    total_courses = Course.objects.count()
    total_students = Student.objects.count()
    total_documents = StudentDocument.objects.count()
    pdf_documents = StudentDocument.objects.filter(file__iendswith=".pdf").count()
    image_documents = StudentDocument.objects.filter(
        Q(file__iendswith=".jpg")
        | Q(file__iendswith=".jpeg")
        | Q(file__iendswith=".png")
        | Q(file__iendswith=".webp")
    ).count()

    status_counts = {
        row["status"]: row["total"]
        for row in Student.objects.values("status").annotate(total=Count("id"))
    }
    document_type_counts = {
        row["document_type"]: row["total"]
        for row in StudentDocument.objects.values("document_type").annotate(
            total=Count("id")
        )
    }

    context["dashboard_stats"] = [
        {
            "label": "Colleges",
            "value": total_colleges,
            "icon": "account_balance",
            "icon_classes": "bg-cyan-100 text-cyan-700 dark:bg-cyan-500/20 dark:text-cyan-400",
            "link": reverse("admin:records_college_changelist"),
        },
        {
            "label": "Courses",
            "value": total_courses,
            "icon": "menu_book",
            "icon_classes": "bg-indigo-100 text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-400",
            "link": reverse("admin:records_course_changelist"),
        },
        {
            "label": "Students",
            "value": total_students,
            "icon": "school",
            "icon_classes": "bg-primary-100 text-primary-700 dark:bg-primary-500/20 dark:text-primary-400",
            "link": reverse("admin:records_student_changelist"),
        },
        {
            "label": "Documents",
            "value": total_documents,
            "icon": "folder_copy",
            "icon_classes": "bg-sky-100 text-sky-700 dark:bg-sky-500/20 dark:text-sky-400",
            "link": reverse("admin:records_studentdocument_changelist"),
        },
        {
            "label": "PDF files",
            "value": pdf_documents,
            "icon": "picture_as_pdf",
            "icon_classes": "bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400",
            "link": reverse("admin:records_studentdocument_changelist"),
        },
        {
            "label": "Image files",
            "value": image_documents,
            "icon": "image",
            "icon_classes": "bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400",
            "link": reverse("admin:records_studentdocument_changelist"),
        },
        {
            "label": "Archived",
            "value": status_counts.get(Student.Status.ARCHIVED, 0),
            "icon": "inventory_2",
            "icon_classes": "bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-400",
            "link": (
                f"{reverse('admin:records_student_changelist')}"
                f"?status__exact={Student.Status.ARCHIVED}"
            ),
        },
        {
            "label": "Users",
            "value": User.objects.count(),
            "icon": "group",
            "icon_classes": "bg-orange-100 text-orange-700 dark:bg-orange-500/20 dark:text-orange-400",
            "link": reverse("admin:accounts_user_changelist"),
        },
    ]
    context["account_stats"] = context["dashboard_stats"]

    context["student_status_stats"] = [
        {
            "label": label,
            "value": status_counts.get(value, 0),
            "percent": round((status_counts.get(value, 0) / total_students) * 100)
            if total_students
            else 0,
            "link": f"{reverse('admin:records_student_changelist')}?status__exact={value}",
        }
        for value, label in Student.Status.choices
    ]
    context["document_type_stats"] = [
        {
            "label": label,
            "value": document_type_counts.get(value, 0),
            "percent": round(
                (document_type_counts.get(value, 0) / total_documents) * 100
            )
            if total_documents
            else 0,
            "link": (
                f"{reverse('admin:records_studentdocument_changelist')}"
                f"?document_type__exact={value}"
            ),
        }
        for value, label in StudentDocument.DocumentType.choices
    ]
    context["recent_students"] = Student.objects.select_related(
        "course", "course__college"
    ).order_by("-updated_at")[:5]
    context["recent_documents"] = StudentDocument.objects.select_related(
        "student", "student__course", "student__course__college", "archived_by"
    ).order_by("-created_at")[:5]
    context["quick_actions"] = [
        {
            "label": "Add college",
            "icon": "account_balance",
            "link": reverse("admin:records_college_add"),
        },
        {
            "label": "Add course",
            "icon": "add_business",
            "link": reverse("admin:records_course_add"),
        },
        {
            "label": "Add student",
            "icon": "person_add",
            "link": reverse("admin:records_student_add"),
        },
        {
            "label": "Upload document",
            "icon": "upload_file",
            "link": reverse("admin:records_studentdocument_add"),
        },
        {
            "label": "View student archive",
            "icon": "folder_open",
            "link": reverse("admin:records_student_changelist"),
        },
        {
            "label": "Activity log",
            "icon": "history",
            "link": reverse("admin:admin_logentry_changelist"),
        },
        {
            "label": "Manage users",
            "icon": "manage_accounts",
            "link": reverse("admin:accounts_user_changelist"),
        },
    ]

    context["account_overview"] = [
        {
            "label": "Active users",
            "value": User.objects.filter(is_active=True).count(),
            "icon": "verified_user",
            "icon_classes": "bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400",
        },
        {
            "label": "Superusers",
            "value": User.objects.filter(is_superuser=True).count(),
            "icon": "shield_person",
            "icon_classes": "bg-orange-100 text-orange-700 dark:bg-orange-500/20 dark:text-orange-400",
        },
    ]

    return context
