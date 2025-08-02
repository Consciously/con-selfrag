"""Migration script template for Alembic."""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = '${revision}'
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}

def upgrade() -> None:
    """Apply migration."""
    ${upgrades if upgrades else "pass"}

def downgrade() -> None:
    """Rollback migration.""" 
    ${downgrades if downgrades else "pass"}
