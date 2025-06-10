from .config import settings
import openai
import httpx

async def query_openai(prompt: str, api_key: str, model: str) -> str:
    """
    Query OpenAI API with user-provided API key.
    
    Args:
        prompt: The user prompt
        api_key: User's OpenAI API key
        model: The OpenAI model to use
        
    Returns:
        The generated response content
    """
    client = openai.AsyncOpenAI(api_key=api_key)
    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    # Return empty string if no content is None
    return response.choices[0].message.content or ""

async def query_deepinfra(prompt: str, api_key: str, model: str) -> str:
    """
    Query DeepInfra API with user-provided API key.
    
    Args:
        prompt: The user prompt
        api_key: User's DeepInfra API key
        model: The DeepInfra model to use
        
    Returns:
        The generated response content
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
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