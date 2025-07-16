import re


def clean_json_string(json_string):
    """
    Clean JSON string by removing markdown code blocks if present.
    
    Args:
        json_string (str): The raw JSON string that may be wrapped in ```json ... ``` or ``` ... ```
        
    Returns:
        str: The cleaned JSON string without markdown code blocks
    """
    # Handle both ```json and plain ``` code blocks
    patterns = [
        r'^```json\s*(.*?)\s*```$',  # ```json ... ```
        r'^```\s*(.*?)\s*```$',     # ``` ... ```
    ]
    
    cleaned_string = json_string.strip()
    
    for pattern in patterns:
        match = re.search(pattern, cleaned_string, flags=re.DOTALL)
        if match:
            cleaned_string = match.group(1).strip()
            break
    
    return cleaned_string
