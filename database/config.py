from pathlib import Path
from urllib.parse import quote_plus

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT_DIR / '.env'


class DatabaseSettings(BaseSettings):
    """
    PostgreSQL settings loaded from ``DATABASE_*`` variables.
    """

    host: str
    port: int
    name: str
    user: str
    password: str

    @field_validator('user', 'password', mode='before')
    @classmethod
    def url_encode_credentials(cls, value: str) -> str:
        """
        Encode a database credential for safe inclusion in a URL.

        Args:
            value (str): Raw database username or password.

        Returns:
            str: URL-encoded credential.
        """
        return quote_plus(value)

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding='utf-8',
        env_prefix='DATABASE_',
        extra='ignore'
    )

    @property
    def database_url(self) -> str:
        """
        Build the SQLAlchemy connection URL.

        Returns:
            str: PostgreSQL URL configured for the psycopg2 driver.
        """
        return (
            f'postgresql+psycopg2://{self.user}:{self.password}'
            f'@{self.host}:{self.port}/{self.name}'
        )


class Settings(BaseModel):
    """
    Application settings grouped by concern.
    """

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)


settings = Settings()
