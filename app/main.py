from __future__ import annotations
import os
from pathlib import Path
from typing import Any, Literal, Optional
from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .engine import CalculationError, calculate_chart, calculate_day
from .notion_sync import NotionSync

ROOT=Path(__file__).parent
STATIC=ROOT/"static"
app=FastAPI(title="Enchanted Saju Calculator",version="0.1.0")
app.mount("/static",StaticFiles(directory=STATIC),name="static")
notion=NotionSync()

@app.middleware("http")
async def embed_headers(request:Request,call_next):
    response=await call_next(request)
    response.headers["Content-Security-Policy"]="frame-ancestors 'self' https://*.notion.so https://*.notion.site https://www.notion.so https://www.notion.site"
    return response

class ChartInput(BaseModel):
    name:str=""
    nickname:str=""
    sex:Literal["male","female","unspecified"]="unspecified"
    birth_date:str
    birth_time:Optional[str]=None
    time_status:Literal["exact","approximate","unknown"]="exact"
    uncertainty_minutes:int=Field(default=30,ge=1,le=360)
    place:str=""
    latitude:float
    longitude:float
    timezone:str
    use_true_solar_time:bool=True
    day_boundary:Literal["midnight","zi_start"]="midnight"
    luck_direction:Literal["auto","forward","backward"]="auto"
    boundary_safety_minutes:int=Field(default=120,ge=1,le=1440)

class SaveInput(BaseModel):
    result:dict[str,Any]

def _guard(key:Optional[str]):
    required=os.getenv("APP_ACCESS_KEY")
    if required and key!=required: raise HTTPException(status_code=401,detail="Invalid app access key")

@app.get("/")
async def home(): return FileResponse(STATIC/"index.html")

@app.get("/health")
async def health(): return {"ok":True,"notion_configured":notion.configured}

@app.post("/api/calculate")
async def calculate(payload:ChartInput,x_app_key:Optional[str]=Header(default=None)):
    _guard(x_app_key)
    try: return calculate_chart(payload.model_dump())
    except (CalculationError,ValueError,KeyError) as e: raise HTTPException(status_code=422,detail=str(e))

@app.get("/api/day/{date_iso}")
async def day(date_iso:str,x_app_key:Optional[str]=Header(default=None)):
    _guard(x_app_key)
    try:return calculate_day(date_iso)
    except ValueError as e:raise HTTPException(status_code=422,detail=str(e))

@app.get("/api/geocode")
async def geocode(q:str=Query(min_length=2),x_app_key:Optional[str]=Header(default=None)):
    _guard(x_app_key)
    from geopy.geocoders import Nominatim
    from timezonefinder import TimezoneFinder
    loc=Nominatim(user_agent=os.getenv("GEOCODER_USER_AGENT","enchanted-saju-calculator/0.1")).geocode(q,exactly_one=True,language="en")
    if not loc: raise HTTPException(status_code=404,detail="Location not found")
    tz=TimezoneFinder().timezone_at(lat=loc.latitude,lng=loc.longitude)
    if not tz: raise HTTPException(status_code=422,detail="Timezone could not be resolved")
    return {"display_name":loc.address,"latitude":loc.latitude,"longitude":loc.longitude,"timezone":tz}

@app.post("/api/notion/save")
async def save_to_notion(payload:SaveInput,x_app_key:Optional[str]=Header(default=None)):
    _guard(x_app_key)
    if not notion.configured: raise HTTPException(status_code=503,detail="Notion sync is not configured")
    try:return await notion.save_verified_chart(payload.result)
    except Exception as e: raise HTTPException(status_code=502,detail=f"Notion save failed: {e}")
