import os
from typing import List, Dict
from main import ScholarshipScraper, ScholarshipURLScraper

class CategoryScraper:
    def __init__(self, api_key: str, base_output_dir: str = "/content/scholar_scraper"):
        """
        Initialize the category scraper
        
        Args:
            api_key: Gemini API key
            base_output_dir: Base directory for storing scraped data
        """
        self.scholarship_scraper = ScholarshipScraper(api_key)
        self.url_scraper = ScholarshipURLScraper()
        self.base_output_dir = base_output_dir

    def create_category_folder(self, category_name: str) -> str:
        """
        Create folder for category if it doesn't exist
        
        Args:
            category_name: Name of the category
            
        Returns:
            str: Path to category folder
        """
        # Clean category name to create folder name
        folder_name = category_name.strip().replace("/", "_").replace(" ", "_")
        folder_path = os.path.join(self.base_output_dir, folder_name)
        
        # Create folder if it doesn't exist
        os.makedirs(folder_path, exist_ok=True)
        return folder_path

    def extract_category_name(self, url: str) -> str:
        """
        Extract category name from URL
        
        Args:
            url: Category URL
            
        Returns:
            str: Category name
        """
        # Extract category name from URL
        parts = url.strip("/").split("/")
        return parts[-1].title()

    def scrape_category(self, category_url: str):
        """
        Scrape all scholarships from a category URL
        
        Args:
            category_url: URL of the category to scrape
        """
        # Extract category name and create folder
        category_name = self.extract_category_name(category_url)
        category_folder = self.create_category_folder(category_name)
        
        print(f"\nScraping category: {category_name}")
        print(f"Saving results to: {category_folder}")
        
        # Get all scholarship URLs for this category
        scholarship_urls = self.url_scraper.scrape_all_scholarship_urls(category_url)
        
        print(f"Found {len(scholarship_urls)} items to scrape")
        
        # Process each scholarship URL
        for url in scholarship_urls:
            try:
                # Fetch content
                html_content = self.scholarship_scraper.fetch_page(url)
                if not html_content:
                    continue
                
                # Extract data
                data = self.scholarship_scraper.extract_scholarship_data(html_content)
                if data:
                    # Create filename from URL
                    filename = f"{url.split('/')[-2]}.json"
                    file_path = os.path.join(category_folder, filename)
                    
                    # Save to file
                    self.scholarship_scraper.save_scholarship(data, file_path)
                    print(f"Saved: {filename}")
                    
            except Exception as e:
                print(f"Error processing {url}: {e}")

    def scrape_categories(self, category_urls: List[str]):
        """
        Scrape multiple categories
        
        Args:
            category_urls: List of category URLs to scrape
        """
        for url in category_urls:
            self.scrape_category(url)

def main():
    # Get API key from environment
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    
    # Initialize scraper
    scraper = CategoryScraper(api_key)
    
    # Define categories to scrape
    categories = [
        #"https://opportunitiescorners.com/category/bachelor-master-phd-scholarships/",
        #"https://opportunitiescorners.com/category/conferences/",
        #"https://opportunitiescorners.com/category/internships/",
        #"https://opportunitiescorners.com/category/fellowships/",
        #"https://opportunitiescorners.com/category/exchange-programs/",
        "https://opportunitiescorners.com/category/online-courses/"

    ]
    
    # Start scraping
    scraper.scrape_categories(categories)

if __name__ == "__main__":
    main()
