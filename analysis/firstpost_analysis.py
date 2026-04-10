"""
================================================================================
FIRSTPOST WEBSITE DEEP ANALYSIS
================================================================================

Date: 2026-04-10
Website: https://www.firstpost.com
Analysis Tool: Beautiful Soup + Requests

================================================================================
SECTION 1: BASIC STRUCTURE
================================================================================

URL PATTERNS:
- Homepage: https://www.firstpost.com
- Sections: /news/, /world/, /india/, /sports/, /entertainment/, /tech/, /business/
- Articles: /<filename>.html (old pattern) or /<category>/<slug>
- Videos: /video-listing/, /video-library/
- AMP: /amp/
- Search: /search/?query=<term>

NAVIGATION ELEMENTS:
- Main menu via data-qa selectors
- Section links in header/footer
- Category tags on articles

================================================================================
SECTION 2: TECHNOLOGY STACK
================================================================================

Frontend Framework: React with JSX (evidenced by jsx- class names)
Rendering: Server-side rendering with hydration
CSS: CSS-in-JS (emotion/styled-jsx patterns)
Analytics: New Relic, Google Analytics, various ad tech

KEY OBSERVATIONS:
- Heavy JavaScript usage for dynamic content
- Lazy loading for images
- Infinite scroll on some sections
- Multiple ad placements

================================================================================
SECTION 3: ARTICLE STRUCTURE ANALYSIS
================================================================================

TYPICAL ARTICLE HTML:
```html
<article>
  <h1 class="hero-ttl">Article Title</h1>
  <div class="byline">
    <span class="author">Author Name</span>
    <time datetime="2026-04-10">Date</time>
  </div>
  <div class="image__container">
    <img src="https://images.firstpost.com/..." alt="...">
  </div>
  <div class="article_content">
    <p>Paragraph 1...</p>
    <p>Paragraph 2...</p>
  </div>
</article>
```

EXTRACTABLE DATA:
✓ Title: h1.hero-ttl
✓ Author: .author or meta[name="author"]
✓ Date: time[datetime] or meta[property="article:published_time"]
✓ Image: .image__container img src
✓ Content: .article_content p
✓ Tags: .tags a or meta[property="article:tag"]
✓ Description: meta[name="description"]

================================================================================
SECTION 4: IMAGE HANDLING
================================================================================

CDN Domain: images.firstpost.com

URL Pattern:
https://images.firstpost.com/<path>/image.jpg?im=FitAndFill,width=1200,height=675

Image URL Parameters:
- im=FitAndFill,width=X,height=Y - Resize image
- im=Crop,width=X,height=Y - Crop to size
- im=FaceCrop,width=X,height=Y - Focus on face

Lazy Loading:
- data-src attribute for lazy-loaded images
- placeholder images during load

================================================================================
SECTION 5: VIDEO CONTENT
================================================================================

Video Sources:
- YouTube embeds
- Firstpost video player (custom)
- Video sections: /video-listing/, /shorts/

Video Thumbnails:
- Extractable from article listings
- Usually in video player containers
- Shorts section has special format

SCRAPING LIMITATION:
- Actual video streams are protected
- Only thumbnails and metadata available
- Playback requires JavaScript

================================================================================
SECTION 6: RSS FEEDS
================================================================================

Not explicitly found in initial analysis. May need to check:
- /feed/
- /rss/
- /xml/

================================================================================
SECTION 7: SCRAPING RECOMMENDATIONS
================================================================================

DIFFICULTY: MEDIUM-HIGH

STRATEGY:
1. Start with section pages for listing
2. Parse article links from listings
3. Fetch individual articles for content
4. Use AMP version for cleaner HTML when available

CODE TEMPLATE:
```python
import requests
from bs4 import BeautifulSoup

class FirstpostScraper:
    BASE_URL = 'https://www.firstpost.com'
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    def get_home_news(self):
        url = f'{self.BASE_URL}'
        resp = requests.get(url, headers=self.HEADERS)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        articles = []
        # Find article links - adjust selectors based on current HTML
        for article in soup.select('article, .article-card, a[href*="/news/"]'):
            title = article.get_text(strip=True)
            link = article.find('a')
            href = link.get('href') if link else ''
            
            if title and href and '/article' in href:
                articles.append({
                    'title': title[:100],
                    'link': href if href.startswith('http') else f'{self.BASE_URL}{href}'
                })
        
        return articles[:30]
    
    def get_article(self, url):
        # Try AMP version first for cleaner content
        amp_url = url.rstrip('/') + '/amp/'
        
        resp = requests.get(amp_url, headers=self.HEADERS)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        title = soup.find('h1')
        title = title.get_text(strip=True) if title else ''
        
        # Extract content from article body
        content = ''
        article_body = soup.find('article') or soup.find('div', class_='article_content')
        if article_body:
            paragraphs = article_body.find_all('p')
            content = ' '.join(p.get_text(strip=True) for p in paragraphs)
        
        # Extract image
        img = soup.find('meta', property='og:image')
        image = img['content'] if img else ''
        
        return {
            'title': title,
            'content': content,
            'image': image,
            'link': url
        }
```

POTENTIAL ISSUES:
- JavaScript-rendered content may be missing
- Class names may change (are hashed)
- Rate limiting may apply
- Some content may require subscription

================================================================================
SECTION 8: CONCLUSION
================================================================================

Beautiful Soup CAN extract:
- Article titles and summaries
- Author information
- Publication dates
- Main article content (if server-rendered)
- Images (URLs)
- Section/category information
- Metadata

Beautiful Soup CANNOT extract:
- Content loaded via JavaScript after page load
- Video streams
- Real-time updates
- Personalized content
- Interactive features

OVERALL VIABILITY: MEDIUM
- Basic scraping is feasible
- Use AMP version when available
- Consider API alternatives if available
"""

if __name__ == "__main__":
    print(__doc__)