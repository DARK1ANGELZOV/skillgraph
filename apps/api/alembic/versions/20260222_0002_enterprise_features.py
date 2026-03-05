"""enterprise feature expansion

Revision ID: 20260222_0002
Revises: 20260221_0001
Create Date: 2026-02-22 12:20:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260222_0002"
down_revision = "20260221_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("candidates", sa.Column("experience_years", sa.Integer(), nullable=True))
    op.add_column("candidates", sa.Column("skills", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("candidates", sa.Column("education", sa.Text(), nullable=True))
    op.alter_column("candidates", "skills", server_default=None)

    op.add_column("interviews", sa.Column("suspicious_events_count", sa.Integer(), nullable=False, server_default="0"))
    op.alter_column("interviews", "suspicious_events_count", server_default=None)

    op.add_column("questions", sa.Column("question_type", sa.String(length=32), nullable=False, server_default="technical"))
    op.add_column("questions", sa.Column("time_limit_sec", sa.Integer(), nullable=False, server_default="180"))
    op.alter_column("questions", "question_type", server_default=None)
    op.alter_column("questions", "time_limit_sec", server_default=None)

    op.add_column("answers", sa.Column("source_type", sa.String(length=32), nullable=False, server_default="text"))
    op.add_column("answers", sa.Column("stt_confidence", sa.Float(), nullable=True))
    op.add_column("answers", sa.Column("speech_pause_ratio", sa.Float(), nullable=True))
    op.add_column("answers", sa.Column("filler_word_ratio", sa.Float(), nullable=True))
    op.add_column("answers", sa.Column("instability_score", sa.Float(), nullable=True))
    op.add_column("answers", sa.Column("anti_cheat_flags", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("answers", sa.Column("ai_quality_score", sa.Float(), nullable=True))
    op.alter_column("answers", "source_type", server_default=None)
    op.alter_column("answers", "anti_cheat_flags", server_default=None)

    op.add_column("scores", sa.Column("soft_skills_score", sa.Float(), nullable=False, server_default="0"))
    op.add_column("scores", sa.Column("logic_score", sa.Float(), nullable=False, server_default="0"))
    op.add_column("scores", sa.Column("psychological_stability_score", sa.Float(), nullable=False, server_default="0"))
    op.add_column("scores", sa.Column("nervousness_score", sa.Float(), nullable=False, server_default="0"))
    op.add_column(
        "scores",
        sa.Column("recommendation", sa.String(length=64), nullable=False, server_default="recommended_with_conditions"),
    )
    op.add_column("scores", sa.Column("risk_level", sa.String(length=32), nullable=False, server_default="medium"))
    op.alter_column("scores", "soft_skills_score", server_default=None)
    op.alter_column("scores", "logic_score", server_default=None)
    op.alter_column("scores", "psychological_stability_score", server_default=None)
    op.alter_column("scores", "nervousness_score", server_default=None)
    op.alter_column("scores", "recommendation", server_default=None)
    op.alter_column("scores", "risk_level", server_default=None)

    op.add_column("embeddings", sa.Column("dimensions", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("embeddings", sa.Column("is_normalized", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.alter_column("embeddings", "dimensions", server_default=None)
    op.alter_column("embeddings", "is_normalized", server_default=None)

    op.create_table(
        "ai_model_status",
        sa.Column("service_name", sa.String(length=64), nullable=False),
        sa.Column("model_role", sa.String(length=64), nullable=False),
        sa.Column("model_id", sa.String(length=255), nullable=False),
        sa.Column("version", sa.String(length=128), nullable=False),
        sa.Column("is_loaded", sa.Boolean(), nullable=False),
        sa.Column("ram_usage_mb", sa.Float(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_model_status")),
    )
    op.create_index(op.f("ix_ai_model_status_model_role"), "ai_model_status", ["model_role"], unique=False)
    op.create_index(op.f("ix_ai_model_status_service_name"), "ai_model_status", ["service_name"], unique=False)

    op.create_table(
        "tests",
        sa.Column("company_id", sa.String(), nullable=False),
        sa.Column("interview_id", sa.String(), nullable=False),
        sa.Column("candidate_id", sa.String(), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("duration_sec", sa.Integer(), nullable=False),
        sa.Column("questions", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], name=op.f("fk_tests_candidate_id_candidates"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_tests_company_id_companies"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["interview_id"], ["interviews.id"], name=op.f("fk_tests_interview_id_interviews"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tests")),
    )
    op.create_index(op.f("ix_tests_candidate_id"), "tests", ["candidate_id"], unique=False)
    op.create_index(op.f("ix_tests_category"), "tests", ["category"], unique=False)
    op.create_index(op.f("ix_tests_company_id"), "tests", ["company_id"], unique=False)
    op.create_index(op.f("ix_tests_interview_id"), "tests", ["interview_id"], unique=False)

    op.create_table(
        "test_results",
        sa.Column("company_id", sa.String(), nullable=False),
        sa.Column("test_id", sa.String(), nullable=False),
        sa.Column("interview_id", sa.String(), nullable=False),
        sa.Column("candidate_id", sa.String(), nullable=False),
        sa.Column("answers", sa.JSON(), nullable=False),
        sa.Column("raw_score", sa.Float(), nullable=False),
        sa.Column("normalized_score", sa.Float(), nullable=False),
        sa.Column("ai_analysis", sa.JSON(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["candidate_id"],
            ["candidates.id"],
            name=op.f("fk_test_results_candidate_id_candidates"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name=op.f("fk_test_results_company_id_companies"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["interview_id"],
            ["interviews.id"],
            name=op.f("fk_test_results_interview_id_interviews"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["test_id"], ["tests.id"], name=op.f("fk_test_results_test_id_tests"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_test_results")),
    )
    op.create_index(op.f("ix_test_results_candidate_id"), "test_results", ["candidate_id"], unique=False)
    op.create_index(op.f("ix_test_results_company_id"), "test_results", ["company_id"], unique=False)
    op.create_index(op.f("ix_test_results_interview_id"), "test_results", ["interview_id"], unique=False)
    op.create_index(op.f("ix_test_results_test_id"), "test_results", ["test_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_test_results_test_id"), table_name="test_results")
    op.drop_index(op.f("ix_test_results_interview_id"), table_name="test_results")
    op.drop_index(op.f("ix_test_results_company_id"), table_name="test_results")
    op.drop_index(op.f("ix_test_results_candidate_id"), table_name="test_results")
    op.drop_table("test_results")

    op.drop_index(op.f("ix_tests_interview_id"), table_name="tests")
    op.drop_index(op.f("ix_tests_company_id"), table_name="tests")
    op.drop_index(op.f("ix_tests_category"), table_name="tests")
    op.drop_index(op.f("ix_tests_candidate_id"), table_name="tests")
    op.drop_table("tests")

    op.drop_index(op.f("ix_ai_model_status_service_name"), table_name="ai_model_status")
    op.drop_index(op.f("ix_ai_model_status_model_role"), table_name="ai_model_status")
    op.drop_table("ai_model_status")

    op.drop_column("embeddings", "is_normalized")
    op.drop_column("embeddings", "dimensions")

    op.drop_column("scores", "risk_level")
    op.drop_column("scores", "recommendation")
    op.drop_column("scores", "nervousness_score")
    op.drop_column("scores", "psychological_stability_score")
    op.drop_column("scores", "logic_score")
    op.drop_column("scores", "soft_skills_score")

    op.drop_column("answers", "ai_quality_score")
    op.drop_column("answers", "anti_cheat_flags")
    op.drop_column("answers", "instability_score")
    op.drop_column("answers", "filler_word_ratio")
    op.drop_column("answers", "speech_pause_ratio")
    op.drop_column("answers", "stt_confidence")
    op.drop_column("answers", "source_type")

    op.drop_column("questions", "time_limit_sec")
    op.drop_column("questions", "question_type")

    op.drop_column("interviews", "suspicious_events_count")

    op.drop_column("candidates", "education")
    op.drop_column("candidates", "skills")
    op.drop_column("candidates", "experience_years")
