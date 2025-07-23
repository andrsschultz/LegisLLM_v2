import json
import os
from typing import List, Optional
from fastapi import HTTPException
from .llm_service import query_llm
from .models import NormEntry, ProposalEntry
from .xml_parser import extract_table_of_contents, extract_section_from_law
from .utils import clean_json_string


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
    raw_response = await query_llm(prompt, api_key, model or "gpt-4")

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
                "P": "<Absatz>",
                "amendmentDescription": "<Abstrakte Beschreibung, welche Änderung notwendig zur Umsetzung der Regelungsalternative ist>"        
                }},
                {{
                "jurabk": "<Abkürzung des Gesetzes>", 
                "enbez": "<§‑Angabe>",                
                "P": "<Absatz>",
                "amendmentDescription": "<Abstrakte Beschreibung, welche Änderung notwendig zur Umsetzung der Regelungsalternative ist>"          
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
                "P": "<Absatz>",
                "amendmentDescription": "<Abstrakte Beschreibung, welche Änderung notwendig zur Umsetzung der Regelungsalternative ist>"           
                }}
            ]
            }}
        ]
        }}

        Die JSON Liste soll sämtliche Regelungsalternativen enthalten, die für die Maßnahme in Betracht kommen. Es können auch mehr als zwei Regelungsalternativen in Betracht kommen.

        Jede Regelungsalternative muss innerhalb des "affectedNorms" Eintrag sämtliche von ihr betroffenen Rechtsnormen enthalten. Dies umfasst alle Rechtsnormen welche unmittelbar durch die Regelungsalternative geändert werden sowie sämtliche Rechtsnormen welche als Folge der Umsetzung der Regelungsalternative mittelbar geändert werden müssen.

        Halte dich bitte **genau** an dieses JSON-Format und verwende keine zusätzlichen Außentexte oder Einleitungen.
    """

    print("Querying LLM to develop amendment proposals...")
    raw_response = await query_llm(prompt, api_key, model or "gpt-4")

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
    

async def evaluate_proposals(task_description: str, relevant_norms: List[NormEntry], amendment_proposals: List[ProposalEntry], api_key: str, model: str) -> List:
    
    """Evaluate the amendment proposals."""
    print("\n==== EVALUATE PROPOSALS ====")
    print(f"Task description length: {len(task_description)} characters")
    print(f"Number of amendment proposals: {len(amendment_proposals)}")

    # Convert relevant_norms to readable text format
    relevant_norms_text = "\n".join([f"- {norm.jurabk} {norm.enbez} Abs. {norm.P}: {norm.wording}" for norm in relevant_norms])
    
    # Convert amendment_proposals to readable text format
    amendment_proposals_text = "\n\n".join([
        f"""{i+1}. **{proposal.proposalTitle}**
    **Beschreibung**: {proposal.description}
    **Betroffene Rechtsnormen**:\n""" + "\n".join([
            f"- {norm.jurabk} {norm.enbez} Abs. {norm.P}  \n  Änderungsbeschreibung: {norm.amendmentDescription}"
            for norm in proposal.affectedNorms
        ])
        for i, proposal in enumerate(amendment_proposals)
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
    raw_response = await query_llm(prompt, api_key, model or "gpt-4")

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

    

async def deep_evaluate_proposals(task_description: str, relevant_norms: List[NormEntry], amendment_proposal: ProposalEntry, api_key: str, model: str) -> List:
    
    """Deep Evaluate the amendment proposals against juridical, technical, and dogmatic criteria."""
    print("\n==== DEEP EVALUATE PROPOSALS ====")
    print(f"Task description length: {len(task_description)} characters")

    # Convert relevant_norms to readable text format
    relevant_norms_text = "\n".join([f"- {norm.jurabk} {norm.enbez} Abs. {norm.P}: {norm.wording}" for norm in relevant_norms])

    # Convert amendment_proposals to readable text format
    amendment_proposals_text = "\n\n".join([
        f"""**{amendment_proposal.proposalTitle}**
    **Beschreibung**: {amendment_proposal.description}
    **Betroffene Rechtsnormen**:\n""" + "\n".join([
            f"- {norm.jurabk} {norm.enbez} Abs. {norm.P}  \n  Änderungsbeschreibung: {norm.amendmentDescription}"
            for norm in amendment_proposal.affectedNorms
        ])
    ])

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

    print("Querying LLM to evaluate proposals...")
    raw_response = await query_llm(prompt, api_key, model or "gpt-4")

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



async def generate_final_amendment(task_description: str, amendment_proposal: ProposalEntry, relevant_norms: List[NormEntry], api_key: str,  model: str, custom_instructions: str | None = None) -> List:
    """Generate the final amendment text based on the selected proposal and any custom adjustments."""
    print("\n==== GENERATE FINAL AMENDMENT ====")
    print(f"Task description length: {len(task_description)} characters")

    # Convert relevant_norms to readable text format
    relevant_norms_text = "\n".join([f"- {norm.jurabk} {norm.enbez} Abs. {norm.P}: {norm.wording}" for norm in relevant_norms])
    
    # Convert amendment_proposals to readable text format
    amendment_proposals_text = "\n\n".join([
        f"""**{amendment_proposal.proposalTitle}**
    **Beschreibung**: {amendment_proposal.description}
    **Betroffene Rechtsnormen**:\n""" + "\n".join([
            f"- {norm.jurabk} {norm.enbez} Abs. {norm.P}  \n  Änderungsbeschreibung: {norm.amendmentDescription}"
            for norm in amendment_proposal.affectedNorms
        ])
    ])

    prompt = f"""
        Du bist Legist im Bundesfinanzministerium und sollst einen Gesetzesentwurf anfertigen.

        Maßnahme: {task_description}

        Du hast bereits eine bestimmte Regelungsalternative ausgewählt:

        Regelungsalternative: {amendment_proposals_text}

        {'Zusätzliche Anpassungswünsche: ' + custom_instructions if custom_instructions else ''}

        Regelungskontext: {relevant_norms_text}

        Setze die Regelungsalternative um. Gebe die zu ändernden Norm(en) in ihrer geänderten Fassung zurück. Hebe Änderungen mit [ ] hervor. Wichtig: Gebe den Wortlaut der gesamten Norm mitsamt Änderungen wieder.
    
        Verwende dabei juristisch präzise Formulierungen und berücksichtige die gängigen Prinzipien der Legistik.

        Gib als Antwort ausschließlich eine JSON-Liste zurück, welche wie folgt formatiert ist:

        {{
            "entries": [
                {{
                    "amendedNorm": {{
                        "jurabk": "<Abkürzung des Gesetzes>",   // z. B. "EStG"
                        "enbez": "<Paragraf>",                  // z. B. "§ 21"
                        "P": "<Absatz>",                        // z. B. "1"
                        "wording": "<geänderter Normtext mit [] Hervorhebungen>"
                    }}
                }}
            ]
        }}

        Halte dich bitte **genau** an dieses JSON-Format und verwende keine zusätzlichen Außentexte oder Einleitungen.
    """

    print("Querying LLM to generate final amendment...")
    raw_response = await query_llm(prompt, api_key, model or "gpt-4")

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






async def identify_relevant_norms_multistep(task_description: str, api_key: str, model: str) -> List[NormEntry]:
    
    """Identify the relevant legal norms for the given task."""
    print("\n==== IDENTIFY RELEVANT NORMS ====")
    print(f"Task description length: {len(task_description)} characters")

    norm_entries: List[NormEntry] = []

    print("Content of norm_entries:", norm_entries)
	
    # Step 1: Identify potentially affected laws
    print("Step 1: Querying LLM to identify potentially affected laws...")

    prompt_step_1 = f"""
        Du bist Legist im Bundesfinanzministerium und sollst einen Gesetzesentwurf anfertigen.

        Maßnahme:  {task_description}

        Die Maßnahme soll durch Änderung eines oder mehrerer bereits bestehender Stammgesetze umgesetzt werde. Bestimme in einem ersten Schritt sämtliche für eine Änderung in Betracht kommende Rechtsnormen. Achte darauf, sämtliche von der Änderungsmaßnahme möglicherweise betroffenen Rechtsnormen einzubeziehen. Nehme noch keine Änderung vor.

        Gebe mir im ersten Schritt NUR den Namen möglicherweise betroffenener Gesetze wieder (z.B. BGB, EStG, StGB, EStDV)

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

    raw_response_step1 = await query_llm(prompt_step_1, api_key, model or "gpt-4")
	
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

        xml_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", f"{entry.jurabk}.xml")
        law_toc = extract_table_of_contents(xml_file=xml_file_path)

        # Step 2: For each law, identify relevant paragraphs

        prompt_step_2 = f"""
        Du bist Legist im Bundesfinanzministerium und sollst einen Gesetzesentwurf anfertigen.

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

        raw_response_step2 = await query_llm(prompt_step_2, api_key, model or "gpt-4")
        
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

    print("Step 3: Add wordings for each norm entry")

    # Define data directory path
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    
    for i, entry in enumerate(norm_entries):
        jurabk = entry.jurabk
        enbez = entry.enbez

        xml_file = os.path.join(data_dir, f"{jurabk}.xml")
        section_num = enbez.replace("§", "").strip() if enbez else ""

        wording = ""
        try:
            # Extract the entire section
            wording = extract_section_from_law(xml_file, section_num)
        except Exception as e:
            print(f"Error extracting wording for {jurabk} {enbez}: {e}")
            wording = f"Fehler beim Laden des Wortlauts für {jurabk} {enbez}"
        
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

        # Step 4: Identify relevant paragraphs in the wording
        prompt_step_4 = f"""
            Du bist Legist im Bundesfinanzministerium und sollst einen Gesetzesentwurf anfertigen.

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

        raw_response_step4 = await query_llm(prompt_step_4, api_key, model or "gpt-4")
        
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


    # Step 5: Reattach wording for each norm entry, manual reattachment to save api costs, reaattach wording of whole section each time to keep context
    temp_norm_entries = []

    for entry in norm_entries:
        jurabk = entry.jurabk
        enbez = entry.enbez
        P = entry.P
        
        # Construct XML file path
        xml_file = os.path.join(data_dir, f"{jurabk}.xml")
        
        # Extract section number from enbez (e.g., "§ 21" -> "21")
        section_num = enbez.replace("§", "").strip() if enbez else ""
        
        # Get the wording from XML
        wording = ""
        try:
            # Extract the entire section
            wording = extract_section_from_law(xml_file, section_num)
        except Exception as e:
            print(f"Error extracting wording for {jurabk} {enbez} P{P}: {e}")
            wording = f"Fehler beim Laden des Wortlauts für {jurabk} {enbez}"
        
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























