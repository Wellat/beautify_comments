from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from scraper import get_jisilu_data

app = FastAPI()

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
    title: str
    content: str
    author: Optional[str] = None
    publish_time: Optional[str] = None
    comments: List[Comment]

@app.get("/api/parse", response_model=ArticleData)
async def parse_url(url: str = Query(..., description="The Jisilu article URL")):
    if "jisilu.cn/question" not in url:
        raise HTTPException(status_code=400, detail="Invalid URL. Must be a Jisilu question URL.")
    
    try:
        data = get_jisilu_data(url)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
