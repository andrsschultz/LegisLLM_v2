import json
import os
from typing import List
from .llm_service import query_openai, query_deepinfra
from .models import NormEntry


#TBD: Functions always use OpenAI, but should use DeepInfra if specified

async def identify_relevant_norms(task_description: str) -> list:
    
    """Identify the relevant legal norms for the given task."""
    print("\n==== IDENTIFY RELEVANT NORMS ====")
    print(f"Task description length: {len(task_description)} characters")
    
    prompt = f"""
        Du bist Legist im Bundesfinanzministerium und sollst einen Gesetzesentwurf anfertigen.

        Maßnahme:  {task_description}

        Die Maßnahme soll durch Änderung eines oder mehrerer bereits bestehender Stammgesetze umgesetzt werde. Bestimme in einem ersten Schritt sämtliche für eine Änderung in Betracht kommende Rechtsnormen. Achte darauf, sämtliche von der Änderungsmaßnahme möglicherweise betroffenen Rechtsnormen einzubeziehen. Nehme noch keine Änderung vor.

        Gib als Antwort ausschließlich eine JSON-Liste zurück, welches wie folgt formatiert ist:

        {{
        "entries": [
            {{
            "jurabk": "EStG",
            "enbez": "§ 21",
            "P": "2"
            }},
            {{
            "jurabk": "EStG",
            "enbez": "§ 3",
            "P": "2a"
            }}
        ]
        }}

        "jurabk" ist die Abkürzung für das betreffende Gesetzes, "enbez" der Paraph und "P" der jeweilige Absatz.
    """

    print("Querying LLM to identify relevant norms...")
    raw_response = await query_openai(prompt)

    print(f"Response received. Length: {len(raw_response)} characters")
    
    try:
        parsed_response = json.loads(raw_response)
        entries = parsed_response.get("entries", [])
        print(f"Successfully parsed {len(entries)} legal norms")
        return entries
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Raw response: {raw_response}")
        return []
    


async def develop_amendment_proposals(task_description: str, relevant_norms: List[NormEntry]) -> List:
    
    """Develop amendment proposals for the relevant legal norms."""
    print("\n==== DEVELOP AMENDMENT PROPOSALS ====")
    
    # Convert relevant_norms to readable text format
    relevant_norms_text = "\n".join([f"- {norm.jurabk} {norm.enbez} Abs. {norm.P}" for norm in relevant_norms])
    
    prompt = f"""
        Du bist Legist im Bundesfinanzministerium und sollst einen Gesetzesentwurf anfertigen.

        Maßnahme: {task_description}

        Die Maßnahme soll durch Änderung eines oder mehrerer bereits bestehender Stammgesetze umgesetzt werden. 
        Entwickle abstrakte Regelungsalternativen vor dem gegebenen Regelungskontext.

        Regelungskontext: {relevant_norms_text}

        Gib als Antwort ausschließlich eine JSON-Liste zurück, welches wie folgt formatiert ist:

        {{
        "entries": [
            {{
            "proposalTitle": "Kurze, prägnante Bezeichnung der Alternative",
            "description": "Detaillierte Beschreibung der Alternative mit Begründung.",
            "affectedNorms": [
                {{
                "jurabk": "EStG",
                "enbez": "§ 21",
                "P": "2"
                }},
                {{
                "jurabk": "EStG", 
                "enbez": "§ 3",
                "P": "2a"
                }}
            ]
            }},
            {{
            "proposalTitle": "Kurze, prägnante Bezeichnung der Alternative",
            "description": "Detaillierte Beschreibung der Alternative mit Begründung",
            "affectedNorms": [
                {{
                "jurabk": "EStG",
                "enbez": "§ 21", 
                "P": "1"
                }}
            ]
            }}
        ]
        }}

        Hinweis: "jurabk" ist die Abkürzung für das betreffende Gesetz, "enbez" der Paragraph und "P" der jeweilige Absatz.
    """

    print("Querying LLM to develop amendment proposals...")
    raw_response = await query_openai(prompt)

    print(f"Response received. Length: {len(raw_response)} characters")
    
    try:
        parsed_response = json.loads(raw_response)
        entries = parsed_response.get("entries", [])
        print(f"Successfully parsed {len(entries)} amendment proposals")
        return entries
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Raw response: {raw_response}")
        return []
