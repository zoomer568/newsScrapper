import requests
import xml.etree.ElementTree as ET
import re
from bs4 import BeautifulSoup
from scrapers import BaseScraper, register_scraper


class MyAnimeListScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = 'https://myanimelist.net'
        self.rss_url = 'https://myanimelist.net/rss/news.xml'

    def get_home_news(self, include_images=True):
        all_news = []
        seen = set()
        try:
            resp = requests.get(self.base_url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')

            for news in soup.select('.news-unit, .news-list-item'):
                title_elem = news.select_one('.title a, .news-title a')
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                link = title_elem.get('href', '')

                if not title or len(title) < 10:
                    continue
                if not link:
                    continue

                if not link.startswith('http'):
                    link = self.base_url + link

                if link in seen:
                    continue
                seen.add(link)

                img = ''
                if include_images:
                    img_elem = news.select_one('.picLeft img')
                    if img_elem:
                        img = img_elem.get('src', '') or img_elem.get('data-src', '')

                desc = ''
                content_elem = news.select_one('.content')
                if content_elem:
                    desc = content_elem.get_text(strip=True)[:200]

                topic = ''
                topic_elem = news.select_one('.information .genre a')
                if topic_elem:
                    topic = topic_elem.get_text(strip=True)

                all_news.append({
                    'title': title,
                    'link': link,
                    'image': img,
                    'description': desc,
                    'category': topic.upper() if topic else 'NEWS'
                })
        except Exception as e:
            print(f"Error in get_home_news: {e}")

        if not all_news:
            return self.get_rss_news(include_images)

        return all_news[:30]

    def get_rss_news(self, include_images=True):
        all_news = []
        seen = set()
        try:
            resp = requests.get(self.rss_url, headers=self.headers, timeout=15)
            root = ET.fromstring(resp.content)

            for item in root.findall('.//item')[:30]:
                title = item.find('title').text if item.find('title') is not None else ''
                link = item.find('link').text if item.find('link') is not None else ''
                desc = item.find('description').text if item.find('description') is not None else ''

                if not title or not link:
                    continue
                if link in seen:
                    continue
                seen.add(link)

                desc = re.sub('<[^>]+>', '', desc) if desc else ''

                all_news.append({
                    'title': title,
                    'link': link,
                    'image': '',
                    'description': desc[:200],
                    'category': 'NEWS'
                })
        except Exception as e:
            print(f"Error fetching RSS: {e}")

        return all_news

    def get_section_news(self, section, include_images=True):
        all_news = []
        seen = set()

        if section == 'home':
            return self.get_home_news(include_images)

        if section == 'anime':
            url = 'https://myanimelist.net/topanime.php'
        elif section == 'manga':
            url = 'https://myanimelist.net/topmanga.php'
        else:
            url = f'{self.base_url}/news'

        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')

            if section in ('anime', 'manga'):
                for row in soup.select('tr.ranking-list'):
                    title_elem = row.select_one('.title a')
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    link = title_elem.get('href', '')

                    if not title or len(title) < 5:
                        continue
                    if not link:
                        continue
                    if not link.startswith('http'):
                        link = self.base_url + link

                    if link in seen:
                        continue
                    seen.add(link)

                    rank_elem = row.select_one('.rank .fll')
                    rank = rank_elem.get_text(strip=True) if rank_elem else ''

                    img = ''
                    if include_images:
                        img_elem = row.select_one('.image img')
                        if img_elem:
                            img = img_elem.get('src', '')

                    all_news.append({
                        'title': f"{rank}. {title}" if rank else title,
                        'link': link,
                        'image': img,
                        'description': '',
                        'category': section.upper()
                    })
            else:
                for news in soup.select('.news-unit'):
                    title_elem = news.select_one('.title a')
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    link = title_elem.get('href', '')

                    if not title or len(title) < 10:
                        continue
                    if not link:
                        continue
                    if not link.startswith('http'):
                        link = self.base_url + link

                    if link in seen:
                        continue
                    seen.add(link)

                    img = ''
                    if include_images:
                        img_elem = news.select_one('.picLeft img')
                        if img_elem:
                            img = img_elem.get('src', '')

                    all_news.append({
                        'title': title,
                        'link': link,
                        'image': img,
                        'description': '',
                        'category': section.upper()
                    })

            if len(all_news) >= 30:
                all_news = all_news[:30]

        except Exception as e:
            print(f"Error fetching section {section}: {e}")

        return all_news

    def get_related_news(self, url):
        related_news = []
        seen = set()

        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')

            related_section = soup.select('.news-recommendations .news-unit a, .related .news-unit a')
            for a in related_section[:10]:
                href = a.get('href', '')
                if not href:
                    continue

                if not href.startswith('http'):
                    href = self.base_url + href

                if href in seen or href == url:
                    continue
                seen.add(href)

                title = a.get_text(strip=True)
                if title and len(title) > 10:
                    related_news.append({
                        'title': title,
                        'link': href,
                        'image': '',
                        'category': 'RELATED'
                    })

                if len(related_news) >= 6:
                    break
        except Exception as e:
            print(f"Error getting related news: {e}")

        if len(related_news) < 3:
            related_news.extend(self.get_home_news()[:6])

        return related_news[:6]

    def get_sections(self):
        return [
            {'id': 'home', 'name': 'Home', 'default': True},
            {'id': 'news', 'name': 'News'},
            {'id': 'anime', 'name': 'Top Anime'},
            {'id': 'manga', 'name': 'Top Manga'},
        ]

    def get_article(self, url):
        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')

            title = ''
            title_elem = soup.find('h1')
            if title_elem:
                title = title_elem.get_text(strip=True)

            if not title:
                og_title = soup.find('meta', property='og:title')
                title = og_title.get('content', '') if og_title else ''

            article_content = ''
            article_body = soup.find('div', class_='news-body') or soup.find('article')
            if article_body:
                for p in article_body.find_all('p'):
                    text = p.get_text(strip=True)
                    if text and len(text) > 20:
                        article_content += f'<p>{text}</p>'

            img = ''
            og_image = soup.find('meta', property='og:image')
            if og_image:
                img = og_image.get('content', '')

            if not img:
                img_elem = soup.select_one('.news-detail .picLeft img')
                if img_elem:
                    img = img_elem.get('src', '')

            if not article_content:
                article_content = '<p>Could not load article content.</p>'

            related_news = self.get_related_news(url)
            if len(related_news) < 3:
                related_news = self.get_home_news()[:6]

            return {
                'title': title,
                'content': article_content,
                'image': img,
                'related_news': related_news[:6]
            }
        except Exception as e:
            return {
                'title': 'Error',
                'content': f'Error loading article: {str(e)}',
                'image': '',
                'related_news': []
            }


register_scraper('myanimelist', MyAnimeListScraper)