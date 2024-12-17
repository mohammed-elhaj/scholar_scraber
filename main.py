import requests
from bs4 import BeautifulSoup
import json
import google.generativeai as genai
import os
from typing import Dict, Any
import time

class ScholarshipScraper:
    def __init__(self, api_key: str):
        # Initialize Gemini
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        
        # Load JSON structure
        with open('structure.json', 'r') as f:
            self.structure = json.load(f)
            
        # Headers for requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def fetch_page(self, url: str) -> str:
        """Fetch page content with error handling and rate limiting"""
        try:
            time.sleep(2)  # Rate limiting
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def clean_html(self, html_content: str) -> str:
        """Clean HTML content to extract main scholarship information"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove unnecessary elements
        for element in soup.find_all(['script', 'style', 'iframe', 'nav', 'footer']):
            element.decompose()
            
        # Get main content
        main_content = soup.find('article') or soup.find('main') or soup.find('div', class_='entry-content')
        
        if main_content:
            return str(main_content)
        return html_content

    def generate_prompt(self, cleaned_html: str) -> str:
        """Generate prompt for Gemini"""
        return f"""You are a scholarship data extractor. Given the HTML content of a scholarship post and a JSON structure, 
        extract the relevant information and format it according to the structure.
        
        The JSON structure is:
        {json.dumps(self.structure, indent=2)}
        
        Extract information from this HTML content and fill the JSON structure:
        {cleaned_html}
        
        Only return a valid JSON object following the provided structure. Do not include any other text or explanations.
        Leave fields empty ("") if information is not found. Format should match the structure exactly."""

    def extract_scholarship_data(self, html_content: str) -> Dict[str, Any]:
        """Use Gemini to extract structured data from HTML"""
        cleaned_content = self.clean_html(html_content)
        prompt = self.generate_prompt(cleaned_content)
        
        try:
            response = self.model.generate_content(prompt)
            parsed_data = json.loads(response.text)
            return parsed_data
        except Exception as e:
            print(f"Error extracting data: {e}")
            return None

    def save_scholarship(self, data: Dict[str, Any], filename: str):
        """Save extracted scholarship data to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving data: {e}")

def main():
    # Initialize scraper
    api_key = os.getenv('GEMINI_API_KEY')
    scraper = ScholarshipScraper(api_key)
    
    # Example usage
    urls = [
        'https://opportunitiescorners.com/erasmus-mundus-dafm-scholarship/',
        'https://opportunitiescorners.com/open-doors-russian-government-scholarship-2024/'
    ]
    
    for url in urls:
        # Fetch content
        html_content = scraper.fetch_page(url)
        if not html_content:
            continue
            
        # Extract data
        scholarship_data = scraper.extract_scholarship_data(html_content)
        if scholarship_data:
            # Save to file
            filename = f"scholarships/{url.split('/')[-2]}.json"
            scraper.save_scholarship(scholarship_data, filename)

if __name__ == "__main__":
    main()