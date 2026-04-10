import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()
from scrapers import BaseScraper, register_scraper


class WIONScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = 'https://www.wionews.com'

    def get_home_news(self, include_images=True):
        all_news = []
        seen = set()
        try:
            resp = requests.get(self.base_url, headers=self.headers, timeout=15, verify=False)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Get all links and filter for news articles
            for link in soup.select('a'):
                title = link.get_text(strip=True)
                href = link.get('href', '')

                if not title or len(title) < 15:
                    continue
                if not href:
                    continue
                if '/video' in href or '/gallery' in href:
                    continue
                if not href.startswith('http'):
                    href = self.base_url + href
                if href in seen or self.base_url not in href:
                    continue
                seen.add(href)

                all_news.append({
                    'title': title,
                    'link': href,
                    'image': '',
                    'description': '',
                    'category': 'WORLD'
                })
                
                if len(all_news) >= 30:
                    break
                    
        except Exception as e:
            print(f"WION error: {e}")

        if not all_news:
            all_news = [{'title': 'WION News', 'link': 'https://www.wionews.com', 'image': '', 'description': 'Visit WION', 'category': 'NEWS'}]

        return all_news[:30]

    def get_section_news(self, section, include_images=True):
        return self.get_home_news(include_images)

    def get_related_news(self, url):
        return self.get_home_news()[:6]

    def get_sections(self):
        return [{'id': 'home', 'name': 'Home', 'default': True}]

    def get_article(self, url):
        return {'title': 'Article', 'content': '<p>Content</p>', 'image': '', 'related_news': []}

    def get_capabilities(self):
        return {
            'has_images': False,
            'has_sections': False,
            'has_article_content': False,
            'has_related_news': False
        }


register_scraper('wion', WIONScraper)