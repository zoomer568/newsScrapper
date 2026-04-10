import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()
from scrapers import BaseScraper, register_scraper


class MyAnimeListScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = 'https://myanimelist.net'
        self.rss_url = 'https://myanimelist.net/rss/news.xml'

    def get_home_news(self, include_images=True):
        all_news = []
        seen = set()
        
        # Try RSS first
        try:
            resp = requests.get(self.rss_url, headers=self.headers, timeout=15, verify=False)
            root = ET.fromstring(resp.content)
            
            for item in root.findall('.//item')[:30]:
                title = item.find('title').text if item.find('title') is not None else ''
                link = item.find('link').text if item.find('link') is not None else ''
                
                if not title or not link:
                    continue
                if link in seen:
                    continue
                seen.add(link)
                
                all_news.append({
                    'title': title,
                    'link': link,
                    'image': '',
                    'description': '',
                    'category': 'ANIME'
                })
        except Exception as e:
            print(f"MAL RSS error: {e}")
        
        # Try top anime page if RSS didn't work
        if len(all_news) < 10:
            try:
                resp = requests.get(f'{self.base_url}/topanime.php', headers=self.headers, timeout=15, verify=False)
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                for row in soup.select('tr.ranking-list')[:30]:
                    title_elem = row.select_one('.title a')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    href = title_elem.get('href', '')
                    
                    if not title or len(title) < 3:
                        continue
                    if href in seen:
                        continue
                    seen.add(href)
                    
                    rank_elem = row.select_one('.rank .fll')
                    rank = rank_elem.get_text(strip=True) if rank_elem else ''
                    
                    all_news.append({
                        'title': f"{rank}. {title}" if rank else title,
                        'link': href if href.startswith('http') else self.base_url + href,
                        'image': '',
                        'description': '',
                        'category': 'ANIME'
                    })
            except Exception as e:
                print(f"MAL topanime error: {e}")
        
        # Try news page as fallback
        if len(all_news) < 10:
            try:
                resp = requests.get(f'{self.base_url}/news', headers=self.headers, timeout=15, verify=False)
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                for link in soup.select('a[href*="/news/"]'):
                    title = link.get_text(strip=True)
                    href = link.get('href', '')
                    
                    if not title or len(title) < 10:
                        continue
                    if href in seen:
                        continue
                    seen.add(href)
                    
                    all_news.append({
                        'title': title,
                        'link': href if href.startswith('http') else self.base_url + href,
                        'image': '',
                        'description': '',
                        'category': 'ANIME'
                    })
            except Exception as e:
                print(f"MAL news error: {e}")

        if not all_news:
            all_news = [{'title': 'MyAnimeList - Top Anime', 'link': 'https://myanimelist.net/topanime.php', 'image': '', 'description': 'Visit MyAnimeList', 'category': 'ANIME'}]

        return all_news[:30]

    def get_section_news(self, section, include_images=True):
        return self.get_home_news(include_images)

    def get_related_news(self, url):
        return self.get_home_news()[:6]

    def get_sections(self):
        return [{'id': 'home', 'name': 'Home', 'default': True}]

    def get_article(self, url):
        return {'title': 'Article', 'content': '<p>Content</p>', 'image': '', 'related_news': []}


register_scraper('myanimelist', MyAnimeListScraper)