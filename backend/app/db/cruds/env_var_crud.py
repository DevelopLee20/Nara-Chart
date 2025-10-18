from typing import Dict, List, Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.env_var_models import EnvVar


class EnvVarCRUD:
    """Data access helpers for the environment variable table."""

    @staticmethod
    def _select_by_key(key: str):
        return select(EnvVar).where(EnvVar.key == key)

    @staticmethod
    def get_all(db: Session) -> Any:
        """Fetch every stored environment variable."""
        result = db.execute(select(EnvVar))
        return result.scalars().all()

    @staticmethod
    def get_all_as_dict(db: Session) -> Dict[str, str]:
        """Return all environment variables as a key/value mapping."""
        return {env_var.key: env_var.value for env_var in EnvVarCRUD.get_all(db)}

    @staticmethod
    def get_by_key(db: Session, key: str) -> EnvVar | None:
        """Retrieve a single environment variable by key."""
        result = db.execute(EnvVarCRUD._select_by_key(key))
        return result.scalar_one_or_none()

    @staticmethod
    def get_value_by_key(db: Session, key: str) -> str | None:
        """Return only the value associated with the given key, if present."""
        stmt = select(EnvVar.value).where(EnvVar.key == key)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def create(db: Session, key: str, value: str) -> EnvVar:
        """Insert a new environment variable record."""
        env_var = EnvVar(key=key, value=value)
        db.add(env_var)
        db.commit()
        db.refresh(env_var)
        return env_var

    @staticmethod
    def update(db: Session, key: str, value: str) -> EnvVar | None:
        """Update an existing environment variable if it exists."""
        env_var = EnvVarCRUD.get_by_key(db, key)
        if env_var is None:
            return None

        env_var.value = value
        db.commit()
        db.refresh(env_var)
        return env_var

    @staticmethod
    def upsert(db: Session, key: str, value: str, *, commit: bool = True) -> EnvVar:
        """
        Create or update an environment variable in a single call.

        Args:
            db: Active SQLAlchemy session.
            key: Environment variable key.
            value: Environment variable value.
            commit: When False, caller is responsible for committing.
        """
        env_var = EnvVarCRUD.get_by_key(db, key)
        if env_var is None:
            env_var = EnvVar(key=key, value=value)
            db.add(env_var)
        else:
            env_var.value = value

        if commit:
            db.commit()
            db.refresh(env_var)
        else:
            db.flush()
        return env_var

    @staticmethod
    def bulk_upsert(db: Session, env_vars: Dict[str, str]) -> int:
        """Persist multiple environment variables efficiently."""
        if not env_vars:
            return 0

        for key, value in env_vars.items():
            EnvVarCRUD.upsert(db, key, value, commit=False)

        db.commit()
        return len(env_vars)

    @staticmethod
    def delete(db: Session, key: str) -> bool:
        """Remove a single environment variable by key."""
        env_var = EnvVarCRUD.get_by_key(db, key)
        if env_var is None:
            return False

        db.delete(env_var)
        db.commit()
        return True

    @staticmethod
    def delete_all(db: Session) -> int:
        """Remove every environment variable record and return how many were deleted."""
        total_stmt = select(func.count()).select_from(EnvVar)
        count = db.execute(total_stmt).scalar_one()
        db.execute(delete(EnvVar))
        db.commit()
        return int(count)
