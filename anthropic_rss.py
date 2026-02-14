import asyncio
from datetime import datetime, timezone
from feedgen.feed import FeedGenerator
from playwright.async_api import async_playwright
from dateutil import parser as date_parser

RAW_BASE = "https://raw.githubusercontent.com/taobojlen/anthropic-rss-feed/main"


def parse_date(date_text):
    """Parse date text and return a datetime object with timezone"""
    try:
        date_text = date_text.strip()
        parsed_date = date_parser.parse(date_text)
        if parsed_date.tzinfo is None:
            parsed_date = parsed_date.replace(tzinfo=timezone.utc)
        return parsed_date
    except Exception as e:
        print(f"Error parsing date '{date_text}': {e}")
        return datetime.now(timezone.utc)


async def fetch_news(page):
    """Scrape articles from anthropic.com/news"""
    await page.goto("https://www.anthropic.com/news")
    await page.wait_for_selector("[class*='PublicationList'][class*='listItem']")

    seen_urls = set()
    articles = []

    # Featured grid: main item
    featured_main = await page.query_selector("[class*='FeaturedGrid'][class*='content']")
    if featured_main:
        try:
            title_el = await featured_main.query_selector("h2")
            date_el = await featured_main.query_selector("time")
            href = await featured_main.get_attribute("href")
            if title_el and date_el and href:
                title = (await title_el.text_content()).strip()
                date_text = (await date_el.text_content()).strip()
                url = href if href.startswith("http") else f"https://www.anthropic.com{href}"
                seen_urls.add(url)
                articles.append({'title': title, 'url': url, 'date': parse_date(date_text)})
                print(f"[news] Found (featured): {title} - {date_text}")
        except Exception as e:
            print(f"[news] Error processing featured main item: {e}")

    # Featured grid: side items
    for item in await page.query_selector_all("[class*='FeaturedGrid'][class*='sideLink']"):
        try:
            title_el = await item.query_selector("[class*='title']")
            date_el = await item.query_selector("time")
            href = await item.get_attribute("href")
            if title_el and date_el and href:
                title = (await title_el.text_content()).strip()
                date_text = (await date_el.text_content()).strip()
                url = href if href.startswith("http") else f"https://www.anthropic.com{href}"
                if url not in seen_urls:
                    seen_urls.add(url)
                    articles.append({'title': title, 'url': url, 'date': parse_date(date_text)})
                    print(f"[news] Found (featured): {title} - {date_text}")
        except Exception as e:
            print(f"[news] Error processing featured side item: {e}")

    # Publication list
    for item in await page.query_selector_all("[class*='PublicationList'][class*='listItem']"):
        try:
            title_el = await item.query_selector("[class*='title']")
            date_el = await item.query_selector("time")
            href = await item.get_attribute("href")
            if title_el and date_el and href:
                title = (await title_el.text_content()).strip()
                date_text = (await date_el.text_content()).strip()
                url = href if href.startswith("http") else f"https://www.anthropic.com{href}"
                if url not in seen_urls:
                    seen_urls.add(url)
                    articles.append({'title': title, 'url': url, 'date': parse_date(date_text)})
                    print(f"[news] Found: {title} - {date_text}")
        except Exception as e:
            print(f"[news] Error processing list item: {e}")

    articles.sort(key=lambda x: x['date'], reverse=True)
    return articles


async def fetch_engineering(page):
    """Scrape articles from anthropic.com/engineering"""
    await page.goto("https://www.anthropic.com/engineering")
    await page.wait_for_selector("[class*='ArticleList'][class*='article']")

    seen_urls = set()
    articles = []

    for item in await page.query_selector_all("[class*='ArticleList'][class*='article']"):
        try:
            link = await item.query_selector("a[class*='cardLink']")
            if not link:
                continue
            href = await link.get_attribute("href")
            url = href if href.startswith("http") else f"https://www.anthropic.com{href}"
            if url in seen_urls:
                continue
            seen_urls.add(url)

            content = await item.query_selector("[class*='content']")
            if not content:
                continue

            # Featured items use h2, regular items use h3
            title_el = await content.query_selector("h2")
            if not title_el:
                title_el = await content.query_selector("h3")
            if not title_el:
                continue
            title = (await title_el.text_content()).strip()

            date_el = await content.query_selector("[class*='date']")
            if date_el:
                date_text = (await date_el.text_content()).strip()
                date = parse_date(date_text)
                print(f"[engineering] Found: {title} - {date_text}")
            else:
                # Featured item has no date displayed
                date = datetime.now(timezone.utc)
                print(f"[engineering] Found (featured, no date): {title}")

            articles.append({'title': title, 'url': url, 'date': date})
        except Exception as e:
            print(f"[engineering] Error processing article: {e}")

    articles.sort(key=lambda x: x['date'], reverse=True)
    return articles


def generate_rss(articles, title, description, page_url, feed_filename):
    feed = FeedGenerator()
    feed.title(title)
    feed.link(href=page_url, rel='alternate')
    feed.link(href=f"{RAW_BASE}/{feed_filename}", rel='self')
    feed.description(description)
    feed.language('en')

    for article in articles:
        entry = feed.add_entry()
        entry.title(article['title'])
        entry.link(href=article['url'])
        entry.pubDate(article['date'])
        entry.description(article['title'])
        entry.guid(article['url'], permalink=True)

    return feed.rss_str(pretty=True)


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        news_articles = await fetch_news(page)
        eng_articles = await fetch_engineering(page)

        await browser.close()

    news_rss = generate_rss(
        news_articles,
        title='Anthropic News',
        description='Latest news and announcements from Anthropic',
        page_url='https://www.anthropic.com/news',
        feed_filename='anthropic_news_rss.xml',
    )
    with open('anthropic_news_rss.xml', 'wb') as f:
        f.write(news_rss)
    print(f"News feed generated ({len(news_articles)} articles)")

    eng_rss = generate_rss(
        eng_articles,
        title='Anthropic Engineering Blog',
        description='Latest engineering posts from Anthropic',
        page_url='https://www.anthropic.com/engineering',
        feed_filename='anthropic_engineering_rss.xml',
    )
    with open('anthropic_engineering_rss.xml', 'wb') as f:
        f.write(eng_rss)
    print(f"Engineering feed generated ({len(eng_articles)} articles)")


if __name__ == "__main__":
    asyncio.run(main())
