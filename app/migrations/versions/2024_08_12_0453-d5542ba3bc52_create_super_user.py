"""create super user

Revision ID: d5542ba3bc52
Revises: 43a8d976dcf0
Create Date: 2024-08-12 04:53:08.799553

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d5542ba3bc52"
down_revision: Union[str, None] = "43a8d976dcf0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.sql.text(
            """
            INSERT INTO users (email, hashed_password, first_name, last_name, is_active, is_superuser, is_verified)
            VALUES (
                'prince_of_dragonstone@westeros.com',
                '$argon2id$v=19$m=65536,t=3,p=4$JKETYQIAQmEXfrSbUMrlPQ$DnNFFnyT79q33yUQC+J8/GLGnf7fEMuE/GnJzlPJbV0',
                'Jacaerys',
                'Velaryon',
                True,
                True,
                True
            )
            """
        ),
    )


def downgrade() -> None:
    op.execute(
        sa.sql.text(
            """
            DELETE FROM users WHERE email = "prince_of_dragonstone@westeros.com"
            """
        ),
    )
