from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


DOCUMENT_EXTENSIONS = ["pdf", "jpg", "jpeg", "png", "webp"]
IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}


def student_document_upload_path(instance, filename):
    extension = Path(filename).suffix.lower()
    student_identifier = slugify(instance.student.student_number)

    if not student_identifier:
        student_identifier = f"student-{instance.student_id or uuid4().hex[:8]}"

    return f"student-records/{student_identifier}/{uuid4().hex}{extension}"


class College(models.Model):
    code = models.CharField(max_length=30, blank=True, db_index=True)
    name = models.CharField(max_length=150, unique=True, db_index=True)
    is_active = models.BooleanField(default=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("code", "name")
        indexes = [
            models.Index(fields=["code", "name"], name="records_college_code_name_idx"),
        ]

    def __str__(self):
        if self.code:
            return f"{self.code} - {self.name}"

        return self.name


class Course(models.Model):
    class DegreeType(models.TextChoices):
        BS = "BS", "BS"
        BA = "BA", "BA"

    degree_type = models.CharField(
        "degree template",
        max_length=2,
        choices=DegreeType.choices,
        default=DegreeType.BS,
        db_index=True,
    )
    code = models.CharField(max_length=30, blank=True, db_index=True)
    name = models.CharField(max_length=200, db_index=True)
    college = models.ForeignKey(
        College,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="courses",
    )
    years = models.PositiveSmallIntegerField(default=4)
    is_active = models.BooleanField(default=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("college__name", "code", "name")
        indexes = [
            models.Index(fields=["college", "name"], name="rec_course_college_name_idx"),
            models.Index(fields=["college", "code"], name="rec_course_college_code_idx"),
            models.Index(fields=["degree_type", "college"], name="rec_course_degree_college_idx"),
        ]

    def __str__(self):
        if self.code:
            return f"{self.code} - {self.name}"

        return self.name


class Student(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        GRADUATED = "graduated", "Graduated"
        TRANSFERRED = "transferred", "Transferred"
        INACTIVE = "inactive", "Inactive"
        ARCHIVED = "archived", "Archived"

    student_number = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=150)
    middle_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150)
    suffix = models.CharField(max_length=30, blank=True)
    course = models.ForeignKey(
        Course,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="students",
    )
    college = models.CharField(max_length=150, blank=True, db_index=True)
    program = models.CharField("legacy course name", max_length=150, blank=True)
    year_level = models.CharField(max_length=50, blank=True, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    birth_date = models.DateField(blank=True, null=True)
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("last_name", "first_name", "student_number")
        indexes = [
            models.Index(fields=["course", "year_level"]),
            models.Index(fields=["status", "year_level"]),
        ]

    def __str__(self):
        return f"{self.student_number} - {self.full_name}"

    @property
    def full_name(self):
        parts = [self.first_name, self.middle_name, self.last_name, self.suffix]
        return " ".join(part for part in parts if part).strip()

    @property
    def course_name(self):
        if self.course_id:
            return str(self.course)

        return self.program

    @property
    def college_name(self):
        if self.course_id and self.course.college_id:
            return str(self.course.college)

        return self.college


class StudentDocument(models.Model):
    class DocumentType(models.TextChoices):
        ADMISSION = "admission", "Admission"
        TRANSCRIPT = "transcript", "Transcript of Records"
        GRADES = "grades", "Grades"
        BIRTH_CERTIFICATE = "birth_certificate", "Birth Certificate"
        GOOD_MORAL = "good_moral", "Good Moral"
        DIPLOMA = "diploma", "Diploma"
        REQUEST_FORM = "request_form", "Request Form"
        OTHER = "other", "Other"

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    title = models.CharField(max_length=200)
    document_type = models.CharField(
        max_length=30,
        choices=DocumentType.choices,
        default=DocumentType.OTHER,
    )
    file = models.FileField(
        upload_to=student_document_upload_path,
        validators=[FileExtensionValidator(DOCUMENT_EXTENSIONS)],
    )
    issued_at = models.DateField(blank=True, null=True)
    received_at = models.DateField(default=timezone.localdate)
    archived_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="archived_student_documents",
    )
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("student__last_name", "student__first_name", "-received_at", "title")

    def __str__(self):
        return f"{self.student} - {self.title}"

    @property
    def file_extension(self):
        return Path(self.file.name).suffix.lower().lstrip(".")

    @property
    def file_kind(self):
        extension = self.file_extension

        if extension == "pdf":
            return "PDF"

        if extension in IMAGE_EXTENSIONS:
            return "Image"

        return "File"
