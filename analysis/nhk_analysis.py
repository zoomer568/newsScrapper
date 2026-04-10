"""================================================================================
NHK NEWS WEBSITE DEEP ANALYSIS
================================================================================

Date: 2026-04-10
Website: https://www3.nhk.or.jp/news
Analysis Tool: Beautiful Soup + Requests

================================================================================
SECTION 1: BASIC STRUCTURE
================================================================================

URL PATTERNS:
- Homepage: https://www3.nhk.or.jp/news
- News Categories: /newsweb/genre/{category}
- Article Detail: /newsweb/na/na-{id}
- Easy News: /news/easy
- Video: /newsweb/video

SECTIONS AVAILABLE:
- 社会 (Society)
- 政治 (Politics)
- 経済 (Economy)
- 気象・災害 (Weather/Disaster)
- 国際 (International)
- 科学・文化 (Science/Culture)
- スポーツ (Sports)
- 暮らし (Life)

================================================================================
SECTION 2: TECHNOLOGY STACK
================================================================================

Frontend Framework: Custom JavaScript (lightweight)
CSS: NHK custom CSS, responsive design
Analytics: NHK internal analytics
Ads: None (public broadcaster)

KEY OBSERVATIONS:
- Traditional server-rendered HTML (easy to scrape)
- Clean, minimal JavaScript
- No heavy frameworks
- Very scrape-friendly structure
- Content also available in English: https://www3.nhk.jp/nhkworld/

================================================================================
SECTION 3: ARTICLE STRUCTURE ANALYSIS
================================================================================

META TAGS FOUND:
- og:title, og:description, og:image, og:url
- Standard meta description

EXTRACTABLE DATA:
✓ Title: h1, .article-title
✓ Summary: .article-summary, .lead
✓ Content: .article-body p
✓ Image: .article-img img, meta[property="og:image"]
✓ Category: .category-link
✓ Date: .article-date, time[datetime]

================================================================================
SECTION 4: IMAGE HANDLING
================================================================================

CDN Domain: imgu.web.nhk.or.jp, imgu.nhk.or.jp

Image URL Patterns:
- https://imgu.web.nhk/news/u/news/html/.../image.jpg
- https://imgu.web.nhk/news/u/nwo/top/.../image.jpg

Lazy Loading:
- Uses src attributes directly
- Multiple sizes available

================================================================================
SECTION 5: RSS FEED
================================================================================

RSS URL: Not directly available for news
Alternative: Use web scraping

================================================================================
SECTION 6: SCRAPING STRATEGY
================================================================================

DIFFICULTY: LOW (easy to scrape)

CODE TEMPLATE:
```python
import requests
from bs4 import BeautifulSoup
import re

class NHKScraper:
    BASE_URL = 'https://www3.nhk.or.jp/news'
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    def get_home_news(self):
        resp = requests.get(self.BASE_URL, headers=self.HEADERS)
        soup = BeautifulSoup(resp.text, 'html.parser')

        articles = []
        for article in soup.select('.content .item, .news-list .item'):
            link = article.find('a')
            if not link:
                continue
            
            title = link.get_text(strip=True)
            href = link.get('href', '')
            
            if title and href:
                full_url = href if href.startswith('http') else f"{self.BASE_URL}{href}"
                articles.append({
                    'title': title[:200],
                    'link': full_url
                })

        return articles[:30]

    def get_category_news(self, category='society'):
        url = f'{self.BASE_URL}/newsweb/genre/{category}'
        resp = requests.get(url, headers=self.HEADERS)
        soup = BeautifulSoup(resp.text, 'html.parser')

        articles = []
        for article in soup.select('.content .item, .news-list .item'):
            link = article.find('a')
            if not link:
                continue
            
            title = link.get_text(strip=True)
            href = link.get('href', '')
            
            if title and href:
                full_url = href if href.startswith('http') else f"{self.BASE_URL}{href}"
                articles.append({
                    'title': title[:200],
                    'link': full_url
                })

        return articles[:30]

    def get_article(self, url):
        resp = requests.get(url, headers=self.HEADERS)
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Extract title
        title = ''
        title_elem = soup.find('h1') or soup.find('title')
        if title_elem:
            title = title_elem.get_text(strip=True)

        # Extract content
        content = ''
        article_body = soup.find('div', class_='article-body') or soup.find('article')
        if article_body:
            for p in article_body.find_all('p'):
                text = p.get_text(strip=True)
                if text and len(text) > 10:
                    content += f'<p>{text}</p>'

        # Extract image
        image = ''
        og_image = soup.find('meta', property='og:image')
        if og_image:
            image = og_image.get('content', '')

        # Extract date
        date = ''
        time_elem = soup.find('time')
        if time_elem:
            date = time_elem.get('datetime', '') or time_elem.get_text(strip=True)

        return {
            'title': title,
            'content': content,
            'image': image,
            'date': date,
            'link': url
        }

    def get_latest_news(self):
        url = f'{self.BASE_URL}/newsweb/pl/news-nwa-latest-nationwide'
        resp = requests.get(url, headers=self.HEADERS)
        soup = BeautifulSoup(resp.text, 'html.parser')

        articles = []
        for article in soup.select('.content .item'):
            link = article.find('a')
            if not link:
                continue
            
            title = link.get_text(strip=True)
            href = link.get('href', '')
            
            # Get thumbnail
            img = article.select_one('img')
            image = img.get('src', '') if img else ''
            
            if title and href:
                full_url = href if href.startswith('http') else f"{self.BASE_URL}{href}"
                articles.append({
                    'title': title[:200],
                    'link': full_url,
                    'image': image
                })

        return articles[:30]
```

================================================================================
SECTION 7: CONCLUSION
================================================================================

Beautiful Soup VIABILITY: LOW (very easy)

ADVANTAGES:
✓ Traditional server-rendered HTML
✓ Clean URL patterns
✓ Simple structure
✓ No JavaScript rendering issues
✓ Good meta tags for extraction
✓ Public broadcaster (no ads blocking)
✓ Multiple categories
✓ Also available in English

CAN EXTRACT:
- All article content
- Images
- Categories
- Publication dates

CANNOT EXTRACT:
- Video content (streaming)
- Live broadcasts
- Some interactive features

OVERALL: NHK News is VERY EASY to scrape with Beautiful Soup.
Best for: Japanese news, international news coverage, weather/disaster info.
"""