from .config import is_deepinfra_model
import openai
import httpx


def _normalize_deepinfra_content(content: str) -> str:
    """Strip common wrapper formats from DeepInfra model output."""
    normalized = content or ""

    if "<think>" in normalized:
        think_end = normalized.rfind("</think>")
        if think_end != -1:
            normalized = normalized[think_end + len("</think>"):].strip()

    if "```json" in normalized:
        json_start = normalized.find("```json") + len("```json")
        json_end = normalized.find("```", json_start)
        if json_end != -1:
            normalized = normalized[json_start:json_end].strip()
    elif normalized.startswith("```"):
        block_start = normalized.find("\n")
        block_end = normalized.rfind("```")
        if block_start != -1 and block_end > block_start:
            normalized = normalized[block_start:block_end].strip()

    return normalized

async def query_llm(prompt: str, api_key: str, model: str) -> str:
    """
    Route the query to the appropriate LLM service based on the model.
    
    Args:
        prompt: The user prompt
        api_key: User's API key (used for both OpenAI and DeepInfra models)
        model: The model to use
        
    Returns:
        The generated response content
    """

    print("Prompt:")
    print(prompt)
    
    if is_deepinfra_model(model):
        # Use user-provided API key for DeepInfra models
        return await query_deepinfra(prompt, api_key, model)
    else:
        # Use user-provided API key for OpenAI models
        return await query_openai(prompt, api_key, model)
    
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

    #print("Prompt:", prompt[:500] + "..." if len(prompt) > 50 else prompt)
    
    client = openai.AsyncOpenAI(api_key=api_key)
    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )

    print("Response from OpenAI:", response)

    # Return empty string if no content is None
    return response.choices[0].message.content or ""

async def query_deepinfra(prompt: str, api_key: str, model: str) -> str:
    """
    Query DeepInfra API using OpenAI-compatible format.
    
    Args:
        prompt: The user prompt
        api_key: DeepInfra API key
        model: The DeepInfra model to use
        
    Returns:
        The generated response content
    """
    
    #print("Prompt:", prompt[:50] + "..." if len(prompt) > 50 else prompt)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Use OpenAI-compatible format for DeepInfra
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 16384
    }
    
    # Use OpenAI-compatible endpoint
    url = "https://api.deepinfra.com/v1/openai/chat/completions"
    
    # Set timeout to 600 seconds (10 minutes) for LLM API calls
    timeout = httpx.Timeout(600.0)
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                print("Response from DeepInfra:", result)
                
                # Extract content from OpenAI-compatible response format
                if "choices" in result and len(result["choices"]) > 0:
                    choice = result["choices"][0]

                    if choice.get("finish_reason") == "length":
                        print("ERROR: Response truncated (finish_reason: length)")
                        raise Exception(
                            "Die Antwort des Sprachmodells wurde abgeschnitten (Token-Limit erreicht). "
                            "Bitte versuchen Sie es erneut oder wählen Sie ein Modell mit höherem Token-Limit."
                        )

                    generated_text = choice["message"]["content"]

                    generated_text = _normalize_deepinfra_content(generated_text)
                    return generated_text or ""

                else:
                    print("ERROR: Unexpected DeepInfra response format")
                    return ""
            else:
                print(f"DeepInfra API error: {response.status_code} - {response.text}")
                raise Exception(f"DeepInfra API call failed with status {response.status_code}: {response.text}")
    except httpx.TimeoutException:
        print("ERROR: DeepInfra API request timed out")
        raise Exception("DeepInfra API request timed out. The model may be taking too long to respond.")
    except Exception as e:
        print(f"ERROR in DeepInfra query: {str(e)}")
        raise


