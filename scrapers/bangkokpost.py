import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()
from scrapers import BaseScraper, register_scraper


class BangkokPostScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = 'https://www.bangkokpost.com'

    def get_home_news(self, include_images=True):
        all_news = []
        seen = set()
        
        # Try multiple section pages
        sections = ['/thailand', '/world', '/business', '/politics', '/news']
        
        for section in sections:
            if len(all_news) >= 30:
                break
            try:
                url = self.base_url + section
                resp = requests.get(url, headers=self.headers, timeout=10, verify=False)
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                for a in soup.find_all('a', href=True):
                    title = a.get_text(strip=True)
                    href = a.get('href', '')
                    
                    # Filter for article-like links
                    if not title or len(title) < 15:
                        continue
                    if not href or href in ['javascript:;', '#', '/']:
                        continue
                    if '/author/' in href or '/tag/' in href or '/search' in href:
                        continue
                    if href in seen:
                        continue
                        
                    if not href.startswith('http'):
                        href = self.base_url + href
                    elif self.base_url not in href:
                        continue
                        
                    seen.add(href)
                    
                    all_news.append({
                        'title': title,
                        'link': href,
                        'image': '',
                        'description': '',
                        'category': 'THAILAND'
                    })
                    
                    if len(all_news) >= 30:
                        break
            except Exception as e:
                continue

        if not all_news:
            all_news = [
                {'title': 'Thailand News', 'link': 'https://www.bangkokpost.com/thailand', 'image': '', 'description': 'Thailand News', 'category': 'THAILAND'},
                {'title': 'World News', 'link': 'https://www.bangkokpost.com/world', 'image': '', 'description': 'World News', 'category': 'WORLD'},
                {'title': 'Business News', 'link': 'https://www.bangkokpost.com/business', 'image': '', 'description': 'Business News', 'category': 'BUSINESS'},
                {'title': 'Politics News', 'link': 'https://www.bangkokpost.com/politics', 'image': '', 'description': 'Politics News', 'category': 'POLITICS'},
                {'title': 'Sports News', 'link': 'https://www.bangkokpost.com/sports', 'image': '', 'description': 'Sports News', 'category': 'SPORTS'},
                {'title': 'Lifestyle', 'link': 'https://www.bangkokpost.com/lifestyle', 'image': '', 'description': 'Lifestyle News', 'category': 'LIFESTYLE'},
                {'title': 'Opinion', 'link': 'https://www.bangkokpost.com/opinion', 'image': '', 'description': 'Opinion', 'category': 'OPINION'},
                {'title': 'Tech News', 'link': 'https://www.bangkokpost.com/tech', 'image': '', 'description': 'Tech News', 'category': 'TECH'},
                {'title': 'Science', 'link': 'https://www.bangkokpost.com/science', 'image': '', 'description': 'Science News', 'category': 'SCIENCE'},
                {'title': 'Health', 'link': 'https://www.bangkokpost.com/health', 'image': '', 'description': 'Health News', 'category': 'HEALTH'},
            ]

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


register_scraper('bangkokpost', BangkokPostScraper)