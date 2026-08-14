from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Di sini cara setup config dari env menggunakan pydantic
# Dengan pydantic_settings, aplikasi akan faile ketika startup jika ada env penting yang tidak ada
# Alias type configuration
class Settings(BaseSettings):
    google_api_key: str = Field(..., alias="GOOGLE_API_KEY")
    model_name: str = Field(default="google_genai:gemini-3.1-flash-lite", alias="MODEL_NAME")
    default_currency: str = Field(default="IDR", alias="DEFAULT_CURRENCY")
    database_url: str = Field(default="sqlite:///./tracker.db", alias="DATABASE_URL")

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()