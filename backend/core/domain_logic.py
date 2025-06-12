import json
import os
from typing import List, Optional
from .llm_service import query_openai, query_deepinfra
from .models import NormEntry, ProposalEntry


#TBD: Functions always use OpenAI, but should use DeepInfra if specified

async def identify_relevant_norms(task_description: str, api_key: str, model: str) -> List:
    
    """Identify the relevant legal norms for the given task."""
    print("\n==== IDENTIFY RELEVANT NORMS ====")
    print(f"Task description length: {len(task_description)} characters")
    
    prompt = f"""
        Du bist Legist im Bundesfinanzministerium und sollst einen Gesetzesentwurf anfertigen.

        Maßnahme:  {task_description}

        Die Maßnahme soll durch Änderung eines oder mehrerer bereits bestehender Stammgesetze umgesetzt werde. Bestimme in einem ersten Schritt sämtliche für eine Änderung in Betracht kommende Rechtsnormen. Achte darauf, sämtliche von der Änderungsmaßnahme möglicherweise betroffenen Rechtsnormen einzubeziehen. Nehme noch keine Änderung vor.

        Gib als Antwort ausschließlich eine JSON-Liste zurück, welche wie folgt formatiert ist:

        {{
            "entries": [
                {{
                "jurabk": "<Abkürzung des Gesetzes>",   // z. B. "EStG"
                "enbez": "<§‑Angabe>",                  // z. B. "§ 21"
                "P": "<Absatz>"               // z. B. "2a"
                }}
            ]
        }}

        Halte dich bitte **genau** an dieses JSON-Format und verwende keine zusätzlichen Außentexte oder Einleitungen.
    """
    

    print("Querying LLM to identify relevant norms...")
    raw_response = await query_openai(prompt, api_key, model or "gpt-3.5-turbo")

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
    


async def develop_amendment_proposals(task_description: str, relevant_norms: List[NormEntry], api_key: str, model: str) -> List:
    
    """Develop amendment proposals for the relevant legal norms."""
    print("\n==== DEVELOP AMENDMENT PROPOSALS ====")
    
    # Convert relevant_norms to readable text format
    relevant_norms_text = "\n".join([f"- {norm.jurabk} {norm.enbez} Abs. {norm.P}: {norm.wording}" for norm in relevant_norms])
    
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
                "jurabk": "<Abkürzung des Gesetzes>", 
                "enbez": "<§‑Angabe>",             
                "P": "<Absatz>"             
                }},
                {{
                "jurabk": "<Abkürzung des Gesetzes>", 
                "enbez": "<§‑Angabe>",                
                "P": "<Absatz>"             
                }}
            ]
            }},
            {{
            "proposalTitle": "Kurze, prägnante Bezeichnung der Alternative",
            "description": "Detaillierte Beschreibung der Alternative mit Begründung",
            "affectedNorms": [
                {{
                "jurabk": "<Abkürzung des Gesetzes>",   
                "enbez": "<§‑Angabe>",                  
                "P": "<Absatz>"          
                }}
            ]
            }}
        ]
        }}

        Die JSON Liste soll sämtliche Regelungsalternativen enthalten, die für die Maßnahme in Betracht kommen. Es können auch mehr als zwei Regelungsalternativen in Betracht kommen.

        Halte dich bitte **genau** an dieses JSON-Format und verwende keine zusätzlichen Außentexte oder Einleitungen.
    """

    print("Querying LLM to develop amendment proposals...")
    raw_response = await query_openai(prompt, api_key, model or "gpt-3.5-turbo")

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
    

async def evaluate_proposals(task_description: str, relevant_norms: List[NormEntry], amendment_proposals: List[ProposalEntry], api_key: str, model: str) -> List:
    
    """Evaluate the amendment proposals."""
    print("\n==== EVALUATE PROPOSALS ====")
    print(f"Task description length: {len(task_description)} characters")
    print(f"Number of amendment proposals: {len(amendment_proposals)}")

    # Convert relevant_norms to readable text format
    relevant_norms_text = "\n".join([f"- {norm.jurabk} {norm.enbez} Abs. {norm.P}: {norm.wording}" for norm in relevant_norms])
    
    # Convert amendment_proposals to readable text format
    amendment_proposals_text = "\n".join([
        f"- {proposal.proposalTitle}: {proposal.description}\n  Affected Norms: {', '.join([f'{norm.jurabk} {norm.enbez} Abs. {norm.P}' for norm in proposal.affectedNorms])}" 
        for proposal in amendment_proposals
    ])


    prompt = f"""
        Du bist Legist im Bundesfinanzministerium und sollst einen Gesetzesentwurf anfertigen.

        Maßnahme: {task_description}

        Die Maßnahme soll durch folgende mögliche Änderungen umgesetzt werden: 
        {amendment_proposals_text}

        Regelungskontext: {relevant_norms_text}

        Füge jeder von dir Änderungsmaßnahmen im nächsten Schritt eine Abwägung hinzu, in deren Rahmen du evaluierst,
        was aus juristischer, rechtstechnischer und dogmatischer Sicht für und was gegen die jeweilige Änderung spricht. 
        Politische Erwägungen sind dabei zu vernachlässigen.
        Sortiere die Änderungsvorschläge nach dem Grad deren Eignung im Sinne der vorgenannten Abwägung.

        Gib als Antwort ausschließlich eine JSON-Liste zurück, welches wie folgt formatiert ist:

        {{
        "entries": [
            {{
            "proposalTitle": "Kurze, prägnante Bezeichnung der Alternative mit Nennung der zu ändernden Norm",
            "affectedNorms": [
                {{
                "jurabk": "<Abkürzung des Gesetzes>",  
                "enbez": "<§‑Angabe>",                
                "P": "<Absatz>"               
                }}
            ],
            "pro": ["Pro-Argument 1", "Pro-Argument 2"],
            "contra": ["Contra-Argument 1", "Contra-Argument 2"]
            }}
        ]
        }}

        Die JSON Liste soll alle für die jeweilige Regelungsalternative in Betracht kommenden Argumente enthalten. Es können auch mehr auch jeweils mehr als zwei Argumente in Betracht kommen.

        Halte dich bitte **genau** an dieses JSON-Format und verwende keine zusätzlichen Außentexte oder Einleitungen.
    """

    print("Querying LLM to evaluate proposals...")
    raw_response = await query_openai(prompt, api_key, model or "gpt-3.5-turbo")

    print(f"Response received. Length: {len(raw_response)} characters")
    
    try:
        parsed_response = json.loads(raw_response)
        entries = parsed_response.get("entries", [])
        print(f"Successfully parsed evaluation entries")
        return entries
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Raw response: {raw_response}")
        return []

    

async def deep_evaluate_proposals(task_description: str, relevant_norms: List[NormEntry], amendment_proposal: ProposalEntry, api_key: str, model: str) -> List:
    
    """Deep Evaluate the amendment proposals against juridical, technical, and dogmatic criteria."""
    print("\n==== DEEP EVALUATE PROPOSALS ====")
    print(f"Task description length: {len(task_description)} characters")

    # Convert relevant_norms to readable text format
    relevant_norms_text = "\n".join([f"- {norm.jurabk} {norm.enbez} Abs. {norm.P}: {norm.wording}" for norm in relevant_norms])
    
    # Convert amendment_proposal to readable text format
    amendment_proposals_text = f"- {amendment_proposal.proposalTitle}: {amendment_proposal.description}\n  Affected Norms: {', '.join([f'{norm.jurabk} {norm.enbez} Abs. {norm.P}' for norm in amendment_proposal.affectedNorms])}"

    prompt = f"""
        Du bist Legist im Bundesfinanzministerium und sollst einen Gesetzesentwurf anfertigen.

        Maßnahme: {task_description}

        Du hast bereits eine bestimmte Regelungsalternative ausgewählt:

        Regelungsalternative: {amendment_proposals_text}

        Regelungskontext: {relevant_norms_text}

        Bitte unterziehe diesen Änderungsvorschlag einer vertieften Abwägung und nutze dabei insbesondere 
        juristische, rechtstechnische und dogmatische Gesichtspunkte. Politische Erwägungen bleiben außen vor. 
        Berücksichtige zusätzlich mögliche Folgen in Bezug auf:

        - Verwaltungsaufwand (für Behörden)
        - Fiskalische Auswirkungen (z.B. Steuerausfälle oder Mehreinnahmen)
        - Praktikabilität für Bürgerinnen und Bürger bzw. Unternehmen

        Strukturiere deine Evaluation folgendermaßen:

        1. Juristische Beurteilung
        - Beziehe dich auf relevante verfassungsrechtliche Anforderungen, EU-Rechtskonformität, 
        Auslegungsfragen (systematisch, teleologisch etc.) und mögliche Querverweise. 
        2. Rechtstechnische Beurteilung
        - Prüfe Klarheit der Regelung, Anschlussfähigkeit an bestehende Gesetzesstrukturen, 
        Widersprüche oder Dopplungen, ggf. Formulierungsvorschläge. 
        3. Dogmatische Beurteilung 
        - Ordne die Änderung in die Grundsätze des Steuerrechts (oder des betroffenen Rechtsgebiets) ein. 
        - Prüfe, ob zentrale Rechtsprinzipien tangiert werden oder ob es dogmatische Unstimmigkeiten gibt. 
        4. Folgenabschätzung
        - Erläutere absehbaren Verwaltungsaufwand, fiskalische Effekte und Praktikabilität/Umsetzbarkeit. 
        - Gehe auch auf mögliche Übergangs- oder Durchführungsregelungen ein. 

        Fasse die Vor- und Nachteile (Pro/Contra) kompakt zusammen und benenne offene Fragen oder 
        Nachbesserungsbedarf. 

        Gib als Antwort ausschließlich eine JSON-Liste zurück, welches wie folgt formatiert ist:

        {{
        "entries": [
            {{
            "proposalTitle": "Kurze, prägnante Bezeichnung der Alternative mit Nennung der zu ändernden Norm",
            "affectedNorms": [
                {{
                "jurabk": "<Abkürzung des Gesetzes>",  
                "enbez": "<§‑Angabe>",                  
                "P": "<Absatz>"               
                }}
            ],
            "juristischeBeurteilung": {{
                "Bewertung": "Detaillierte juristische Bewertung",
                "PotentielleProbleme": "Beschreibung möglicher rechtlicher Probleme",
                "Querverweise": [
                    {{
                    "jurabk": "<Abkürzung des Gesetzes>",   
                    "enbez": "<§‑Angabe>",              
                    "P": "<Absatz>"               
                    }}
                ]
            }},
            "rechtstechnischeBeurteilung": {{
                "Klarheit": "Bewertung der Klarheit der Regelung",
                "Formulierungsvorschlag": "Konkreter Formulierungsvorschlag",
                "Risikopunkte": ["Risikopunkt 1", "Risikopunkt 2"]
            }},
            "dogmatischeBeurteilung": {{
                "Systematik": "Bewertung der systematischen Einordnung",
                "Prinzipien": "Bewertung der Vereinbarkeit mit Rechtsprinzipien"
            }},
            "folgenabschätzung": {{
                "Verwaltungsaufwand": "Bewertung des Verwaltungsaufwands",
                "FiskalischeAuswirkungen": "Bewertung der fiskalischen Auswirkungen",
                "Praktikabilität": "Bewertung der praktischen Umsetzbarkeit",
                "Übergangsregelungen": "Notwendige Übergangsregelungen"
            }},
            "fazitProContra": {{
                "Pro": ["Pro-Argument 1", "Pro-Argument 2"],
                "Contra": ["Contra-Argument 1", "Contra-Argument 2"],
                "OffeneFragen": ["Offene Frage 1", "Offene Frage 2"]
            }}
            }}
        ]
        }}

        Die JSON Liste soll alle für die Regelungsalternative in Betracht kommenden Argumente enthalten. Es können auch mehr auch jeweils mehr als zwei Argumente in Betracht kommen.

        Halte dich bitte **genau** an dieses JSON-Format und verwende keine zusätzlichen Außentexte oder Einleitungen.
    """

    print("Querying LLM to evaluate proposals...")
    raw_response = await query_openai(prompt, api_key, model or "gpt-3.5-turbo")

    print(f"Response received. Length: {len(raw_response)} characters")
    
    try:
        parsed_response = json.loads(raw_response)
        entries = parsed_response.get("entries", [])
        print(f"Successfully parsed evaluation entries")
        return entries
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Raw response: {raw_response}")
        return []



async def generate_final_amendment(task_description: str, amendment_proposal: ProposalEntry, relevant_norms: List[NormEntry], api_key: str,  model: str, custom_instructions: str | None = None) -> List:
    """Generate the final amendment text based on the selected proposal and any custom adjustments."""
    print("\n==== GENERATE FINAL AMENDMENT ====")
    print(f"Task description length: {len(task_description)} characters")

    # Convert relevant_norms to readable text format
    relevant_norms_text = "\n".join([f"- {norm.jurabk} {norm.enbez} Abs. {norm.P}: {norm.wording}" for norm in relevant_norms])
    
    # Convert amendment_proposal to readable text format
    amendment_proposals_text = f"- {amendment_proposal.proposalTitle}: {amendment_proposal.description}\n  Affected Norms: {', '.join([f'{norm.jurabk} {norm.enbez} Abs. {norm.P}' for norm in amendment_proposal.affectedNorms])}"

    prompt = f"""
        Du bist Legist im Bundesfinanzministerium und sollst einen Gesetzesentwurf anfertigen.

        Maßnahme: {task_description}

        Du hast bereits eine bestimmte Regelungsalternative ausgewählt:

        Regelungsalternative: {amendment_proposals_text}

        {'Zusätzliche Anpassungswünsche: ' + custom_instructions if custom_instructions else ''}

        Regelungskontext: {relevant_norms_text}

        Mache einen Änderungsvorschlag. Gebe die ausschließlich die Norm in der geänderten Fassung zurück. Hebe Änderungen mit [ ] hervor.
    
        Verwende dabei juristisch präzise Formulierungen und berücksichtige die gängigen Prinzipien der Legistik.

        Gebe ausschließlich die Norm in der geänderten Fassung zurück und verwende keine zusätzlichen Außentexte oder Einleitungen.
    """

    print("Querying LLM to generate final amendment...")
    raw_response = await query_openai(prompt, api_key, model or "gpt-3.5-turbo")

    print(f"Response received. Length: {len(raw_response)} characters")
    
    # Since we're asking for direct text output (not JSON), return the text directly
    # The response should be the amended norm text
    return [{"amendedNorm": raw_response.strip()}]

