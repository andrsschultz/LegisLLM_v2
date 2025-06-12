from .config import settings, is_deepinfra_model
import openai
import httpx

async def query_llm(prompt: str, api_key: str, model: str) -> str:
    """
    Route the query to the appropriate LLM service based on the model.
    
    Args:
        prompt: The user prompt
        api_key: User's API key (used for OpenAI models)
        model: The model to use
        
    Returns:
        The generated response content
    """
    if is_deepinfra_model(model):
        # Use DeepInfra API key from environment for DeepInfra models
        return await query_deepinfra(prompt, settings.deepinfra_api_key, model)
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

    print("Full prompt:", prompt)
    
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
    
    print("Full prompt:", prompt)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Use OpenAI-compatible format for DeepInfra
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 2048
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
                    generated_text = result["choices"][0]["message"]["content"]
                    
                    # Handle DeepSeek reasoning format - extract JSON after <think> tags
                    if generated_text and "<think>" in generated_text:
                        # Find the last occurrence of </think> and get everything after it
                        think_end = generated_text.rfind("</think>")
                        if think_end != -1:
                            # Extract content after </think> and strip whitespace
                            json_content = generated_text[think_end + 8:].strip()
                            print(f"Extracted JSON content after think tags: {json_content}")
                            generated_text = json_content
                    
                    # Handle markdown code block formatting (```json ... ```)
                    if generated_text and "```json" in generated_text:
                        # Find the start of JSON content after ```json
                        json_start = generated_text.find("```json") + 7
                        # Find the end of JSON content before closing ```
                        json_end = generated_text.find("```", json_start)
                        if json_end != -1:
                            json_content = generated_text[json_start:json_end].strip()
                            print(f"Extracted JSON content from markdown code block: {json_content}")
                            return json_content or ""
                    
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

