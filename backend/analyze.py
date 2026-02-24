import requests
from bs4 import BeautifulSoup
import json

def analyze_jisilu(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        # 1. Analyze Title
        title = soup.find('h2')
        print(f"Title: {title.get_text(strip=True) if title else 'Not Found'}")
        
        # 2. Analyze Content
        # Usually in div class="aw-question-detail" or similar
        content = soup.find('div', class_='aw-question-detail-txt')
        print(f"Content found: {bool(content)}")
        
        # 3. Analyze Comments
        # Usually in div class="aw-mod aw-question-comment"
        comments_container = soup.find('div', class_='aw-question-comment')
        if comments_container:
            # Individual comments
            comments = comments_container.find_all('div', class_='aw-item')
            print(f"Found {len(comments)} comments.")
            
            if comments:
                first_comment = comments[0]
                print("\n--- First Comment Structure ---")
                # Print class names and structure to understand where ID and Parent ID are
                print(first_comment.prettify()[:1000]) # Print first 1000 chars
                
                # Check for specific attributes
                print("\n--- Attributes ---")
                print(f"ID: {first_comment.get('data-id')}")
                
                # Check content for "Reply" pattern
                comment_body = first_comment.find('div', class_='markitup-box')
                if comment_body:
                    print(f"Body text: {comment_body.get_text(strip=True)[:100]}")
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    url = "https://www.jisilu.cn/question/517247"
    analyze_jisilu(url)
