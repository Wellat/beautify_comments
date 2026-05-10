import requests
from bs4 import BeautifulSoup
import json
import os
import time
import re
import argparse
import sys
from urllib.parse import urljoin

class JisiluUserScraper:
    BASE_URL = "https://www.jisilu.cn"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }

    def __init__(self, username, output_dir="backend/knowledge"):
        self.username = username
        self.output_dir = os.path.join(output_dir, username)
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        self.user_id = None
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def get_user_id(self):
        """
        Fetch the user profile page to extract the numeric user ID.
        """
        url = f"{self.BASE_URL}/people/{self.username}"
        print(f"Fetching profile for {self.username} at {url}...")
        try:
            # First request without XMLHttpRequest to get full page
            headers = self.HEADERS.copy()
            del headers["X-Requested-With"]
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            
            # Look for var PEOPLE_USER_ID = '12345';
            match = re.search(r"var PEOPLE_USER_ID = '(\d+)';", response.text)
            if match:
                self.user_id = match.group(1)
                print(f"Found User ID: {self.user_id}")
                return self.user_id
            else:
                print("Could not find User ID in profile page.")
                return None
        except Exception as e:
            print(f"Error fetching profile: {e}")
            return None

    def get_user_actions(self, action_type):
        """
        Fetch user actions (topics or replies).
        action_type: 101 (Topics), 201 (Replies)
        Returns a set of article IDs.
        """
        article_ids = set()
        page = 0
        while True:
            # Jisilu pages might start at 0 or 1, let's try 0 then increment
            # Actually, looking at the pattern, it seems to be just appending items.
            # But usually it's `__page-{page}`.
            # Let's try fetching until empty response.
            
            url = f"{self.BASE_URL}/people/ajax/user_actions/uid-{self.user_id}__actions-{action_type}__page-{page}"
            print(f"Fetching actions (type {action_type}) page {page}...")
            
            try:
                response = self.session.get(url)
                if not response.text.strip():
                    print("Empty response, stopping.")
                    break
                
                soup = BeautifulSoup(response.text, 'lxml')
                items = soup.find_all('div', class_='aw-item')
                
                if not items:
                    print("No more items found.")
                    break
                
                for item in items:
                    # Extract link to question
                    # Usually in h4 > a
                    h4 = item.find('h4')
                    if h4:
                        link = h4.find('a')
                        if link and link.get('href'):
                            href = link.get('href')
                            # href structure: https://www.jisilu.cn/question/{id}
                            match = re.search(r'/question/(\d+)', href)
                            if match:
                                article_ids.add(match.group(1))
                
                page += 1
                time.sleep(0.5) # Be polite
                
                # Safety break
                if page > 50: 
                    print("Reached page limit (50), stopping.")
                    break
            except Exception as e:
                print(f"Error fetching actions: {e}")
                break
                
        return article_ids

    def clean_html(self, html_content):
        """
        Remove style tags, images, etc. Keep text.
        """
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Remove script and style elements
        for script in soup(["script", "style", "img", "iframe", "video"]):
            script.decompose()
            
        # Get text
        text = soup.get_text(separator="\n", strip=True)
        return text

    def clean_html_keep_structure(self, element):
        """
        Remove unwanted tags but keep basic structure (p, br) converted to text/newlines.
        Actually, prompt says "Remove style tags... keep text".
        Let's just use get_text() for simplicity as MVP.
        """
        if not element:
            return ""
        # Remove images
        for img in element.find_all('img'):
            img.decompose()
        return element.get_text(separator="\n", strip=True)

    def scrape_article(self, article_id):
        """
        Scrape a specific article and filter for user content.
        """
        url = f"{self.BASE_URL}/question/{article_id}"
        print(f"Scraping article {article_id}...")
        
        article_data = {
            "id": article_id,
            "url": url,
            "title": "",
            "author": "", # Author of the topic
            "publish_time": "",
            "content": "", # Main content if user is author
            "comments": []
        }
        
        try:
            headers = self.HEADERS.copy()
            del headers["X-Requested-With"]
            response = self.session.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Title
            title_tag = soup.find('div', class_='aw-mod-head').find('h1') if soup.find('div', class_='aw-mod-head') else None
            article_data['title'] = title_tag.get_text(strip=True) if title_tag else "Unknown Title"
            
            # Check author of main topic
            # The author info is usually in the sidebar or meta.
            # In Jisilu question page:
            # <div class="aw-side-bar"> ... <a class="aw-user-name" href="...">User</a>
            # OR in the main content area meta.
            # Let's look for `aw-question-detail-meta` or similar.
            # Actually, the first item in the stream is often the question itself.
            # But the author link is often: <a class="aw-user-name" ...>Name</a>
            
            # Find the main content div
            content_div = soup.find('div', class_='aw-question-detail-txt')
            
            # Find the author of the question
            # It's tricky on some pages. Usually:
            # <div class="aw-mod-head"> ... <a class="aw-user-name">Author</a>
            # Let's try to find the first user link in the content area or side bar.
            # Actually, let's look at `aw-side-bar` -> `aw-user-center-signature` -> `aw-user-name`
            # Or `aw-question-detail` area.
            
            # Let's assume we can find the author name in the side bar "发起人" section usually.
            # But for now, let's look for `aw-user-name` inside `aw-side-bar` if it exists.
            side_bar = soup.find('div', class_='aw-side-bar')
            topic_author = ""
            if side_bar:
                author_link = side_bar.find('a', class_='aw-user-name')
                if author_link:
                    topic_author = author_link.get_text(strip=True)
            
            article_data['author'] = topic_author
            
            # If target user is the author, save content
            if topic_author == self.username and content_div:
                article_data['content'] = self.clean_html_keep_structure(content_div)
                
                # Get publish time
                meta_div = soup.find('div', class_='aw-question-detail-meta')
                if meta_div:
                    # Extract text
                    raw_time = meta_div.get_text(strip=True)
                    # Try to extract date like 2026-01-08 07:46
                    match = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}', raw_time)
                    if match:
                        article_data['publish_time'] = match.group(0)
                    else:
                        article_data['publish_time'] = raw_time

            # Process comments (pagination needed?)
            # Pagination is usually at the bottom: <div class="pagination">
            # If pagination exists, we need to loop.
            
            # Function to parse comments from a soup
            def parse_comments(current_soup):
                comments_list = []
                comment_items = current_soup.find_all('div', class_='aw-item')
                for item in comment_items:
                    # Check if it's a comment
                    if item.get('id', '').startswith('answer_list_'):
                        # Check author
                        author_tag = item.find('a', class_='aw-user-name')
                        if author_tag and author_tag.get_text(strip=True) == self.username:
                            # Extract content
                            body = item.find('div', class_='markitup-box')
                            
                            # Handle quote
                            quote_text = ""
                            quote = body.find('blockquote') if body else None
                            if quote:
                                quote_text = quote.get_text(strip=True)
                                quote.decompose() # Remove quote from body to get only user's text
                            
                            content_text = self.clean_html_keep_structure(body)
                            
                            # Re-assemble if quote exists (as per requirement: "含回复别人的引用")
                            full_text = ""
                            if quote_text:
                                full_text += f"> {quote_text}\n\n"
                            full_text += content_text
                            
                            # Time
                            meta = item.find('div', class_='aw-dynamic-topic-meta') or item.find('div', class_='meta')
                            time_str = ""
                            if meta:
                                raw_time = meta.get_text(strip=True)
                                # Clean up unwanted action text
                                raw_time = re.sub(r'(引用|回复|编辑|赞同).*$', '', raw_time).strip()
                                time_str = raw_time
                                
                            comments_list.append({
                                "id": item.get('id'),
                                "content": full_text,
                                "time": time_str
                            })
                return comments_list

            # Get comments from page 1
            article_data['comments'].extend(parse_comments(soup))
            
            # Check pagination
            pagination = soup.find('div', class_='pagination')
            if pagination:
                # Find max page
                links = pagination.find_all('a')
                max_page = 1
                for link in links:
                    try:
                        p = int(link.get_text())
                        if p > max_page:
                            max_page = p
                    except:
                        pass
                
                # Loop through other pages
                for p in range(2, max_page + 1):
                    print(f"  Scraping page {p}/{max_page}...")
                    page_url = f"{url}?page={p}"
                    # Usually url structure is /question/id?page=p OR /question/id?sort_key=add_time&sort=ASC&page=p
                    # Let's try appending parameter
                    try:
                        page_resp = self.session.get(page_url, headers=headers)
                        page_soup = BeautifulSoup(page_resp.text, 'lxml')
                        article_data['comments'].extend(parse_comments(page_soup))
                        time.sleep(0.5)
                    except Exception as e:
                        print(f"Error scraping page {p}: {e}")

        except Exception as e:
            print(f"Error scraping article {article_id}: {e}")
            
        # Save if there is content (either main post or comments)
        if article_data['content'] or article_data['comments']:
            filename = os.path.join(self.output_dir, f"{article_id}.json")
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(article_data, f, ensure_ascii=False, indent=2)
            print(f"Saved to {filename}")
        else:
            print(f"No content found for user {self.username} in article {article_id}, skipping save.")

    def run(self):
        if not self.get_user_id():
            return
        
        print("Fetching topics (Articles)...")
        # Only fetch topics (101) as per user request ("主题" tab)
        topic_ids = self.get_user_actions(101) 
        print(f"Found {len(topic_ids)} topics.")
        
        # print("Fetching replies...")
        # reply_ids = self.get_user_actions(201) # Replies
        # print(f"Found {len(reply_ids)} replies (articles).")
        
        # all_ids = topic_ids.union(reply_ids)
        all_ids = topic_ids
        print(f"Total unique articles to scrape: {len(all_ids)}")
        
        for idx, aid in enumerate(all_ids):
            print(f"Processing {idx+1}/{len(all_ids)}: Article {aid}")
            self.scrape_article(aid)
            time.sleep(1) # Delay between articles

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scrape Jisilu user content.')
    parser.add_argument('username', help='Username to scrape (e.g. gaigai777)')
    args = parser.parse_args()
    
    scraper = JisiluUserScraper(args.username)
    scraper.run()
