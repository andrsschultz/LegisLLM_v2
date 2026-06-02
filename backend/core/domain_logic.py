import json
import os
from typing import List, Optional, Callable, Awaitable
from fastapi import HTTPException
from .llm_service import query_llm
from .models import NormEntry, ProposalEntry, AmendEntry
from .xml_parser import extract_table_of_contents, extract_section_from_law
from .utils import clean_json_string, format_norm_reference, resolve_law_xml_path, get_available_laws


async def identify_relevant_norms(task_description: str, api_key: str, model: str, selected_laws: Optional[List[str]] = None, on_thinking: Optional[Callable[[str], Awaitable[None]]] = None) -> List:

    """Identify the relevant legal norms for the given task."""
    print("\n==== IDENTIFY RELEVANT NORMS ====")
    print(f"Task description length: {len(task_description)} characters")

    all_laws = get_available_laws()
    laws_to_use = selected_laws if selected_laws else all_laws
    available_laws = ", ".join(laws_to_use)

    prompt = f"""
        Du bist Legist in einem Bundesministerium und sollst einen Gesetzesentwurf anfertigen.

        Maßnahme:  {task_description}

        Die Maßnahme soll durch Änderung eines oder mehrerer bereits bestehender Stammgesetze umgesetzt werde. Bestimme in einem ersten Schritt sämtliche für eine Änderung in Betracht kommende Rechtsnormen. Achte darauf, sämtliche von der Änderungsmaßnahme möglicherweise betroffenen Rechtsnormen einzubeziehen. Nehme noch keine Änderung vor.

        Verwende ausschließlich Gesetze aus der folgenden Liste verfügbarer Bundesgesetze:
        {available_laws}

        Gib als Antwort ausschließlich eine JSON-Liste zurück, welche wie folgt formatiert ist:

        {{
            "entries": [
                {{
                "jurabk": "<Abkürzung des Gesetzes>",   // z. B. "EStG"
                "enbez": "<§‑Angabe>"                  // z. B. "§ 21"
                }}
            ]
        }}

        Gib in diesem ersten Schritt nur die Vorschrift auf Paragraphenebene an. Nenne noch keine Absätze.

        Halte dich bitte **genau** an dieses JSON-Format und verwende keine zusätzlichen Außentexte oder Einleitungen.
    """

    print("Querying LLM to identify relevant norms...")
    raw_response = await query_llm(prompt, api_key, model or "gpt-4", on_thinking=on_thinking)

    print(f"Response received. Length: {len(raw_response)} characters")
    
    try:
        # Clean the response using the new helper function
        cleaned_response = clean_json_string(raw_response)
        parsed_response = json.loads(cleaned_response)
        entries = parsed_response.get("entries", [])
        print(f"Successfully parsed {len(entries)} legal norms")
        return entries
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Raw response: {raw_response}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse LLM response. The AI model returned an invalid JSON format. Please try again."
        )
    


async def develop_amendment_proposals(task_description: str, relevant_norms: List[NormEntry], api_key: str, model: str, on_thinking: Optional[Callable[[str], Awaitable[None]]] = None) -> List:
    
    """Develop amendment proposals for the relevant legal norms."""
    print("\n==== DEVELOP AMENDMENT PROPOSALS ====")
    
    # Convert relevant_norms to readable text format
    relevant_norms_text = "\n".join([
        f"- {format_norm_reference(norm.jurabk, norm.enbez, norm.P)}: {norm.wording}"
        for norm in relevant_norms
    ])
    
    prompt = f"""
        Du bist Legist in einem Bundesministerium und sollst einen Gesetzesentwurf anfertigen.

        Maßnahme: {task_description}

        Die Maßnahme soll durch Änderung eines oder mehrerer bereits bestehender Stammgesetze umgesetzt werden.

        Entwickle verschiedene Regelungsalternativen, mit denen die Maßnahme umgesetzt werden könnte. Jede Regelungsalternative stellt einen eigenständigen, in sich vollständigen Umsetzungsweg dar. Die Alternativen sollen sich inhaltlich voneinander unterscheiden — z.B. durch unterschiedliche Regelungstechnik, unterschiedlichen Regelungsort oder unterschiedlichen Regelungsumfang. Es geht nicht darum, die Maßnahme in Teilaspekte zu zerlegen, sondern um echte Alternativen, die jeweils für sich genommen die gesamte Maßnahme vollständig umsetzen.

        Regelungskontext: {relevant_norms_text}

        Gib als Antwort ausschließlich eine JSON-Liste zurück, welches wie folgt formatiert ist:

        {{
        "entries": [
            {{
            "proposalTitle": "Kurze, prägnante Bezeichnung der Alternative",
            "description": "Detaillierte Beschreibung der Alternative mit Begründung. Erläutere, worin sich diese Alternative von den anderen unterscheidet.",
            "affectedNorms": [
                {{
                "jurabk": "<Abkürzung des Gesetzes>",
                "enbez": "<§‑Angabe>",
                "P": "<Absatz>",
                "amendmentDescription": "<Abstrakte Beschreibung, welche Änderung notwendig zur Umsetzung der Regelungsalternative ist>"
                }}
            ]
            }}
        ]
        }}

        Wenn du die Überschrift änderst, gebe für "P" den Wert "Überschrift" zurück.

        Wichtige Regeln:
        - Jede Regelungsalternative muss die Maßnahme **vollständig** umsetzen. Das bedeutet: Jede Alternative muss in ihrem "affectedNorms"-Eintrag **sämtliche** Teiländerungen enthalten, die für die vollständige Umsetzung der Maßnahme erforderlich sind — sowohl unmittelbar betroffene als auch mittelbar anzupassende Normen (Folgeänderungen).
        - Stelle keine Alternative dar, die nur einen Teilaspekt der Maßnahme abdeckt. Jede Alternative muss für sich allein zur vollständigen Umsetzung genügen.
        - Es können zwei oder mehr Alternativen in Betracht kommen.

        Halte dich bitte **genau** an dieses JSON-Format und verwende keine zusätzlichen Außentexte oder Einleitungen.
    """

    print("Querying LLM to develop amendment proposals...")
    raw_response = await query_llm(prompt, api_key, model or "gpt-4", on_thinking=on_thinking)

    print(f"Response received. Length: {len(raw_response)} characters")
    
    try:
        # Clean the response using the new helper function
        cleaned_response = clean_json_string(raw_response)
        parsed_response = json.loads(cleaned_response)
        entries = parsed_response.get("entries", [])
        print(f"Successfully parsed {len(entries)} amendment proposals")
        return entries
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Raw response: {raw_response}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse LLM response. The AI model returned an invalid JSON format. Please try again."
        )
    

async def evaluate_proposals(task_description: str, relevant_norms: List[NormEntry], amendment_proposals: List[ProposalEntry], api_key: str, model: str, on_thinking: Optional[Callable[[str], Awaitable[None]]] = None) -> List:
    
    """Evaluate the amendment proposals."""
    print("\n==== EVALUATE PROPOSALS ====")
    print(f"Task description length: {len(task_description)} characters")
    print(f"Number of amendment proposals: {len(amendment_proposals)}")

    # Convert relevant_norms to readable text format
    relevant_norms_text = "\n".join([
        f"- {format_norm_reference(norm.jurabk, norm.enbez, norm.P)}: {norm.wording}"
        for norm in relevant_norms
    ])
    
    # Convert amendment_proposals to readable text format
    amendment_proposals_text = "\n\n".join([
        f"""{i+1}. **{proposal.proposalTitle}**
    **Beschreibung**: {proposal.description}
    **Betroffene Rechtsnormen**:\n""" + "\n".join([
            f"- {format_norm_reference(norm.jurabk, norm.enbez, norm.P)}  \n  Änderungsbeschreibung: {norm.amendmentDescription}"
            for norm in proposal.affectedNorms
        ])
        for i, proposal in enumerate(amendment_proposals)
    ])


    prompt = f"""
        Du bist Legist in einem Bundesministerium und sollst einen Gesetzesentwurf anfertigen.

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
            "proposalTitle": "VERWENDE EXAKT DEN TITEL AUS DEM EINGABETEXT",
            "pro": ["Pro-Argument 1", "Pro-Argument 2"],
            "contra": ["Contra-Argument 1", "Contra-Argument 2"]
            }}
        ]
        }}

        Die JSON Liste soll alle für die jeweilige Regelungsalternative in Betracht kommenden Argumente enthalten. Es können auch mehr auch jeweils mehr als zwei Argumente in Betracht kommen.

        Halte dich bitte **genau** an dieses JSON-Format und verwende keine zusätzlichen Außentexte oder Einleitungen.
    """

    print("Querying LLM to evaluate proposals...")
    raw_response = await query_llm(prompt, api_key, model or "gpt-4", on_thinking=on_thinking)

    print(f"Response received. Length: {len(raw_response)} characters")

    try:
        # Clean the response using the new helper function
        cleaned_response = clean_json_string(raw_response)
        parsed_response = json.loads(cleaned_response)
        entries = parsed_response.get("entries", [])
        print(f"Successfully parsed evaluation entries")
        return entries
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Raw response: {raw_response}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse LLM response. The AI model returned an invalid JSON format. Please try again."
        )



async def deep_evaluate_proposals(task_description: str, relevant_norms: List[NormEntry], amendment_proposal: ProposalEntry, api_key: str, model: str, on_thinking: Optional[Callable[[str], Awaitable[None]]] = None) -> List:
    
    """Deep Evaluate the amendment proposals against juridical, technical, and dogmatic criteria."""
    print("\n==== DEEP EVALUATE PROPOSALS ====")
    print(f"Task description length: {len(task_description)} characters")

    # Convert relevant_norms to readable text format
    relevant_norms_text = "\n".join([
        f"- {format_norm_reference(norm.jurabk, norm.enbez, norm.P)}: {norm.wording}"
        for norm in relevant_norms
    ])

    # Convert amendment_proposals to readable text format
    amendment_proposals_text = "\n\n".join([
        f"""**{amendment_proposal.proposalTitle}**
    **Beschreibung**: {amendment_proposal.description}
    **Betroffene Rechtsnormen**:\n""" + "\n".join([
            f"- {format_norm_reference(norm.jurabk, norm.enbez, norm.P)}  \n  Änderungsbeschreibung: {norm.amendmentDescription}"
            for norm in amendment_proposal.affectedNorms
        ])
    ])

    prompt = f"""
        Du bist Legist in einem Bundesministerium und sollst einen Gesetzesentwurf anfertigen.

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
        Auslegungsfragen (systematisch, teleologisch etc.) und mögliche Querverweise auf relevante Normen, Rechtskonzepte, Rechtsprechung etc. 
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
            "proposalTitle": "VERWENDE EXAKT DEN TITEL AUS DEM EINGABETEXT",
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

    print("Querying LLM to deep evaluate proposals...")
    raw_response = await query_llm(prompt, api_key, model or "gpt-4", on_thinking=on_thinking)

    print(f"Response received. Length: {len(raw_response)} characters")

    try:
        # Clean the response using the new helper function
        cleaned_response = clean_json_string(raw_response)
        parsed_response = json.loads(cleaned_response)
        entries = parsed_response.get("entries", [])
        print(f"Successfully parsed evaluation entries")
        return entries
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Raw response: {raw_response}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse LLM response. The AI model returned an invalid JSON format. Please try again."
        )



async def generate_final_amendment(task_description: str, amendment_proposal: ProposalEntry, relevant_norms: List[NormEntry], api_key: str,  model: str, custom_instructions: str | None = None, on_thinking: Optional[Callable[[str], Awaitable[None]]] = None) -> List:
    """Generate the final amendment text based on the selected proposal and any custom adjustments."""
    print("\n==== GENERATE FINAL AMENDMENT ====")
    print(f"Task description length: {len(task_description)} characters")

    # Convert relevant_norms to readable text format
    relevant_norms_text = "\n".join([
        f"- {format_norm_reference(norm.jurabk, norm.enbez, norm.P)}: {norm.wording}"
        for norm in relevant_norms
    ])
    
    # Convert amendment_proposals to readable text format
    amendment_proposals_text = "\n\n".join([
        f"""**{amendment_proposal.proposalTitle}**
    **Beschreibung**: {amendment_proposal.description}
    **Betroffene Rechtsnormen**:\n""" + "\n".join([
            f"- {format_norm_reference(norm.jurabk, norm.enbez, norm.P)}  \n  Änderungsbeschreibung: {norm.amendmentDescription}"
            for norm in amendment_proposal.affectedNorms
        ])
    ])

    prompt = f"""
        Du bist Legist in einem Bundesministerium und sollst einen Gesetzesentwurf anfertigen.

        Maßnahme: {task_description}

        Du hast bereits eine bestimmte Regelungsalternative ausgewählt:

        Regelungsalternative: {amendment_proposals_text}

        {'Zusätzliche Anpassungswünsche: ' + custom_instructions if custom_instructions else ''}

        Regelungskontext: {relevant_norms_text}

        Setze die Regelungsalternative um. Gib sowohl den ursprünglichen als auch den geänderten Wortlaut für jede betroffene Norm zurück. Gebe nur den Teil des Wortlauts zurück, der sich geändert hat, z.B. den Absatz, die Überschrift oder den gesamten Paragraphen. Geänderter und ursprünglicher Wortlaut müssen kongruent sein. Wenn davor und danach Normtext steht, markiere diesen mit "(...)". Entfällt der Wortlaut gebe als geändert Wortlaut "entfällt" an.
    
        Verwende dabei juristisch präzise Formulierungen und berücksichtige die gängigen Prinzipien der Legistik.

        Gib als Antwort ausschließlich eine JSON-Liste zurück, welche wie folgt formatiert ist:

        {{
            "entries": [
                {{
                    "amendedNorm": {{
                        "jurabk": "<Abkürzung des Gesetzes>",   // z. B. "EStG"
                        "enbez": "<Paragraf>",                  // z. B. "§ 21"
                        "P": "<Absatz>",                        // z. B. "1"
                        "originalWording": "<ursprünglicher Wortlaut>"
                        "amendedWording": "<geänderter Wortlaut>"
                    }}
                }}
            ]
        }}

        Halte dich bitte **genau** an dieses JSON-Format und verwende keine zusätzlichen Außentexte oder Einleitungen.
    """

    print("Querying LLM to generate final amendment...")
    raw_response = await query_llm(prompt, api_key, model or "gpt-4", on_thinking=on_thinking)

    print(f"Response received. Length: {len(raw_response)} characters")
    
    try:
        # Clean the response to remove markdown code blocks if present
        cleaned_response = clean_json_string(raw_response)
        parsed_response = json.loads(cleaned_response)
        raw_entries = parsed_response.get("entries", [])
        
        print(f"Successfully parsed {len(raw_entries)} amendment entries")
        return raw_entries
        
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Raw response: {raw_response}")
        # Fallback: return empty list if JSON parsing fails
        return []






async def identify_relevant_norms_multistep(task_description: str, api_key: str, model: str, selected_laws: Optional[List[str]] = None, on_step: Optional[callable] = None, on_thinking: Optional[Callable[[str], Awaitable[None]]] = None) -> List[NormEntry]:

    """Identify the relevant legal norms for the given task."""
    print("\n==== IDENTIFY RELEVANT NORMS ====")
    print(f"Task description length: {len(task_description)} characters")

    norm_entries: List[NormEntry] = []

    print("Content of norm_entries:", norm_entries)

    # Step 1: Identify potentially affected laws
    if on_step: await on_step(0, "Identifiziere betroffene Gesetze...")
    print("Step 1: Querying LLM to identify potentially affected laws...")

    all_laws = get_available_laws()
    laws_to_use = selected_laws if selected_laws else all_laws
    available_laws = ", ".join(laws_to_use)

    prompt_step_1 = f"""
        Du bist Legist in einem Bundesministerium und sollst einen Gesetzesentwurf anfertigen.

        Maßnahme:  {task_description}

        Die Maßnahme soll durch Änderung eines oder mehrerer bereits bestehender Stammgesetze umgesetzt werde. Bestimme in einem ersten Schritt sämtliche für eine Änderung in Betracht kommende Rechtsnormen. Achte darauf, sämtliche von der Änderungsmaßnahme möglicherweise betroffenen Rechtsnormen einzubeziehen. Nehme noch keine Änderung vor.

        Gebe mir im ersten Schritt NUR den Namen möglicherweise betroffenener Gesetze wieder.

        Verwende ausschließlich Gesetze aus der folgenden Liste verfügbarer Bundesgesetze:
        {available_laws}

        Gib als Antwort ausschließlich eine JSON-Liste zurück, welche wie folgt formatiert ist:

        {{
            "entries": [
                {{
                "jurabk": "<Abkürzung des Gesetzes>",   // z. B. "EStG"
                }}
            ]
        }}

        Halte dich bitte **genau** an dieses JSON-Format und verwende keine zusätzlichen Außentexte oder Einleitungen.

    """

    raw_response_step1 = await query_llm(prompt_step_1, api_key, model or "gpt-4", on_thinking=on_thinking)
	
    print(f"Step 1 response received. Length: {len(raw_response_step1)} characters")
    
    try:
        # Clean the response to remove markdown code blocks if present
        cleaned_response = clean_json_string(raw_response_step1)
        parsed_response_step1 = json.loads(cleaned_response)
        raw_entries = parsed_response_step1.get("entries", [])
        
        # Convert dictionaries to NormEntry objects
        norm_entries = [NormEntry(**entry) for entry in raw_entries]
        print(f"Step 1: Successfully identified {len(norm_entries)} potentially affected laws")
    except json.JSONDecodeError as e:
        print(f"Step 1: Error parsing JSON response: {e}")
        print(f"Step 1: Raw response: {raw_response_step1}")
        print(f"Step 1: Cleaned response: {clean_json_string(raw_response_step1)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse LLM response in step 1. The AI model returned an invalid JSON format. Please try again."
        )
    except Exception as e:
        print(f"Step 1: Error creating NormEntry objects: {e}")
        return []
    
    if not norm_entries:
        print("Step 1: No laws identified, returning empty list")
        return []
    
    print("Content of norm_entries:", norm_entries)

    temp_norm_entries = []

    for entry in norm_entries:

        xml_file_path = resolve_law_xml_path(
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"),
            entry.jurabk
        )
        law_toc = extract_table_of_contents(xml_file=xml_file_path)

        # Step 2: For each law, identify relevant paragraphs
        if on_step: await on_step(1, f"Bestimme relevante Paragraphen in {entry.jurabk}...")

        prompt_step_2 = f"""
        Du bist Legist in einem Bundesministerium und sollst einen Gesetzesentwurf anfertigen.

        Maßnahme:  {task_description}

        Die Maßnahme soll durch Änderung eines oder mehrerer bereits bestehender Stammgesetze umgesetzt werde. Bestimme in einem ersten Schritt sämtliche für eine Änderung in Betracht kommende Rechtsnormen. Achte darauf, sämtliche von der Änderungsmaßnahme möglicherweise betroffenen Rechtsnormen einzubeziehen. Nehme noch keine Änderung vor.

        Du hast bereits die Abkürzung des möglicherweise betroffenen Gesetzes identifiziert. Es handelt sich um das Gesetz mit der Abkürzung {entry.jurabk}.

        Hier das Inhaltsverzeichnis des {entry.jurabk}: {law_toc}

        Gebe mir im nächsten Schritt NUR die Paragraphen möglicherweise betroffener Rechtsnormen wieder.

        Gib als Antwort ausschließlich eine JSON-Liste zurück, welche wie folgt formatiert ist:

        {{
            "entries": [
                {{
                "jurabk": "<Abkürzung des Gesetzes>",   // z. B. "EStG"
                "enbez": "<§‑Angabe>",                  // z. B. "§ 21"
                }}
            ]
        }}

        Halte dich bitte **genau** an dieses JSON-Format und verwende keine zusätzlichen Außentexte oder Einleitungen

        """

        raw_response_step2 = await query_llm(prompt_step_2, api_key, model or "gpt-4", on_thinking=on_thinking)
        
        print(f"Step 2 response received. Length: {len(raw_response_step2)} characters")
        
        try:
            # Clean the response to remove markdown code blocks if present
            cleaned_response = clean_json_string(raw_response_step2)
            parsed_response_step2 = json.loads(cleaned_response)
            raw_entries = parsed_response_step2.get("entries", [])
            
            # Convert dictionaries to NormEntry objects
            step2_entries = [NormEntry(**entry) for entry in raw_entries]
        except json.JSONDecodeError as e:
            print(f"Step 2: Error parsing JSON response: {e}")
            print(f"Step 2: Raw response: {raw_response_step2}")
            print(f"Step 2: Cleaned response: {clean_json_string(raw_response_step2)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse LLM response in step 2. The AI model returned an invalid JSON format. Please try again."
            )
        except Exception as e:
            print(f"Step 2: Error creating NormEntry objects: {e}")
            return []
        
        if not step2_entries:
            print("Step 2: No laws identified, continuing with next law")
            continue
            
        # Add the entries from this law to the final result
        temp_norm_entries.extend(step2_entries)

    print(f"Step 2: Successfully identified {len(temp_norm_entries)} laws with paragraphs")

    norm_entries = temp_norm_entries

    print("Content of norm_entries:", norm_entries)

    if on_step: await on_step(2, "Lade Normtexte...")
    print("Step 3: Add wordings for each norm entry")

    # Define data directory path
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

    # Track already extracted sections to avoid duplicates
    extracted_sections = {}

    for i, entry in enumerate(norm_entries):
        jurabk = entry.jurabk
        enbez = entry.enbez

        # Create unique key for section
        section_key = f"{jurabk}|{enbez}"

        # Check if we already extracted this section
        if section_key in extracted_sections:
            # Reuse the already extracted wording
            wording = extracted_sections[section_key]
        else:
            xml_file = resolve_law_xml_path(data_dir, jurabk)
            section_num = enbez.replace("§", "").strip() if enbez else ""

            wording = ""
            try:
                # Extract the entire section
                wording = extract_section_from_law(xml_file, section_num)
                # Cache the extracted wording
                extracted_sections[section_key] = wording
            except Exception as e:
                print(f"Error extracting wording for {jurabk} {enbez}: {e}")
                wording = f"Fehler beim Laden des Wortlauts für {jurabk} {enbez}"
                extracted_sections[section_key] = wording

        # Create new NormEntry object with wording and replace the existing entry
        norm_entries[i] = NormEntry(
            jurabk=jurabk,
            enbez=enbez,
            P=None,
            wording=wording
        )


    print("Content of norm_entries:", norm_entries)

    temp_norm_entries = []

    for entry in norm_entries:
        if on_step: await on_step(3, f"Identifiziere relevante Absätze in {entry.enbez} {entry.jurabk}...")

        # Step 4: Identify relevant paragraphs in the wording
        prompt_step_4 = f"""
            Du bist Legist in einem Bundesministerium und sollst einen Gesetzesentwurf anfertigen.

            Maßnahme:  {task_description}

            Die Maßnahme soll durch Änderung eines oder mehrerer bereits bestehender Stammgesetze umgesetzt werde. Bestimme in einem ersten Schritt sämtliche für eine Änderung in Betracht kommende Rechtsnormen. Achte darauf, sämtliche von der Änderungsmaßnahme möglicherweise betroffenen Rechtsnormen einzubeziehen. Nehme noch keine Änderung vor.

            Du hast bereits das möglicherweise betroffene Gesetz identifiziert. Dieses ist {entry.enbez} {entry.jurabk}.

            Bestimme im nächsten Schritt den maßgeblichen Paragraphen von {entry.enbez} {entry.jurabk}.
            
            Hier der Wortlaut von {entry.enbez} {entry.jurabk}.: {entry.wording}

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

            Wenn der Paragraph keinen Absatz hat, lasse das Feld "P" aus. Es können auch mehrere Paragraphen betroffen sein. In diesem Fall erstelle mehrere Einträge in der Liste.

            Halte dich bitte **genau** an dieses JSON-Format und verwende keine zusätzlichen Außentexte oder Einleitungen.
        """

        print(prompt_step_4)

        raw_response_step4 = await query_llm(prompt_step_4, api_key, model or "gpt-4", on_thinking=on_thinking)
        
        print(f"Step 4 response received. Length: {len(raw_response_step4)} characters")
        
        try:
            # Clean the response to remove markdown code blocks if present
            cleaned_response = clean_json_string(raw_response_step4)
            parsed_response_step4 = json.loads(cleaned_response)
            raw_entries = parsed_response_step4.get("entries", [])
            
            # Convert dictionaries to NormEntry objects
            step4_entries = [NormEntry(**entry) for entry in raw_entries]
        except json.JSONDecodeError as e:
            print(f"Step 4: Error parsing JSON response: {e}")
            print(f"Step 4: Raw response: {raw_response_step4}")
            print(f"Step 4: Cleaned response: {clean_json_string(raw_response_step4)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse LLM response in step 4. The AI model returned an invalid JSON format. Please try again."
            )
        except Exception as e:
            print(f"Step 4: Error creating NormEntry objects: {e}")
            return []
        
        if not step4_entries:
            print("Step 4: No laws identified, continuing with next law")
            continue
            
        # Add the entries from this law to the final result
        temp_norm_entries.extend(step4_entries)
    
    norm_entries = temp_norm_entries

    print("Content of norm_entries:", norm_entries)

    print(f"Step 4: Successfully identified {len(norm_entries)} laws with paragraphs and wordings")


    if on_step: await on_step(4, "Finalisiere Ergebnisse...")
    # Step 5: Reattach wording for each norm entry, manual reattachment to save api costs, reaattach wording of whole section each time to keep context
    temp_norm_entries = []

    # Track already extracted sections to avoid duplicates
    extracted_sections_step5 = {}

    for entry in norm_entries:
        jurabk = entry.jurabk
        enbez = entry.enbez
        P = entry.P

        # Create unique key for section
        section_key = f"{jurabk}|{enbez}"

        # Check if we already extracted this section
        if section_key in extracted_sections_step5:
            # Reuse the already extracted wording
            wording = extracted_sections_step5[section_key]
        else:
            # Construct XML file path
            xml_file = resolve_law_xml_path(data_dir, jurabk)

            # Extract section number from enbez (e.g., "§ 21" -> "21")
            section_num = enbez.replace("§", "").strip() if enbez else ""

            # Get the wording from XML
            wording = ""
            try:
                # Extract the entire section
                wording = extract_section_from_law(xml_file, section_num)
                # Cache the extracted wording
                extracted_sections_step5[section_key] = wording
            except Exception as e:
                print(f"Error extracting wording for {jurabk} {enbez} P{P}: {e}")
                wording = f"Fehler beim Laden des Wortlauts für {jurabk} {enbez}"
                extracted_sections_step5[section_key] = wording

        # Create NormEntry object
        norm_entry = NormEntry(
            jurabk=jurabk,
            enbez=enbez,
            P=P,
            wording=wording
        )
        temp_norm_entries.append(norm_entry)

    print("Content of norm_entries:", norm_entries)

    norm_entries = temp_norm_entries




    

    return norm_entries


async def generate_aenderungsbefehle(task_description: str, final_amendments: List[AmendEntry], api_key: str, model: str, on_thinking: Optional[Callable[[str], Awaitable[None]]] = None) -> str:
    """Generate Änderungsbefehle from final amendments using LLM."""
    print("\n==== GENERATE ÄNDERUNGSBEFEHLE ====")
    print(f"Task description: {task_description}")
    print(f"Number of final amendments: {len(final_amendments)}")
    print(f"Model: {model}")
    
    # Load template from file
    templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
    aenderungsbefehl_template_path = os.path.join(templates_dir, "aenderungsbefehl_prompt.md")
    
    try:
        with open(aenderungsbefehl_template_path, 'r', encoding='utf-8') as f:
            aenderungsbefehl_template = f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading Änderungsbefehl template: {str(e)}")
    
    # Format amendment data for the prompt
    amendment_data = "\n\n".join([
        f"""**Norm:** {amendment.originalNorm.jurabk} {amendment.originalNorm.enbez}{f" Absatz {amendment.originalNorm.P}" if amendment.originalNorm.P else ''}
**Ursprünglicher Wortlaut:** {amendment.originalNorm.wording or 'Nicht verfügbar'}
**Geänderter Wortlaut:** {amendment.amendedNorm.wording or 'Nicht verfügbar'}
**Art der Änderung:** {amendment.amendedNorm.amendmentDescription or 'Ersetzung'}"""
        for amendment in final_amendments
    ])
    
    # Replace placeholder with actual amendment data
    aenderungsbefehl_prompt = aenderungsbefehl_template.replace(
        '[HIER WERDEN DIE NORM-ÄNDERUNGEN EINGEFÜGT]',
        amendment_data
    )
    
    # Query LLM for Änderungsbefehle generation
    print("Querying LLM to generate Änderungsbefehle...")
    response = await query_llm(aenderungsbefehl_prompt, api_key, model, on_thinking=on_thinking)
    
    print(f"Response received. Length: {len(response)} characters")
    return response


async def generate_gesetzesentwurf_content(task_description: str, aenderungsbefehle: str, api_key: str, model: str, final_amendments: Optional[List] = None, on_thinking: Optional[Callable[[str], Awaitable[None]]] = None) -> str:
    """Generate Gesetzesentwurf content from Änderungsbefehle using LLM."""
    print("\n==== GENERATE GESETZESENTWURF CONTENT ====")
    print(f"Task description: {task_description}")
    print(f"Änderungsbefehle length: {len(aenderungsbefehle)} characters")
    print(f"Model: {model}")
    
    # Extract metadata for all affected laws
    law_metadata = {}
    if final_amendments:
        print("Extracting metadata for affected laws...")
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        
        # Collect unique law abbreviations
        law_codes = set()
        for amendment in final_amendments:
            if hasattr(amendment, 'originalNorm') and amendment.originalNorm and amendment.originalNorm.jurabk:
                law_codes.add(amendment.originalNorm.jurabk)
            elif hasattr(amendment, 'amendedNorm') and amendment.amendedNorm and amendment.amendedNorm.jurabk:
                law_codes.add(amendment.amendedNorm.jurabk)
        
        print(f"Found law codes: {law_codes}")
        
        # Extract raw metadata XML for each law
        from .xml_parser import extract_raw_metadaten_xml
        for law_code in law_codes:
            xml_file = os.path.join(data_dir, f"{law_code}.xml")
            metadata = extract_raw_metadaten_xml(xml_file)
            if "error" not in metadata:
                law_metadata[law_code] = metadata
                print(f"Successfully extracted raw metadata XML for {law_code}")
            else:
                print(f"Failed to extract metadata for {law_code}: {metadata.get('error')}")
    
    # Load template from file
    templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
    gesetzesentwurf_template_path = os.path.join(templates_dir, "gesetzesentwurf_prompt.md")
    
    try:
        with open(gesetzesentwurf_template_path, 'r', encoding='utf-8') as f:
            gesetzesentwurf_template = f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading Gesetzesentwurf template: {str(e)}")
    
    # Format law metadata and group amendments by law
    metadata_text = ""
    grouped_changes = {}
    
    if final_amendments and law_metadata:
        # Group amendments by law
        for amendment in final_amendments:
            law_code = None
            if hasattr(amendment, 'originalNorm') and amendment.originalNorm and amendment.originalNorm.jurabk:
                law_code = amendment.originalNorm.jurabk
            elif hasattr(amendment, 'amendedNorm') and amendment.amendedNorm and amendment.amendedNorm.jurabk:
                law_code = amendment.amendedNorm.jurabk
            
            if law_code:
                if law_code not in grouped_changes:
                    grouped_changes[law_code] = []
                grouped_changes[law_code].append(amendment)
        
        # Create structured metadata and change information with raw XML
        metadata_text = "\n\n**GESETZESMETADATEN (RAW XML) UND STRUKTURIERTE ÄNDERUNGEN:**\n"
        
        for law_code, metadata in law_metadata.items():
            if metadata.get("raw_metadaten_xml"):
                jurabk = metadata.get("jurabk", law_code)
                metadata_text += f"\n**{law_code} ({jurabk}):**\n"
                
                # Add raw XML metadata for LLM to parse
                metadata_text += "RAW METADATEN XML:\n"
                metadata_text += f"```xml\n{metadata['raw_metadaten_xml']}\n```\n"
                
                # Add grouped changes for this law
                if law_code in grouped_changes:
                    metadata_text += f"ÄNDERUNGEN FÜR DIESES GESETZ:\n"
                    for i, amendment in enumerate(grouped_changes[law_code], 1):
                        if hasattr(amendment, 'originalNorm') and amendment.originalNorm:
                            norm_ref = f"{amendment.originalNorm.enbez}"
                            if amendment.originalNorm.P:
                                norm_ref += f" Abs. {amendment.originalNorm.P}"
                            metadata_text += f"  {i}. {norm_ref}\n"
                metadata_text += "\n"
        
        # Add current date information
        from datetime import datetime
        current_date = datetime.now()
        german_months = ["", "Januar", "Februar", "März", "April", "Mai", "Juni", 
                        "Juli", "August", "September", "Oktober", "November", "Dezember"]
        formatted_date = f"{current_date.day}. {german_months[current_date.month]} {current_date.year}"
        
        metadata_text += f"**AKTUELLES DATUM:**\n"
        metadata_text += f"Heute: {formatted_date}\n"
        metadata_text += f"Verwende dieses Datum für '**Vom {formatted_date}**' im Gesetzesentwurf\n\n"
        
        metadata_text += "**WICHTIGE ANWEISUNGEN:**\n"
        metadata_text += f"- Es werden {len(law_metadata)} Gesetze geändert: {', '.join(law_metadata.keys())}\n"
        metadata_text += "- Erstelle für JEDES Gesetz einen separaten Artikel\n"
        metadata_text += "- Parse die RAW METADATEN XML oben und erstelle daraus die korrekten Vollzitate\n"
        metadata_text += "- Verwende die XML-Daten für: Zitiername, Ausfertigungsdatum, Fundstelle, letzte Änderung\n"
        metadata_text += "- Gruppiere die Änderungsbefehle nach Gesetzen in den entsprechenden Artikeln\n"
        metadata_text += f"- Ersetze '**Vom ...**' durch '**Vom {formatted_date}**'\n"
    
    # Replace placeholders
    gesetzesentwurf_prompt = gesetzesentwurf_template.replace(
        '[HIER WERDEN DIE ÄNDERUNGSBEFEHLE EINGEFÜGT]',
        aenderungsbefehle + metadata_text
    )
    
    # Query LLM for Gesetzesentwurf generation
    print("Querying LLM to generate Gesetzesentwurf...")
    response = await query_llm(gesetzesentwurf_prompt, api_key, model, on_thinking=on_thinking)
    
    print(f"Response received. Length: {len(response)} characters")
    return response


















