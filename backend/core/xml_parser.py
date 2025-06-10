import os
import xml.etree.ElementTree as ET


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
    
