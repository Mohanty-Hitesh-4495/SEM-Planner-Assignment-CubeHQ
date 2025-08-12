# modules/scraper.py
from playwright.sync_api import sync_playwright
from urllib.parse import urljoin, urlparse

def scrape(url, timeout=30000, max_links=3):
    """
    Scrape main page for meta tags, headings, and crawl a few internal links.
    Returns a dict with all extracted text.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=timeout, wait_until="domcontentloaded")

        # Extract meta tags
        meta = {
            'title': page.title(),
            'description': page.locator('meta[name="description"]').get_attribute('content'),
            'keywords': page.locator('meta[name="keywords"]').get_attribute('content'),
        }

        # Extract headings
        headings = []
        for tag in ['h1', 'h2', 'h3']:
            headings += page.locator(tag).all_inner_texts()

        # Extract main body text
        body_text = page.inner_text('body')

        # Find a few internal links (product/category pages)
        links = page.locator('a').all()
        internal_links = []
        base = urlparse(url).netloc
        for a in links:
            href = a.get_attribute('href')
            if href:
                abs_url = urljoin(url, href)
                if urlparse(abs_url).netloc == base and abs_url != url:
                    internal_links.append(abs_url)
            if len(internal_links) >= max_links:
                break

        # Crawl a few internal links for more text
        extra_pages = {}
        for link in internal_links:
            try:
                page.goto(link, timeout=timeout, wait_until="domcontentloaded")
                extra_pages[link] = {
                    'title': page.title(),
                    'headings': sum([page.locator(tag).all_inner_texts() for tag in ['h1','h2','h3']], []),
                    'body_text': page.inner_text('body'),
                }
            except Exception:
                continue

        browser.close()
        return {
            'meta': meta,
            'headings': headings,
            'body_text': body_text,
            'internal_links': internal_links,
            'extra_pages': extra_pages
        }
