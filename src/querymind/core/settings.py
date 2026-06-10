from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "QueryMind v2"
    app_env: str = "dev"
    mock_mode: bool = True

    elastic_endpoint: str = "https://localhost:9200"
    elastic_api_key: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    query_timeout_ms: int = 30000
    max_results_limit: int = 1000
    request_id_header: str = "X-Request-ID"
    log_level: str = "INFO"
    live_max_retries: int = 2
    live_backoff_base_ms: int = 300

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()