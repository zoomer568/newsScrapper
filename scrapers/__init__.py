from abc import ABC, abstractmethod
import os
import glob
import importlib.util
import sys


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

    def get_capabilities(self):
        return {
            'has_images': True,
            'has_sections': True,
            'has_article_content': True,
            'has_related_news': True
        }


SCRAPERS = {}


def register_scraper(name, scraper_class):
    """Register a scraper class. Called by each scraper module."""
    SCRAPERS[name] = scraper_class


def get_scraper(name):
    return SCRAPERS.get(name)


def get_all_sections():
    sections = {}
    for name, scraper_class in SCRAPERS.items():
        try:
            scraper = scraper_class() if not callable(scraper_class) else scraper_class()
            sections[name] = scraper.get_sections()
        except:
            pass
    return sections


# Auto-discover and load all scraper modules from this directory
def _discover_scrapers():
    """Discover and load all scraper modules in this directory"""
    scrapers_dir = os.path.dirname(__file__)
    
    for filepath in glob.glob(os.path.join(scrapers_dir, '*.py')):
        filename = os.path.basename(filepath)
        
        # Skip non-scraper files
        if filename.startswith('_') or filename in ('__init__.py',):
            continue
        
        module_name = f'scrapers.{filename[:-3]}'
        
        try:
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
        except Exception as e:
            print(f"Warning: Failed to load scraper {filename}: {e}")
            continue


# Auto-load scrapers when this module is imported
_discover_scrapers()