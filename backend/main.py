import os
import json
import glob
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from scraper import get_jisilu_data

app = FastAPI()

CACHE_DIR = "cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Comment(BaseModel):
    id: str
    author: str
    author_avatar: Optional[str] = None
    content: str
    time: str
    location: Optional[str] = None
    reply_to_user: Optional[str] = None
    children: List['Comment'] = []

class ArticleData(BaseModel):
    id: Optional[str] = None
    title: str
    content: str
    author: Optional[str] = None
    publish_time: Optional[str] = None
    comments: List[Comment]

class HistoryItem(BaseModel):
    id: str
    title: str

@app.get("/api/history", response_model=List[HistoryItem])
async def get_history():
    history = []
    try:
        files = glob.glob(os.path.join(CACHE_DIR, "*.json"))
        # Sort by modification time, newest first
        files.sort(key=os.path.getmtime, reverse=True)
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'id' in data and 'title' in data:
                        history.append(HistoryItem(id=data['id'], title=data['title']))
            except Exception as e:
                print(f"Error reading cache file {file_path}: {e}")
                continue
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/parse", response_model=ArticleData)
async def parse_article(
    article_id: str = Query(..., description="The Jisilu article ID"),
    force_update: bool = Query(False, description="Force update from source")
):
    if not article_id.isdigit():
         raise HTTPException(status_code=400, detail="Invalid Article ID. Must be numeric.")

    file_path = os.path.join(CACHE_DIR, f"{article_id}.json")
    
    # Try to load from cache if not force update
    if not force_update and os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        except Exception as e:
            print(f"Error reading cache for {article_id}: {e}")
            # Fallback to fetching if cache read fails
            pass

    url = f"https://www.jisilu.cn/question/{article_id}"
    
    try:
        data = get_jisilu_data(url, force_update=force_update)
        # Inject ID into data
        data['id'] = article_id
        
        # Save to cache
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
