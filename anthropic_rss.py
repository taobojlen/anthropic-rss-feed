import asyncio
from datetime import datetime, timezone
from feedgen.feed import FeedGenerator
from playwright.async_api import async_playwright
import os
import re
from dateutil import parser as date_parser

class AnthropicRSSGenerator:
    def __init__(self):
        self.base_url = "https://www.anthropic.com/news"

    def parse_date(self, date_text):
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

    async def fetch_posts(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(self.base_url)

            # Wait for the publication list to load
            await page.wait_for_selector("[class*='PublicationList'][class*='listItem']")

            seen_urls = set()
            articles_data = []

            # Scrape featured grid items (main + side)
            featured_main = await page.query_selector("[class*='FeaturedGrid'][class*='content']")
            if featured_main:
                try:
                    title_el = await featured_main.query_selector("h2")
                    date_el = await featured_main.query_selector("time")
                    href = await featured_main.get_attribute("href")
                    if title_el and date_el and href:
                        title = await title_el.text_content()
                        date_text = await date_el.text_content()
                        url = href if href.startswith("http") else f"https://www.anthropic.com{href}"
                        seen_urls.add(url)
                        articles_data.append({
                            'title': title.strip(),
                            'url': url,
                            'date': self.parse_date(date_text),
                            'date_text': date_text.strip()
                        })
                        print(f"Found (featured): {title.strip()} - {date_text.strip()}")
                except Exception as e:
                    print(f"Error processing featured main item: {e}")

            featured_sides = await page.query_selector_all("[class*='FeaturedGrid'][class*='sideLink']")
            for item in featured_sides:
                try:
                    title_el = await item.query_selector("[class*='title']")
                    date_el = await item.query_selector("time")
                    href = await item.get_attribute("href")
                    if title_el and date_el and href:
                        title = await title_el.text_content()
                        date_text = await date_el.text_content()
                        url = href if href.startswith("http") else f"https://www.anthropic.com{href}"
                        if url not in seen_urls:
                            seen_urls.add(url)
                            articles_data.append({
                                'title': title.strip(),
                                'url': url,
                                'date': self.parse_date(date_text),
                                'date_text': date_text.strip()
                            })
                            print(f"Found (featured): {title.strip()} - {date_text.strip()}")
                except Exception as e:
                    print(f"Error processing featured side item: {e}")

            # Scrape publication list items
            list_items = await page.query_selector_all("[class*='PublicationList'][class*='listItem']")
            for item in list_items:
                try:
                    title_el = await item.query_selector("[class*='title']")
                    date_el = await item.query_selector("time")
                    href = await item.get_attribute("href")
                    if title_el and date_el and href:
                        title = await title_el.text_content()
                        date_text = await date_el.text_content()
                        url = href if href.startswith("http") else f"https://www.anthropic.com{href}"
                        if url not in seen_urls:
                            seen_urls.add(url)
                            articles_data.append({
                                'title': title.strip(),
                                'url': url,
                                'date': self.parse_date(date_text),
                                'date_text': date_text.strip()
                            })
                            print(f"Found: {title.strip()} - {date_text.strip()}")
                except Exception as e:
                    print(f"Error processing list item: {e}")

            # Sort articles by date (newest first)
            articles_data.sort(key=lambda x: x['date'], reverse=True)

            await browser.close()
            return articles_data

    def create_feed(self):
        """Create a fresh feed instance"""
        feed = FeedGenerator()
        feed.title('Anthropic News')
        feed.link(href=self.base_url, rel='alternate')
        feed.link(href='https://raw.githubusercontent.com/taobojlen/anthropic-rss-feed/main/anthropic_news_rss.xml', rel='self')
        feed.description('Latest news and announcements from Anthropic')
        feed.language('en')
        return feed

    def generate_rss(self, articles_data):
        feed = self.create_feed()

        for article_data in articles_data:
            entry = feed.add_entry()
            entry.title(article_data['title'])
            entry.link(href=article_data['url'])
            entry.pubDate(article_data['date'])
            entry.description(article_data['title'])
            entry.guid(article_data['url'], permalink=True)

        rss_content = feed.rss_str(pretty=True)
        return rss_content

async def main():
    generator = AnthropicRSSGenerator()
    articles_data = await generator.fetch_posts()
    rss_content = generator.generate_rss(articles_data)

    with open('anthropic_news_rss.xml', 'wb') as f:
        f.write(rss_content)

    print("RSS feed generated successfully!")

if __name__ == "__main__":
    asyncio.run(main())
