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
        # Since debug_tree.py imports get_jisilu_data from scraper, 
        # calling it will trigger the fetch and save to cache.
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
    # suliang: "这么说，券商app显示的不准确?"
    # xusm0731: "券商app显示大体相似..." (Reply to suliang)
    # 酱油面: "券商APP历来都显示不准确..." (Reply to suliang)
    
    target_authors = ["suliang", "xusm0731", "酱油面"]
    found_comments = {}
    
    for c in comments_raw:
        if c['author'] in target_authors:
            found_comments[c['id']] = c
            print(f"Found Comment: {c['id']} by {c['author']} ({c['time']})")
            print(f"  Content: {c['content_text'][:50]}...")
            print(f"  Reply To User: {c['reply_to_user']}")
            # print(f"  Quoted Text: {c['quoted_text']}")

    print("-" * 30)
    print("Building Tree...")
    tree = build_comment_tree(comments_raw)
    
    # Check the tree structure for suliang
    suliang_node = None
    
    def find_in_tree(nodes, author):
        for node in nodes:
            if node['author'] == author:
                return node
            res = find_in_tree(node['children'], author)
            if res:
                return res
        return None

    suliang_node = find_in_tree(tree, "suliang")
    
    if suliang_node:
        print(f"Found suliang node. Children count: {len(suliang_node['children'])}")
        for child in suliang_node['children']:
            print(f" - Child: {child['author']} ({child['id']})")
            if child['children']:
                print(f"   - Grandchild count: {len(child['children'])}")
                for grandchild in child['children']:
                     print(f"     - Grandchild: {grandchild['author']} ({grandchild['id']})")
    else:
        print("suliang node not found in tree.")

if __name__ == "__main__":
    debug_comments()
