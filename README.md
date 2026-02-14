# Anthropic RSS Feed Generator

This script generates RSS feeds for Anthropic's website using Playwright to scrape the client-side rendered content.

**Feeds:**
- **News & Announcements:** `https://raw.githubusercontent.com/taobojlen/anthropic-rss-feed/main/anthropic_news_rss.xml`
- **Engineering Blog:** `https://raw.githubusercontent.com/taobojlen/anthropic-rss-feed/main/anthropic_engineering_rss.xml`

## Features

- **Client-side rendering support**: Uses Playwright to handle JavaScript-rendered content
- **Proper date parsing**: Extracts and formats publication dates with timezone support
- **RSS compliance**: Includes GUID elements and atom:link for better interoperability
- **Reverse chronological order**: Articles sorted newest first
- **Deduplication**: Featured and list items are deduplicated by URL
- **Error handling**: Robust error handling for missing elements
- **Automated updates**: GitHub Action runs every 6 hours to keep the feeds current

## Setup

### Local Usage

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
playwright install chromium
```

3. Run the main script:
```bash
python anthropic_rss.py
```

### GitHub Action Setup

1. Fork this repository to your GitHub account

2. Create a Personal Access Token (PAT):
   - Go to GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens
   - Click "Generate new token"
   - Name it "GitHub Actions RSS Updater"
   - Set repository access to your forked repository
   - Under "Repository permissions", grant:
     - Contents: Read and write
   - Click "Generate token" and copy the token

3. Add the token to your repository secrets:
   - Go to your repository → Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `ANTHROPIC_RSS_GH_TOKEN`
   - Value: Paste the token you copied
   - Click "Add secret"

4. The GitHub Action will automatically:
   - Run every 6 hours (and on push to main)
   - Generate both RSS feeds
   - Commit and push updates to the repository

## Manual Triggering

You can manually trigger the RSS generation by:
- Going to the "Actions" tab in your GitHub repository
- Selecting "Generate Anthropic News RSS Feed"
- Clicking "Run workflow"

## Output

The generated RSS feed includes:
- Post titles
- Post URLs
- Publication dates (properly formatted)
- GUID elements for unique identification
- Proper RSS metadata and atom:link elements
