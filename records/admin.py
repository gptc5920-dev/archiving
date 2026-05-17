from django.contrib import admin, messages
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from unfold.admin import ModelAdmin, StackedInline
from unfold.decorators import display

from .models import College, Course, Student, StudentDocument


def render_document_viewer(document):
    if not document.pk or not document.file:
        return "Save the document first to preview the file."

    file_url = document.file.url

    if document.file_kind == "PDF":
        return format_html(
            (
                '<div class="border border-base-200 overflow-hidden rounded-default '
                'dark:border-base-800">'
                '<iframe src="{}#toolbar=1&navpanes=0" title="{}" '
                'style="border:0;height:520px;width:100%;" loading="lazy"></iframe>'
                "</div>"
            ),
            file_url,
            document.title,
        )

    if document.file_kind == "Image":
        return format_html(
            (
                '<a href="{}" target="_blank" rel="noopener" '
                'class="block border border-base-200 overflow-hidden rounded-default '
                'dark:border-base-800">'
                '<img src="{}" alt="{}" '
                'style="display:block;max-height:520px;max-width:100%;object-fit:contain;'
                'width:100%;" loading="lazy">'
                "</a>"
            ),
            file_url,
            file_url,
            document.title,
        )

    return format_html(
        '<a href="{}" target="_blank" rel="noopener">Open file</a>',
        file_url,
    )


@admin.register(College)
class CollegeAdmin(ModelAdmin):
    fieldsets = (
        (
            "College",
            {
                "fields": (
                    "code",
                    "name",
                    "is_active",
                    "courses_link",
                    "students_link",
                ),
                "classes": ("tab",),
            },
        ),
        ("Notes", {"fields": ("remarks",), "classes": ("tab",)}),
        (
            "Dates",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("tab",),
            },
        ),
    )
    readonly_fields = ("courses_link", "students_link", "created_at", "updated_at")
    list_display = (
        "code",
        "name",
        "course_total",
        "student_total",
        "status_badge",
        "updated_at",
    )
    list_display_links = ("code", "name")
    list_filter = ("is_active",)
    list_filter_submit = True
    list_fullwidth = True
    list_per_page = 25
    ordering = ("code", "name")
    search_fields = ("code", "name")
    date_hierarchy = "created_at"
    actions = ("activate_colleges", "deactivate_colleges")

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            course_count=Count("courses", distinct=True),
            student_count=Count("courses__students", distinct=True),
        )

    @display(description="Courses", ordering="course_count")
    def course_total(self, obj):
        total = getattr(obj, "course_count", obj.courses.count())

        if not obj.pk:
            return total

        url = f"{reverse('admin:records_course_changelist')}?college__id__exact={obj.pk}"
        return format_html('<a href="{}">{} course(s)</a>', url, total)

    @display(description="Students", ordering="student_count")
    def student_total(self, obj):
        total = getattr(obj, "student_count", 0)

        if not obj.pk:
            return total

        url = (
            f"{reverse('admin:records_student_changelist')}"
            f"?course__college__id__exact={obj.pk}"
        )
        return format_html('<a href="{}">{} student(s)</a>', url, total)

    @display(description="Courses")
    def courses_link(self, obj):
        if not obj.pk:
            return "-"

        url = f"{reverse('admin:records_course_changelist')}?college__id__exact={obj.pk}"
        return format_html('<a href="{}">View courses in this college</a>', url)

    @display(description="Students")
    def students_link(self, obj):
        if not obj.pk:
            return "-"

        url = (
            f"{reverse('admin:records_student_changelist')}"
            f"?course__college__id__exact={obj.pk}"
        )
        return format_html('<a href="{}">View students in this college</a>', url)

    @display(
        description="Status",
        label={
            "active": "success",
            "inactive": "danger",
        },
    )
    def status_badge(self, obj):
        if obj.is_active:
            return ("active", "Active")

        return ("inactive", "Inactive")

    @admin.action(description="Activate selected colleges")
    def activate_colleges(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Activated {updated} college(s).", messages.SUCCESS)

    @admin.action(description="Deactivate selected colleges")
    def deactivate_colleges(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {updated} college(s).", messages.WARNING)


@admin.register(Course)
class CourseAdmin(ModelAdmin):
    fieldsets = (
        (
            "Course",
            {
                "fields": (
                    "degree_type",
                    "code",
                    "name",
                    "college",
                    "years",
                    "is_active",
                    "students_link",
                    "year_level_links",
                ),
                "classes": ("tab",),
            },
        ),
        ("Notes", {"fields": ("remarks",), "classes": ("tab",)}),
        (
            "Dates",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("tab",),
            },
        ),
    )
    readonly_fields = (
        "students_link",
        "year_level_links",
        "created_at",
        "updated_at",
    )
    list_display = (
        "code",
        "degree_type_badge",
        "name",
        "college_link",
        "years",
        "student_total",
        "status_badge",
        "updated_at",
    )
    list_display_links = ("code", "name")
    list_filter = ("degree_type", "college", "years", "is_active")
    list_filter_submit = True
    list_fullwidth = True
    list_per_page = 25
    ordering = ("college__name", "code", "name")
    search_fields = ("degree_type", "code", "name", "college__code", "college__name")
    autocomplete_fields = ("college",)
    list_select_related = ("college",)
    radio_fields = {"degree_type": admin.HORIZONTAL}
    date_hierarchy = "created_at"
    actions = ("activate_courses", "deactivate_courses")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("college")
            .annotate(student_count=Count("students"))
        )

    @display(description="College", ordering="college__name", empty_value="-")
    def college_link(self, obj):
        if obj.college_id:
            url = reverse("admin:records_college_change", args=[obj.college_id])
            return format_html('<a href="{}">{}</a>', url, obj.college)

        return "-"

    @display(description="Students", ordering="student_count")
    def student_total(self, obj):
        total = getattr(obj, "student_count", obj.students.count())

        if not obj.pk:
            return total

        url = f"{reverse('admin:records_student_changelist')}?course__id__exact={obj.pk}"
        return format_html('<a href="{}">{} student(s)</a>', url, total)

    @display(description="Students")
    def students_link(self, obj):
        if not obj.pk:
            return "-"

        url = f"{reverse('admin:records_student_changelist')}?course__id__exact={obj.pk}"
        return format_html('<a href="{}">View students in this course</a>', url)

    @display(description="Students by year")
    def year_level_links(self, obj):
        if not obj.pk:
            return "-"

        student_url = reverse("admin:records_student_changelist")
        links = [
            (
                f"{student_url}?course__id__exact={obj.pk}&year_level__exact={year}",
                f"Year {year}",
            )
            for year in range(1, obj.years + 1)
        ]

        return format_html_join(
            " ",
            '<a class="inline-block mr-2" href="{}">{}</a>',
            links,
        )

    @display(
        description="Template",
        ordering="degree_type",
        label={
            Course.DegreeType.BS: "success",
            Course.DegreeType.BA: "info",
        },
    )
    def degree_type_badge(self, obj):
        return (obj.degree_type, obj.get_degree_type_display())

    @display(
        description="Status",
        label={
            "active": "success",
            "inactive": "danger",
        },
    )
    def status_badge(self, obj):
        if obj.is_active:
            return ("active", "Active")

        return ("inactive", "Inactive")

    @admin.action(description="Activate selected courses")
    def activate_courses(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Activated {updated} course(s).", messages.SUCCESS)

    @admin.action(description="Deactivate selected courses")
    def deactivate_courses(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {updated} course(s).", messages.WARNING)


class StudentDocumentInline(StackedInline):
    model = StudentDocument
    extra = 0
    collapsible = True
    show_count = True
    show_change_link = True
    verbose_name_plural = "Files and documents"
    fields = (
        "title",
        "document_type",
        "file",
        "file_link",
        "file_viewer",
        "file_kind",
        "received_at",
        "archived_by",
        "remarks",
    )
    readonly_fields = ("file_link", "file_viewer", "file_kind", "archived_by")
    autocomplete_fields = ("archived_by",)

    @display(description="Open")
    def file_link(self, obj):
        if obj.pk and obj.file:
            return format_html(
                '<a href="{}" target="_blank" rel="noopener">Open file</a>',
                obj.file.url,
            )

        return "-"

    @display(description="Viewer")
    def file_viewer(self, obj):
        return render_document_viewer(obj)

    @display(description="Format")
    def file_kind(self, obj):
        if obj.pk:
            return obj.file_kind

        return "-"


@admin.register(Student)
class StudentAdmin(ModelAdmin):
    fieldsets = (
        (
            "Student",
            {
                "fields": (
                    "student_number",
                    "first_name",
                    "middle_name",
                    "last_name",
                    "suffix",
                    "birth_date",
                ),
                "classes": ("tab",),
            },
        ),
        (
            "Academic",
            {
                "fields": ("course", "college_display", "year_level", "status"),
                "classes": ("tab",),
            },
        ),
        (
            "Contact",
            {
                "fields": ("email", "phone_number", "address"),
                "classes": ("tab",),
            },
        ),
        ("Notes", {"fields": ("remarks",), "classes": ("tab",)}),
        (
            "Dates",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("tab",),
            },
        ),
    )
    readonly_fields = ("college_display", "created_at", "updated_at")
    autocomplete_fields = ("course",)
    list_select_related = ("course", "course__college")
    inlines = (StudentDocumentInline,)
    list_display = (
        "full_name_display",
        "student_number",
        "college_display",
        "course_display",
        "year_level",
        "status_badge",
        "document_total",
        "updated_at",
    )
    list_display_links = ("full_name_display",)
    list_filter = ("course", "course__college", "year_level", "status")
    list_filter_submit = True
    list_fullwidth = True
    list_per_page = 25
    ordering = ("last_name", "first_name")
    search_fields = (
        "student_number",
        "first_name",
        "middle_name",
        "last_name",
        "course__code",
        "course__name",
        "course__college__code",
        "course__college__name",
        "college",
        "program",
    )
    date_hierarchy = "created_at"
    actions = ("mark_active", "mark_archived")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("course", "course__college")
            .annotate(document_count=Count("documents"))
        )

    @display(description="Name", ordering="last_name")
    def full_name_display(self, obj):
        return obj.full_name

    @display(description="College", ordering="course__college__name", empty_value="-")
    def college_display(self, obj):
        return obj.college_name or "-"

    @display(description="Course", ordering="course__name", empty_value="-")
    def course_display(self, obj):
        return obj.course_name or "-"

    @display(
        description="Status",
        label={
            Student.Status.ACTIVE: "success",
            Student.Status.GRADUATED: "info",
            Student.Status.TRANSFERRED: "warning",
            Student.Status.INACTIVE: "danger",
            Student.Status.ARCHIVED: "neutral",
        },
    )
    def status_badge(self, obj):
        return (obj.status, obj.get_status_display())

    @display(description="Documents", ordering="document_count")
    def document_total(self, obj):
        total = getattr(obj, "document_count", obj.documents.count())
        url = (
            f"{reverse('admin:records_studentdocument_changelist')}"
            f"?student__id__exact={obj.pk}"
        )

        return format_html('<a href="{}">{} document(s)</a>', url, total)

    @admin.action(description="Mark selected students active")
    def mark_active(self, request, queryset):
        updated = queryset.update(status=Student.Status.ACTIVE)
        self.message_user(request, f"Marked {updated} student(s) active.", messages.SUCCESS)

    @admin.action(description="Mark selected students archived")
    def mark_archived(self, request, queryset):
        updated = queryset.update(status=Student.Status.ARCHIVED)
        self.message_user(request, f"Archived {updated} student record(s).", messages.WARNING)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)

        for deleted_object in formset.deleted_objects:
            deleted_object.delete()

        for instance in instances:
            if isinstance(instance, StudentDocument) and not instance.archived_by_id:
                instance.archived_by = request.user

            instance.save()

        formset.save_m2m()


@admin.register(StudentDocument)
class StudentDocumentAdmin(ModelAdmin):
    fieldsets = (
        (
            "Document",
            {
                "fields": (
                    "student",
                    "title",
                    "document_type",
                    "file",
                    "file_link",
                    "file_kind",
                ),
                "classes": ("tab",),
            },
        ),
        (
            "Viewer",
            {
                "fields": ("file_viewer",),
                "classes": ("tab",),
            },
        ),
        (
            "Archive",
            {
                "fields": ("issued_at", "received_at", "archived_by", "remarks"),
                "classes": ("tab",),
            },
        ),
        (
            "Dates",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("tab",),
            },
        ),
    )
    readonly_fields = (
        "file_link",
        "file_viewer",
        "file_kind",
        "created_at",
        "updated_at",
    )
    autocomplete_fields = ("student", "archived_by")
    list_select_related = (
        "student",
        "student__course",
        "student__course__college",
        "archived_by",
    )
    list_display = (
        "title",
        "student_link",
        "document_type",
        "file_kind_badge",
        "received_at",
        "archived_by",
        "created_at",
    )
    list_filter = ("document_type", "received_at", "created_at", "archived_by")
    list_filter_submit = True
    list_fullwidth = True
    list_per_page = 25
    ordering = ("student__last_name", "student__first_name", "-received_at")
    search_fields = (
        "title",
        "student__student_number",
        "student__first_name",
        "student__middle_name",
        "student__last_name",
        "student__course__code",
        "student__course__name",
        "student__course__college__code",
        "student__course__college__name",
        "remarks",
    )
    date_hierarchy = "received_at"

    @display(description="Student", ordering="student__last_name")
    def student_link(self, obj):
        url = reverse("admin:records_student_change", args=[obj.student_id])
        return format_html('<a href="{}">{}</a>', url, obj.student)

    @display(description="File")
    def file_link(self, obj):
        if obj.pk and obj.file:
            return format_html('<a href="{}" target="_blank" rel="noopener">Open file</a>', obj.file.url)

        return "-"

    @display(description="Viewer")
    def file_viewer(self, obj):
        return render_document_viewer(obj)

    @display(description="Format")
    def file_kind(self, obj):
        if obj.pk:
            return obj.file_kind

        return "-"

    @display(
        description="Format",
        label={
            "pdf": "danger",
            "image": "success",
            "file": "neutral",
        },
    )
    def file_kind_badge(self, obj):
        kind = obj.file_kind
        return (kind.lower(), kind)

    def save_model(self, request, obj, form, change):
        if not obj.archived_by_id:
            obj.archived_by = request.user

        super().save_model(request, obj, form, change)
