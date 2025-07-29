import os
import xml.etree.ElementTree as ET
import re


def format_content_with_paragraphs(content_elem):
    """Format XML content with proper paragraph breaks and enumeration formatting."""
    # Get all text from the content element
    raw_text = ET.tostring(content_elem, encoding='unicode', method='text').strip()
    
    # Check if the text already contains paragraph numbering like (1), (2), (3)
    has_paragraph_numbers = re.search(r'\(\d+\)', raw_text)
    
    if has_paragraph_numbers:
        # Text already has paragraph numbers, just improve formatting
        # Add line breaks and empty lines before paragraph numbers for better readability
        formatted_text = re.sub(r'\((\d+)\)', r'\n\n(\1)', raw_text)
        
        # Add line breaks before numbered enumeration within paragraphs
        formatted_text = re.sub(r'(\d+)\.(?=\w)', r'\n\1. ', formatted_text)
        formatted_text = re.sub(r'(\d+),(?=(?:für|bei|wenn|soweit|vor|als))', r'\n\1, ', formatted_text)
        
        # Clean up: remove leading newlines and normalize spacing
        formatted_text = formatted_text.lstrip('\n')
        formatted_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', formatted_text)
        
        return formatted_text.strip()
    else:
        # No existing paragraph numbers, look for P elements
        p_elements = content_elem.findall(".//P")
        
        if p_elements and len(p_elements) > 1:
            text = ""
            for i, p_elem in enumerate(p_elements):
                p_text = ET.tostring(p_elem, encoding='unicode', method='text').strip()
                if p_text:
                    text += f"({i + 1}) {p_text}\n\n"
            return text.strip()
        else:
            # Single paragraph or no P elements, apply basic formatting
            formatted_text = re.sub(r'(\d+)\.(?=\w)', r'\n\1. ', raw_text)
            formatted_text = re.sub(r'(\d+),(?=\w)', r'\n\1, ', raw_text)
            formatted_text = re.sub(r'\n\s*\n+', '\n\n', formatted_text)
            return formatted_text.strip()


# Function to extract specific section from a law
def extract_section_from_law(xml_file: str, section_num: str) -> str:
    """
    Extract a specific section from an XML law file.
    """
    print(f"\n==== EXTRACT SECTION FROM LAW: Section {section_num} from {xml_file} ====")
    try:
        # Extract law_code from xml_file path
        law_code = os.path.basename(xml_file).replace('.xml', '')
        
        print(f"Extracting section {section_num} from {xml_file} (law code: {law_code})")
        
        # Check if file exists
        if not os.path.exists(xml_file):
            print(f"ERROR: XML file not found: {xml_file}")
            return f"XML-Datei für {law_code} nicht gefunden"
        
        print("Parsing XML file...")
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        print(f"Root tag: {root.tag}")
        
        # Format norm from dokumente XML structure
        def format_norm(norm_elem):
            print("Formatting norm element...")
            # Extract enbez (section number)
            enbez_elem = norm_elem.find(".//enbez")
            enbez = enbez_elem.text if enbez_elem is not None else ""
            print(f"  Enbez: {enbez}")
            
            # Extract title
            titel_elem = norm_elem.find(".//titel")
            title = titel_elem.text if titel_elem is not None else ""
            print(f"  Title: {title}")
            
            # Start with section header
            formatted_text = f"{enbez} {title}\n\n"
            
            # Extract content - try different content locations
            content_elem = norm_elem.find(".//Content")
            if content_elem is not None:
                print("  Found Content element")
                # Get structured text with paragraph formatting
                formatted_text += format_content_with_paragraphs(content_elem)
            else:
                print("  No Content element found, searching for text elements")
                # If no content element, try to get text directly from norm or its children
                text_elems = norm_elem.findall(".//text")
                print(f"  Found {len(text_elems)} text elements")
                for elem in text_elems:
                    if elem.text and elem.text.strip():
                        formatted_text += elem.text.strip() + "\n"
            
            print(f"Finished formatting norm. Text length: {len(formatted_text)} characters")
            return formatted_text
        
        # Find matching norms
        matching_norms = []
        
        if root.tag == "dokumente":
            print("Using 'dokumente' XML structure parser")
            # First, try to match by enbez (exact section number)
            print(f"Searching for exact match with '§ {section_num}'")
            for norm in root.findall(".//norm"):
                enbez_elem = norm.find(".//enbez")
                if enbez_elem is not None and enbez_elem.text == f"§ {section_num}":
                    matching_norms.append(norm)
                    print(f"Found matching norm with enbez: {enbez_elem.text}")
            
            # If no exact match, try alternate matching methods
            if not matching_norms:
                print("No exact matches found. Trying pattern matching...")
                # Try looking for patterns like "§ {section_num}" in any text
                pattern = f"§ {section_num}"
                for norm in root.findall(".//norm"):
                    # Convert the entire norm to text to search
                    norm_text = ET.tostring(norm, encoding='unicode', method='text')
                    if pattern in norm_text:
                        matching_norms.append(norm)
                        print(f"Found matching norm with pattern '{pattern}' in text")
        
        # Extract text from matching norms
        if matching_norms:
            print(f"Found {len(matching_norms)} matching norms for section {section_num}")
            norm_text = format_norm(matching_norms[0])
            return norm_text
        else:
            print(f"No matching norms found for section {section_num}")
            return f"§ {section_num} in XML-Datei nicht gefunden."
    
    except Exception as e:
        print(f"ERROR in extract_section_from_law: {str(e)}")
        import traceback
        print(f"Error extracting norm text: {str(e)}")
        print(traceback.format_exc())
        return f"Fehler beim Parsen der XML-Datei: {str(e)}"


def extract_table_of_contents(xml_file: str) -> str:
    """
    Extract the Table of Contents (Inhaltsübersicht) from an XML law file.
    
    Args:
        xml_file: Path to the XML file
        
    Returns:
        Formatted string containing the table of contents, or error message if not found
    """
    print(f"\n==== EXTRACT TABLE OF CONTENTS FROM: {xml_file} ====")
    try:
        # Extract law_code from xml_file path
        law_code = os.path.basename(xml_file).replace('.xml', '')
        
        print(f"Extracting Table of Contents from {xml_file} (law code: {law_code})")
        
        # Check if file exists
        if not os.path.exists(xml_file):
            print(f"ERROR: XML file not found: {xml_file}")
            return f"XML-Datei für {law_code} nicht gefunden"
        
        print("Parsing XML file...")
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        print(f"Root tag: {root.tag}")
        
        # Find the norm with enbez "Inhaltsübersicht"
        toc_norm = None
        for norm in root.findall(".//norm"):
            enbez_elem = norm.find(".//enbez")
            if enbez_elem is not None and enbez_elem.text == "Inhaltsübersicht":
                toc_norm = norm
                print("Found norm with Inhaltsübersicht")
                break
        
        if toc_norm is None:
            print("No Inhaltsübersicht norm found")
            return f"Inhaltsübersicht in {law_code} nicht gefunden"
        
        # Extract TOC content - try both TOC and Content structures
        toc_elem = toc_norm.find(".//TOC")
        if toc_elem is None:
            # Try alternative structure with Content element
            toc_elem = toc_norm.find(".//Content")
            if toc_elem is None:
                print("No TOC or Content element found in Inhaltsübersicht norm")
                return f"TOC-Struktur in {law_code} nicht gefunden"
            print("Using Content-based TOC structure")
        
        print("Parsing TOC structure...")
        formatted_toc = f"Inhaltsübersicht - {law_code}\n"
        formatted_toc += "=" * (len(formatted_toc) - 1) + "\n\n"
        
        # Process TOC elements
        for element in toc_elem:
            if element.tag == "Title":
                # Extract title text and class for formatting
                title_text = element.text if element.text else ""
                title_class = element.get("Class", "")
                
                # Format based on class (S2 = main section, S1 = subsection, S0 = sub-subsection)
                if title_class == "S2":
                    formatted_toc += f"\n{title_text}\n"
                    formatted_toc += "-" * len(title_text) + "\n"
                elif title_class == "S1":
                    formatted_toc += f"\n  {title_text}\n"
                elif title_class == "S0":
                    formatted_toc += f"\n    {title_text}\n"
                else:
                    # Handle other title elements or those without class
                    formatted_toc += f"\n{title_text}\n"
            
            elif element.tag == "table":
                # Extract table rows for TOC entries
                rows = element.findall(".//row")
                for row in rows:
                    entries = row.findall("entry")
                    
                    # Handle different table structures
                    if len(entries) >= 3:
                        # 3-column structure (UStG style): section level, section number, title
                        level_entry = entries[0].text if entries[0].text else ""
                        section_num = entries[1].text if entries[1].text else ""
                        section_title = entries[2].text if entries[2].text else ""
                        
                        # Clean up whitespace
                        level_entry = level_entry.strip()
                        section_num = section_num.strip()
                        section_title = section_title.strip()
                        
                        # Check if this is a section header (bold entries)
                        b_elem = entries[0].find("B") or entries[1].find("B")
                        if b_elem is not None:
                            # This is a main section header
                            header_text = b_elem.text if b_elem.text else ""
                            if not header_text and len(entries) > 1:
                                b_elem2 = entries[1].find("B")
                                if b_elem2 is not None:
                                    header_text = b_elem2.text if b_elem2.text else ""
                            if header_text:
                                formatted_toc += f"\n{header_text}\n"
                                formatted_toc += "-" * len(header_text) + "\n"
                        elif section_num and section_title:
                            formatted_toc += f"    {section_num:<10} {section_title}\n"
                        elif section_num:
                            formatted_toc += f"    {section_num}\n"
                            
                    elif len(entries) >= 2:
                        # 2-column structure (EStG style): section number, title
                        section_num = entries[0].text if entries[0].text else ""
                        section_title = entries[1].text if entries[1].text else ""
                        
                        # Clean up whitespace
                        section_num = section_num.strip()
                        section_title = section_title.strip()
                        
                        if section_num and section_title:
                            formatted_toc += f"    {section_num:<10} {section_title}\n"
                        elif section_num:
                            # Section without title (e.g., some entries are just section numbers)
                            formatted_toc += f"    {section_num}\n"
            
            elif element.tag == "Ident":
                # Handle Ident elements (like special section identifiers)
                ident_text = element.text if element.text else ""
                formatted_toc += f"\n{ident_text}\n"
                
            elif element.tag == "P":
                # Handle paragraph elements that might contain tables (UStG style)
                tables = element.findall(".//table")
                for table in tables:
                    rows = table.findall(".//row")
                    for row in rows:
                        entries = row.findall("entry")
                        
                        if len(entries) >= 3:
                            # 3-column structure: section level, section number, title
                            level_entry = entries[0].text if entries[0].text else ""
                            section_num = entries[1].text if entries[1].text else ""
                            section_title = entries[2].text if entries[2].text else ""
                            
                            # Clean up whitespace
                            level_entry = level_entry.strip()
                            section_num = section_num.strip()
                            section_title = section_title.strip()
                            
                            # Check if this is a section header (bold entries)
                            b_elem = entries[0].find("B") or entries[1].find("B") or entries[2].find("B")
                            if b_elem is not None:
                                # This is a main section header
                                header_text = ""
                                b0 = entries[0].find("B")
                                if b0 is not None:
                                    header_text = b0.text if b0.text else ""
                                elif len(entries) > 1:
                                    b1 = entries[1].find("B")
                                    if b1 is not None:
                                        header_text = b1.text if b1.text else ""
                                elif len(entries) > 2:
                                    b2 = entries[2].find("B")
                                    if b2 is not None:
                                        header_text = b2.text if b2.text else ""
                                    
                                if header_text:
                                    formatted_toc += f"\n{header_text}\n"
                                    formatted_toc += "-" * len(header_text) + "\n"
                            elif section_num and section_title:
                                formatted_toc += f"    {section_num:<10} {section_title}\n"
                            elif section_num:
                                formatted_toc += f"    {section_num}\n"
        
        print(f"Successfully extracted TOC. Length: {len(formatted_toc)} characters")
        return formatted_toc
        
    except Exception as e:
        print(f"ERROR in extract_table_of_contents: {str(e)}")
        import traceback
        print(f"Error extracting TOC: {str(e)}")
        print(traceback.format_exc())
        return f"Fehler beim Parsen der Inhaltsübersicht: {str(e)}"

