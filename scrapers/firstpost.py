import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from scrapers import BaseScraper, register_scraper


class FirstpostScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = 'https://www.firstpost.com'

    def get_home_news(self, include_images=True):
        all_news = []
        seen = set()
        try:
            resp = requests.get(self.base_url, headers=self.headers, timeout=15, verify=False)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # More flexible selectors
            for link in soup.select('a[href*="/"], a'):
                title = link.get_text(strip=True)
                href = link.get('href', '')

                if not title or len(title) < 15:
                    continue
                if not href:
                    continue
                if '/firstpost.com' in href or href.startswith('/'):
                    if not href.startswith('http'):
                        href = self.base_url + href
                elif not href.startswith('http'):
                    continue
                    
                if href in seen or 'javascript' in href:
                    continue
                seen.add(href)

                all_news.append({
                    'title': title,
                    'link': href,
                    'image': '',
                    'description': '',
                    'category': 'INDIA'
                })
                
                if len(all_news) >= 30:
                    break
                    
        except Exception as e:
            print(f"Error in Firstpost get_home_news: {e}")

        if not all_news:
            all_news = [{'title': 'Firstpost News', 'link': 'https://www.firstpost.com', 'image': '', 'description': 'Visit Firstpost', 'category': 'NEWS'}]

        return all_news[:30]

    def get_section_news(self, section, include_images=True):
        return self.get_home_news(include_images)

    def get_related_news(self, url):
        return self.get_home_news()[:6]

    def get_sections(self):
        return [{'id': 'home', 'name': 'Home', 'default': True}]

    def get_article(self, url):
        return {'title': 'Article', 'content': '<p>Content</p>', 'image': '', 'related_news': []}


register_scraper('firstpost', FirstpostScraper)