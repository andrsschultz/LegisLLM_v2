import os
import xml.etree.ElementTree as ET
import re


def format_content_with_paragraphs(content_elem):
    """Format XML content with proper paragraph breaks and enumeration formatting."""
    
    # Check if this content has Definition List (DL) structure for enumeration
    dl_elements = content_elem.findall(".//DL")
    
    if dl_elements:
        return format_definition_list_content(content_elem)
    else:
        # Fallback to paragraph-based formatting
        return format_paragraph_content(content_elem)


def format_definition_list_content(content_elem):
    """Format content that uses Definition List (DL) structure for enumeration."""
    formatted_text = ""
    
    # Process all elements in content
    for elem in content_elem:
        if elem.tag == 'P':
            # Regular paragraph - add the text
            p_text = elem.text.strip() if elem.text else ""
            if p_text:
                formatted_text += p_text + " "
            
            # Process children within the paragraph and any tail text
            for child in elem:
                if child.tag == 'DL':
                    formatted_text += format_dl_element(child)
                    # Check for text after the DL element (tail text)
                    if child.tail and child.tail.strip():
                        formatted_text += " " + child.tail.strip() + " "
                elif child.tag == 'SUP':
                    # SUP elements are numbered sentences within a paragraph
                    # Get only the direct text content, not recursive
                    sup_text = (child.text or "").strip()
                    if sup_text:
                        formatted_text += f"\n\n{sup_text}"
                        # Check for text after the SUP element (tail text)
                        if child.tail and child.tail.strip():
                            formatted_text += " " + child.tail.strip()
        elif elem.tag == 'DL':
            # Direct DL element
            formatted_text += format_dl_element(elem)
    
    return formatted_text.strip()


def format_dl_element(dl_elem, indent_level=0):
    """Format a Definition List (DL) element with proper indentation."""
    formatted_text = ""
    indent = "  " * indent_level
    
    i = 0
    while i < len(dl_elem):
        child = dl_elem[i]
        
        if child.tag == 'DT':
            # Definition Term (number or letter)
            dt_text = ET.tostring(child, encoding='unicode', method='text').strip()
            formatted_text += f"\n\n{indent}{dt_text} "
            
            # Look for corresponding DD
            if i + 1 < len(dl_elem) and dl_elem[i + 1].tag == 'DD':
                dd_elem = dl_elem[i + 1]
                dd_text = format_dd_element(dd_elem, indent_level)
                formatted_text += dd_text
                i += 2  # Skip the DD we just processed
            else:
                i += 1
        else:
            i += 1
    
    return formatted_text


def format_dd_element(dd_elem, indent_level=0):
    """Format a Definition Description (DD) element."""
    formatted_text = ""
    
    # Get direct text
    if dd_elem.text and dd_elem.text.strip():
        formatted_text += dd_elem.text.strip()
    
    # Process children
    for child in dd_elem:
        if child.tag == 'LA':
            # Check if LA has nested DL (sub-enumeration) or just text content
            has_nested_dl = any(la_child.tag == 'DL' for la_child in child)
            
            if has_nested_dl:
                # Look for nested DL within LA
                for la_child in child:
                    if la_child.tag == 'DL':
                        # This is a sub-enumeration (a), b), c))
                        formatted_text += format_dl_element(la_child, indent_level + 1)
                    else:
                        # Other content in LA
                        child_text = ET.tostring(la_child, encoding='unicode', method='text').strip()
                        if child_text:
                            formatted_text += child_text + " "
            else:
                # LA without nested DL - get all text content
                la_text = ET.tostring(child, encoding='unicode', method='text').strip()
                if la_text:
                    formatted_text += la_text
        else:
            # Other elements - get their text content
            child_text = ET.tostring(child, encoding='unicode', method='text').strip()
            if child_text:
                formatted_text += child_text + " "
    
    return formatted_text


def format_paragraph_content(content_elem):
    """Fallback formatting for content without DL structure."""
    # Get all text from the content element
    raw_text = ET.tostring(content_elem, encoding='unicode', method='text').strip()
    
    # Check if the text already contains paragraph numbering like (1), (2), (3)
    has_paragraph_numbers = re.search(r'\(\d+\)', raw_text)
    
    if has_paragraph_numbers:
        # Text already has paragraph numbers, just improve formatting
        # Add line breaks and empty lines before paragraph numbers for better readability
        formatted_text = re.sub(r'\((\d+)\)', r'\n\n(\1)', raw_text)
        
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
            # Single paragraph or no P elements, return as-is
            return raw_text


# Import the new XML extractor
from .new_xml_extractor import extract_section_from_law_new

# Function to extract specific section from a law
def extract_section_from_law(xml_file: str, section_num: str) -> str:
    """
    Extract a specific section from an XML law file.
    Uses the new improved XML extractor for better formatting and completeness.
    """
    return extract_section_from_law_new(xml_file, section_num)


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

