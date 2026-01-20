# scripts/sense_uci_majors.py
"""
Sense UCI undergraduate degrees page data

Usage: python scripts/sense_uci_majors.py
"""

import json
import re
from pathlib import Path
from collections import Counter
from urllib.parse import urljoin

INPUT_DIR = Path('output')


def load_latest_action():
    """Load latest action result."""
    files = sorted(INPUT_DIR.glob('action_*/task1_action.json'), reverse=True)
    if not files:
        raise FileNotFoundError("No action result found")
    return json.loads(files[0].read_text(encoding='utf-8'))


def extract_links_from_markdown(markdown):
    """Extract links from markdown content."""
    links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', markdown)
    return [{'title': t, 'url': u} for t, u in links]


def extract_links_from_html(html):
    """Extract links from HTML content."""
    link_pattern = r'<a [^>]*href="([^"]+)"[^>]*>([^<]*)</a>'
    links = re.findall(link_pattern, html, re.IGNORECASE)
    return [{'url': u, 'title': t} for u, t in links]


def sense_major_links():
    """Sense major links from UCI undergraduate degrees page."""
    data = load_latest_action()

    markdown = data.get('markdown', '')
    cleaned_html = data.get('cleaned_html', '')
    page_info = data.get('page_info', {})

    print("=" * 60)
    print("Sense Report: UCI Undergraduate Degrees Page")
    print("=" * 60)

    # Extract from markdown
    print("\n### From Markdown:")
    md_links = extract_links_from_markdown(markdown)
    print(f"Total links: {len(md_links)}")

    # Filter major-related links
    major_keywords = ['major', 'degree', 'b.a.', 'b.s.', 'minor']
    md_majors = [l for l in md_links
                 if any(kw in l['url'].lower() or kw in l['title'].lower()
                        for kw in major_keywords)]

    print(f"Major-related links: {len(md_majors)}")
    if md_majors:
        print("\nSample major links:")
        for link in md_majors[:10]:
            print(f"  - {link['title']}")
            print(f"    URL: {link['url']}")

    # Extract from HTML
    print("\n### From Cleaned HTML:")
    html_links = extract_links_from_html(cleaned_html)
    print(f"Total links: {len(html_links)}")

    base_url = 'https://catalogue.uci.edu/'

    # Filter relative URLs (starting with /)
    relative_links = [l for l in html_links if l['url'].startswith('/') and l['url'].count('/') > 1]

    print(f"Relative links (potential majors): {len(relative_links)}")

    # Convert relative URLs to absolute
    for link in relative_links:
        if link['url'].startswith('/'):
            link['absolute_url'] = urljoin(base_url, link['url'])
        else:
            link['absolute_url'] = link['url']

    # Find all unique major links (ends with / and has multi-level path)
    print("\n### Major Page Detection:")
    all_majors = {}

    for link in relative_links:
        url = link['url']
        # Pattern: /school/department/major/ or /school/major/
        # URLs ending with / and having at least 2 path segments
        if url.endswith('/') and url.count('/') >= 3:
            absolute_url = link['absolute_url']
            title = link['title'].strip()
            all_majors[absolute_url] = title

    print(f"Total unique majors found: {len(all_majors)}")
    print("\nSample majors:")
    for url, title in sorted(all_majors.items())[:20]:
        print(f"  - {title}")
        print(f"    {url}")

    # Check for accordion/toggle content
    print("\n### Interactive Elements (from page_info):")
    buttons = page_info.get('buttons', [])
    print(f"Buttons found: {len(buttons)}")

    if buttons:
        print("\nSample buttons:")
        for btn in buttons[:5]:
            text = btn.get('text', '')[:50]
            print(f"  - {text}")

    # Summary
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    print(f"Markdown links: {len(md_links)}")
    print(f"HTML links: {len(html_links)}")
    print(f"Relative links: {len(relative_links)}")
    print(f"Unique majors found: {len(all_majors)}")

    # Save results for further analysis
    result = {
        'total_markdown_links': len(md_links),
        'total_html_links': len(html_links),
        'relative_links': len(relative_links),
        'unique_majors': len(all_majors),
        'major_links': [{'title': t, 'url': u} for u, t in sorted(all_majors.items())]
    }

    output_file = INPUT_DIR / 'sense_result.json'
    output_file.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"\nResults saved to: {output_file}")

    return result


if __name__ == '__main__':
    sense_major_links()
