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

    def _extract_image(self, element, base_url=None):
        """Extract image URL from any element"""
        if not element:
            return ''
        
        url = base_url or self.base_url
        
        picture = element.select_one('picture')
        if picture:
            source = picture.find('source')
            if source:
                srcset = source.get('srcset', '')
                if srcset:
                    img = srcset.split(',')[0].strip().split(' ')[0]
                    if img:
                        return img
        
        img_elem = element.select_one('img')
        if img_elem:
            for attr in ['data-lazy-src', 'data-src', 'data-original', 'data-image', 'src']:
                img = img_elem.get(attr, '')
                if img and not img.startswith('data:'):
                    if not img.startswith('http'):
                        img = url + img
                    if img and 'cdn.i-scmp.com' in img:
                        return img
        
        return ''

    def get_home_news(self, include_images=True):
        all_news = []
        seen = set()

        try:
            resp = requests.get(f'{self.base_url}/news', headers=self.headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')

            # Build a map of href -> image from all picture elements in the page
            # Use path (without query params) as key since article links may have params
            href_to_img = {}
            if include_images:
                pictures = soup.find_all('picture')
                for pic in pictures:
                    parent_a = pic.find_parent('a')
                    if parent_a:
                        href = parent_a.get('href', '')
                        if href and '/article/' in href:
                            source = pic.find('source')
                            if source:
                                srcset = source.get('srcset', '')
                                if srcset:
                                    from urllib.parse import urlparse
                                    path = urlparse(href).path
                                    href_to_img[path] = srcset.split(',')[0].strip().split(' ')[0]
            
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
                
                # Look up image from pre-built map (using path without query params)
                from urllib.parse import urlparse
                path = urlparse(href).path
                img = href_to_img.get(path, '')

                desc = ''
                parent = a.find_parent(['div', 'li', 'article'])
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
                    'image': img,
                    'description': desc[:200] if desc else '',
                    'category': ', '.join(tags) if tags else 'News'
                })

        except Exception as e:
            print(f"Error in get_home_news: {e}")

        return all_news[:30]

    def get_section_news(self, section, include_images=True):
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

            # Build a map of href -> image from all picture elements in the page
            # Use path (without query params) as key since article links may have params
            href_to_img = {}
            if include_images:
                pictures = soup.find_all('picture')
                for pic in pictures:
                    parent_a = pic.find_parent('a')
                    if parent_a:
                        href = parent_a.get('href', '')
                        if href and '/article/' in href:
                            source = pic.find('source')
                            if source:
                                srcset = source.get('srcset', '')
                                if srcset:
                                    from urllib.parse import urlparse
                                    path = urlparse(href).path
                                    href_to_img[path] = srcset.split(',')[0].strip().split(' ')[0]

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
                
                # Look up image from pre-built map (using path without query params)
                from urllib.parse import urlparse
                path = urlparse(href).path
                img = href_to_img.get(path, '')

                all_news.append({
                    'title': title,
                    'link': full_url,
                    'image': img,
                    'description': '',
                    'category': section.upper().replace('_', ' ')
                })

                if len(all_news) >= 30:
                    break

        except Exception as e:
            print(f"Error: {e}")

        return all_news

    def get_related_news(self, url):
        from urllib.parse import urlparse, urljoin
        related_news = []
        parsed_url = urlparse(url)
        article_id = parsed_url.path.split('/article/')[-1].split('/')[0] if '/article/' in parsed_url.path else ''
        base_article_path = parsed_url.path.split('/article/')[0] if '/article/' in parsed_url.path else ''

        try:
            section = ''
            if '/news/china/' in url or '/china/' in url:
                section = '/news/china'
            elif '/news/hong-kong/' in url:
                section = '/news/hong-kong'
            elif '/news/world/' in url:
                section = '/news/world'
            elif '/business/' in url or '/economy/' in url:
                section = '/business'
            elif '/tech/' in url:
                section = '/tech'
            elif '/sport/' in url:
                section = '/sport'
            elif '/lifestyle/' in url:
                section = '/lifestyle'
            else:
                section = '/news'

            resp = requests.get(f'{self.base_url}{section}', headers=self.headers, timeout=10)
            section_soup = BeautifulSoup(resp.text, 'html.parser')

            seen_ids = {article_id}
            all_links = section_soup.find_all('a', href=True)
            links = [a for a in all_links if '/article/' in a.get('href', '')]

            section_path = section.replace('/news/', '/news/').replace('/', '') if '/news/' in section else section.replace('/', '')

            for a in links:
                href = a.get('href', '')
                if not href:
                    continue
                if '/plus/' in href:
                    continue

                full_url = urljoin(self.base_url, href)
                parsed_link = urlparse(full_url)
                link_path = parsed_link.path

                if section == '/news':
                    if '/news/' not in link_path:
                        continue
                elif section == '/business':
                    if '/business/' not in link_path and '/economy/' not in link_path:
                        continue
                elif section == '/tech':
                    if '/tech/' not in link_path:
                        continue
                else:
                    if section not in link_path:
                        continue

                link_id = link_path.split('/article/')[-1].split('/')[0] if '/article/' in link_path else ''

                if link_id in seen_ids:
                    continue
                seen_ids.add(link_id)

                title = a.get_text(strip=True)
                if not title or len(title) < 15:
                    continue

                img = self.get_article_image(full_url) if hasattr(self, 'get_article_image') else ''
                related_news.append({
                    'title': title,
                    'link': full_url,
                    'image': img,
                    'category': 'RELATED'
                })

                if len(related_news) >= 6:
                    break

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
            picture = soup.find('picture')
            if picture:
                source = picture.find('source')
                if source:
                    srcset = source.get('srcset', '')
                    if srcset:
                        img = srcset.split(',')[0].strip().split(' ')[0]
                        if img and not img.startswith('http'):
                            img = f'{parsed.scheme}://{parsed.netloc}{img}'
            
            if not img:
                for img_elem in soup.find_all('img'):
                    src = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('data-lazy-src') or ''
                    if src and 'cdn.i-scmp.com' in src:
                        if not src.startswith('http'):
                            src = f'{parsed.scheme}://{parsed.netloc}{src}'
                        if src:
                            img = src
                            break
            
            if not img:
                og_image = soup.find('meta', property='og:image')
                if og_image:
                    img = og_image.get('content', '')

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
            clean_url = f'{parsed.scheme}://{parsed.netloc}{path}'

            resp = requests.get(clean_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')

            picture = soup.find('picture')
            if picture:
                source = picture.find('source')
                if source:
                    srcset = source.get('srcset', '')
                    if srcset:
                        img = srcset.split(',')[0].strip().split(' ')[0]
                        if img and not img.startswith('http'):
                            img = f'{parsed.scheme}://{parsed.netloc}{img}'
                        return img

            for img_elem in soup.find_all('img'):
                src = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('data-lazy-src') or ''
                if src and 'cdn.i-scmp.com' in src:
                    if not src.startswith('http'):
                        src = f'{parsed.scheme}://{parsed.netloc}{src}'
                    if src:
                        return src
                    
            meta_og = soup.find('meta', property='og:image')
            if meta_og:
                return meta_og.get('content', '')
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

    def get_capabilities(self):
        return {
            'has_images': True,
            'has_sections': True,
            'has_article_content': True,
            'has_related_news': True
        }


register_scraper('scmp', SCMPScraper)