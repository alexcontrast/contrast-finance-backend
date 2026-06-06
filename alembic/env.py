from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import normalize_database_url

# Import models so Alembic sees them.
from app.models import (  # noqa: F401
    Department,
    User,
    Event,
    EventItem,
    Contractor,
    TaxpayerCheck,
    PaymentRequest,
    EventShare,
    AuditLog,
    MonthlyPlan,
    MonthlyExpense,
    MonthlyClosing,
    Export,
    TelegramMessage,
)


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
database_url = normalize_database_url(settings.DATABASE_URL)

if not database_url:
    raise RuntimeError("DATABASE_URL is not configured")

config.set_main_option("sqlalchemy.url", database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section)
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
