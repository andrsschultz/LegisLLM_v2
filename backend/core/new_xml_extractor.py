import os
import xml.etree.ElementTree as ET


def extract_norm_wording(xml_file: str, section_num: str) -> str:
    """
    Extract and format legal norm wording from German legal XML documents.
    
    Args:
        xml_file: Path to the XML file
        section_num: Section number (e.g., "3", "3b")
        
    Returns:
        Formatted wording text with proper structure and readability
    """
    try:
        if not os.path.exists(xml_file):
            return f"XML-Datei nicht gefunden: {xml_file}"
        
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Find the norm with matching section number
        target_enbez = f"§ {section_num}"
        norm = find_norm_by_section(root, target_enbez)
        
        if not norm:
            return f"§ {section_num} nicht gefunden in der XML-Datei."
        
        # Extract title and format complete norm
        return format_complete_norm(norm)
        
    except Exception as e:
        return f"Fehler beim Verarbeiten der XML-Datei: {str(e)}"


def find_norm_by_section(root, target_enbez):
    """Find norm element by section identifier."""
    for norm in root.findall(".//norm"):
        enbez_elem = norm.find(".//enbez")
        if enbez_elem is not None and enbez_elem.text == target_enbez:
            return norm
    return None


def format_complete_norm(norm):
    """Format the complete norm including title and content."""
    result = []
    
    # Extract section identifier and title
    enbez_elem = norm.find(".//enbez")
    titel_elem = norm.find(".//titel")
    
    if enbez_elem is not None:
        section_header = enbez_elem.text
        if titel_elem is not None and titel_elem.text:
            section_header += f" {titel_elem.text}"
        result.append(section_header)
        result.append("")  # Empty line after title
    
    # Extract and format content
    content_elem = norm.find(".//Content")
    if content_elem is not None:
        formatted_content = format_content_element(content_elem)
        result.append(formatted_content)
    
    return "\n".join(result)


def format_content_element(content_elem):
    """Format the main Content element containing all norm text."""
    result = []
    
    for element in content_elem:
        if element.tag == 'P':
            paragraph_text = format_paragraph_element(element)
            if paragraph_text.strip():
                result.append(paragraph_text)
        else:
            # Handle other potential direct children of Content
            other_text = format_generic_element(element)
            if other_text.strip():
                result.append(other_text)
    
    return "\n\n".join(result)


def format_paragraph_element(p_elem):
    """Format a paragraph (P) element with all its content."""
    result = []
    
    # Get the initial text of the paragraph (usually paragraph number like "(1)")
    if p_elem.text and p_elem.text.strip():
        result.append(p_elem.text.strip())
    
    # Process all child elements
    for child in p_elem:
        if child.tag == 'DL':
            # Definition list (numbered/lettered items)
            dl_content = format_definition_list(child)
            if dl_content.strip():
                result.append(dl_content)
        elif child.tag == 'SUP':
            # Numbered sentences within paragraph
            sup_content = format_sup_element(child)
            if sup_content.strip():
                result.append(sup_content)
        else:
            # Other elements
            other_content = format_generic_element(child)
            if other_content.strip():
                result.append(other_content)
        
        # Handle text that comes after this child element (tail text)
        if child.tail and child.tail.strip():
            result.append(child.tail.strip())
    
    return " ".join(result)


def format_definition_list(dl_elem):
    """Format a Definition List (DL) with DT/DD pairs."""
    result = []
    dl_type = dl_elem.get('Type', 'arabic')  # arabic, alpha, etc.
    
    i = 0
    while i < len(dl_elem):
        child = dl_elem[i]
        
        if child.tag == 'DT':
            # Definition Term (the number/letter)
            dt_text = get_element_text(child).strip()
            
            # Look for corresponding DD
            if i + 1 < len(dl_elem) and dl_elem[i + 1].tag == 'DD':
                dd_elem = dl_elem[i + 1]
                dd_text = format_definition_description(dd_elem)
                
                # Format as "1. content" with proper line break
                if dt_text and dd_text:
                    result.append(f"\n{dt_text} {dd_text}")
                
                i += 2  # Skip both DT and DD
            else:
                # DT without corresponding DD
                if dt_text:
                    result.append(f"\n{dt_text}")
                i += 1
        else:
            i += 1
    
    return "".join(result)


def format_definition_description(dd_elem):
    """Format a Definition Description (DD) element."""
    result = []
    
    # Get direct text
    if dd_elem.text and dd_elem.text.strip():
        result.append(dd_elem.text.strip())
    
    # Process child elements
    for child in dd_elem:
        if child.tag == 'LA':
            # LA usually contains the actual content text or nested DL
            la_content = format_la_element(child)
            if la_content.strip():
                result.append(la_content)
        elif child.tag == 'DL':
            # Nested definition list
            nested_dl = format_definition_list(child)
            if nested_dl.strip():
                result.append(nested_dl)
        else:
            # Other child elements
            child_text = get_element_text(child).strip()
            if child_text:
                result.append(child_text)
        
        # Handle tail text
        if child.tail and child.tail.strip():
            result.append(child.tail.strip())
    
    return " ".join(result)


def format_la_element(la_elem):
    """Format an LA element which can contain text or nested DL."""
    result = []
    
    # Check if LA contains nested DL (sub-enumeration like a), b), c))
    has_nested_dl = any(child.tag == 'DL' for child in la_elem)
    
    if has_nested_dl:
        # Handle nested enumeration
        for child in la_elem:
            if child.tag == 'DL':
                # Format nested DL with indentation for sub-items
                nested_dl = format_nested_definition_list(child)
                if nested_dl.strip():
                    result.append(nested_dl)
            else:
                # Other content in LA
                child_text = get_element_text(child).strip()
                if child_text:
                    result.append(child_text)
    else:
        # Simple LA with just text content
        la_text = get_element_text(la_elem).strip()
        if la_text:
            result.append(la_text)
    
    return " ".join(result)


def format_nested_definition_list(dl_elem):
    """Format a nested Definition List with proper indentation for sub-items."""
    result = []
    dl_type = dl_elem.get('Type', 'arabic')
    
    i = 0
    while i < len(dl_elem):
        child = dl_elem[i]
        
        if child.tag == 'DT':
            # Definition Term (the letter/number for sub-items)
            dt_text = get_element_text(child).strip()
            
            # Look for corresponding DD
            if i + 1 < len(dl_elem) and dl_elem[i + 1].tag == 'DD':
                dd_elem = dl_elem[i + 1]
                dd_text = format_definition_description(dd_elem)
                
                # Format as indented sub-item with line break
                if dt_text and dd_text:
                    result.append(f"\n  {dt_text} {dd_text}")
                
                i += 2  # Skip both DT and DD
            else:
                # DT without corresponding DD
                if dt_text:
                    result.append(f"\n  {dt_text}")
                i += 1
        else:
            i += 1
    
    return "".join(result)


def format_sup_element(sup_elem):
    """Format a SUP (numbered sentence) element with superscript markers."""
    # SUP elements are numbered sentences like "1Grundlohn ist..."
    sup_text = get_element_text(sup_elem).strip()
    
    if sup_text:
        # Extract the sentence number and the rest of the text
        # Pattern: number at start, followed by text
        import re
        match = re.match(r'^(\d+)(.*)$', sup_text)
        if match:
            sentence_num = match.group(1)
            sentence_text = match.group(2)
            # Mark sentence number for superscript with special markers
            # No line breaks - sentences flow together within paragraph
            formatted_text = f"<SUP>{sentence_num}</SUP>{sentence_text}"
            return f" {formatted_text}"
        else:
            # Fallback if pattern doesn't match
            return f" {sup_text}"
    
    return ""


def format_generic_element(elem):
    """Format any generic element by extracting its text content."""
    return get_element_text(elem).strip()


def get_element_text(elem):
    """
    Get all text content from an element, including text from child elements.
    This is a comprehensive text extraction that handles mixed content.
    """
    text_parts = []
    
    # Get the element's direct text
    if elem.text:
        text_parts.append(elem.text)
    
    # Recursively get text from child elements
    for child in elem:
        child_text = get_element_text(child)
        if child_text:
            text_parts.append(child_text)
        
        # Get text that comes after the child element
        if child.tail:
            text_parts.append(child.tail)
    
    return "".join(text_parts)


# Integration function to replace the old extractor
def extract_section_from_law_new(xml_file: str, section_num: str) -> str:
    """
    New implementation of section extraction using the improved XML parser.
    This function maintains compatibility with the existing API.
    """
    return extract_norm_wording(xml_file, section_num)