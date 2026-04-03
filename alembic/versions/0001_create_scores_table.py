"""create scores table

Revision ID: 0001_create_scores_table
Revises:
Create Date: 2026-04-01 00:00:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001_create_scores_table"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("player_name", sa.String(length=50), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_scores_id"), "scores", ["id"], unique=False)
    op.create_index(
        op.f("ix_scores_player_name"), "scores", ["player_name"], unique=False
    )
    op.create_index(op.f("ix_scores_score"), "scores", ["score"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_scores_score"), table_name="scores")
    op.drop_index(op.f("ix_scores_player_name"), table_name="scores")
    op.drop_index(op.f("ix_scores_id"), table_name="scores")
    op.drop_table("scores")
