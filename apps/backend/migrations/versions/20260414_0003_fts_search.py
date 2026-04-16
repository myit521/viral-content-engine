"""add sqlite fts5 search indexes

Revision ID: 20260414_0003
Revises: 20260414_0002
Create Date: 2026-04-14 12:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260414_0003"
down_revision = "20260414_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        return

    op.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS posts_fts USING fts5(
          post_id UNINDEXED,
          title,
          content_text,
          topic_keywords,
          tokenize = 'unicode61'
        );
        """
    )
    op.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS templates_fts USING fts5(
          template_id UNINDEXED,
          name,
          template_type,
          template_category,
          tokenize = 'unicode61'
        );
        """
    )

    op.execute(
        """
        CREATE TRIGGER IF NOT EXISTS posts_ai AFTER INSERT ON posts BEGIN
          INSERT INTO posts_fts(post_id, title, content_text, topic_keywords)
          VALUES (
            new.post_id,
            new.title,
            new.content_text,
            COALESCE((SELECT group_concat(value, ' ') FROM json_each(new.topic_keywords)), '')
          );
        END;
        """
    )
    op.execute(
        """
        CREATE TRIGGER IF NOT EXISTS posts_ad AFTER DELETE ON posts BEGIN
          DELETE FROM posts_fts WHERE post_id = old.post_id;
        END;
        """
    )
    op.execute(
        """
        CREATE TRIGGER IF NOT EXISTS posts_au AFTER UPDATE ON posts BEGIN
          DELETE FROM posts_fts WHERE post_id = old.post_id;
          INSERT INTO posts_fts(post_id, title, content_text, topic_keywords)
          VALUES (
            new.post_id,
            new.title,
            new.content_text,
            COALESCE((SELECT group_concat(value, ' ') FROM json_each(new.topic_keywords)), '')
          );
        END;
        """
    )

    op.execute(
        """
        CREATE TRIGGER IF NOT EXISTS templates_ai AFTER INSERT ON templates BEGIN
          INSERT INTO templates_fts(template_id, name, template_type, template_category)
          VALUES (new.template_id, new.name, new.template_type, new.template_category);
        END;
        """
    )
    op.execute(
        """
        CREATE TRIGGER IF NOT EXISTS templates_ad AFTER DELETE ON templates BEGIN
          DELETE FROM templates_fts WHERE template_id = old.template_id;
        END;
        """
    )
    op.execute(
        """
        CREATE TRIGGER IF NOT EXISTS templates_au AFTER UPDATE ON templates BEGIN
          DELETE FROM templates_fts WHERE template_id = old.template_id;
          INSERT INTO templates_fts(template_id, name, template_type, template_category)
          VALUES (new.template_id, new.name, new.template_type, new.template_category);
        END;
        """
    )

    op.execute("DELETE FROM posts_fts;")
    op.execute(
        """
        INSERT INTO posts_fts(post_id, title, content_text, topic_keywords)
        SELECT
          post_id,
          title,
          content_text,
          COALESCE((SELECT group_concat(value, ' ') FROM json_each(posts.topic_keywords)), '')
        FROM posts;
        """
    )
    op.execute("DELETE FROM templates_fts;")
    op.execute(
        """
        INSERT INTO templates_fts(template_id, name, template_type, template_category)
        SELECT template_id, name, template_type, template_category
        FROM templates;
        """
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        return

    op.execute("DROP TRIGGER IF EXISTS posts_ai;")
    op.execute("DROP TRIGGER IF EXISTS posts_ad;")
    op.execute("DROP TRIGGER IF EXISTS posts_au;")
    op.execute("DROP TRIGGER IF EXISTS templates_ai;")
    op.execute("DROP TRIGGER IF EXISTS templates_ad;")
    op.execute("DROP TRIGGER IF EXISTS templates_au;")
    op.execute("DROP TABLE IF EXISTS posts_fts;")
    op.execute("DROP TABLE IF EXISTS templates_fts;")
