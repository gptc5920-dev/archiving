import shutil
import tempfile

from django.contrib import admin
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from records.admin import (
    CollegeAdmin,
    CourseAdmin,
    StudentAdmin,
    StudentDocumentAdmin,
    StudentDocumentInline,
    render_document_viewer,
)
from records.models import College, Course, Student, StudentDocument


TEST_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class StudentDocumentModelTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.college = College.objects.create(
            code="CCS",
            name="College of Computing Studies",
        )
        self.course = Course.objects.create(
            degree_type=Course.DegreeType.BS,
            code="BSIT",
            name="Bachelor of Science in Information Technology",
            college=self.college,
            years=4,
        )
        self.student = Student.objects.create(
            student_number="2026-0001",
            first_name="Ana",
            last_name="Santos",
            course=self.course,
            year_level="4",
        )

    def test_document_accepts_pdf_uploads(self):
        document = StudentDocument.objects.create(
            student=self.student,
            title="Transcript",
            document_type=StudentDocument.DocumentType.TRANSCRIPT,
            file=SimpleUploadedFile(
                "transcript.pdf",
                b"%PDF-1.4 sample",
                content_type="application/pdf",
            ),
        )

        self.assertEqual(document.file_kind, "PDF")
        self.assertEqual(document.file_extension, "pdf")
        self.assertTrue(document.file.name.startswith("student-records/2026-0001/"))
        self.assertTrue(document.file.name.endswith(".pdf"))

    def test_pdf_document_renders_embedded_viewer(self):
        document = StudentDocument.objects.create(
            student=self.student,
            title="Transcript",
            document_type=StudentDocument.DocumentType.TRANSCRIPT,
            file=SimpleUploadedFile(
                "transcript.pdf",
                b"%PDF-1.4 sample",
                content_type="application/pdf",
            ),
        )

        viewer = str(render_document_viewer(document))

        self.assertIn("<iframe", viewer)
        self.assertIn(document.file.url, viewer)

    def test_document_accepts_image_uploads(self):
        document = StudentDocument.objects.create(
            student=self.student,
            title="Birth Certificate",
            document_type=StudentDocument.DocumentType.BIRTH_CERTIFICATE,
            file=SimpleUploadedFile(
                "birth-certificate.jpg",
                b"image-bytes",
                content_type="image/jpeg",
            ),
        )

        self.assertEqual(document.file_kind, "Image")
        self.assertEqual(document.file_extension, "jpg")

    def test_image_document_renders_image_viewer(self):
        document = StudentDocument.objects.create(
            student=self.student,
            title="Birth Certificate",
            document_type=StudentDocument.DocumentType.BIRTH_CERTIFICATE,
            file=SimpleUploadedFile(
                "birth-certificate.jpg",
                b"image-bytes",
                content_type="image/jpeg",
            ),
        )

        viewer = str(render_document_viewer(document))

        self.assertIn("<img", viewer)
        self.assertIn(document.file.url, viewer)

    def test_document_rejects_unsupported_file_extensions(self):
        document = StudentDocument(
            student=self.student,
            title="Executable",
            file=SimpleUploadedFile(
                "script.exe",
                b"not allowed",
                content_type="application/octet-stream",
            ),
        )

        with self.assertRaises(ValidationError):
            document.full_clean()

    def test_student_stores_college_and_course(self):
        self.assertEqual(self.student.college_name, "CCS - College of Computing Studies")
        self.assertEqual(
            self.student.course_name,
            "BSIT - Bachelor of Science in Information Technology",
        )

    def test_student_can_fall_back_to_legacy_course_text(self):
        student = Student.objects.create(
            student_number="2026-0002",
            first_name="Ben",
            last_name="Reyes",
            college="College of Teacher Education",
            program="BSED",
            year_level="3",
        )

        self.assertEqual(student.college_name, "College of Teacher Education")
        self.assertEqual(student.course_name, "BSED")


class CourseModelTests(TestCase):
    def test_course_string_uses_code_and_name(self):
        college = College.objects.create(
            code="CCS",
            name="College of Computing Studies",
        )
        course = Course.objects.create(
            degree_type=Course.DegreeType.BS,
            code="BSCS",
            name="Bachelor of Science in Computer Science",
            college=college,
        )

        self.assertEqual(str(course), "BSCS - Bachelor of Science in Computer Science")

    def test_course_supports_bs_and_ba_templates(self):
        college = College.objects.create(
            code="CAS",
            name="College of Arts and Sciences",
        )
        course = Course.objects.create(
            degree_type=Course.DegreeType.BA,
            code="BAEL",
            name="English Language",
            college=college,
        )

        self.assertEqual(course.degree_type, Course.DegreeType.BA)
        self.assertEqual(course.get_degree_type_display(), "BA")


class CollegeModelTests(TestCase):
    def test_college_string_uses_code_and_name(self):
        college = College.objects.create(
            code="CTE",
            name="College of Teacher Education",
        )

        self.assertEqual(str(college), "CTE - College of Teacher Education")


class StudentAdminConfigurationTests(TestCase):
    def test_student_name_is_the_admin_list_link(self):
        self.assertIn("full_name_display", StudentAdmin.list_display)
        self.assertEqual(StudentAdmin.list_display_links, ("full_name_display",))

    def test_student_admin_shows_academic_context_and_documents(self):
        academic_fieldset = StudentAdmin.fieldsets[1][1]["fields"]

        self.assertIn("course", academic_fieldset)
        self.assertIn("college_display", academic_fieldset)
        self.assertIn(StudentDocumentInline, StudentAdmin.inlines)
        self.assertIn("file_link", StudentDocumentInline.fields)
        self.assertIn("file_viewer", StudentDocumentInline.fields)
        self.assertIn("file_viewer", StudentDocumentInline.readonly_fields)
        self.assertIn("file_viewer", StudentDocumentAdmin.readonly_fields)
        self.assertTrue(StudentDocumentInline.collapsible)
        self.assertTrue(StudentDocumentInline.show_count)

    def test_student_admin_filters_by_course_and_year(self):
        self.assertIn("course", StudentAdmin.list_filter)
        self.assertIn("year_level", StudentAdmin.list_filter)
        self.assertIn("course__name", StudentAdmin.search_fields)
        self.assertEqual(StudentAdmin.list_select_related, ("course", "course__college"))

    def test_course_admin_links_to_filtered_students(self):
        self.assertIn("student_total", CourseAdmin.list_display)
        self.assertIn("degree_type_badge", CourseAdmin.list_display)
        self.assertIn("students_link", CourseAdmin.readonly_fields)
        self.assertIn("year_level_links", CourseAdmin.readonly_fields)
        self.assertIn("degree_type", CourseAdmin.fieldsets[0][1]["fields"])
        self.assertEqual(CourseAdmin.radio_fields["degree_type"], admin.HORIZONTAL)
        self.assertIn("degree_type", CourseAdmin.list_filter)
        self.assertIn("college", CourseAdmin.list_filter)
        self.assertIn("college__name", CourseAdmin.search_fields)

    def test_college_admin_links_to_filtered_courses_and_students(self):
        self.assertIn("course_total", CollegeAdmin.list_display)
        self.assertIn("student_total", CollegeAdmin.list_display)
        self.assertIn("courses_link", CollegeAdmin.readonly_fields)
        self.assertIn("students_link", CollegeAdmin.readonly_fields)
        self.assertIn("name", CollegeAdmin.search_fields)
