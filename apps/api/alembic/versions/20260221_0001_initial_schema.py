"""initial schema

Revision ID: 20260221_0001
Revises: 
Create Date: 2026-02-21 12:00:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260221_0001"
down_revision = None
branch_labels = None
depends_on = None


role_enum = sa.Enum(
    "OWNER",
    "HR_SENIOR",
    "HR_JUNIOR",
    "SUPERVISOR",
    "SUPERADMIN",
    name="companyrole",
    native_enum=False,
)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "companies",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_companies")),
    )
    op.create_index(op.f("ix_companies_name"), "companies", ["name"], unique=True)

    op.create_table(
        "user_company_roles",
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("company_id", sa.String(), nullable=False),
        sa.Column("role", role_enum, nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_user_company_roles_company_id_companies"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_user_company_roles_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_company_roles")),
        sa.UniqueConstraint("user_id", "company_id", name="uq_user_company"),
    )
    op.create_index(op.f("ix_user_company_roles_company_id"), "user_company_roles", ["company_id"], unique=False)
    op.create_index(op.f("ix_user_company_roles_role"), "user_company_roles", ["role"], unique=False)
    op.create_index(op.f("ix_user_company_roles_user_id"), "user_company_roles", ["user_id"], unique=False)

    op.create_table(
        "invites",
        sa.Column("company_id", sa.String(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("role", role_enum, nullable=False),
        sa.Column("token", sa.String(length=128), nullable=False),
        sa.Column("invited_by", sa.String(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_invites_company_id_companies"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["invited_by"], ["users.id"], name=op.f("fk_invites_invited_by_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_invites")),
    )
    op.create_index(op.f("ix_invites_email"), "invites", ["email"], unique=False)
    op.create_index(op.f("ix_invites_role"), "invites", ["role"], unique=False)
    op.create_index(op.f("ix_invites_token"), "invites", ["token"], unique=True)

    op.create_table(
        "vacancies",
        sa.Column("company_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("department", sa.String(length=255), nullable=False),
        sa.Column("seniority", sa.String(length=64), nullable=False),
        sa.Column("requirements", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_vacancies_company_id_companies"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_vacancies")),
    )
    op.create_index(op.f("ix_vacancies_company_id"), "vacancies", ["company_id"], unique=False)
    op.create_index(op.f("ix_vacancies_title"), "vacancies", ["title"], unique=False)

    op.create_table(
        "candidates",
        sa.Column("company_id", sa.String(), nullable=False),
        sa.Column("vacancy_id", sa.String(), nullable=True),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("magic_link_token", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_candidates_company_id_companies"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vacancy_id"], ["vacancies.id"], name=op.f("fk_candidates_vacancy_id_vacancies"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_candidates")),
    )
    op.create_index(op.f("ix_candidates_company_id"), "candidates", ["company_id"], unique=False)
    op.create_index(op.f("ix_candidates_email"), "candidates", ["email"], unique=False)
    op.create_index(op.f("ix_candidates_magic_link_token"), "candidates", ["magic_link_token"], unique=True)
    op.create_index(op.f("ix_candidates_status"), "candidates", ["status"], unique=False)

    op.create_table(
        "interviews",
        sa.Column("company_id", sa.String(), nullable=False),
        sa.Column("candidate_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], name=op.f("fk_interviews_candidate_id_candidates"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_interviews_company_id_companies"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_interviews")),
    )
    op.create_index(op.f("ix_interviews_candidate_id"), "interviews", ["candidate_id"], unique=False)
    op.create_index(op.f("ix_interviews_company_id"), "interviews", ["company_id"], unique=False)
    op.create_index(op.f("ix_interviews_status"), "interviews", ["status"], unique=False)

    op.create_table(
        "questions",
        sa.Column("interview_id", sa.String(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("prompt_version", sa.String(length=50), nullable=False),
        sa.Column("audio_base64", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["interview_id"], ["interviews.id"], name=op.f("fk_questions_interview_id_interviews"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_questions")),
    )
    op.create_index(op.f("ix_questions_interview_id"), "questions", ["interview_id"], unique=False)

    op.create_table(
        "answers",
        sa.Column("interview_id", sa.String(), nullable=False),
        sa.Column("question_id", sa.String(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("sentiment_label", sa.String(length=50), nullable=True),
        sa.Column("sentiment_score", sa.Float(), nullable=True),
        sa.Column("duration_sec", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["interview_id"], ["interviews.id"], name=op.f("fk_answers_interview_id_interviews"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], name=op.f("fk_answers_question_id_questions"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_answers")),
    )
    op.create_index(op.f("ix_answers_interview_id"), "answers", ["interview_id"], unique=False)
    op.create_index(op.f("ix_answers_question_id"), "answers", ["question_id"], unique=False)

    op.create_table(
        "scores",
        sa.Column("interview_id", sa.String(), nullable=False),
        sa.Column("technical_score", sa.Float(), nullable=False),
        sa.Column("communication_score", sa.Float(), nullable=False),
        sa.Column("culture_score", sa.Float(), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("rationale", sa.JSON(), nullable=False),
        sa.Column("model_version", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["interview_id"], ["interviews.id"], name=op.f("fk_scores_interview_id_interviews"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_scores")),
    )
    op.create_index(op.f("ix_scores_interview_id"), "scores", ["interview_id"], unique=True)

    op.create_table(
        "reports",
        sa.Column("company_id", sa.String(), nullable=False),
        sa.Column("interview_id", sa.String(), nullable=True),
        sa.Column("report_type", sa.String(length=64), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_reports_company_id_companies"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_reports_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["interview_id"], ["interviews.id"], name=op.f("fk_reports_interview_id_interviews"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reports")),
    )
    op.create_index(op.f("ix_reports_company_id"), "reports", ["company_id"], unique=False)
    op.create_index(op.f("ix_reports_interview_id"), "reports", ["interview_id"], unique=False)
    op.create_index(op.f("ix_reports_report_type"), "reports", ["report_type"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("company_id", sa.String(), nullable=True),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("action", sa.String(length=255), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.String(length=100), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_audit_logs_company_id_companies"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_audit_logs_user_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_logs")),
    )
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_audit_logs_company_id"), "audit_logs", ["company_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_created_at"), "audit_logs", ["created_at"], unique=False)
    op.create_index(op.f("ix_audit_logs_entity_type"), "audit_logs", ["entity_type"], unique=False)
    op.create_index(op.f("ix_audit_logs_user_id"), "audit_logs", ["user_id"], unique=False)

    op.create_table(
        "embeddings",
        sa.Column("company_id", sa.String(), nullable=False),
        sa.Column("candidate_id", sa.String(), nullable=True),
        sa.Column("interview_id", sa.String(), nullable=True),
        sa.Column("source_type", sa.String(length=100), nullable=False),
        sa.Column("source_id", sa.String(length=100), nullable=False),
        sa.Column("vector", sa.JSON(), nullable=False),
        sa.Column("model_name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], name=op.f("fk_embeddings_candidate_id_candidates"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_embeddings_company_id_companies"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["interview_id"], ["interviews.id"], name=op.f("fk_embeddings_interview_id_interviews"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_embeddings")),
    )
    op.create_index(op.f("ix_embeddings_company_id"), "embeddings", ["company_id"], unique=False)
    op.create_index(op.f("ix_embeddings_source_id"), "embeddings", ["source_id"], unique=False)
    op.create_index(op.f("ix_embeddings_source_type"), "embeddings", ["source_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_embeddings_source_type"), table_name="embeddings")
    op.drop_index(op.f("ix_embeddings_source_id"), table_name="embeddings")
    op.drop_index(op.f("ix_embeddings_company_id"), table_name="embeddings")
    op.drop_table("embeddings")

    op.drop_index(op.f("ix_audit_logs_user_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_entity_type"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_created_at"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_company_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_action"), table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index(op.f("ix_reports_report_type"), table_name="reports")
    op.drop_index(op.f("ix_reports_interview_id"), table_name="reports")
    op.drop_index(op.f("ix_reports_company_id"), table_name="reports")
    op.drop_table("reports")

    op.drop_index(op.f("ix_scores_interview_id"), table_name="scores")
    op.drop_table("scores")

    op.drop_index(op.f("ix_answers_question_id"), table_name="answers")
    op.drop_index(op.f("ix_answers_interview_id"), table_name="answers")
    op.drop_table("answers")

    op.drop_index(op.f("ix_questions_interview_id"), table_name="questions")
    op.drop_table("questions")

    op.drop_index(op.f("ix_interviews_status"), table_name="interviews")
    op.drop_index(op.f("ix_interviews_company_id"), table_name="interviews")
    op.drop_index(op.f("ix_interviews_candidate_id"), table_name="interviews")
    op.drop_table("interviews")

    op.drop_index(op.f("ix_candidates_status"), table_name="candidates")
    op.drop_index(op.f("ix_candidates_magic_link_token"), table_name="candidates")
    op.drop_index(op.f("ix_candidates_email"), table_name="candidates")
    op.drop_index(op.f("ix_candidates_company_id"), table_name="candidates")
    op.drop_table("candidates")

    op.drop_index(op.f("ix_vacancies_title"), table_name="vacancies")
    op.drop_index(op.f("ix_vacancies_company_id"), table_name="vacancies")
    op.drop_table("vacancies")

    op.drop_index(op.f("ix_invites_token"), table_name="invites")
    op.drop_index(op.f("ix_invites_role"), table_name="invites")
    op.drop_index(op.f("ix_invites_email"), table_name="invites")
    op.drop_table("invites")

    op.drop_index(op.f("ix_user_company_roles_user_id"), table_name="user_company_roles")
    op.drop_index(op.f("ix_user_company_roles_role"), table_name="user_company_roles")
    op.drop_index(op.f("ix_user_company_roles_company_id"), table_name="user_company_roles")
    op.drop_table("user_company_roles")

    op.drop_index(op.f("ix_companies_name"), table_name="companies")
    op.drop_table("companies")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
