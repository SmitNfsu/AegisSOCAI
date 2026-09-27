"""Configure Alias Robotics LLM in AegisSOC DB, secrets, and Bifrost."""
import asyncio
import sys

from core.secrets import set_secret
from core.storage.connection import get_db_manager
from core.storage.models import LLMProviderConfig, AIModelConfig
from core.llm.bifrost.admin import (
    push_provider_key,
    sync_provider_base_url,
    sync_provider_models,
    sync_all_provider_models,
)

import os

ALIAS_KEY = (
    os.environ.get("ALIAS_API_KEY")
    or os.environ.get("OPENAI_API_KEY")
    or ""
)
PROXY_BASE_URL = os.environ.get("OPENAI_BASE_URL") or "http://127.0.0.1:7787/api/llm/alias-proxy"
MODEL_ID = os.environ.get("CAI_MODEL") or "alias2-mini"

async def main():
    print("1. Saving secrets...")
    set_secret("OPENAI_API_KEY", ALIAS_KEY)
    set_secret("llm_provider_bifrost-openai_api_key", ALIAS_KEY)
    print("   Secrets saved.")

    print("2. Updating database provider and model configs...")
    db_manager = get_db_manager()
    if db_manager._engine is None:
        db_manager.initialize()

    with db_manager.session_scope() as session:
        # Reset defaults
        anthropic = session.query(LLMProviderConfig).filter_by(provider_id="bifrost-anthropic").first()
        if anthropic:
            anthropic.is_default = False

        # Configure bifrost-openai
        openai = session.query(LLMProviderConfig).filter_by(provider_id="bifrost-openai").first()
        if openai:
            openai.base_url = PROXY_BASE_URL
            openai.default_model = MODEL_ID
            openai.api_key_ref = "llm_provider_bifrost-openai_api_key"
            openai.is_active = True
            openai.is_default = True
            openai.name = "Alias Robotics (OpenAI-compatible)"
        else:
            openai = LLMProviderConfig(
                provider_id="bifrost-openai",
                provider_type="openai",
                name="Alias Robotics (OpenAI-compatible)",
                base_url=PROXY_BASE_URL,
                api_key_ref="llm_provider_bifrost-openai_api_key",
                default_model=MODEL_ID,
                is_active=True,
                is_default=True,
                config={},
            )
            session.add(openai)

        # Update chat_default in AIModelConfig
        chat_default = session.query(AIModelConfig).filter_by(component="chat_default").first()
        if chat_default:
            chat_default.provider_id = "bifrost-openai"
            chat_default.model_id = MODEL_ID
        else:
            chat_default = AIModelConfig(
                component="chat_default",
                provider_id="bifrost-openai",
                model_id=MODEL_ID,
                settings={},
            )
            session.add(chat_default)

    print("   Database configs updated.")

    print("3. Syncing Bifrost configuration...")
    base_ok = sync_provider_base_url("openai", PROXY_BASE_URL)
    print(f"   sync_provider_base_url: {base_ok}")

    key_ok = push_provider_key("openai", ALIAS_KEY)
    print(f"   push_provider_key: {key_ok}")

    models_ok = sync_provider_models("openai", [MODEL_ID, "alias1"], key_value=ALIAS_KEY)
    print(f"   sync_provider_models: {models_ok}")

    sync_result = await sync_all_provider_models()
    print(f"   sync_all_provider_models result: {sync_result}")

    print("Setup completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
