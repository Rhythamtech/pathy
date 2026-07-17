from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    OPENAI_API_KEY: str
    OPENAI_BASE_URL: str
    OPENAI_MODEL_NAME: str

    JINA_AI_KEY : str


    max_creators: int = 5
    max_courses: int = 8
    max_reviews_per_course: int = 3
    max_resource_candidates: int = 3


settings = Settings()