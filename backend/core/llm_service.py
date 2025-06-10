from .config import settings
import openai
import httpx

async def query_openai(prompt: str, model: str = settings.model) -> str:
    client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    # Return empty string if no content is None
    return response.choices[0].message.content or ""

async def query_deepinfra(prompt: str, model: str) -> str:
    headers = {
        "Authorization": f"Bearer {settings.deepinfra_api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "input": prompt,
        "max_new_tokens": 2048,
        "temperature": 0.7
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(f"https://api.deepinfra.com/v1/inference/{model}", json=payload, headers=headers)
        data = response.json()
    
    return data