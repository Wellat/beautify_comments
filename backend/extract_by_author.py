import json
import argparse
import os

def extract_comments_recursive(comments, result_dict):
    """
    递归提取评论内容并按作者分组
    """
    if not comments:
        return

    for comment in comments:
        author = comment.get('author')
        content = comment.get('content_text', '')
        
        # 如果作者存在且有内容，则添加到结果中
        if author and content:
            if author not in result_dict:
                result_dict[author] = []
            
            # 避免重复内容（可选，这里先不做去重，只简单追加）
            result_dict[author].append(content)
        
        # 递归处理子评论
        children = comment.get('children', [])
        extract_comments_recursive(children, result_dict)

def main():
    parser = argparse.ArgumentParser(description='Extract comments by author from a JSON cache file.')
    parser.add_argument('input_file', help='Path to the input JSON file (e.g., cache/517247.json)')
    parser.add_argument('--output', '-o', default='abstract.json', help='Path to the output JSON file (default: abstract.json)')
    
    args = parser.parse_args()
    
    input_path = args.input_file
    output_path = args.output
    
    if not os.path.exists(input_path):
        print(f"Error: Input file '{input_path}' not found.")
        return

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # 结果字典：Key=Author, Value=List[Content]
        grouped_comments = {}
        
        # 处理主楼内容
        main_author = data.get('author')
        main_content = data.get('content')
        
        # 主楼内容通常是HTML，为了保持一致性，如果能转成纯文本最好，这里暂时直接存HTML或者做简单清理
        # 由于用户指定 value 为 content_text 列表，而主楼没有 content_text，只有 content (HTML)
        # 我们可以尝试简单移除 HTML 标签或者直接使用 content
        # 这里为了简单起见，且通常主楼是最重要的，我们直接存 content
        # 或者如果有 beautifulsoup，可以用它来提取文本
        
        if main_author and main_content:
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(main_content, 'lxml')
                main_content_text = soup.get_text(strip=True)
            except ImportError:
                # Fallback: simple tag removal or keep as is
                import re
                main_content_text = re.sub(r'<[^>]+>', '', main_content).strip()

            if main_author not in grouped_comments:
                grouped_comments[main_author] = []
            grouped_comments[main_author].append(main_content_text)
        
        # 提取评论列表
        comments = data.get('comments', [])
        extract_comments_recursive(comments, grouped_comments)
        
        # 保存结果
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(grouped_comments, f, ensure_ascii=False, indent=2)
            
        print(f"Successfully processed {len(comments)} top-level comments.")
        print(f"Found {len(grouped_comments)} unique authors.")
        print(f"Results saved to: {output_path}")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
