"""================================================================================
YONHAP NEWS WEBSITE DEEP ANALYSIS
================================================================================

Date: 2026-04-10
Website: https://www.yna.co.kr
Analysis Tool: Beautiful Soup + Requests

================================================================================
SECTION 1: BASIC STRUCTURE
================================================================================

URL PATTERNS:
- Homepage: https://www.yna.co.kr
- Articles: /view/{article-code}
- Sections: /politics/, /economy/, /society/, /international/
- English: https://en.yna.co.kr
- Chinese: https://cn.yna.co.kr
- Japanese: https://jp.yna.co.kr
- Arabic: https://ar.yna.co.kr

SECTIONS AVAILABLE:
- 정치 (Politics)
- 북한 (North Korea)
- 경제 (Economy)
- 산업 (Industry)
- 사회 (Society)
- 세계 (International)
- 문화 (Culture)
- 스포츠 (Sports)
- 연예 (Entertainment)

================================================================================
SECTION 2: TECHNOLOGY STACK
================================================================================

Frontend Framework: jQuery + Custom JavaScript
CSS: Custom CSS, responsive design
Analytics: Google Analytics
Ads: Various ad networks

KEY OBSERVATIONS:
- Traditional server-rendered HTML (easy to scrape)
- Clean URL patterns
- Multiple language versions
- Responsive design

================================================================================
SECTION 3: ARTICLE STRUCTURE ANALYSIS
================================================================================

META TAGS FOUND:
- og:title, og:description, og:image, og:url
- twitter:card
- Standard meta description

EXTRACTABLE DATA:
✓ Title: h1, .article-title
✓ Summary: .article-lead, .lead
✓ Content: .article-body p
✓ Image: .article-photo img, meta[property="og:image"]
✓ Category: .category, .section
✓ Date: .article-date, time

================================================================================
SECTION 4: IMAGE HANDLING
================================================================================

CDN Domain: img*.yna.co.kr

Image URL Patterns:
- https://img*.yna.co.kr/photo/.../image.jpg
- https://img*.yna.co.kr/template/.../image.jpg

Lazy Loading:
- Uses src attributes
- Multiple sizes available

================================================================================
SECTION 5: RSS FEED
================================================================================

RSS URL: Limited availability

================================================================================
SECTION 6: SCRAPING STRATEGY
================================================================================

DIFFICULTY: LOW (easy to scrape)

CODE TEMPLATE:
```python
import requests
from bs4 import BeautifulSoup

class YonhapScraper:
    BASE_URL = 'https://www.yna.co.kr'
    ENGLISH_URL = 'https://en.yna.co.kr'
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    def get_home_news(self):
        resp = requests.get(self.BASE_URL, headers=self.HEADERS)
        soup = BeautifulSoup(resp.text, 'html.parser')

        articles = []
        for article in soup.select('.article-item, .news-item, .headline-item'):
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

    def get_english_news(self):
        resp = requests.get(self.ENGLISH_URL, headers=self.HEADERS)
        soup = BeautifulSoup(resp.text, 'html.parser')

        articles = []
        for article in soup.select('.article-item, .news-item'):
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
        title_elem = soup.find('h1')
        if title_elem:
            title = title_elem.get_text(strip=True)

        # Extract content
        content = ''
        article_body = soup.find('article') or soup.find('div', class_='article-body')
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

        return {
            'title': title,
            'content': content,
            'image': image,
            'link': url
        }
```

================================================================================
SECTION 7: CONCLUSION
================================================================================

Beautiful Soup VIABILITY: LOW (easy to scrape)

ADVANTAGES:
✓ Traditional server-rendered HTML
✓ Clean URL patterns
✓ Multiple language versions (EN/CN/JP/AR)
✓ Simple structure

CAN EXTRACT:
- All article content
- Images
- Publication dates

CANNOT EXTRACT:
- Video content
- Some dynamic features

OVERALL: Yonhap News is EASY to scrape with Beautiful Soup.
Best for: Korean news, North Korea coverage, international news.
"""