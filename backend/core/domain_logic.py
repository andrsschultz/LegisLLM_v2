import json
import os
from typing import List, Optional
from .llm_service import query_llm
from .models import NormEntry, ProposalEntry, AmendEntry
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
    raw_response = await query_llm(prompt, api_key, model or "gpt-4")

    print(f"Response received. Length: {len(raw_response)} characters")
    
    # Since we're asking for direct text output (not JSON), return the text directly
    # The response should be the amended norm text
    return [{"amendedNorm": raw_response.strip()}]






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
        return []
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
            return []
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
            return []
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




async def identify_erfüllungsaufwand(task_description: str, relevant_norms: List[NormEntry], amendment_proposal: ProposalEntry, amended_norms: List[AmendEntry], api_key: str, model: str) -> List:
    print("\n==== GENERATE ERFÜLLUNGSAUFWAND ====")
    print(f"Task description length: {len(task_description)} characters")
    print(f"Number of relevant norms: {len(relevant_norms)}")
    print(f"Number of amended norms: {len(amended_norms)}")

    # Convert relevant_norms to readable text format
    relevant_norms_text = "\n".join([f"- {norm.jurabk} {norm.enbez} Abs. {norm.P}: {norm.wording}" for norm in relevant_norms])
    
    # Convert amendment_proposal to readable text format
    amendment_proposal_text = f"- {amendment_proposal.proposalTitle}: {amendment_proposal.description}\n  Affected Norms: {', '.join([f'{norm.jurabk} {norm.enbez} Abs. {norm.P}' for norm in amendment_proposal.affectedNorms])}"
    
    # Convert amended_norms to readable text format
    amended_norms_text = "\n".join([f"- {amend.amendedNorm}" for amend in amended_norms])

    prompt = f"""
        Der Erfüllungsaufwand umfasst gem. § 2 Absatz 1 NKRG den gesamten messbaren Zeitaufwand und die Kosten, die durch die Befolgung einer bundesrechtlichen Vorschrift bei Bürgerinnen und Bürgern, der Wirtschaft sowie der öffentlichen Verwaltung entstehen.

        ## Ausnahmen vom Erfüllungsaufwand

        Nicht unter den Begriff Erfüllungsaufwand fallen insbesondere die in Anlage 3 zu § 42 Absatz 1 GGO unter F. aufgeführten Kostenarten, die als „Weitere Kosten" bezeichnet werden. Hierzu gehören:

        - sonstige Kosten für die Wirtschaft
        - Kosten für soziale Sicherungssysteme
        - Auswirkungen auf Einzelpreise und das Preisniveau
        - Öffentlich-rechtliche Gebühren, z. B. nach dem Gesetz über Gebühren und Auslagen des Bundes (Bundesgebührengesetz) und dem Gerichtskostengesetz
        - Differenzkosten, die sich z. B. aufgrund von Mindest- oder Höchstgrenzen für Arbeitsentgelte oder Preise wie dem Mindestlohn oder der Mietpreisbindung ergeben
        - Aufwand der Justiz (Personal- und Sachaufwand für den sog. justiziellen Kernbereich gefasst, also insbesondere die Tätigkeit der Richterinnen und Richter zur Klärung der Rechtslage (einschließlich der Ausübung der Strafgerichtsbarkeit) oder die der Staatsanwaltschaft/Polizei bei der Strafermittlung und -verfolgung). **Hinweis:** Personal- und Sachaufwand bei Gerichten und Staatsanwaltschaften sowie bei anderen Justizakteuren (z. B. Gerichtsvollzieherin und Gerichtsvollzieher) außerhalb des justiziellen Kernbereichs ist dagegen als Erfüllungsaufwand der Verwaltung darzustellen. Darunter fällt z. B. die Ausstattung der Gerichte mit IT.
        - Indirekte Effekte, wie z. B. kalkulatorische Kosten (etwa: Differenz zu entgangenen, hypothetischen Einnahmen aus Kapital, die ohne gesetzliche Vorgabe ertragreicher hätten verwendet werden können) oder Gemeinkosten, d. h. solche Kosten, die sich nur indirekt einem bestimmten Kostenträger wie einem Produkt, einer Tätigkeit oder Leistungseinheit zurechnen lassen
        - Steuern, Sozialabgaben, sonstige Abgaben (z. B. Ausgleichsabgaben) und Aufwendungen gemäß Artikel 104a Absatz 3 und 4 des Grundgesetzes (GG)

        ## Datenquellen

        Es bleibt dir überlassen, welche Quellen du zur Ermittlung des Erfüllungsaufwands nutzt. Insbesondere folgende Datenquellen kommen in Betracht:

        - Angaben aus früheren Ermittlungen von Bürokratiekosten oder Erfüllungsaufwand aus Datenbanken, z. B. der Online-Datenbank des Erfüllungsaufwands
        - Veröffentlichungen
        - Statistisches Bundesamt
        - Länder- und Verbändebeteiligung
        - Externe Sachverständige

        In keinem Fall entbindet die Nutzung externer Quellen dich davon, die zu erwartende Änderung des Erfüllungsaufwands eigenverantwortlich zu ermitteln. Ziel ist es, dass vor der abschließenden Entscheidung über ein Regelungsvorhaben alle relevanten Daten und Quellen nachvollziehbar dargestellt werden.

        ## Aufgabenstellung

        Du bist ein Experte für die Berechnung des Erfüllungsaufwands von Gesetzesentwürfen. Analysiere den vorgelegten Gesetzesentwurf und berechne systematisch den Erfüllungsaufwand für alle betroffenen Adressatengruppen.

        **EINGABE:** Du erhältst folgende Informationen:
        - Aufgabenbeschreibung des ursprünglichen Vorhabens
        - Relevante Rechtsnormen mit Wortlaut
        - Gewählter Änderungsvorschlag
        - Finale Änderungstexte

        **Aufgabenbeschreibung des ursprünglichen Vorhabens:**
        {task_description}

        **Relevante Rechtsnormen mit Wortlaut:**
        {relevant_norms_text}

        **Gewählter Änderungsvorschlag:**
        {amendment_proposal_text}

        **Finale Änderungstexte:**
        {amended_norms_text}

        **AUSGABE:** Gib deine Antwort als JSON-Array mit folgendem Schema zurück:

        {{
        "entries": [
            {{
            "title": "string",
            "description": "string", 
            "cost_category": "high|low",
            "citizens_cost_eur": "float",
            "business_cost_eur": "float",
            "administration_cost_eur": "float",
            "total_cost_eur": "float"
            }}
        ]
        }}

        **VORGEHEN:**
        1. Identifiziere alle Einzelregelungen, die Erfüllungsaufwand auslösen
        2. Schätze für jede Vorgabe und Adressatengruppe: Zeitaufwand, Fallzahlen, Lohnsätze
        3. Berechne: Aufwand pro Fall × Fallzahl pro Jahr = Jährlicher Erfüllungsaufwand
        4. Kategorisiere als "high" (>100.000 EUR/Jahr) oder "low" (≤100.000 EUR/Jahr)
        5. Verwende realistische Schätzungen basierend auf vergleichbaren Regelungen

        ## Berechnungsmethodik

        Zur Berechnung des jährlichen Erfüllungsaufwands eines Regelungsvorhabens geht man in drei logisch aufeinanderfolgenden Schritten vor.

        ### Schritt 1 – Vorgaben erfassen

        Zunächst werden sämtliche Einzelregelungen („Vorgaben") des Vorhabens identifiziert, die den Erfüllungsaufwand beeinflussen können. Mehrere inhaltlich zusammenhängende Vorgaben lassen sich dabei zu Prozessen oder – wenn dieselbe Vorgabe für unterschiedliche Adressatengruppen gilt – zu Fallgruppen bündeln. Jede Vorgabe erhält eine eindeutige Kennung.

        ### Schritt 2 – Ängerung des Erfüllungsaufwands bestimmen

        Für jede Vorgabe (bzw. jeden gebündelten Prozess/Fallgruppe) werden nun drei Grundgrößen erhoben oder geschätzt:

        #### 1. Aufwandsparameter pro Fall

        - **Lohnsatz in Euro pro Stunde** (entfällt bei Bürgerinnen und Bürgern)
        - **Zeitaufwand in Stunden pro Fall**
        - **Sachaufwand in Euro pro Fall**

        Aus ihnen ergibt sich der **Aufwand pro Fall** als:

        > Aufwand = Lohnsatz × Zeitaufwand + Sachaufwand

        #### 2. Fallzahl pro Jahr

        Entweder wird sie direkt angesetzt oder indirekt aus:

        - **Zahl der Normadressaten** (nur erforderlich, wenn sie zur Bestimmung der jährlichen Fallzahl benötigt werden) und
        - **Häufigkeit je Adressat pro Jahr** (nur erforderlich, wenn sie zur Bestimmung der jährlichen Fallzahl benötigt werden) abgeleitet.

        #### 3. Erfüllungsaufwand je Vorgabe

        Multipliziert man den Aufwand pro Fall mit der Fallzahl pro Jahr, erhält man den **jährlichen Erfüllungsaufwand** der jeweiligen Vorgabe bzw. des jeweiligen Prozesses.

        > Erfüllungsaufwand je Vorgabe (€/a) = Aufwand pro Fall × Fallzahl pro Jahr

        Die Berechnung erfolgt jeweils getrennt für die drei Adressatengruppen – Bürgerinnen und Bürger, Wirtschaft und Verwaltung – sodass Änderungen in jeder Gruppe transparent werden.

        ### Schritt 3 – Ergebnis darstellen

        Die so gewonnenen Ergebnisse werden zusammengeführt:

        - Die Einzelbeträge aller Vorgaben werden addiert und als **Gesamterfüllungsaufwand der Norm pro Jahr** ausgewiesen.
        - Die Aufsplittung nach Adressatengruppen bleibt erhalten, um die Belastungsverteilung sichtbar zu machen.

        Halte dich bitte **genau** an dieses JSON-Format und verwende keine zusätzlichen Außentexte oder Einleitungen.
    """

    print("Querying LLM to calculate Erfüllungsaufwand...")
    raw_response = await query_llm(prompt, api_key, model or "gpt-4")

    print(f"Response received. Length: {len(raw_response)} characters")
    
    try:
        # Clean the response using the helper function
        cleaned_response = clean_json_string(raw_response)
        parsed_response = json.loads(cleaned_response)
        entries = parsed_response.get("entries", [])
        print(f"Successfully parsed {len(entries)} Erfüllungsaufwand entries")
        return entries
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Raw response: {raw_response}")
        return []


















