#!/usr/bin/env python3
"""
Script to parse resume.tex and generate volunteering.json
"""

import re
import json
from typing import List, Dict

def parse_date_range(date_str: str) -> tuple:
    """Parse date range string and return start and end dates."""
    # Handle different date formats
    date_str = date_str.strip()
    
    if " -- " in date_str:
        start, end = date_str.split(" -- ")
    elif " - " in date_str:
        start, end = date_str.split(" - ")
    else:
        start, end = date_str, "Present"
    
    return start.strip(), end.strip()

def parse_resume_tex(file_path: str) -> List[Dict]:
    """Parse the LaTeX resume file and extract volunteering experience."""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Find the VOLUNTEERING section
    volunteer_section_match = re.search(r'\\section\{\\textbf\{VOLUNTEERING\}\}.*?\\resumeSubHeadingListStart(.*?)\\resumeSubHeadingListEnd', content, re.DOTALL)
    
    if not volunteer_section_match:
        return []
    
    volunteer_section = volunteer_section_match.group(1)
    
    # Pattern to match each volunteering experience entry
    # \resumeSubheading{Role}{Date Range}{Company Name}{Location}
    # Handle nested braces in company names (e.g., \href{...}{...})
    pattern = r'\\resumeSubheading\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
    
    experiences = []
    matches = re.findall(pattern, volunteer_section)
    
    for match in matches:
        role, date_range, company_name, location = match
        start_date, end_date = parse_date_range(date_range)
        
        # Find the description for this volunteering role
        # Look for the resumeItemListStart after this resumeSubheading
        # More flexible pattern to handle whitespace variations
        role_pattern = (
            r'\\resumeSubheading\s*\{' + re.escape(role) + r'\}\{' + re.escape(date_range) + r'\}\s*\{' +
            re.escape(company_name) + r'\}\{' + re.escape(location) + r'\}.*?\\resumeItemListStart(.*?)\\resumeItemListEnd'
        )
        role_section_match = re.search(role_pattern, volunteer_section, re.DOTALL)
        
        description_items = []
        if role_section_match:
            items_section = role_section_match.group(1)
            # Extract individual \resumeItem{...} entries
            item_pattern = r'\\resumeItem\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'
            item_matches = re.findall(item_pattern, items_section)
            description_items = [item.strip() for item in item_matches if item.strip()]
        
        # Clean up LaTeX commands in each description item
        cleaned_description_items = []
        for item in description_items:
            cleaned_item = re.sub(r'\\&', '&', item)  # Replace \& with &
            cleaned_item = re.sub(r'\\%', '%', cleaned_item)  # Replace \% with %
            cleaned_item = re.sub(r'\\textit\{([^}]+)\}', r'\1', cleaned_item)  # Remove \textit{}
            cleaned_item = re.sub(r'\\textbf\{([^}]+)\}', r'\1', cleaned_item)  # Remove \textbf{}
            cleaned_item = re.sub(r'\\href\{[^}]+\}\{([^}]+)\}', r'\1', cleaned_item)  # Remove \href{}
            cleaned_description_items.append(cleaned_item.strip())
        
        # Clean up LaTeX commands in role, company name, and location
        def clean_latex(text):
            cleaned = re.sub(r'\\&', '&', text)  # Replace \& with &
            cleaned = re.sub(r'\\%', '%', cleaned)  # Replace \% with %
            cleaned = re.sub(r'\\textit\{([^}]+)\}', r'\1', cleaned)  # Remove \textit{}
            cleaned = re.sub(r'\\textbf\{([^}]+)\}', r'\1', cleaned)  # Remove \textbf{}
            cleaned = re.sub(r'\\href\{[^}]+\}\{([^}]+)\}', r'\1', cleaned)  # Remove \href{}
            return cleaned.strip()

        experience = {
            "companyImage": "https://placehold.co/48x48",
            "role": clean_latex(role),
            "companyName": clean_latex(company_name),
            "location": clean_latex(location),
            "startDate": start_date,
            "endDate": end_date,
            "description": cleaned_description_items
        }
        
        experiences.append(experience)
    
    return experiences

def load_existing_company_images(file_path: str) -> Dict[str, str]:
    """Load existing company images from the JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
            
        # Create a mapping of company name to company image
        company_images = {}
        for exp in existing_data.get('experiences', []):
            company_name = exp.get('companyName', '')
            company_image = exp.get('companyImage', '')
            if company_name and company_image:
                company_images[company_name] = company_image
                
        return company_images
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def main():
    """Main function to generate the JSON file."""
    import os
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Load existing company images
    json_path = 'data/volunteering.json'
    existing_images = load_existing_company_images(json_path)
    
    experiences = parse_resume_tex('resume.tex')
    
    # Preserve existing company images or use placeholder for new companies
    for exp in experiences:
        company_name = exp['companyName']
        if company_name in existing_images:
            exp['companyImage'] = existing_images[company_name]
        # If not found, keep the default placeholder already set
    
    output = {
        "experiences": experiences
    }
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"Generated data/volunteering.json with {len(experiences)} experiences")
    print(f"Preserved {len([exp for exp in experiences if exp['companyImage'] != 'https://placehold.co/48x48'])} existing company images")

if __name__ == "__main__":
    main()