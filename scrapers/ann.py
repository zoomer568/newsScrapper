import requests
from bs4 import BeautifulSoup
from scrapers import BaseScraper, register_scraper


class AnimeNewsNetworkScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = 'https://www.animenewsnetwork.com'

    def get_home_news(self, include_images=True):
        all_news = []
        seen = set()
        try:
            resp = requests.get(self.base_url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')

            for article in soup.select('.news-type .story, .herald .story'):
                title_elem = article.select_one('.headline a, .headline')
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                link = title_elem.get('href', '')

                if not title or len(title) < 10:
                    continue
                if not link:
                    continue

                if link.startswith('/'):
                    link = self.base_url + link
                elif not link.startswith('http'):
                    link = self.base_url + '/' + link

                if link in seen:
                    continue
                seen.add(link)

                img = ''
                if include_images:
                    img_elem = article.select_one('img')
                    if img_elem:
                        img = img_elem.get('src', '') or img_elem.get('data-src', '')

                desc = ''
                content_elem = article.select_one('.content')
                if content_elem:
                    desc = content_elem.get_text(strip=True)[:200]

                topic = ''
                topic_elem = article.select_one('.topic')
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

        return all_news[:30]

    def get_section_news(self, section, include_images=True):
        all_news = []
        seen = set()

        section_urls = {
            'anime': f'{self.base_url}/news/all?topic=anime',
            'games': f'{self.base_url}/news/all?topic=games',
            'industry': f'{self.base_url}/news/all?topic=industry',
            'manga': f'{self.base_url}/news/all?topic=manga',
            'culture': f'{self.base_url}/interest',
            'reviews': f'{self.base_url}/review',
        }

        url = section_urls.get(section, f'{self.base_url}/news')
        if section == 'home':
            return self.get_home_news(include_images)

        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')

            for article in soup.select('.news-list li, .herald li, .news-type .story'):
                title_elem = article.select_one('a')
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                href = title_elem.get('href', '')

                if not title or len(title) < 10:
                    continue
                if not href:
                    continue

                if href.startswith('/'):
                    href = self.base_url + href
                elif not href.startswith('http'):
                    href = self.base_url + '/' + href

                if href in seen:
                    continue
                seen.add(href)

                img = ''
                if include_images:
                    img_elem = article.select_one('img')
                    if img_elem:
                        img = img_elem.get('src', '') or img_elem.get('data-src', '')

                all_news.append({
                    'title': title,
                    'link': href,
                    'image': img,
                    'description': '',
                    'category': section.upper()
                })

                if len(all_news) >= 30:
                    break

        except Exception as e:
            print(f"Error fetching section {section}: {e}")

        return all_news

    def get_related_news(self, url):
        related_news = []
        seen = set()

        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')

            topic_elem = soup.select_one('.topic, .news-topic')
            topic = ''
            if topic_elem:
                topic = topic_elem.get_text(strip=True).lower()

            related_section = soup.select('.related-stories li a, .news-list li a')
            for a in related_section[:10]:
                href = a.get('href', '')
                if not href:
                    continue

                if href.startswith('/'):
                    href = self.base_url + href
                elif not href.startswith('http'):
                    href = self.base_url + '/' + href

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
            section = 'anime'
            if 'game' in topic:
                section = 'games'
            elif 'manga' in topic:
                section = 'manga'
            related_news.extend(self.get_section_news(section)[:6])

        return related_news[:6]

    def get_sections(self):
        return [
            {'id': 'home', 'name': 'Home', 'default': True},
            {'id': 'anime', 'name': 'Anime'},
            {'id': 'games', 'name': 'Games'},
            {'id': 'manga', 'name': 'Manga'},
            {'id': 'industry', 'name': 'Industry'},
            {'id': 'reviews', 'name': 'Reviews'},
            {'id': 'culture', 'name': 'Interest'},
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
            article_body = soup.find('article') or soup.find('.story-body')
            if article_body:
                for p in article_body.find_all(['p', 'div']):
                    text = p.get_text(strip=True)
                    if text and len(text) > 20:
                        article_content += f'<p>{text}</p>'

            img = ''
            og_image = soup.find('meta', property='og:image')
            if og_image:
                img = og_image.get('content', '')

            if not img:
                img_elem = soup.select_one('.news-image img')
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


register_scraper('ann', AnimeNewsNetworkScraper)