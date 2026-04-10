from abc import ABC, abstractmethod


class BaseScraper(ABC):
    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    @abstractmethod
    def get_home_news(self, include_images=True):
        pass

    @abstractmethod
    def get_section_news(self, section, include_images=True):
        pass

    @abstractmethod
    def get_article(self, url):
        pass

    @abstractmethod
    def get_related_news(self, url):
        pass

    @abstractmethod
    def get_sections(self):
        pass

    def get_article_image(self, url):
        return ''


SCRAPERS = {}


def register_scraper(name, scraper_class):
    SCRAPERS[name] = scraper_class


def get_scraper(name):
    return SCRAPERS.get(name)


def get_all_sections():
    sections = {}
    for name, scraper_class in SCRAPERS.items():
        try:
            scraper = scraper_class()
            sections[name] = scraper.get_sections()
        except:
            pass
    return sections