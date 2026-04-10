import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from scrapers import BaseScraper, register_scraper


class GuardianScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = 'https://www.theguardian.com'

    def get_home_news(self, include_images=True):
        all_news = []
        seen = set()
        try:
            resp = requests.get(self.base_url, headers=self.headers, timeout=15, verify=False)
            soup = BeautifulSoup(resp.text, 'html.parser')

            for link in soup.select('a[href*="/news/"], a[href*="/world/"]'):
                title = link.get_text(strip=True)
                href = link.get('href', '')

                if not title or len(title) < 15:
                    continue
                if not href or '/video' in href or '/live' in href:
                    continue
                if '/news/' not in href and '/world/' not in href:
                    continue

                if not href.startswith('http'):
                    href = self.base_url + href

                if href in seen:
                    continue
                seen.add(href)

                all_news.append({
                    'title': title,
                    'link': href,
                    'image': '',
                    'description': '',
                    'category': 'UK'
                })

                if len(all_news) >= 30:
                    break
        except Exception as e:
            print(f"Error in Guardian get_home_news: {e}")

        if not all_news:
            all_news = [{'title': 'The Guardian News', 'link': 'https://www.theguardian.com', 'image': '', 'description': 'Visit The Guardian', 'category': 'NEWS'}]

        return all_news[:30]

    def get_section_news(self, section, include_images=True):
        if section == 'home':
            return self.get_home_news(include_images)
        return self.get_home_news(include_images)

    def get_related_news(self, url):
        return self.get_home_news()[:6]

    def get_sections(self):
        return [
            {'id': 'home', 'name': 'Home', 'default': True},
        ]

    def get_article(self, url):
        return {
            'title': 'Article',
            'content': '<p>Article content</p>',
            'image': '',
            'related_news': []
        }

    def get_capabilities(self):
        return {
            'has_images': False,
            'has_sections': False,
            'has_article_content': False,
            'has_related_news': False
        }


register_scraper('guardian', GuardianScraper)