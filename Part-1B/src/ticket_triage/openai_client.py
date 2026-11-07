import os

from openai import OpenAI, OpenAIError

from .errors import ServiceError


class OpenAIClient:
    def complete(self, system: str, user: str) -> str:
        api_key = os.environ.get("OPENAI_API_KEY")
        model = os.environ.get("OPENAI_MODEL")
        if api_key is None or not api_key.strip() or model is None or not model.strip():
            raise ServiceError()

        try:
            client = OpenAI(api_key=api_key, timeout=30.0, max_retries=0)
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                response_format={"type": "json_object"},
            )
        except OpenAIError:
            raise ServiceError() from None

        content = response.choices[0].message.content
        return "" if content is None else content
