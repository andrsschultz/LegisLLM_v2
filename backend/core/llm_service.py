from typing import Callable, Optional, Awaitable
import httpx
import json


# Models that support thinking mode via enable_thinking parameter
_THINKING_MODELS = {"Qwen/Qwen3-32B", "Qwen/Qwen3.5-122B-A10B", "Qwen/Qwen3.5-397B-A17B", "Qwen/Qwen3.6-35B-A3B"}


def _supports_thinking(model: str) -> bool:
    """Check if the model supports enable_thinking parameter."""
    return model in _THINKING_MODELS


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

async def query_llm(
    prompt: str,
    api_key: str,
    model: str,
    on_thinking: Optional[Callable[[str], Awaitable[None]]] = None,
) -> str:
    """
    Route the query to the appropriate LLM service based on the model.
    When on_thinking is provided, uses streaming mode to yield thinking tokens.
    """

    print("Prompt:")
    print(prompt[:200] + "..." if len(prompt) > 200 else prompt)

    if on_thinking:
        return await query_llm_streaming(prompt, api_key, model, on_thinking)

    return await query_deepinfra(prompt, api_key, model)

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

    if _supports_thinking(model):
        payload["enable_thinking"] = True

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


async def query_llm_streaming(
    prompt: str,
    api_key: str,
    model: str,
    on_thinking: Optional[Callable[[str], Awaitable[None]]] = None,
) -> str:
    """
    Query LLM with streaming enabled. Yields <think> content via on_thinking callback
    in real-time, then returns the final content (with thinking stripped).
    """
    print("Prompt (streaming):")
    print(prompt[:200] + "..." if len(prompt) > 200 else prompt)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 16384,
        "stream": True,
    }

    if _supports_thinking(model):
        payload["enable_thinking"] = True

    url = "https://api.deepinfra.com/v1/openai/chat/completions"
    timeout = httpx.Timeout(600.0)

    full_content = ""
    in_think_block = False
    has_think_blocks = False

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    raise Exception(f"DeepInfra API call failed with status {response.status_code}: {body.decode()}")

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue

                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break

                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    choices = chunk.get("choices", [])
                    if not choices:
                        continue

                    delta = choices[0].get("delta", {})
                    token = delta.get("content", "")
                    reasoning_token = delta.get("reasoning_content", "")
                    finish_reason = choices[0].get("finish_reason")

                    if finish_reason == "length":
                        raise Exception(
                            "Die Antwort des Sprachmodells wurde abgeschnitten (Token-Limit erreicht). "
                            "Bitte versuchen Sie es erneut oder wählen Sie ein Modell mit höherem Token-Limit."
                        )

                    # Handle reasoning_content (Qwen3 thinking mode)
                    if reasoning_token and on_thinking:
                        has_think_blocks = True
                        await on_thinking(reasoning_token)

                    if not token:
                        continue

                    full_content += token

                    # Stream tokens to the frontend via on_thinking callback.
                    # For reasoning models: only stream <think> block content.
                    # For non-reasoning models: stream all content tokens.
                    if "<think>" in token and not in_think_block:
                        in_think_block = True
                        has_think_blocks = True
                        after_tag = token.split("<think>", 1)[1]
                        if "</think>" in after_tag:
                            think_text = after_tag.split("</think>", 1)[0]
                            if on_thinking and think_text.strip():
                                await on_thinking(think_text)
                            in_think_block = False
                        elif after_tag and on_thinking:
                            await on_thinking(after_tag)
                    elif in_think_block:
                        if "</think>" in token:
                            before_end = token.split("</think>", 1)[0]
                            if on_thinking and before_end.strip():
                                await on_thinking(before_end)
                            in_think_block = False
                        elif on_thinking:
                            await on_thinking(token)
                    elif not has_think_blocks and on_thinking:
                        # Non-reasoning model: stream all content so user sees progress
                        await on_thinking(token)

        # Normalize the full content (strip <think> blocks, extract JSON)
        result = _normalize_deepinfra_content(full_content)
        print(f"Streaming response complete. Length: {len(result)} characters")
        return result or ""

    except httpx.TimeoutException:
        print("ERROR: DeepInfra API streaming request timed out")
        raise Exception("DeepInfra API request timed out. The model may be taking too long to respond.")
    except Exception as e:
        print(f"ERROR in DeepInfra streaming query: {str(e)}")
        raise


