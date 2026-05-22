from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="127.0.0.1", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")

    database_url: str = Field(
        default="postgresql://postgres:password@localhost:5432/tech_intel",
        alias="DATABASE_URL",
    )
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="tech_intel", alias="POSTGRES_DB")
    postgres_user: str = Field(default="postgres", alias="POSTGRES_USER")
    postgres_password: str = Field(default="password", alias="POSTGRES_PASSWORD")

    kafka_bootstrap_servers: str = Field(default="localhost:9092", alias="KAFKA_BOOTSTRAP_SERVERS")
    kafka_topic_github: str = Field(default="github_events", alias="KAFKA_TOPIC_GITHUB")
    kafka_topic_hn: str = Field(default="hn_events", alias="KAFKA_TOPIC_HN")
    kafka_topic_stack: str = Field(default="stackexchange_events", alias="KAFKA_TOPIC_STACK")
    kafka_topic_arxiv: str = Field(default="arxiv_events", alias="KAFKA_TOPIC_ARXIV")
    kafka_topic_producthunt: str = Field(default="producthunt_events", alias="KAFKA_TOPIC_PRODUCTHUNT")
    kafka_topic_gdelt: str = Field(default="gdelt_events", alias="KAFKA_TOPIC_GDELT")
    kafka_topic_normalized: str = Field(default="normalized_events", alias="KAFKA_TOPIC_NORMALIZED")
    kafka_topic_summaries: str = Field(default="summaries", alias="KAFKA_TOPIC_SUMMARIES")
    kafka_topic_forecasts: str = Field(default="forecasts", alias="KAFKA_TOPIC_FORECASTS")

    github_token: str | None = Field(default=None, alias="GITHUB_TOKEN")
    stackexchange_key: str | None = Field(default=None, alias="STACKEXCHANGE_KEY")
    producthunt_client_id: str | None = Field(default=None, alias="PRODUCTHUNT_CLIENT_ID")
    producthunt_client_secret: str | None = Field(default=None, alias="PRODUCTHUNT_CLIENT_SECRET")
    producthunt_access_token: str | None = Field(default=None, alias="PRODUCTHUNT_ACCESS_TOKEN")

    hf_token: str | None = Field(default=None, alias="HF_TOKEN")
    llm_provider: str = Field(default="local", alias="LLM_PROVIDER")
    llm_api_key: str | None = Field(default=None, alias="LLM_API_KEY")
    llm_model: str = Field(default="mistral-small", alias="LLM_MODEL")

    langchain_tracing_v2: bool = Field(default=False, alias="LANGCHAIN_TRACING_V2")
    langsmith_api_key: str | None = Field(default=None, alias="LANGSMITH_API_KEY")

    @property
    def kafka_topics(self) -> dict[str, str]:
        return {
            "github": self.kafka_topic_github,
            "hn": self.kafka_topic_hn,
            "stackexchange": self.kafka_topic_stack,
            "arxiv": self.kafka_topic_arxiv,
            "producthunt": self.kafka_topic_producthunt,
            "gdelt": self.kafka_topic_gdelt,
            "normalized": self.kafka_topic_normalized,
            "summaries": self.kafka_topic_summaries,
            "forecasts": self.kafka_topic_forecasts,
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
