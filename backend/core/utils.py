import re


def clean_json_string(json_string):
    """
    Clean JSON string by removing markdown code blocks if present.
    
    Args:
        json_string (str): The raw JSON string that may be wrapped in ```json ... ```
        
    Returns:
        str: The cleaned JSON string without markdown code blocks
    """
    pattern = r'^```json\s*(.*?)\s*```$'
    cleaned_string = re.sub(pattern, r'\1', json_string, flags=re.DOTALL)
    return cleaned_string.strip()
