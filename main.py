import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import db, create_document, get_documents
from schemas import Song

app = FastAPI(title="Free Music Listing API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Free Music Listing API is running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    # Check environment variables
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response

# -------------------- Music Endpoints --------------------

class SongIn(BaseModel):
    title: str
    artist: str
    album: Optional[str] = None
    genre: Optional[str] = None
    year: Optional[int] = None
    cover_url: Optional[str] = None
    listen_url: Optional[str] = None
    is_free: bool = True

@app.post("/api/songs", status_code=201)
async def add_song(song: SongIn):
    try:
        song_model = Song(**song.model_dump())
        doc_id = create_document("song", song_model)
        return {"id": doc_id, **song_model.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/songs")
async def list_songs(q: Optional[str] = None, genre: Optional[str] = None, limit: int = 50):
    try:
        filter_dict = {"is_free": True}
        if genre:
            filter_dict["genre"] = genre
        # Simple text filters on title/artist if q provided
        if q:
            filter_dict["$or"] = [
                {"title": {"$regex": q, "$options": "i"}},
                {"artist": {"$regex": q, "$options": "i"}}
            ]
        docs = get_documents("song", filter_dict, limit)
        # Normalize ObjectId
        for d in docs:
            if "_id" in d:
                d["id"] = str(d.pop("_id"))
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
