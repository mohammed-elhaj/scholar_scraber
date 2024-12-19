import requests
from bs4 import BeautifulSoup
import json
import google.generativeai as genai
import os
from typing import Dict, Any
import time
from typing import Set, Optional, List
import logging

class ScholarshipScraper:
    def __init__(self, api_key: str):
        # Initialize Gemini
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Load JSON structure
        with open('complete_structure.json', 'r') as f:
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
        return f"""Analyze this educational opportunity posting and create a structured summary.
        Focus on extracting factual information about dates, requirements, and program details.
        Present the information in this JSON format:
        
        {json.dumps(self.structure, indent=2)}
        
        Source content to analyze:
        {cleaned_html}
        
        Requirements:
        1. Return only a valid JSON object
        2. No additional text or explanations
        3. Use empty strings ("") for missing information
        4. Keep responses concise and factual
        5. Focus on publicly available program details only
        6. Exclude any copyrighted content or direct quotes"""

    def extract_scholarship_data(self, html_content: str) -> Dict[str, Any]:
        """
        Use Gemini to extract structured data from HTML with improved error handling
        and retries.
        
        Args:
            html_content (str): Raw HTML content to process
            
        Returns:
            Dict[str, Any]: Extracted scholarship data or None if extraction fails
        """
        # Clean the HTML content
        cleaned_content = self.clean_html(html_content)
        if not cleaned_content:
            print("Warning: No content after cleaning HTML")
            return None
            
        # Generate the prompt
        prompt = self.generate_prompt(cleaned_content)
        
        # Configure retry parameters
        max_retries = 3
        current_try = 0
        base_delay = 2  # Base delay in seconds
        
        while current_try < max_retries:
            try:
                # Generate content with Gemini
                generation_config = {
                    "temperature": 0.3,  # Lower temperature for more consistent output
                    "top_p": 0.8,
                    "top_k": 40
                }
                
                response = self.model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
                
                # Handle different response formats
                if hasattr(response, 'text'):
                    content = response.text
                else:
                    # For newer Gemini versions that return parts
                    content = ''
                    for part in response.parts:
                        if hasattr(part, 'text'):
                            content += part.text
                        
                # Clean the content
                content = content.strip()
                if not content:
                    raise ValueError("Empty response from Gemini")
                
                # Remove any markdown code block indicators if present
                content = content.replace('```json', '').replace('```', '')
                
                # Attempt to parse JSON
                try:
                    parsed_data = json.loads(content)
                    
                    # Validate the parsed data has required fields
                    if not isinstance(parsed_data, dict):
                        raise ValueError("Parsed data is not a dictionary")
                        
                    # Success! Return the parsed data
                    return parsed_data
                    
                except json.JSONDecodeError as e:
                    print(f"JSON Parse Error: {str(e)}")
                    print(f"Raw content (first 500 chars): {content[:500]}...")
                    raise
                    
            except Exception as e:
                current_try += 1
                print(f"Error on attempt {current_try}: {str(e)}")
                
                if current_try < max_retries:
                    # Calculate exponential backoff delay
                    delay = base_delay * (2 ** (current_try - 1))
                    print(f"Retrying in {delay} seconds... (Attempt {current_try + 1} of {max_retries})")
                    time.sleep(delay)
                else:
                    print("Max retries reached. Moving to next item.")
                    return None
        
        return None

    def save_scholarship(self, data: Dict[str, Any], filename: str):
        """Save extracted scholarship data to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving data: {e}")

class ScholarshipURLScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.scholarship_urls = set()
        self.base_url = "https://opportunitiescorners.com"

        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Selectors from analysis
        self.SCHOLARSHIP_SELECTOR = "div.td_module_6 .td-module-thumb a"
        self.NEXT_PAGE_SELECTOR = "div.page-nav a[aria-label='next-page']"
        self.CURRENT_PAGE_SELECTOR = "div.page-nav span.current"
        self.LAST_PAGE_SELECTOR = "div.page-nav a.last"

    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a page, with error handling and rate limiting"""
        try:
            # Rate limiting
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return None

    def extract_scholarship_urls(self, soup: BeautifulSoup) -> Set[str]:
        """Extract all scholarship URLs from a page"""
        urls = set()
        scholarship_links = soup.select(self.SCHOLARSHIP_SELECTOR)

        for link in scholarship_links:
            href = link.get('href')
            if href:
                # Ensure absolute URL
                if not href.startswith('http'):
                    href = self.base_url + href
                urls.add(href)
                self.logger.debug(f"Found scholarship URL: {href}")

        return urls

    def get_next_page_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract the next page URL if it exists"""
        next_link = soup.select_one(self.NEXT_PAGE_SELECTOR)
        if next_link and 'href' in next_link.attrs:
            return next_link['href']
        return None

    def get_pagination_info(self, soup: BeautifulSoup) -> tuple[int, int]:
        """Extract current page number and total pages"""
        try:
            current = soup.select_one(self.CURRENT_PAGE_SELECTOR)
            current_page = int(current.text) if current else 1

            last_page_link = soup.select_one(self.LAST_PAGE_SELECTOR)
            total_pages = int(last_page_link.text) if last_page_link else 1

            return current_page, total_pages
        except Exception as e:
            self.logger.error(f"Error getting pagination info: {e}")
            return 1, 1

    def scrape_all_scholarship_urls(self, start_url: str) -> Set[str]:
        """Scrape all scholarship URLs from all pages"""
        current_url = start_url

        while current_url:
            self.logger.info(f"Scraping page: {current_url}")

            # Fetch and parse page
            soup = self.fetch_page(current_url)
            if not soup:
                break

            # Extract URLs from current page
            page_urls = self.extract_scholarship_urls(soup)
            self.scholarship_urls.update(page_urls)

            # Get pagination information
            current_page, total_pages = self.get_pagination_info(soup)
            self.logger.info(f"Processing page {current_page} of {total_pages}")

            # Get next page URL
            current_url = self.get_next_page_url(soup)

            if not current_url:
                self.logger.info("No more pages to scrape")
                break

        self.logger.info(f"Found total of {len(self.scholarship_urls)} scholarship URLs")
        return self.scholarship_urls

    def get_urls(self) -> Set[str]:
        """Return the collected URLs"""
        return self.scholarship_urls





def main():
    # Initialize scraper
    api_key = os.getenv('GEMINI_API_KEY')
    scraper = ScholarshipScraper(api_key)
    url_scraper = ScholarshipURLScraper()
    
    # Get all scholarship URLs
    start_url = "https://opportunitiescorners.com/category/bachelor-master-phd-scholarships/"
    scholarship_urls = url_scraper.scrape_all_scholarship_urls(start_url)
    
    # Example usage
    urls = scholarship_urls
    
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
