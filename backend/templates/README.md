# Legal Document Templates

This directory contains templates and prompts for German legal document generation.

## Prompt Templates (for LLM)

These files are used as prompts for the LLM to generate legal content:

- **`aenderungsbefehl_prompt.md`** - Prompt for generating Änderungsbefehle (amendment commands) from before/after norm wordings
- **`gesetzesentwurf_prompt.md`** - Prompt for creating complete Gesetzesentwurf (legal draft) from Änderungsbefehle
- **`masterprompt.md`** - Comprehensive single-prompt template (currently unused in favor of two-step approach)

## Documentation Templates

These files document the structure and rules for German legal documents:

- **`aenderungsbefehl.md`** - Documentation of Änderungsbefehl rules and formats
- **`Entwurf.md`** - Structure template for Gesetzesentwurf documents
- **`EntwurfsMantel.md`** - Template for the cover/wrapper of legal drafts
- **`Begründung.md`** - Template for legal justifications (Begründung)

## Usage

Templates are served via the backend API:
- `GET /templates/` - List all available templates
- `GET /templates/{template_name}` - Get specific template content

## Security

Only predefined template files are accessible through the API to prevent directory traversal attacks.