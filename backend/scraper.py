import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional
import uuid
from datetime import datetime

def get_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()

def extract_comment_data(item_div) -> Dict:
    """Extract raw data from a single comment div."""
    try:
        # ID
        # id="answer_list_XXXXXX"
        raw_id = item_div.get('id', '')
        comment_id = raw_id.replace('answer_list_', '') if raw_id else str(uuid.uuid4())
        
        # Author
        author_tag = item_div.find('a', class_='aw-user-name')
        author = author_tag.get_text(strip=True) if author_tag else "Anonymous"
        
        # Avatar
        avatar_tag = item_div.find('a', class_='aw-user-img')
        avatar = avatar_tag.find('img')['src'] if avatar_tag and avatar_tag.find('img') else ""
        
        # Content (HTML)
        content_div = item_div.find('div', class_='markitup-box')
        content_text = content_div.get_text(strip=True) if content_div else ""
        
        quoted_text = None
        
        # Check for blockquote
        if content_div:
            blockquote = content_div.find('blockquote')
            if blockquote:
                quoted_text = blockquote.get_text(strip=True)
                # Remove blockquote from content HTML to avoid duplication in display
                blockquote.decompose()
        
        content_html = str(content_div) if content_div else ""
        
        # Time & Location
        meta_div = item_div.find('div', class_='aw-dynamic-topic-meta')
        time_loc_span = meta_div.find('span', class_='aw-text-color-999') if meta_div else None
        time_loc = time_loc_span.get_text(strip=True) if time_loc_span else ""
        # Split "2026-02-21 16:51 来自河北"
        parts = time_loc.split(' 来自')
        publish_time = parts[0]
        location = parts[1] if len(parts) > 1 else ""
        
        # Parse time for sorting
        try:
            # Remove potential "修改" suffix
            clean_time_str = publish_time.replace("修改", "").strip()
            timestamp = datetime.strptime(clean_time_str, "%Y-%m-%d %H:%M").timestamp()
        except ValueError:
            print(f"Failed to parse time: {publish_time}")
            timestamp = 0
        
        # Determine if it's a reply
        reply_to_user = None
        
        # Check for @username
        # Usually inside markitup-box -> a.aw-user-name
        if content_div:
            # We need to search in the original soup because we might have decomposed blockquote
            # But wait, blockquote was decomposed from content_div which is a Tag object.
            # So subsequent searches on content_div won't find it. That's fine.
            # But what if the @user was inside the blockquote? Usually not.
            # But wait, sometimes @user is the first thing.
            
            # Re-find content_div from item_div because we modified it?
            # No, we want to find @user in the CLEANED content (without quote).
            # Because if the quote contains @user, we don't want to reply to that user (that user is likely the original author).
            
            first_link = content_div.find('a', class_='aw-user-name')
            # Check if text starts with @
            # content_div.get_text() might have changed.
            current_text = content_div.get_text(strip=True)
            if first_link and current_text.startswith('@'):
                 reply_to_user = first_link.get_text(strip=True).replace('@', '')

        return {
            "id": comment_id,
            "author": author,
            "author_avatar": avatar,
            "content": content_html,
            "content_text": content_text, # For matching (this includes quote text because we extracted it before decompose)
            "time": publish_time,
            "timestamp": timestamp,
            "location": location,
            "reply_to_user": reply_to_user,
            "quoted_text": quoted_text,
            "children": []
        }
    except Exception as e:
        print(f"Error extracting comment: {e}")
        return None

def build_comment_tree(comments: List[Dict]) -> List[Dict]:
    """
    Convert flat list of comments to a tree based on reply logic.
    Heuristic:
    1. If quote exists -> find comment with matching content (substring).
    2. If @user exists -> find last comment by that user.
    3. Else -> Top level.
    """
    tree = []
    processed_comments = [] # List of dicts
    
    for comment in comments:
        parent_found = None
        
        # Priority 1: @User AND Quoted Text
        # Strongest signal: replying to a specific user and quoting specific content
        if comment.get('reply_to_user') and comment.get('quoted_text'):
            target_user = comment['reply_to_user']
            quote = comment['quoted_text'][:50]
            for prev in reversed(processed_comments):
                # Must match both author and content
                if prev['author'] == target_user and quote in prev['content_text']:
                    parent_found = prev
                    break
        
        # Priority 2: @User Only (if not found above)
        # Fallback: finding latest comment by that user
        if not parent_found and comment.get('reply_to_user'):
            target_user = comment['reply_to_user']
            for prev in reversed(processed_comments):
                if prev['author'] == target_user:
                    parent_found = prev
                    break
        
        # Priority 3: Quoted Text Only (if not found above)
        # Fallback: finding comment with matching content (e.g. no @user used)
        if not parent_found and comment.get('quoted_text'):
            quote = comment['quoted_text'][:50]
            for prev in reversed(processed_comments):
                if quote in prev['content_text']:
                    parent_found = prev
                    break
        
        if parent_found:
            parent_found['children'].append(comment)
        else:
            tree.append(comment)
            
        processed_comments.append(comment)
        
    return tree

import os
import hashlib

def get_jisilu_data(url: str, force_update: bool = False):
    # Cache key based on URL
    url_hash = hashlib.md5(url.encode()).hexdigest()
    
    # Ensure cache directory exists
    cache_dir = "cache"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
        
    cache_file = os.path.join(cache_dir, f"cache_{url_hash}.html")
    
    html_content = ""
    if not force_update and os.path.exists(cache_file):
        print(f"Loading from cache: {cache_file}")
        with open(cache_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
    else:
        print(f"Fetching from URL: {url}")
        response = requests.get(url, headers=get_headers(), timeout=30)
        response.raise_for_status()
        html_content = response.text
        # Save to cache
        with open(cache_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
    soup = BeautifulSoup(html_content, 'lxml')
    
    # 1. Article Info
    title_tag = soup.find('div', class_='aw-mod-head').find('h1') if soup.find('div', class_='aw-mod-head') else None
    title = title_tag.get_text(strip=True) if title_tag else "Unknown Title"
    
    # Content
    content_div = soup.find('div', class_='aw-question-detail-txt')
    content = str(content_div) if content_div else ""
    
    # Author (Try to find from meta)
    # The meta structure is messy, let's just use "Unknown" or parse if needed.
    # Actually, the main post author is not easily available in a specific class for the question.
    # But usually the first item in the stream is the question itself.
    # Let's assume Unknown for now or "楼主".
    author = "楼主" 
    
    # Publish Time
    meta_div = soup.find('div', class_='aw-question-detail-meta')
    publish_time = ""
    if meta_div:
        text = meta_div.get_text()
        # Extract date like 2026-01-08
        match = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}', text)
        if match:
            publish_time = match.group(0)

    # 2. Comments
    comments_raw = []
    
    # Support Pagination (MVP: First Page Only)
    # TODO: Loop through pages if needed.
    
    comment_list_div = soup.find('div', class_='aw-mod-body aw-dynamic-topic')
    if comment_list_div:
        items = comment_list_div.find_all('div', class_='aw-item')
        for item in items:
            # Check if it's a real comment (has id starting with answer_list)
            if item.get('id', '').startswith('answer_list_'):
                c_data = extract_comment_data(item)
                if c_data:
                    comments_raw.append(c_data)
    
    # Sort comments by timestamp ascending (Oldest first)
    comments_raw.sort(key=lambda x: x['timestamp'])

    # 3. Build Tree
    comments_tree = build_comment_tree(comments_raw)
    
    return {
        "title": title,
        "content": content,
        "author": author,
        "publish_time": publish_time,
        "comments": comments_tree
    }
