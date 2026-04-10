import requests
from bs4 import BeautifulSoup
from scrapers import BaseScraper, register_scraper


class SCMPScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = 'https://www.scmp.com'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }

    def get_home_news(self):
        all_news = []
        seen = set()

        try:
            resp = requests.get(f'{self.base_url}/news', headers=self.headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')

            all_links = soup.find_all('a', href=True)
            links = [a for a in all_links if '/article/' in a.get('href', '')]

            for a in links:
                href = a.get('href', '')
                if not href or not href.startswith('/'):
                    continue
                if '/plus/' in href:
                    continue
                if href in seen:
                    continue
                seen.add(href)

                title = a.get_text(strip=True)
                if not title or len(title) < 15:
                    continue

                full_url = self.base_url + href if href.startswith('/') else href

                parent = a.find_parent(['div', 'li', 'article'])

                desc = ''
                if parent:
                    for p in parent.find_all('p')[:2]:
                        text = p.get_text(strip=True)
                        if text and len(text) > 40:
                            desc = text
                            break

                tags = []
                if '/china/' in href:
                    tags.append('CHINA')
                elif '/hong-kong/' in href:
                    tags.append('HONG KONG')
                elif '/world/' in href:
                    tags.append('WORLD')
                elif '/business/' in href:
                    tags.append('BUSINESS')
                elif '/tech/' in href:
                    tags.append('TECH')
                elif '/sport/' in href:
                    tags.append('SPORT')
                elif '/lifestyle/' in href:
                    tags.append('LIFESTYLE')

                all_news.append({
                    'title': title,
                    'link': full_url,
                    'image': '',
                    'description': desc[:200] if desc else '',
                    'category': ', '.join(tags) if tags else 'News'
                })

        except Exception as e:
            print(f"Error in get_home_news: {e}")

        return all_news[:30]

    def get_section_news(self, section):
        all_news = []
        seen = set()

        section_urls = {
            'china': f'{self.base_url}/news/china',
            'hong_kong': f'{self.base_url}/news/hong-kong',
            'world': f'{self.base_url}/news/world',
            'business': f'{self.base_url}/business',
            'tech': f'{self.base_url}/tech',
            'sport': f'{self.base_url}/sport',
            'lifestyle': f'{self.base_url}/lifestyle',
            'politics': f'{self.base_url}/news/hong-kong/politics',
        }

        url = section_urls.get(section)
        if not url:
            return []

        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')

            all_links = soup.find_all('a', href=True)
            links = [a for a in all_links if '/article/' in a.get('href', '')]

            for a in links:
                href = a.get('href', '')
                if not href or not href.startswith('/'):
                    continue
                if '/plus/' in href:
                    continue
                if href in seen:
                    continue
                seen.add(href)

                title = a.get_text(strip=True)
                if not title or len(title) < 15:
                    continue

                full_url = self.base_url + href

                all_news.append({
                    'title': title,
                    'link': full_url,
                    'image': '',
                    'description': '',
                    'category': section.upper().replace('_', ' ')
                })

                if len(all_news) >= 30:
                    break

        except Exception as e:
            print(f"Error: {e}")

        return all_news

    def get_related_news(self, url):
        related_news = []
        seen = {url}

        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            path = parsed.path
            if not path.endswith('/'):
                path = path + '/'
            clean_url = f'{parsed.scheme}://{parsed.netloc}{path}'
            
            resp = requests.get(clean_url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')

            related_selectors = [
                ('div', {'class': lambda x: x and 'related' in str(x).lower() if x else False}),
                ('section', {'class': lambda x: x and 'related' in str(x).lower() if x else False}),
                ('div', {'data-component': 'related-articles'}),
                ('aside', {'class': lambda x: x and 'related' in str(x).lower() if x else False}),
            ]

            for tag, attrs in related_selectors:
                related_section = soup.find(tag, attrs)
                if related_section:
                    links = related_section.find_all('a', href=lambda x: x and '/article/' in x if x else False)
                    for a in links[:10]:
                        href = a.get('href', '')
                        if not href:
                            continue
                        if not href.startswith('/'):
                            continue
                        if '/plus/' in href:
                            continue
                        if href in seen:
                            continue
                        seen.add(href)
                        
                        title = a.get_text(strip=True)
                        if not title or len(title) < 15:
                            continue
                        
                        full_url = self.base_url + href
                        related_news.append({
                            'title': title,
                            'link': full_url,
                            'image': '',
                            'category': 'RELATED'
                        })
                        
                        if len(related_news) >= 6:
                            break
                    
                    if related_news:
                        break

            if not related_news:
                section = ''
                if '/news/china/' in url:
                    section = '/news/china'
                elif '/news/hong-kong/' in url:
                    section = '/news/hong-kong'
                elif '/news/world/' in url:
                    section = '/news/world'
                elif '/business/' in url:
                    section = '/business'
                elif '/tech/' in url:
                    section = '/tech'
                else:
                    section = '/news'

                try:
                    resp = requests.get(f'{self.base_url}{section}', headers=self.headers, timeout=10)
                    section_soup = BeautifulSoup(resp.text, 'html.parser')

                    all_links = section_soup.find_all('a', href=True)
                    links = [a for a in all_links if '/article/' in a.get('href', '') and not a.get('href', '').startswith('http')]

                    for a in links[:30]:
                        href = a.get('href', '')
                        if not href:
                            continue
                        if '/plus/' in href:
                            continue
                        if href in seen:
                            continue
                        seen.add(href)

                        title = a.get_text(strip=True)
                        if not title or len(title) < 15:
                            continue

                        full_url = self.base_url + href

                        related_news.append({
                            'title': title,
                            'link': full_url,
                            'image': '',
                            'category': 'RELATED'
                        })

                        if len(related_news) >= 6:
                            break
                except Exception as e:
                    print(f"Error getting related from section: {e}")

        except Exception as e:
            print(f"Error getting related news: {e}")

        return related_news[:6]

    def get_article(self, url):
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        path = parsed.path
        if not path.endswith('/'):
            path = path + '/'
        clean_url = f'{parsed.scheme}://{parsed.netloc}{path}'
        
        try:
            resp = requests.get(clean_url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')

            title = ''
            title_elem = soup.find('h1')
            if title_elem:
                title = title_elem.get_text(strip=True)

            article_content = ''
            article_body = soup.find('article')

            if article_body:
                for p in article_body.find_all('p'):
                    text = p.get_text(strip=True)
                    if text and len(text) > 20:
                        article_content += f'<p>{text}</p>'

            if not article_content:
                main = soup.find('main') or soup.find('div', class_=lambda x: x and 'article' in str(x).lower() if x else False)
                if main:
                    for p in main.find_all('p'):
                        text = p.get_text(strip=True)
                        if text and len(text) > 20:
                            article_content += f'<p>{text}</p>'

            img = ''
            for img_elem in soup.find_all('img'):
                src = img_elem.get('src') or ''
                if src and 'cdn.i-scmp.com' in src:
                    img = src
                    break

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

    def get_article_image(self, url):
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            path = parsed.path
            if not path.endswith('/'):
                path = path + '/'
            clean_url = f'{parsed.scheme}://{parsed.netloc}{path}'
            
            resp = requests.get(clean_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            picture = soup.find('picture')
            if picture:
                source = picture.find('source')
                if source:
                    srcset = source.get('srcset', '')
                    if srcset:
                        return srcset.split(',')[0].strip().split(' ')[0]
            
            for img_elem in soup.find_all('img'):
                src = img_elem.get('src') or ''
                if src and 'cdn.i-scmp.com' in src and 'canvas' not in src:
                    return src
        except:
            pass
        return ''

    def get_sections(self):
        return [
            {'id': 'home', 'name': 'Home', 'default': True},
            {'id': 'china', 'name': 'China'},
            {'id': 'hong_kong', 'name': 'Hong Kong'},
            {'id': 'world', 'name': 'World'},
            {'id': 'business', 'name': 'Business'},
            {'id': 'tech', 'name': 'Tech'},
            {'id': 'sport', 'name': 'Sport'},
            {'id': 'lifestyle', 'name': 'Lifestyle'},
            {'id': 'politics', 'name': 'Politics'},
        ]


register_scraper('scmp', SCMPScraper)