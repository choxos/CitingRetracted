# Generated by Django 4.2.23 on 2025-07-23 05:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DataImportLog",
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
                (
                    "import_type",
                    models.CharField(
                        choices=[
                            ("retraction_watch", "Retraction Watch CSV"),
                            ("openalex", "OpenAlex API"),
                            ("semantic_scholar", "Semantic Scholar API"),
                            ("opencitations", "OpenCitations API"),
                        ],
                        max_length=50,
                    ),
                ),
                ("start_time", models.DateTimeField(auto_now_add=True)),
                ("end_time", models.DateTimeField(blank=True, null=True)),
                ("records_processed", models.PositiveIntegerField(default=0)),
                ("records_created", models.PositiveIntegerField(default=0)),
                ("records_updated", models.PositiveIntegerField(default=0)),
                ("records_failed", models.PositiveIntegerField(default=0)),
                ("status", models.CharField(default="running", max_length=20)),
                ("error_message", models.TextField(blank=True, null=True)),
                ("error_details", models.TextField(blank=True, null=True)),
                ("file_path", models.CharField(blank=True, max_length=500, null=True)),
                ("api_endpoint", models.URLField(blank=True, null=True)),
                (
                    "parameters",
                    models.TextField(
                        blank=True,
                        help_text="Import parameters (JSON format)",
                        null=True,
                    ),
                ),
            ],
            options={
                "db_table": "data_import_logs",
                "ordering": ["-start_time"],
            },
        ),
        migrations.CreateModel(
            name="RetractedPaper",
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
                (
                    "record_id",
                    models.CharField(
                        help_text="Retraction Watch unique identifier",
                        max_length=50,
                        unique=True,
                    ),
                ),
                ("title", models.TextField(help_text="Title of the retracted paper")),
                (
                    "original_paper_doi",
                    models.CharField(
                        blank=True,
                        help_text="DOI of the original paper",
                        max_length=255,
                        null=True,
                    ),
                ),
                (
                    "original_paper_doi_url",
                    models.URLField(
                        blank=True, help_text="URL to the original paper", null=True
                    ),
                ),
                (
                    "retraction_doi",
                    models.CharField(
                        blank=True,
                        help_text="DOI of the retraction notice",
                        max_length=255,
                        null=True,
                    ),
                ),
                (
                    "retraction_doi_url",
                    models.URLField(
                        blank=True, help_text="URL to the retraction notice", null=True
                    ),
                ),
                (
                    "journal",
                    models.CharField(
                        blank=True, help_text="Journal name", max_length=500, null=True
                    ),
                ),
                (
                    "publisher",
                    models.CharField(
                        blank=True,
                        help_text="Publisher name",
                        max_length=300,
                        null=True,
                    ),
                ),
                (
                    "author",
                    models.TextField(blank=True, help_text="Author names", null=True),
                ),
                (
                    "original_paper_date",
                    models.DateField(
                        blank=True,
                        help_text="Publication date of original paper",
                        null=True,
                    ),
                ),
                (
                    "retraction_date",
                    models.DateField(
                        blank=True, help_text="Date of retraction", null=True
                    ),
                ),
                (
                    "retraction_nature",
                    models.CharField(
                        blank=True,
                        help_text="Nature of retraction",
                        max_length=500,
                        null=True,
                    ),
                ),
                (
                    "reason",
                    models.TextField(
                        blank=True, help_text="Reason for retraction", null=True
                    ),
                ),
                (
                    "paywalled",
                    models.BooleanField(
                        default=False, help_text="Whether the paper is behind a paywall"
                    ),
                ),
                (
                    "subject",
                    models.CharField(
                        blank=True, help_text="Subject area", max_length=500, null=True
                    ),
                ),
                (
                    "institution",
                    models.CharField(
                        blank=True,
                        help_text="Author institution",
                        max_length=500,
                        null=True,
                    ),
                ),
                (
                    "country",
                    models.CharField(
                        blank=True,
                        help_text="Country of origin",
                        max_length=100,
                        null=True,
                    ),
                ),
                (
                    "abstract",
                    models.TextField(blank=True, help_text="Paper abstract", null=True),
                ),
                (
                    "notes",
                    models.TextField(
                        blank=True, help_text="Additional notes", null=True
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "citation_count",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Number of papers citing this retracted paper",
                    ),
                ),
                (
                    "last_citation_check",
                    models.DateTimeField(
                        blank=True,
                        help_text="Last time citations were checked",
                        null=True,
                    ),
                ),
            ],
            options={
                "db_table": "retracted_papers",
                "ordering": ["-retraction_date", "-original_paper_date"],
                "indexes": [
                    models.Index(
                        fields=["record_id"], name="retracted_p_record__ebdb3d_idx"
                    ),
                    models.Index(
                        fields=["original_paper_doi"],
                        name="retracted_p_origina_4ea2be_idx",
                    ),
                    models.Index(
                        fields=["journal"], name="retracted_p_journal_334375_idx"
                    ),
                    models.Index(
                        fields=["retraction_date"],
                        name="retracted_p_retract_2475ab_idx",
                    ),
                    models.Index(
                        fields=["original_paper_date"],
                        name="retracted_p_origina_361a2a_idx",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="CitingPaper",
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
                (
                    "openalex_id",
                    models.CharField(
                        help_text="OpenAlex unique identifier",
                        max_length=255,
                        unique=True,
                    ),
                ),
                (
                    "doi",
                    models.CharField(
                        blank=True,
                        help_text="DOI of the citing paper",
                        max_length=255,
                        null=True,
                    ),
                ),
                ("title", models.TextField(help_text="Title of the citing paper")),
                (
                    "authors",
                    models.TextField(
                        blank=True, help_text="Author names (JSON format)", null=True
                    ),
                ),
                (
                    "journal",
                    models.CharField(
                        blank=True, help_text="Journal name", max_length=500, null=True
                    ),
                ),
                (
                    "publisher",
                    models.CharField(
                        blank=True,
                        help_text="Publisher name",
                        max_length=300,
                        null=True,
                    ),
                ),
                (
                    "publication_date",
                    models.DateField(
                        blank=True, help_text="Publication date", null=True
                    ),
                ),
                (
                    "publication_year",
                    models.PositiveIntegerField(
                        blank=True, help_text="Publication year", null=True
                    ),
                ),
                (
                    "cited_by_count",
                    models.PositiveIntegerField(
                        default=0, help_text="Number of citations this paper has"
                    ),
                ),
                (
                    "is_open_access",
                    models.BooleanField(
                        default=False, help_text="Whether the paper is open access"
                    ),
                ),
                (
                    "concepts",
                    models.TextField(
                        blank=True,
                        help_text="Research concepts (JSON format)",
                        null=True,
                    ),
                ),
                (
                    "mesh_terms",
                    models.TextField(
                        blank=True, help_text="MeSH terms (JSON format)", null=True
                    ),
                ),
                (
                    "abstract_inverted_index",
                    models.TextField(
                        blank=True,
                        help_text="Abstract inverted index (JSON format)",
                        null=True,
                    ),
                ),
                (
                    "source_api",
                    models.CharField(
                        default="openalex",
                        help_text="API source (openalex, semantic_scholar, etc.)",
                        max_length=50,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "citing_papers",
                "ordering": ["-publication_date"],
                "indexes": [
                    models.Index(
                        fields=["openalex_id"], name="citing_pape_openale_5d3b7c_idx"
                    ),
                    models.Index(fields=["doi"], name="citing_pape_doi_d2bb4f_idx"),
                    models.Index(
                        fields=["publication_date"],
                        name="citing_pape_publica_c55979_idx",
                    ),
                    models.Index(
                        fields=["publication_year"],
                        name="citing_pape_publica_f7bca1_idx",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="Citation",
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
                (
                    "citation_date",
                    models.DateField(
                        blank=True, help_text="Date when citation was made", null=True
                    ),
                ),
                (
                    "days_after_retraction",
                    models.IntegerField(
                        blank=True,
                        help_text="Days between retraction and citation",
                        null=True,
                    ),
                ),
                (
                    "citation_context",
                    models.TextField(
                        blank=True,
                        help_text="Context in which the citation appears",
                        null=True,
                    ),
                ),
                (
                    "is_self_citation",
                    models.BooleanField(
                        default=False, help_text="Whether this is a self-citation"
                    ),
                ),
                (
                    "source_api",
                    models.CharField(
                        default="openalex",
                        help_text="API source for this citation",
                        max_length=50,
                    ),
                ),
                (
                    "confidence_score",
                    models.FloatField(
                        blank=True,
                        help_text="Confidence score for the citation match",
                        null=True,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "citing_paper",
                    models.ForeignKey(
                        help_text="The paper that cites the retracted paper",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="retracted_citations",
                        to="papers.citingpaper",
                    ),
                ),
                (
                    "retracted_paper",
                    models.ForeignKey(
                        help_text="The retracted paper being cited",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="citations",
                        to="papers.retractedpaper",
                    ),
                ),
            ],
            options={
                "db_table": "citations",
                "ordering": ["-citation_date"],
                "indexes": [
                    models.Index(
                        fields=["citation_date"], name="citations_citatio_367acd_idx"
                    ),
                    models.Index(
                        fields=["days_after_retraction"],
                        name="citations_days_af_fcc57b_idx",
                    ),
                ],
                "unique_together": {("retracted_paper", "citing_paper")},
            },
        ),
    ]
