import os
import sys
import json
import argparse
from scraper import get_jisilu_data

# Define paths relative to this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "frontend", "public", "data")

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def update_article(article_id):
    url = f"https://www.jisilu.cn/question/{article_id}"
    print(f"Fetching data for article {article_id}...")
    
    try:
        data = get_jisilu_data(url, force_update=True)
        data['id'] = article_id
        
        # Save article JSON
        ensure_dir(DATA_DIR)
        file_path = os.path.join(DATA_DIR, f"{article_id}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Saved article data to {file_path}")
        
        return True
    except Exception as e:
        print(f"Error fetching article {article_id}: {e}")
        return False

def update_index():
    print("Updating index...")
    ensure_dir(DATA_DIR)
    
    files = [f for f in os.listdir(DATA_DIR) if f.endswith('.json') and f != 'index.json']
    history = []
    
    for filename in files:
        file_path = os.path.join(DATA_DIR, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'id' in data and 'title' in data:
                    history.append({
                        'id': data['id'],
                        'title': data['title'],
                        # Use file modification time or publish time if needed, 
                        # but file mtime is good for "last updated"
                        'updated_at': os.path.getmtime(file_path)
                    })
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            
    # Sort by updated_at desc
    history.sort(key=lambda x: x.get('updated_at', 0), reverse=True)
    
    # Clean up fields for index
    index_data = [{'id': item['id'], 'title': item['title']} for item in history]
    
    index_path = os.path.join(DATA_DIR, "index.json")
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    print(f"Updated index with {len(index_data)} items at {index_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Update article data.')
    parser.add_argument('article_id', help='The Article ID to update')
    args = parser.parse_args()
    
    if args.article_id:
        if update_article(args.article_id):
            update_index()
        else:
            sys.exit(1)
    else:
        print("Please provide an article ID")
        sys.exit(1)
