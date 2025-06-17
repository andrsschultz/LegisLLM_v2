import streamlit as st
import json
import os
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import logging
import sys

# Create a custom logging handler that redirects to session state
class StreamToList:
    def __init__(self):
        self.output = []
    
    def write(self, text):
        self.output.append(text)
        if len(self.output) > 1000:  # Limit log size
            self.output = self.output[-1000:]
    
    def flush(self):
        pass

# Setup log capture at the very beginning to catch all logs
if 'log_capture' not in st.session_state:
    st.session_state.log_capture = StreamToList()
    sys.stdout = st.session_state.log_capture

# Load environment variables from .env file
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="LegisLLM - KI-gestützte Legistik",
    page_icon="⚖️",
    layout="wide"
)

# Backend API configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Get API keys from environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")
deepinfra_api_key = os.getenv("DEEPINFRA_API_KEY")

# Show API key status
if not openai_api_key:
    st.sidebar.warning("Enter OpenAI API key:")
    openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")
else:
    st.sidebar.success("OpenAI API Key loaded from .env file")

if not deepinfra_api_key:
    st.sidebar.warning("Enter DeepInfra API key:")
    deepinfra_api_key = st.sidebar.text_input("DeepInfra API Key", type="password")
else:
    st.sidebar.success("DeepInfra API Key loaded from .env file")

# Fetch available models from backend
@st.cache_data(show_spinner=False)
def fetch_available_models():
    """Fetch available models and default from backend API."""
    try:
        url = f"{BACKEND_URL}/models"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        models = data.get("models", [])
        default = data.get("default", None)
        if not models:
            st.error("Keine Modelle vom Backend erhalten.")
        # Ensure each model stores its provider along with id and name
        models = [
            {
                "id": model.get("id"),
                "name": model.get("name", model.get("id")),
                "provider": model.get("provider", "Unknown")
            }
            for model in models
        ]
        return models, default
    except Exception as e:
        st.error(f"Fehler beim Laden der Modell-Liste vom Backend: {str(e)}")
        return [], None

# Get models from backend (no fallback)
models_data, default_model = fetch_available_models()

if not models_data:
    st.sidebar.warning("Keine Modelle verfügbar. Bitte Backend prüfen.")
    st.stop()

model_options = [model["id"] for model in models_data]
model_names = {model["id"]: model.get("name", model["id"]) for model in models_data}

# Set default model in session state if not set
if 'selected_model' not in st.session_state:
    st.session_state.selected_model = default_model or model_options[0]

st.sidebar.subheader("Modell-Auswahl")

selected_model = st.sidebar.selectbox(
    "Wählen Sie ein Modell:",
    options=model_options,
    index=model_options.index(st.session_state.selected_model) if st.session_state.selected_model in model_options else 0,
    format_func=lambda x: model_names.get(x, x),
    help="Wählen Sie das zu verwendende Sprachmodell. Leistungsfähigere Modelle bieten bessere Ergebnisse, erfordern jedoch mehr Zeit."
)

st.session_state.selected_model = selected_model

# API helper functions
def get_api_headers():
    """Get headers for API requests with appropriate API key based on provider"""
    # Determine provider for the selected model
    selected_model_id = st.session_state.selected_model
    provider = next(
        (m.get("provider", "").lower() for m in models_data if m.get("id") == selected_model_id),
        None
    )
    # Choose API key based on provider
    api_key = deepinfra_api_key if provider == "deepinfra" else openai_api_key
    if not api_key:
        st.error("API Key erforderlich. Bitte geben Sie Ihren API Key in der Seitenleiste ein.")
        return None
    return {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }

def log_api_call(endpoint: str, status_code: int, response_length: int = 0):
    """Log API call information"""
    print(f"\n==== API CALL ====")
    print(f"Endpoint: {endpoint}")
    print(f"Status: {status_code}")
    print(f"Response length: {response_length} characters")

# Function to identify relevant legal norms via API
def identify_relevant_norms(task_description: str, multistep_reasoning: bool) -> List[Dict[str, Any]]:
    """Identify the relevant legal norms for the given task via API."""
    print("\n==== IDENTIFY RELEVANT NORMS VIA API ====")
    print(f"Task description length: {len(task_description)} characters")
    
    headers = get_api_headers()
    if not headers:
        return []
    
    try:
        if multistep_reasoning:
            url = f"{BACKEND_URL}/identify"
        else:
            url = f"{BACKEND_URL}/identify_multistep"
        payload = {
            "task_description": task_description
        }
        
        params = {"model": st.session_state.selected_model}
        
        print(f"Making API call to {url}")
        response = requests.post(url, json=payload, headers=headers, params=params)
        
        log_api_call(url, response.status_code, len(response.text))
        
        if response.status_code == 200:
            data = response.json()
            entries = data.get("entries", [])
            print(f"Successfully received {len(entries)} norm entries")
            
            # Convert to the format expected by the UI
            relevant_norms = []
            for entry in entries:
                relevant_norms.append({
                    "Betroffene Rechtsnorm": f"{entry['jurabk']} {entry['enbez']} Abs. {entry['P']}",
                    "jurabk": entry["jurabk"],
                    "enbez": entry["enbez"],
                    "P": entry["P"],
                    "wording": entry["wording"]
                })
            
            return relevant_norms
        else:
            print(f"API Error: {response.status_code} - {response.text}")
            st.error(f"API-Fehler beim Identifizieren der Normen: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        print(f"ERROR in identify_relevant_norms: {str(e)}")
        st.error(f"Fehler beim Identifizieren der Normen: {str(e)}")
        return []

# Function to develop amendment proposals via API
def develop_amendment_proposals(task_description: str, relevant_norms: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Develop amendment proposals for the relevant legal norms via API."""
    print("\n==== DEVELOP AMENDMENT PROPOSALS VIA API ====")
    print(f"Task description length: {len(task_description)} characters")
    print(f"Number of relevant norms: {len(relevant_norms)}")
    
    headers = get_api_headers()
    if not headers:
        return []
    
    try:
        url = f"{BACKEND_URL}/generate_proposals"
        
        # Convert relevant_norms to the format expected by the API
        norm_entries = []
        for norm in relevant_norms:
            norm_entries.append({
                "jurabk": norm.get("jurabk", ""),
                "enbez": norm.get("enbez", ""),
                "P": norm.get("P", ""),
                "wording": norm.get("wording", "")
            })
        
        payload = {
            "task_description": task_description,
            "relevant_norms": norm_entries
        }
        
        params = {"model": st.session_state.selected_model}
        
        print(f"Making API call to {url}")
        response = requests.post(url, json=payload, headers=headers, params=params)
        
        log_api_call(url, response.status_code, len(response.text))
        
        if response.status_code == 200:
            data = response.json()
            entries = data.get("entries", [])
            print(f"Successfully received {len(entries)} proposal entries")
            
            # Convert to the format expected by the UI
            amendment_proposals = []
            for entry in entries:
                amendment_proposals.append({
                    "Alternative": entry["proposalTitle"],
                    "Beschreibung": entry["description"],
                    "Betroffene Rechtsnormen": ", ".join([f"{norm['jurabk']} {norm['enbez']}" for norm in entry["affectedNorms"]])
                })
            
            return amendment_proposals
        else:
            print(f"API Error: {response.status_code} - {response.text}")
            st.error(f"API-Fehler beim Entwickeln der Vorschläge: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"ERROR in develop_amendment_proposals: {str(e)}")
        st.error(f"Fehler beim Entwickeln der Vorschläge: {str(e)}")
        return []

# Function to evaluate amendment proposals via API
def evaluate_proposals(task_description: str, amendment_proposals: List[Dict[str, str]], relevant_norms: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Evaluate the amendment proposals against juridical, technical, and dogmatic criteria via API."""
    print("\n==== EVALUATE PROPOSALS VIA API ====")
    print(f"Task description length: {len(task_description)} characters")
    print(f"Number of amendment proposals: {len(amendment_proposals)}")
    
    headers = get_api_headers()
    if not headers:
        return []
    
    try:
        url = f"{BACKEND_URL}/evaluate_proposals"
        
        # Convert data to API format
        norm_entries = []
        for norm in relevant_norms:
            norm_entries.append({
                "jurabk": norm.get("jurabk", ""),
                "enbez": norm.get("enbez", ""),
                "P": norm.get("P", ""),
                "wording": norm.get("wording", "")
            })
        
        proposal_entries = []
        for proposal in amendment_proposals:
            # Extract affected norms from the string format
            affected_norms_str = proposal.get("Betroffene Rechtsnormen", "")
            affected_norms = []
            if affected_norms_str:
                # Simple parsing - this could be improved
                for norm_str in affected_norms_str.split(", "):
                    parts = norm_str.strip().split()
                    if len(parts) >= 2:
                        affected_norms.append({
                            "jurabk": parts[0],
                            "enbez": " ".join(parts[1:]),
                            "P": ""
                        })
            
            proposal_entries.append({
                "proposalTitle": proposal.get("Alternative", ""),
                "description": proposal.get("Beschreibung", ""),
                "affectedNorms": affected_norms
            })
        
        payload = {
            "task_description": task_description,
            "relevant_norms": norm_entries,
            "amendment_proposals": proposal_entries
        }
        
        params = {"model": st.session_state.selected_model}
        
        print(f"Making API call to {url}")
        response = requests.post(url, json=payload, headers=headers, params=params)
        
        log_api_call(url, response.status_code, len(response.text))
        
        if response.status_code == 200:
            data = response.json()
            entries = data.get("entries", [])
            print(f"Successfully received {len(entries)} evaluated entries")
            
            # Convert to the format expected by the UI
            evaluated_proposals = []
            for entry in entries:
                evaluated_proposals.append({
                    "Betroffene Rechtsnorm": entry["proposalTitle"],
                    "Änderungsvorschlag": entry["proposalTitle"],  # Using title as both for now
                    "Pro": "\n".join(entry["pro"]) if isinstance(entry["pro"], list) else str(entry["pro"]),
                    "Contra": "\n".join(entry["contra"]) if isinstance(entry["contra"], list) else str(entry["contra"])
                })
            
            return evaluated_proposals
        else:
            print(f"API Error: {response.status_code} - {response.text}")
            st.error(f"API-Fehler beim Evaluieren der Vorschläge: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"ERROR in evaluate_proposals: {str(e)}")
        st.error(f"Fehler beim Evaluieren der Vorschläge: {str(e)}")
        return []

# Function to perform deep evaluation of a single proposal via API
def perform_deep_evaluation(proposal: Dict[str, str], relevant_norms: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Perform a deep evaluation of a selected proposal via API."""
    print("\n==== PERFORM DEEP EVALUATION VIA API ====")
    print(f"Performing deep evaluation for proposal: {proposal.get('Betroffene Rechtsnorm', '')}")
    
    headers = get_api_headers()
    if not headers:
        return {}
    
    try:
        url = f"{BACKEND_URL}/deep_evaluate_proposals"
        
        # Convert data to API format
        norm_entries = []
        for norm in relevant_norms:
            norm_entries.append({
                "jurabk": norm.get("jurabk", ""),
                "enbez": norm.get("enbez", ""),
                "P": norm.get("P", ""),
                "wording": norm.get("wording", "")
            })
        
        # Create proposal entry for API
        proposal_entry = {
            "proposalTitle": proposal.get("Betroffene Rechtsnorm", ""),
            "description": proposal.get("Änderungsvorschlag", ""),
            "affectedNorms": []  # This would need to be parsed from the proposal
        }
        
        payload = {
            "task_description": st.session_state.get('task_description', ''),
            "relevant_norms": norm_entries,
            "amendment_proposal": proposal_entry
        }
        
        params = {"model": st.session_state.selected_model}
        
        print(f"Making API call to {url}")
        response = requests.post(url, json=payload, headers=headers, params=params)
        
        log_api_call(url, response.status_code, len(response.text))
        
        if response.status_code == 200:
            data = response.json()
            entries = data.get("entries", [])
            if entries:
                entry = entries[0]  # Take first entry
                print(f"Successfully received deep evaluation")
                
                # Convert to the format expected by the UI
                deep_evaluation = {
                    "JuristischeBeurteilung": {
                        "Bewertung": entry["juristischeBeurteilung"]["Bewertung"],
                        "PotentielleProbleme": entry["juristischeBeurteilung"]["PotentielleProbleme"],
                        "Querverweise": [f"{ref['jurabk']} {ref['enbez']}" for ref in entry["juristischeBeurteilung"]["Querverweise"]]
                    },
                    "RechtstechnischeBeurteilung": {
                        "Klarheit": entry["rechtstechnischeBeurteilung"]["Klarheit"],
                        "Formulierungsvorschlag": entry["rechtstechnischeBeurteilung"]["Formulierungsvorschlag"],
                        "Risikopunkte": entry["rechtstechnischeBeurteilung"]["Risikopunkte"]
                    },
                    "DogmatischeBeurteilung": {
                        "Systematik": entry["dogmatischeBeurteilung"]["Systematik"],
                        "Prinzipien": entry["dogmatischeBeurteilung"]["Prinzipien"]
                    },
                    "Folgenabschätzung": {
                        "Verwaltungsaufwand": entry["folgenabschätzung"]["Verwaltungsaufwand"],
                        "FiskalischeAuswirkungen": entry["folgenabschätzung"]["FiskalischeAuswirkungen"],
                        "Praktikabilität": entry["folgenabschätzung"]["Praktikabilität"],
                        "Übergangsregelungen": entry["folgenabschätzung"]["Übergangsregelungen"]
                    },
                    "FazitProContra": {
                        "Pro": entry["fazitProContra"]["Pro"],
                        "Contra": entry["fazitProContra"]["Contra"],
                        "OffeneFragen": entry["fazitProContra"]["OffeneFragen"]
                    }
                }
                
                return deep_evaluation
            else:
                print("No entries in deep evaluation response")
                return {}
        else:
            print(f"API Error: {response.status_code} - {response.text}")
            st.error(f"API-Fehler bei der vertieften Evaluierung: {response.status_code}")
            return {}
            
    except Exception as e:
        print(f"ERROR in perform_deep_evaluation: {str(e)}")
        st.error(f"Fehler bei der vertieften Evaluierung: {str(e)}")
        return {}

# Function to generate final amendment text via API
def generate_final_amendment(task_description: str, selected_proposal: Dict[str, str], relevant_norms: List[Dict[str, Any]], custom_adjustments: Optional[str] = None) -> str:
    """Generate the final amendment text based on the selected proposal via API."""
    print("\n==== GENERATE FINAL AMENDMENT VIA API ====")
    print(f"Task description length: {len(task_description)} characters")
    print(f"Selected proposal: {selected_proposal}")
    print(f"Custom adjustments: {custom_adjustments if custom_adjustments else 'None'}")
    
    headers = get_api_headers()
    if not headers:
        return ""
    
    try:
        url = f"{BACKEND_URL}/amend"
        
        # Convert data to API format
        norm_entries = []
        for norm in relevant_norms:
            norm_entries.append({
                "jurabk": norm.get("jurabk", ""),
                "enbez": norm.get("enbez", ""),
                "P": norm.get("P", ""),
                "wording": norm.get("wording", "")
            })
        
        # Create proposal entry for API
        proposal_entry = {
            "proposalTitle": selected_proposal.get("Betroffene Rechtsnorm", ""),
            "description": selected_proposal.get("Änderungsvorschlag", ""),
            "affectedNorms": []  # This would need to be parsed from the proposal
        }
        
        payload = {
            "task_description": task_description,
            "custom_instructions": custom_adjustments,
            "relevant_norms": norm_entries,
            "amendment_proposal": proposal_entry
        }
        
        params = {"model": st.session_state.selected_model}
        
        print(f"Making API call to {url}")
        response = requests.post(url, json=payload, headers=headers, params=params)
        
        log_api_call(url, response.status_code, len(response.text))
        
        if response.status_code == 200:
            data = response.json()
            entries = data.get("entries", [])
            if entries:
                final_text = entries[0]["amendedNorm"]
                print(f"Final amendment generated. Length: {len(final_text)} characters")
                return final_text
            else:
                print("No entries in amendment response")
                return "Keine Änderung generiert."
        else:
            print(f"API Error: {response.status_code} - {response.text}")
            st.error(f"API-Fehler bei der Generierung des finalen Entwurfs: {response.status_code}")
            return ""
            
    except Exception as e:
        print(f"ERROR in generate_final_amendment: {str(e)}")
        st.error(f"Fehler bei der Generierung des finalen Entwurfs: {str(e)}")
        return ""

# Main Application UI
st.title("LegisLLM - KI-gestützte Legistik")

# Initialize session state for storing results of each step
if 'relevant_norms' not in st.session_state:
    st.session_state.relevant_norms = None
if 'relevant_norms_text' not in st.session_state:
    st.session_state.relevant_norms_text = ""
if 'amendment_proposals' not in st.session_state:
    st.session_state.amendment_proposals = None
if 'evaluated_proposals' not in st.session_state:
    st.session_state.evaluated_proposals = None
if 'final_amendment' not in st.session_state:
    st.session_state.final_amendment = None
if 'current_tab' not in st.session_state:
    st.session_state.current_tab = 0

# Create tab navigation
tab_names = [
    "1️⃣ Aufgabenstellung",
    "2️⃣ Regelungskontext",
    "3️⃣ Regelungsalternativen", 
    "4️⃣ Evaluierung",
    "5️⃣ Finalisierung"
]

# Initialize task_description in session_state if it doesn't exist
if 'task_description' not in st.session_state:
    st.session_state.task_description = ""

# Get current task description for use across tabs
task_description = st.session_state.task_description

# Create tab selector that respects session state
selected_tab = st.selectbox(
    "Wählen Sie einen Schritt:",
    options=range(len(tab_names)),
    index=st.session_state.current_tab,
    format_func=lambda x: tab_names[x],
    key="tab_selector"
)

# Update session state when tab is changed via selectbox
if selected_tab != st.session_state.current_tab:
    st.session_state.current_tab = selected_tab
    st.rerun()

st.write("---")

# Tab 1: Task Description
if st.session_state.current_tab == 0:
    st.header("1. Legistische Aufgabenstellung")
    
    # Use the session_state value for the text area
    task_description = st.text_area(
        "Beschreiben Sie die legistische Aufgabenstellung",
        value=st.session_state.task_description,
        height=150,
        help="Geben Sie hier die Aufgabenstellung für die Gesetzesänderung ein.",
        key="task_description_input",
        on_change=lambda: setattr(st.session_state, 'task_description', st.session_state.task_description_input)
    )
    
    # Add suggestion buttons below the text area in a subtle way
    st.caption("Vorschläge:")
    if st.button("Einführung einer Freigrenze für Einnahmen aus Vermietung und Verpachtung", key="suggestion_1", use_container_width=False):
        st.session_state.task_description = "Einführung einer Freigrenze für Einnahmen aus Vermietung und Verpachtung"
        st.rerun()
        
    if st.button("Die Pendlerpauschale wird zum 01.01.2026 auf 38 Cent ab dem ersten Kilometer dauerhaft erhöht", key="suggestion_2", use_container_width=False):
        st.session_state.task_description = "Die Pendlerpauschale wird zum 01.01.2026 auf 38 Cent ab dem ersten Kilometer dauerhaft erhöht"
        st.rerun()
        
    if st.button("Der Gewerbesteuer-Mindesthebesatz wird von 200 auf 280 Prozent erhöht", key="suggestion_3", use_container_width=False):
        st.session_state.task_description = "Der Gewerbesteuer-Mindesthebesatz wird von 200 auf 280 Prozent erhöht"
        st.rerun()
        
    if st.button("Steuerfreistellung von Überstundenzuschlägen, die über die tariflich vereinbarte beziehungsweise an Tarifverträgen orientierte Vollzeitarbeit hinausgehen.", key="suggestion_4", use_container_width=False):
        st.session_state.task_description = "Steuerfreistellung von Überstundenzuschlägen, die über die tariflich vereinbarte beziehungsweise an Tarifverträgen orientierte Vollzeitarbeit hinausgehen"
        st.rerun()
        
    if st.button("Ausnahme gemeinnütziger Organisationen mit Einnahmen bis 100.000 Euro vom Erfordernis einer zeitnahen Mittelverwendung", key="suggestion_5", use_container_width=False):
        st.session_state.task_description = "Ausnahme gemeinnütziger Organisationen mit Einnahmen bis 100.000 Euro vom Erfordernis einer zeitnahen Mittelverwendung"
        st.rerun()
    
    # Use columns for consistent button alignment
    col1, col2 = st.columns([3, 1])  # Adjust ratio to push "Weiter" button to the right
    with col1:
        # First tab doesn't need a back button
        pass
    with col2:
        if st.button("Weiter", key="next_to_context", use_container_width=True):
            st.session_state.current_tab = 1
            st.rerun()

# Tab 2: Identify relevant norms
elif st.session_state.current_tab == 1:
    st.header("2. Ermittlung des maßgeblichen Regelungskontexts")
    
    # Show task description for reference
    with st.expander("Aufgabenstellung (Referenz)", expanded=False):
        st.write(task_description)
    
    # Action buttons
    if st.button("Regelungskontext ermitteln", key="identify_context"):
        with st.spinner("Ermittle maßgeblichen Regelungskontext..."):
            if not st.session_state.relevant_norms:
                print("\n==== STEP 2: IDENTIFY RELEVANT NORMS ====")
                st.session_state.relevant_norms = identify_relevant_norms(task_description, multistep_reasoning=st.session_state.get('multistep_reasoning', False))
                
                # Create combined text from the norms for display
                if st.session_state.relevant_norms:
                    norms_text = ""
                    for norm in st.session_state.relevant_norms:
                        norm_name = norm.get("Betroffene Rechtsnorm", "")
                        wording = norm.get("wording", "")
                        norms_text += f"{norm_name}:\n{wording}\n\n"
                    
                    st.session_state.relevant_norms_text = norms_text

    multistep_reasoning = st.checkbox("Multistep reasoning aktivieren")
    if multistep_reasoning:
        st.caption("⚠️ **Experimentelles Feature:** Diese Funktion befindet sich in der Testphase. Bei der Auswahl von Reasoning-Modellen kann diese Funktion zu sehr langen Antwortzeiten (> 10 min) führen.")  
    
    # Navigation buttons with consistent alignment
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("Zurück", key="back_to_task"):
            st.session_state.current_tab = 0
            st.rerun()
    with col2:
        if st.button("Weiter", key="next_to_alternatives", disabled=not st.session_state.relevant_norms, use_container_width=True):
            st.session_state.current_tab = 2
            st.rerun()
    
    if st.session_state.relevant_norms:
        st.subheader("Identifizierte Rechtsnormen:")
        # Display norms in a more compact way
        norm_cols = st.columns(min(3, len(st.session_state.relevant_norms)))
        for i, norm in enumerate(st.session_state.relevant_norms):
            norm_name = norm.get("Betroffene Rechtsnorm", "")
            with norm_cols[i % 3]:
                st.info(norm_name)
        
        st.text_area("Volltext der relevanten Rechtsnormen", st.session_state.relevant_norms_text, height=200)

# Tab 3: Develop amendment proposals
elif st.session_state.current_tab == 2:
    st.header("3. Entwicklung abstrakter Regelungsalternativen")
    
    # Show task description and norms for reference
    with st.expander("Aufgabenstellung & Regelungskontext (Referenz)", expanded=False):
        st.write("**Aufgabenstellung:**")
        st.write(task_description)
        st.write("**Identifizierte Rechtsnormen:**")
        if st.session_state.relevant_norms:
            for norm in st.session_state.relevant_norms:
                st.write(f'- {norm.get("Betroffene Rechtsnorm", "")}')
    
    # Action button
    if st.button("Regelungsalternativen entwickeln", key="develop_alternatives"):
        with st.spinner("Entwickle Regelungsalternativen..."):
            if not st.session_state.amendment_proposals:
                print("\n==== STEP 3: DEVELOP AMENDMENT PROPOSALS ====")
                st.session_state.amendment_proposals = develop_amendment_proposals(
                    task_description, st.session_state.relevant_norms or []
                )
    
    # Navigation buttons with consistent alignment
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("Zurück", key="back_to_context"):
            st.session_state.current_tab = 1
            st.rerun()
    with col2:
        if st.button("Weiter", key="next_to_evaluation", disabled=not st.session_state.amendment_proposals, use_container_width=True):
            st.session_state.current_tab = 3
            st.rerun()
    
    if st.session_state.amendment_proposals:
        st.subheader("Vorgeschlagene Änderungen:")
        for i, proposal in enumerate(st.session_state.amendment_proposals):
            alt_name = proposal.get("Alternative", "")
            print(f"Displaying proposal {i+1}: {alt_name}")
            with st.expander(f"Vorschlag {i+1}: {alt_name}"):
                st.write("**Alternative:**")
                st.write(alt_name)
                st.write("**Beschreibung:**")
                st.write(proposal.get("Beschreibung", ""))
                st.write("**Betroffene Rechtsnormen:**")
                st.write(proposal.get("Betroffene Rechtsnormen", ""))

# Tab 4: Evaluate proposals
elif st.session_state.current_tab == 3:
    st.header("4. Juristische und rechtstechnische Abwägung")
    
    # Show previous steps for reference
    with st.expander("Aufgabenstellung & Alternativen (Referenz)", expanded=False):
        st.write("**Aufgabenstellung:**")
        st.write(task_description)
        if st.session_state.amendment_proposals:
            st.write("**Vorgeschlagene Alternativen:**")
            for i, proposal in enumerate(st.session_state.amendment_proposals):
                st.write(f"- {proposal.get('Alternative', '')}")
    
    # Action button
    if st.button("Vorschläge evaluieren", key="evaluate_proposals"):
        with st.spinner("Evaluiere Vorschläge..."):
            if not st.session_state.evaluated_proposals:
                print("\n==== STEP 4: EVALUATE PROPOSALS ====")
                st.session_state.evaluated_proposals = evaluate_proposals(
                    task_description, 
                    st.session_state.amendment_proposals or [], 
                    st.session_state.relevant_norms or []
                )
    
    # Navigation buttons with consistent alignment
    col1, col2, col3 = st.columns([2.5, 1, 1])
    with col1:
        if st.button("Zurück", key="back_to_alternatives"):
            st.session_state.current_tab = 2
            st.rerun()
    with col2:
        if st.button("Überspringen", key="skip_to_finalization", use_container_width=True):
            st.session_state.current_tab = 4
            st.rerun()
    with col3:
        if st.button("Weiter", key="next_to_finalization", disabled=not st.session_state.evaluated_proposals, use_container_width=True):
            st.session_state.current_tab = 4
            st.rerun()
    
    if st.session_state.evaluated_proposals:
        st.subheader("Evaluierte Vorschläge (nach Eignung sortiert):")
        for i, proposal in enumerate(st.session_state.evaluated_proposals):
            norm_name = proposal.get("Betroffene Rechtsnorm", "")
            print(f"Displaying evaluated proposal {i+1}: {norm_name}")
            with st.expander(f"Vorschlag {i+1}: {norm_name}"):
                st.write("**Betroffene Rechtsnorm:**")
                st.write(norm_name)
                st.write("**Änderungsvorschlag:**")
                st.write(proposal.get("Änderungsvorschlag", ""))
                st.write("**Pro:**")
                st.write(proposal.get("Pro", ""))
                st.write("**Contra:**")
                st.write(proposal.get("Contra", ""))
        
        # Add deep evaluation section
        st.subheader("Vertiefte Evaluierung:")
        proposal_options = [f"Vorschlag {i+1}: {p.get('Betroffene Rechtsnorm', '')}" 
                           for i, p in enumerate(st.session_state.evaluated_proposals)]
        selected_index = st.selectbox("Wählen Sie einen Vorschlag für vertiefte Evaluierung:", 
                                     range(len(proposal_options)), 
                                     format_func=lambda i: proposal_options[i],
                                     key="deep_eval_selection")
        
        selected_proposal = st.session_state.evaluated_proposals[selected_index]
        
        if st.button("Vertiefte Evaluierung durchführen", key="perform_deep_eval"):
            with st.spinner("Führe vertiefte Evaluierung durch..."):
                deep_eval = perform_deep_evaluation(
                    selected_proposal,
                    st.session_state.relevant_norms or []
                )
                
                # Display the deep evaluation results
                if deep_eval:
                    st.subheader("Ergebnisse der vertieften Evaluierung:")
                    
                    # Juristische Beurteilung
                    with st.expander("Juristische Beurteilung", expanded=True):
                        if "JuristischeBeurteilung" in deep_eval:
                            jur_eval = deep_eval["JuristischeBeurteilung"]
                            st.write("**Bewertung:**")
                            st.write(jur_eval.get("Bewertung", ""))
                            st.write("**Potentielle Probleme:**")
                            st.write(jur_eval.get("PotentielleProbleme", ""))
                            st.write("**Querverweise:**")
                            querverweise = jur_eval.get("Querverweise", [])
                            if isinstance(querverweise, list):
                                for qv in querverweise:
                                    st.write(f"- {qv}")
                            else:
                                st.write(querverweise)
                    
                    # Rechtstechnische Beurteilung
                    with st.expander("Rechtstechnische Beurteilung", expanded=True):
                        if "RechtstechnischeBeurteilung" in deep_eval:
                            rt_eval = deep_eval["RechtstechnischeBeurteilung"]
                            st.write("**Klarheit:**")
                            st.write(rt_eval.get("Klarheit", ""))
                            st.write("**Formulierungsvorschlag:**")
                            st.write(rt_eval.get("Formulierungsvorschlag", ""))
                            st.write("**Risikopunkte:**")
                            risikopunkte = rt_eval.get("Risikopunkte", [])
                            if isinstance(risikopunkte, list):
                                for rp in risikopunkte:
                                    st.write(f"- {rp}")
                            else:
                                st.write(risikopunkte)
                    
                    # Dogmatische Beurteilung
                    with st.expander("Dogmatische Beurteilung", expanded=True):
                        if "DogmatischeBeurteilung" in deep_eval:
                            dog_eval = deep_eval["DogmatischeBeurteilung"]
                            st.write("**Systematik:**")
                            st.write(dog_eval.get("Systematik", ""))
                            st.write("**Prinzipien:**")
                            st.write(dog_eval.get("Prinzipien", ""))
                    
                    # Folgenabschätzung
                    with st.expander("Folgenabschätzung", expanded=True):
                        if "Folgenabschätzung" in deep_eval:
                            folg_eval = deep_eval["Folgenabschätzung"]
                            st.write("**Verwaltungsaufwand:**")
                            st.write(folg_eval.get("Verwaltungsaufwand", ""))
                            st.write("**Fiskalische Auswirkungen:**")
                            st.write(folg_eval.get("FiskalischeAuswirkungen", ""))
                            st.write("**Praktikabilität:**")
                            st.write(folg_eval.get("Praktikabilität", ""))
                            st.write("**Übergangsregelungen:**")
                            st.write(folg_eval.get("Übergangsregelungen", ""))
                    
                    # Fazit Pro/Contra
                    with st.expander("Fazit Pro/Contra", expanded=True):
                        if "FazitProContra" in deep_eval:
                            fazit = deep_eval["FazitProContra"]
                            st.write("**Pro:**")
                            pro_points = fazit.get("Pro", [])
                            if isinstance(pro_points, list):
                                for point in pro_points:
                                    st.write(f"- {point}")
                            else:
                                st.write(pro_points)
                                
                            st.write("**Contra:**")
                            contra_points = fazit.get("Contra", [])
                            if isinstance(contra_points, list):
                                for point in contra_points:
                                    st.write(f"- {point}")
                            else:
                                st.write(contra_points)
                                
                            st.write("**Offene Fragen:**")
                            offene_fragen = fazit.get("OffeneFragen", [])
                            if isinstance(offene_fragen, list):
                                for frage in offene_fragen:
                                    st.write(f"- {frage}")
                            else:
                                st.write(offene_fragen)

# Tab 5: Select and finalize proposal
elif st.session_state.current_tab == 4:
    st.header("5. Entscheidung und Finalisierung")
    
    # Navigation buttons with consistent alignment
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("Zurück", key="back_to_evaluation"):
            st.session_state.current_tab = 3
            st.rerun()
    with col2:
        # No "Weiter" button needed for the last tab
        pass
    
    # If we have evaluated proposals, show selection interface
    if st.session_state.evaluated_proposals:
        proposal_options = [f"Vorschlag {i+1}: {p.get('Betroffene Rechtsnorm', '')}" 
                            for i, p in enumerate(st.session_state.evaluated_proposals)]
        selected_index = st.selectbox("Wählen Sie einen Vorschlag aus:", range(len(proposal_options)), 
                                      format_func=lambda i: proposal_options[i])
        
        selected_proposal = st.session_state.evaluated_proposals[selected_index]
        
        st.subheader("Ausgewählter Vorschlag:")
        st.info(f"**Betroffene Rechtsnorm:** {selected_proposal.get('Betroffene Rechtsnorm', '')}")
        st.info(f"**Änderungsvorschlag:** {selected_proposal.get('Änderungsvorschlag', '')}")
        
        st.subheader("Optionale Anpassungen:")
        custom_adjustments = st.text_area("Geben Sie weitere Anpassungswünsche ein (optional):", height=100)
        
        if st.button("Finalen Entwurf generieren"):
            with st.spinner("Generiere finalen Entwurf..."):
                st.session_state.final_amendment = generate_final_amendment(
                    task_description, selected_proposal, 
                    st.session_state.relevant_norms or [],
                    custom_adjustments
                )
            
            if st.session_state.final_amendment:
                st.subheader("Finaler Änderungsentwurf:")
                st.text("Änderungen sind mit [] hervorgehoben.")
                st.markdown(st.session_state.final_amendment)
                st.download_button(
                    label="Als Textdatei speichern",
                    data=st.session_state.final_amendment,
                    file_name="aenderungsentwurf.txt",
                    mime="text/plain"
                )
    
    # If we skipped the evaluation, allow manual entry
    elif st.session_state.amendment_proposals:
        st.info("Sie haben die Evaluierung übersprungen. Wählen Sie eine der entwickelten Alternativen aus.")
        proposal_options = []
        for i, proposal in enumerate(st.session_state.amendment_proposals):
            proposal_options.append(f"Alternative {i+1}: {proposal.get('Alternative', '')}")
        
        selected_index = st.selectbox("Wählen Sie einen Vorschlag aus:", range(len(proposal_options)), 
                                    format_func=lambda i: proposal_options[i])
        
        selected_proposal = st.session_state.amendment_proposals[selected_index]
        
        st.subheader("Ausgewählter Vorschlag:")
        st.info(f"**Alternative:** {selected_proposal.get('Alternative', '')}")
        st.info(f"**Beschreibung:** {selected_proposal.get('Beschreibung', '')}")
        st.info(f"**Betroffene Rechtsnormen:** {selected_proposal.get('Betroffene Rechtsnormen', '')}")
        
        st.subheader("Optionale Anpassungen:")
        custom_adjustments = st.text_area("Geben Sie weitere Anpassungswünsche ein (optional):", height=100)
        
        if st.button("Finalen Entwurf generieren"):
            with st.spinner("Generiere finalen Entwurf..."):
                # Convert amendment proposal to evaluated proposal format for API call
                eval_proposal = {
                    "Betroffene Rechtsnorm": selected_proposal.get("Alternative", ""),
                    "Änderungsvorschlag": selected_proposal.get("Beschreibung", "")
                }
                st.session_state.final_amendment = generate_final_amendment(
                    task_description, eval_proposal, 
                    st.session_state.relevant_norms or [],
                    custom_adjustments
                )
            
            if st.session_state.final_amendment:
                st.subheader("Finaler Änderungsentwurf:")
                st.markdown(st.session_state.final_amendment)
                st.download_button(
                    label="Als Textdatei speichern",
                    data=st.session_state.final_amendment,
                    file_name="aenderungsentwurf.txt",
                    mime="text/plain"
                )
    
    # If we skipped everything, allow manual entry
    else:
        st.warning("Sie haben alle vorherigen Schritte übersprungen. Bitte geben Sie die Informationen manuell ein.")
        
        st.subheader("Manuelle Eingabe:")
        manual_norm = st.text_input("Betroffene Rechtsnorm:", "")
        manual_proposal = st.text_area("Änderungsvorschlag:", "", height=150)
        
        selected_proposal = {
            "Betroffene Rechtsnorm": manual_norm,
            "Änderungsvorschlag": manual_proposal
        }
        
        st.subheader("Optionale Anpassungen:")
        custom_adjustments = st.text_area("Geben Sie weitere Anpassungswünsche ein (optional):", height=100)
        
        if st.button("Finalen Entwurf generieren"):
            if not manual_norm or not manual_proposal:
                st.error("Bitte geben Sie sowohl die betroffene Rechtsnorm als auch einen Änderungsvorschlag ein.")
            else:
                with st.spinner("Generiere finalen Entwurf..."):
                    st.session_state.final_amendment = generate_final_amendment(
                        task_description, selected_proposal, 
                        st.session_state.relevant_norms or [],
                        custom_adjustments
                    )
                
                if st.session_state.final_amendment:
                    st.subheader("Finaler Änderungsentwurf:")
                    st.markdown(st.session_state.final_amendment)
                    st.download_button(
                        label="Als Textdatei speichern",
                        data=st.session_state.final_amendment,
                        file_name="aenderungsentwurf.txt",
                        mime="text/plain"
                    )

# Add a sidebar with information
with st.sidebar:
    st.header("Über diese Anwendung")
    st.write("""
    Die Anwendung befindet sich in einer sehr frühen Entwicklungsphase und dient der Demonstration. Getestet wurde die Anwendung bisher nur auf Änderungen von Regelungen aus dem Einkommensteuergesetz.
    """)
    
    st.write("---")

# Add log viewer at the bottom of the main interface
st.write("---")
with st.expander("📋 Logs anzeigen", expanded=False):
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("Logs aktualisieren", key="refresh_logs"):
            st.rerun()
    with col2:
        if st.button("Logs löschen", key="clear_logs"):
            st.session_state.log_capture.output = []
            st.rerun()
    with col3:
        st.download_button(
            label="Logs herunterladen",
            data=''.join(st.session_state.log_capture.output),
            file_name="legisllm_logs.txt",
            mime="text/plain"
        )
    
    log_output = st.empty()
    logs = ''.join(st.session_state.log_capture.output)
    
    # Process logs to replace newlines with HTML break tags
    logs_html = logs.replace('\n', '<br>')
    
    # Display logs with a fixed-width font in a scrollable container with explicit text color
    log_output.markdown(f"""
    <div style="height: 300px; overflow-y: scroll; font-family: monospace; background-color: #f0f0f0; color: #000000; padding: 10px; border-radius: 5px; font-size: 0.8em;">
    {logs_html}
    </div>
    """, unsafe_allow_html=True)
