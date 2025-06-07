
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_password_change_required'
down_revision = 'create_root_user'
branch_labels = None
depends_on = None


def upgrade():
    # Add password_change_required column with default True to force existing users to change password
    op.add_column('user', sa.Column('password_change_required', sa.Boolean(), nullable=True, server_default='1'))
    
    # Exclude root users from password change requirement
    op.execute("UPDATE \"user\" SET password_change_required = FALSE WHERE role = 'root' OR is_root = TRUE")


def downgrade():
    # Remove the column
    op.drop_column('user', 'password_change_required')
