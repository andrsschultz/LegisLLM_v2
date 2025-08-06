import os
import xml.etree.ElementTree as ET
import re
from typing import Dict, Optional


# Function to extract specific section from a law
def extract_section_from_law(xml_file: str, section_num: str, paragraph_num: str = None) -> str:
    """
    Extract a specific section from an XML law file.
    If paragraph_num is provided, extract only that paragraph from the section.
    If paragraph_num is "Überschrift", extract only the section heading/title.
    """
    print_msg = f"Section {section_num}"
    if paragraph_num:
        print_msg += f" Paragraph {paragraph_num}"
    print(f"\n==== EXTRACT SECTION FROM LAW: {print_msg} from {xml_file} ====")
    try:
        # Extract law_code from xml_file path
        law_code = os.path.basename(xml_file).replace('.xml', '')
        
        extract_msg = f"Extracting section {section_num}"
        if paragraph_num:
            extract_msg += f" paragraph {paragraph_num}"
        print(f"{extract_msg} from {xml_file} (law code: {law_code})")
        
        # Check if file exists
        if not os.path.exists(xml_file):
            print(f"ERROR: XML file not found: {xml_file}")
            return f"XML-Datei für {law_code} nicht gefunden"
        
        print("Parsing XML file...")
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        print(f"Root tag: {root.tag}")
        
        # Extract specific paragraph from norm element
        def extract_paragraph_from_norm(norm_elem, paragraph_num, section_num):
            print(f"Extracting paragraph {paragraph_num} from norm element...")
            
            # Extract enbez (section number) and title for context
            enbez_elem = norm_elem.find(".//enbez")
            enbez = enbez_elem.text if enbez_elem is not None else ""
            
            titel_elem = norm_elem.find(".//titel")
            title = titel_elem.text if titel_elem is not None else ""
            
            # Don't include section header for paragraph extraction
            formatted_text = ""
            
            # Find Content element
            content_elem = norm_elem.find(".//Content")
            if content_elem is not None:
                print(f"  Found Content element, looking for paragraph ({paragraph_num})")
                
                # Look for paragraph markers - handle different formats
                paragraph_found = False
                
                # First try traditional paragraph format: (1), (2), etc.
                for p_elem in content_elem.findall(".//P"):
                    p_text = ET.tostring(p_elem, encoding='unicode', method='text').strip()
                    
                    # Check for traditional paragraph format like "(1)", "(2)"
                    traditional_patterns = [f"({paragraph_num})", f"({paragraph_num}) "]
                    
                    for pattern in traditional_patterns:
                        if p_text.startswith(pattern):
                            print(f"  Found traditional paragraph {paragraph_num}")
                            formatted_text += p_text
                            paragraph_found = True
                            break
                    
                    if paragraph_found:
                        break
                
                # Don't try numbered list format - if no traditional paragraphs found, 
                # fall back to whole norm content
                
                if not paragraph_found:
                    print(f"  Paragraph {paragraph_num} not found in section {section_num}, returning whole norm content")
                    # Return the whole norm content (excluding header)
                    full_content = ET.tostring(content_elem, encoding='unicode', method='text').strip()
                    formatted_text += full_content
                    
            else:
                print("  No Content element found")
                return f"§ {section_num} Abs. {paragraph_num} - Inhalt nicht verfügbar."
            
            print(f"Finished extracting paragraph {paragraph_num}. Text length: {len(formatted_text)} characters")
            return formatted_text
        
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
                # Get all text from the content element
                text = ET.tostring(content_elem, encoding='unicode', method='text')
                formatted_text += text.strip()
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
            if paragraph_num == "Überschrift":
                # Extract only the heading/title
                titel_elem = matching_norms[0].find(".//titel")
                if titel_elem is not None:
                    norm_text = titel_elem.text if titel_elem.text else f"§ {section_num} - Überschrift nicht verfügbar"
                else:
                    norm_text = f"§ {section_num} - Überschrift nicht verfügbar"
                print(f"Extracted heading: {norm_text}")
            elif paragraph_num:
                # Extract specific paragraph
                norm_text = extract_paragraph_from_norm(matching_norms[0], paragraph_num, section_num)
            else:
                # Extract entire section
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


def extract_law_metadata(xml_file: str) -> Dict[str, Optional[str]]:
    """
    Extract metadata from an XML law file header for use in Gesetzesentwurf generation.
    
    Args:
        xml_file: Path to the XML file
        
    Returns:
        Dictionary containing:
        - zitiername: Full law name (e.g., "Einkommensteuergesetz")
        - ausfertigungsdatum: Original publication date (e.g., "16. Oktober 1934") 
        - urspruengliche_fundstelle: Original publication reference (e.g., "RGBl I 1934, 1005")
        - letzte_aenderung_artikel: Latest amendment article number (e.g., "2")
        - letzte_aenderung_datum: Latest amendment date (e.g., "23. Dezember 2024")
        - letzte_aenderung_fundstelle: Latest amendment publication reference (e.g., "BGBl I Nr. 449")
        - jurabk: Law abbreviation (e.g., "EStG")
    """
    print(f"\n==== EXTRACT LAW METADATA FROM: {xml_file} ====")
    
    try:
        # Extract law_code from xml_file path
        law_code = os.path.basename(xml_file).replace('.xml', '')
        
        print(f"Extracting metadata from {xml_file} (law code: {law_code})")
        
        # Check if file exists
        if not os.path.exists(xml_file):
            print(f"ERROR: XML file not found: {xml_file}")
            return {"error": f"XML-Datei für {law_code} nicht gefunden"}
        
        print("Parsing XML file...")
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        print(f"Root tag: {root.tag}")
        
        # Find the first norm with metadata
        metadata_norm = None
        for norm in root.findall(".//norm"):
            metadaten_elem = norm.find("metadaten")
            if metadaten_elem is not None:
                metadata_norm = metadaten_elem
                print("Found norm with metadata")
                break
        
        if metadata_norm is None:
            print("No metadata found")
            return {"error": f"Metadaten in {law_code} nicht gefunden"}
        
        # Initialize result dictionary
        result = {
            "zitiername": None,
            "ausfertigungsdatum": None,
            "urspruengliche_fundstelle": None,
            "letzte_aenderung_artikel": None,
            "letzte_aenderung_datum": None,
            "letzte_aenderung_fundstelle": None,
            "jurabk": None
        }
        
        # Extract jurabk (law abbreviation)
        jurabk_elem = metadata_norm.find("jurabk")
        if jurabk_elem is not None and jurabk_elem.text:
            result["jurabk"] = jurabk_elem.text.strip()
            print(f"Found jurabk: {result['jurabk']}")
        
        # Extract langue (full law name)
        langue_elem = metadata_norm.find("langue")
        if langue_elem is not None and langue_elem.text:
            result["zitiername"] = langue_elem.text.strip()
            print(f"Found zitiername: {result['zitiername']}")
        
        # Extract ausfertigung-datum (original publication date)
        ausfertigung_elem = metadata_norm.find("ausfertigung-datum")
        if ausfertigung_elem is not None and ausfertigung_elem.text:
            # Convert date format from 1934-10-16 to "16. Oktober 1934"
            date_str = ausfertigung_elem.text.strip()
            try:
                from datetime import datetime
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                months = ["", "Januar", "Februar", "März", "April", "Mai", "Juni", 
                         "Juli", "August", "September", "Oktober", "November", "Dezember"]
                formatted_date = f"{date_obj.day}. {months[date_obj.month]} {date_obj.year}"
                result["ausfertigungsdatum"] = formatted_date
                print(f"Found ausfertigungsdatum: {result['ausfertigungsdatum']}")
            except ValueError:
                # If parsing fails, use original string
                result["ausfertigungsdatum"] = date_str
                print(f"Could not parse date, using original: {date_str}")
        
        # Extract fundstelle (original publication reference)
        fundstelle_elem = metadata_norm.find("fundstelle")
        if fundstelle_elem is not None:
            periodikum_elem = fundstelle_elem.find("periodikum")
            zitstelle_elem = fundstelle_elem.find("zitstelle")
            
            if periodikum_elem is not None and zitstelle_elem is not None:
                periodikum = periodikum_elem.text.strip() if periodikum_elem.text else ""
                zitstelle = zitstelle_elem.text.strip() if zitstelle_elem.text else ""
                
                # Convert "RGBl I" to "BGBl. I" format and combine with citation
                if periodikum and zitstelle:
                    # Handle different periodikum formats
                    if "RGBl" in periodikum:
                        # Convert RGBl I to BGBl. I format
                        periodikum = periodikum.replace("RGBl", "BGBl.")
                    elif "BGBl" in periodikum and "." not in periodikum:
                        # Add period if missing: BGBl I -> BGBl. I
                        periodikum = periodikum.replace("BGBl", "BGBl.")
                    
                    result["urspruengliche_fundstelle"] = f"{periodikum} S. {zitstelle}"
                    print(f"Found urspruengliche_fundstelle: {result['urspruengliche_fundstelle']}")
        
        # Extract latest amendment info from standangabe
        # First prioritize "Stand" type, then fall back to "Neuf" type
        stand_found = False
        
        for standangabe in metadata_norm.findall("standangabe"):
            standtyp_elem = standangabe.find("standtyp")
            standkommentar_elem = standangabe.find("standkommentar")
            
            if (standtyp_elem is not None and standkommentar_elem is not None and standkommentar_elem.text):
                standtyp = standtyp_elem.text.strip()
                comment_text = standkommentar_elem.text.strip()
                print(f"Found {standtyp} comment: {comment_text}")
                
                # Handle different types of standangabe - prioritize "Stand" over "Neuf"
                if standtyp == "Stand" and not stand_found:
                    # Parse "zuletzt geändert durch Art. 2 G v. 23.12.2024 I Nr. 449"
                    article_match = re.search(r"Art\.\s*(\d+)", comment_text)
                    date_match = re.search(r"v\.\s*(\d{1,2})\.(\d{1,2})\.(\d{4})", comment_text)
                    fundstelle_match = re.search(r"I\s+(Nr\.\s*\d+|S\.\s*\d+)", comment_text)
                    
                    if article_match:
                        result["letzte_aenderung_artikel"] = article_match.group(1)
                        print(f"Found letzte_aenderung_artikel: {result['letzte_aenderung_artikel']}")
                    
                    if date_match:
                        day, month, year = date_match.groups()
                        try:
                            from datetime import datetime
                            date_obj = datetime(int(year), int(month), int(day))
                            months = ["", "Januar", "Februar", "März", "April", "Mai", "Juni", 
                                     "Juli", "August", "September", "Oktober", "November", "Dezember"]
                            formatted_date = f"{date_obj.day}. {months[date_obj.month]} {date_obj.year}"
                            result["letzte_aenderung_datum"] = formatted_date
                            print(f"Found letzte_aenderung_datum: {result['letzte_aenderung_datum']}")
                        except (ValueError, IndexError):
                            result["letzte_aenderung_datum"] = f"{day}.{month}.{year}"
                            print(f"Could not format date, using: {result['letzte_aenderung_datum']}")
                    
                    if fundstelle_match:
                        fundstelle_part = fundstelle_match.group(1)
                        result["letzte_aenderung_fundstelle"] = f"BGBl. I {fundstelle_part}"
                        print(f"Found letzte_aenderung_fundstelle: {result['letzte_aenderung_fundstelle']}")
                    
                    stand_found = True  # Mark that we found a Stand type
                    break  # Use first "Stand" type standangabe found
        
        # If no "Stand" type found, look for "Neuf" type as fallback
        if not stand_found:
            for standangabe in metadata_norm.findall("standangabe"):
                standtyp_elem = standangabe.find("standtyp")
                standkommentar_elem = standangabe.find("standkommentar")
                
                if (standtyp_elem is not None and standkommentar_elem is not None and standkommentar_elem.text):
                    standtyp = standtyp_elem.text.strip()
                    comment_text = standkommentar_elem.text.strip()
                    
                    if standtyp == "Neuf":
                        # Parse "Neugefasst durch Bek. v. 23.1.2025 I Nr. 24"
                        date_match = re.search(r"v\.\s*(\d{1,2})\.(\d{1,2})\.(\d{4})", comment_text)
                        fundstelle_match = re.search(r"I\s+(Nr\.\s*\d+|S\.\s*\d+)", comment_text)
                        
                        # For Neufassung, there's no article number, so we use "Bek." (Bekanntmachung)
                        result["letzte_aenderung_artikel"] = "Bek."
                        print(f"Found Neufassung, using Bek. as artikel")
                        
                        if date_match:
                            day, month, year = date_match.groups()
                            try:
                                from datetime import datetime
                                date_obj = datetime(int(year), int(month), int(day))
                                months = ["", "Januar", "Februar", "März", "April", "Mai", "Juni", 
                                         "Juli", "August", "September", "Oktober", "November", "Dezember"]
                                formatted_date = f"{date_obj.day}. {months[date_obj.month]} {date_obj.year}"
                                result["letzte_aenderung_datum"] = formatted_date
                                print(f"Found letzte_aenderung_datum: {result['letzte_aenderung_datum']}")
                            except (ValueError, IndexError):
                                result["letzte_aenderung_datum"] = f"{day}.{month}.{year}"
                                print(f"Could not format date, using: {result['letzte_aenderung_datum']}")
                        
                        if fundstelle_match:
                            fundstelle_part = fundstelle_match.group(1)
                            result["letzte_aenderung_fundstelle"] = f"BGBl. I {fundstelle_part}"
                            print(f"Found letzte_aenderung_fundstelle: {result['letzte_aenderung_fundstelle']}")
                        
                        break  # Use first "Neuf" type standangabe found
        
        print(f"Successfully extracted metadata for {law_code}")
        return result
        
    except Exception as e:
        print(f"ERROR in extract_law_metadata: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return {"error": f"Fehler beim Parsen der Metadaten: {str(e)}"}


def extract_raw_metadaten_xml(xml_file: str) -> Dict[str, Optional[str]]:
    """
    Extract raw metadaten XML from an XML law file for LLM processing.
    
    Args:
        xml_file: Path to the XML file
        
    Returns:
        Dictionary containing:
        - jurabk: Law abbreviation (e.g., "EStG")  
        - raw_metadaten_xml: Raw XML string of the <metadaten> element
    """
    print(f"\n==== EXTRACT RAW METADATEN XML FROM: {xml_file} ====")
    
    try:
        # Extract law_code from xml_file path
        law_code = os.path.basename(xml_file).replace('.xml', '')
        
        print(f"Extracting raw metadata XML from {xml_file} (law code: {law_code})")
        
        # Check if file exists
        if not os.path.exists(xml_file):
            print(f"ERROR: XML file not found: {xml_file}")
            return {"error": f"XML-Datei für {law_code} nicht gefunden"}
        
        print("Parsing XML file...")
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        print(f"Root tag: {root.tag}")
        
        # Find the first norm with metadata
        for norm in root.findall(".//norm"):
            metadaten_elem = norm.find("metadaten")
            if metadaten_elem is not None:
                print("Found metadaten element")
                
                # Convert metadaten element to raw XML string
                raw_xml = ET.tostring(metadaten_elem, encoding='unicode', method='xml')
                
                # Extract jurabk for identification
                jurabk_elem = metadaten_elem.find("jurabk")
                jurabk = jurabk_elem.text.strip() if jurabk_elem is not None and jurabk_elem.text else law_code
                
                print(f"Successfully extracted raw metadata XML for {jurabk}")
                print(f"Raw XML length: {len(raw_xml)} characters")
                
                return {
                    "jurabk": jurabk,
                    "raw_metadaten_xml": raw_xml
                }
        
        print("No metadaten element found")
        return {"error": f"Metadaten in {law_code} nicht gefunden"}
        
    except Exception as e:
        print(f"ERROR in extract_raw_metadaten_xml: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return {"error": f"Fehler beim Extrahieren der Metadaten: {str(e)}"}

