# Generated manually to preserve existing course college text while normalizing colleges.

import django.db.models.deletion
from django.db import migrations, models


def create_colleges_from_courses(apps, schema_editor):
    College = apps.get_model("records", "College")
    Course = apps.get_model("records", "Course")

    for course in Course.objects.filter(college_fk__isnull=True).iterator():
        college_name = (course.college or "").strip() or "Unassigned"
        college, _ = College.objects.get_or_create(name=college_name)
        course.college_fk = college
        course.save(update_fields=["college_fk"])


class Migration(migrations.Migration):

    dependencies = [
        ("records", "0004_course_degree_type"),
    ]

    operations = [
        migrations.CreateModel(
            name="College",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("code", models.CharField(blank=True, db_index=True, max_length=30)),
                ("name", models.CharField(db_index=True, max_length=150, unique=True)),
                ("is_active", models.BooleanField(default=True)),
                ("remarks", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ("code", "name"),
                "indexes": [
                    models.Index(
                        fields=["code", "name"],
                        name="records_college_code_name_idx",
                    ),
                ],
            },
        ),
        migrations.AddField(
            model_name="course",
            name="college_fk",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="courses",
                to="records.college",
            ),
        ),
        migrations.RunPython(create_colleges_from_courses, migrations.RunPython.noop),
        migrations.RemoveIndex(
            model_name="course",
            name="records_cou_college_575a08_idx",
        ),
        migrations.RemoveIndex(
            model_name="course",
            name="records_cou_college_83675b_idx",
        ),
        migrations.RemoveField(
            model_name="course",
            name="college",
        ),
        migrations.RenameField(
            model_name="course",
            old_name="college_fk",
            new_name="college",
        ),
        migrations.AlterModelOptions(
            name="course",
            options={"ordering": ("college__name", "code", "name")},
        ),
        migrations.AddIndex(
            model_name="course",
            index=models.Index(
                fields=["college", "name"],
                name="rec_course_college_name_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="course",
            index=models.Index(
                fields=["college", "code"],
                name="rec_course_college_code_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="course",
            index=models.Index(
                fields=["degree_type", "college"],
                name="rec_course_degree_college_idx",
            ),
        ),
    ]
