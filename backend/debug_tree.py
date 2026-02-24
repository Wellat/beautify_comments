import json
from scraper import get_jisilu_data, build_comment_tree, extract_comment_data
from bs4 import BeautifulSoup
import os
import hashlib

def debug_comments():
    url = "https://www.jisilu.cn/question/517247"
    url_hash = hashlib.md5(url.encode()).hexdigest()
    cache_file = f"cache_{url_hash}.html"
    
    if not os.path.exists(cache_file):
        print("Cache file not found. Please run the main app first to fetch data.")
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
    # gd227228: "借贵贴问一下..."
    # gaigai777: "rtgs？ 百度一下" (Reply to gd227228)
    
    target_author = "gd227228"
    reply_author = "gaigai777"
    
    found_target = None
    found_reply = None
    
    for c in comments_raw:
        if c['author'] == target_author:
            # Check content
            if "借贵贴问一下" in c['content_text']:
                found_target = c
                print(f"Found Target Comment: {c['id']} by {c['author']}")
                print(f"Content: {c['content_text'][:50]}...")
        
        if c['author'] == reply_author:
            if "rtgs" in c['content_text'].lower():
                found_reply = c
                print(f"Found Reply Comment: {c['id']} by {c['author']}")
                print(f"Content: {c['content_text'][:50]}...")
                print(f"Reply To User: {c['reply_to_user']}")
                print(f"Quoted Text: {c['quoted_text']}")

    print("-" * 30)
    print("Building Tree...")
    tree = build_comment_tree(comments_raw)
    
    # Check if the reply is nested correctly
    # We need to find the target comment in the tree (it might be nested itself or top level)
    # But for simplicity, let's just search the whole tree structure
    
    def find_in_tree(nodes, target_id):
        for node in nodes:
            if node['id'] == target_id:
                return node
            res = find_in_tree(node['children'], target_id)
            if res:
                return res
        return None

    if found_target:
        target_node = find_in_tree(tree, found_target['id'])
        if target_node:
            print(f"Target Node Children Count: {len(target_node['children'])}")
            for child in target_node['children']:
                print(f" - Child: {child['id']} by {child['author']} content: {child['content_text'][:30]}")
                if found_reply and child['id'] == found_reply['id']:
                    print("SUCCESS: Reply is correctly nested under target!")
                    return
            
            if found_reply:
                print("FAILURE: Reply NOT found under target.")
                # Check where it ended up
                reply_node = find_in_tree(tree, found_reply['id'])
                if reply_node:
                    print(f"Reply found elsewhere in tree. Is it top level? {reply_node in tree}")
        else:
            print("Target node not found in tree??")

if __name__ == "__main__":
    debug_comments()
