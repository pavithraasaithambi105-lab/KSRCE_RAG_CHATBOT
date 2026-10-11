from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RAG Chatbot"

    llm_base_url: str = "https://openrouter.ai/api/v1"
    llm_api_key: str = ""
    llm_model: str = "openai/gpt-4o"
    llm_max_tokens: int = 1024

    # RAG
    embedding_model: str = "openai/text-embedding-3-small"
    chunk_size: int = 1000  # characters per chunk
    chunk_overlap: int = 200  # characters shared between neighbouring chunks
    top_k: int = 6  # chunks retrieved per question
    vision_model: str = "openai/gpt-4o"  # describes figures with no curated text; "" disables
    data_dir: str = "data"  # uploaded PDFs go to data/pdfs, the index to data/index

    # Student database (dummy data: python -m app.seed)
    database_path: str = "data/college.db"
    agent_model: str = "openai/gpt-4o-mini"  # student assistant (tool calling)

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
