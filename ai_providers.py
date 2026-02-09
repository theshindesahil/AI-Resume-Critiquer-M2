import os
from abc import ABC, abstractmethod
import json
import logging
from openai import OpenAI
from groq import Groq
from src import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIProvider(ABC):
    """Abstract base class for AI Providers."""

    def __init__(self, api_key: str, model_name: str, temperature: float = 0.1):
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature

    @abstractmethod
    def generate_critique(self, prompt: str, system_instruction: str = None) -> str:
        """
        Generates a critique for the given prompt.
        Must return a string resembling a JSON object.
        """
        pass

    def validate(self) -> tuple[bool, str]:
        """Simple validation of the API key availability."""
        if not self.api_key:
            return False, "API Key is missing."
        return True, ""


class OpenAIProvider(AIProvider):
    """Provider for OpenAI (GPT-4, etc.)"""

    def generate_critique(self, prompt: str, system_instruction: str = None) -> str:
        if not self.api_key:
            raise ValueError("OpenAI API Key is missing.")

        client = OpenAI(api_key=self.api_key)

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        try:
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                response_format={"type": "json_object"},  # Force JSON mode
                temperature=self.temperature,
                max_tokens=config.DEFAULT_MAX_TOKENS
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI Error: {e}")
            raise e


class GroqProvider(AIProvider):
    """Provider for Groq (Llama 3, etc.)"""

    def generate_critique(self, prompt: str, system_instruction: str = None) -> str:
        if not self.api_key:
            raise ValueError("Groq API Key is missing.")

        client = Groq(api_key=self.api_key)

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        try:
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=config.DEFAULT_MAX_TOKENS,
                response_format={"type": "json_object"} # Groq supports JSON mode for Llama 3 models
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Groq Error: {e}")
            if "401" in str(e):
                 raise Exception("Invalid Groq API Key.")
            raise e

def get_provider(provider_name: str, api_key: str, model_name: str) -> AIProvider:
    """Factory function to get the correct provider instance."""
    if provider_name == config.PROVIDER_OPENAI:
        return OpenAIProvider(api_key, model_name)
    elif provider_name == config.PROVIDER_GROQ:
        return GroqProvider(api_key, model_name)
    else:
        raise ValueError(f"Unknown provider: {provider_name}")
