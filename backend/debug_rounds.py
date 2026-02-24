import json
from scraper import get_jisilu_data, build_comment_tree, extract_comment_data
from bs4 import BeautifulSoup
import os
import hashlib
from datetime import datetime

def debug_comments():
    url = "https://www.jisilu.cn/question/518718"
    url_hash = hashlib.md5(url.encode()).hexdigest()
    cache_file = f"cache_{url_hash}.html"
    
    # We need to fetch the data first to populate the cache
    if not os.path.exists(cache_file):
        print(f"Fetching data for {url} to create cache...")
        try:
            get_jisilu_data(url)
        except Exception as e:
            print(f"Error fetching data: {e}")
            return

    print(f"Loading from cache: {cache_file}")
    with open(cache_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
        
    soup = BeautifulSoup(html_content, 'lxml')
    comments_raw = []
    comment_list_div = soup.find('div', class_='aw-mod-body aw-dynamic-topic')
    
    if comment_list_div:
        items = comment_list_div.find_all('div', class_='aw-item')
        for item in items:
            if item.get('id', '').startswith('answer_list_'):
                c_data = extract_comment_data(item)
                if c_data:
                    comments_raw.append(c_data)
    
    print(f"Total comments extracted: {len(comments_raw)}")
    
    # Sort comments by timestamp ascending (Oldest first)
    comments_raw.sort(key=lambda x: x['timestamp'])
    
    # Find the specific comments mentioned by the user
    target_authors = ["听风听雨", "xusm0731"]
    found_comments = {}
    
    for c in comments_raw:
        if c['author'] in target_authors:
            found_comments[c['id']] = c
            print(f"Found Comment: {c['id']} by {c['author']} ({c['time']})")
            print(f"  Content: {c['content_text'][:50]}...")
            print(f"  Reply To User: {c['reply_to_user']}")
            if c.get('quoted_text'):
                print(f"  Quoted Text: {c['quoted_text'][:50]}...")

    print("-" * 30)
    print("Building Tree...")
    tree = build_comment_tree(comments_raw)
    
    # Traverse and print the tree structure for target authors
    def print_node(node, depth=0):
        indent = "  " * depth
        if node['author'] in target_authors:
            print(f"{indent}- {node['author']} ({node['id']}) [ReplyTo: {node.get('reply_to_user')}]")
            for child in node['children']:
                print_node(child, depth + 1)
        else:
            # If not target author, just traverse children
            for child in node['children']:
                print_node(child, depth + 1) # Don't increase depth if skipping node display? No, keep depth.

    # Actually, we should print all relevant nodes starting from root.
    for node in tree:
        print_node(node)

if __name__ == "__main__":
    debug_comments()
