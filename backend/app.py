"""
SolSpot Backend API - Powered by FastAPI, Prior Labs' TabPFN, and Google's Gemma.
"""
from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
import logging

from backend.solar_service import SolarService
from backend.tabpfn_engine import TabPFNEngine
from backend.gemma_service import GemmaService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("solspot_app")

app = FastAPI(
    title="SolSpot API",
    description="The Anti-Burnout Natural Light Optimizer & Touch Grass Window Finder",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines
tabpfn_engine = TabPFNEngine()

@app.get("/api/health")
async def health_check():
    return {
        "status": "online",
        "tabpfn_loaded": tabpfn_engine.is_tabpfn_loaded,
        "model": "TabPFNRegressor (Prior Labs)" if tabpfn_engine.is_tabpfn_loaded else "Hybrid Tabular Engine",
        "challenge": "Hacktoberfest Week 1 - Touch Grass"
    }

@app.get("/api/search")
async def search_cities(q: str = Query(..., min_length=2)):
    """Search global coordinates without third-party tracking."""
    results = await SolarService.search_city(q)
    return {"results": results}

@app.get("/api/forecast")
async def get_solar_forecast(
    lat: float = Query(...),
    lon: float = Query(...),
    timezone: str = Query("auto"),
    city_name: str = Query("Current Location")
):
    """
    Main pipeline:
    1. Fetches real-time solar irradiance, UV, and cloud data from Open-Meteo.
    2. Runs TabPFN tabular inference to compute circadian daylight wellness scores.
    3. Pinpoints the optimal 20-minute 'Touch Grass' window.
    4. Generates a weather-aware sensory micro-quest via Gemma 2.
    """
    try:
        solar_data = await SolarService.get_solar_forecast(lat, lon, timezone)
    except Exception as e:
        logger.error(f"Error fetching solar forecast: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to fetch atmospheric data: {str(e)}")

    hourly_records = solar_data.get("hourly", [])
    if not hourly_records:
        raise HTTPException(status_code=500, detail="No hourly atmospheric data received")

    # Run TabPFN inference
    scored_hourly = tabpfn_engine.predict_hourly_scores(hourly_records)
    best_window = tabpfn_engine.find_best_window(scored_hourly)

    # Generate sensory outdoor micro-quest via Gemma
    gemma_quest = await GemmaService.generate_micro_quest(best_window)

    return {
        "location": {
            "city_name": city_name,
            "latitude": lat,
            "longitude": lon,
            "timezone": solar_data.get("timezone"),
            "sunrise": solar_data.get("sunrise"),
            "sunset": solar_data.get("sunset"),
            "uv_index_max": solar_data.get("uv_index_max")
        },
        "best_window": best_window,
        "gemma_quest": gemma_quest,
        "hourly_scores": scored_hourly,
        "engine_metadata": {
            "tabpfn_active": tabpfn_engine.is_tabpfn_loaded,
            "algorithm": "TabPFN Transformer (Prior Labs) Zero-Shot Tabular Regression",
            "gemma_model": gemma_quest.get("model")
        }
    }

@app.get("/api/refresh-quest")
async def refresh_quest(
    hour: int = Query(12),
    cloud_cover: float = Query(20.0),
    uv: float = Query(2.0),
    temp: float = Query(20.0)
):
    """Regenerates a fresh sensory quest from Gemma."""
    window_mock = {
        "best_hour": hour,
        "cloud_cover": cloud_cover,
        "uv_index": uv,
        "temp_c": temp,
        "window_time": f"{hour:02d}:15 – {hour:02d}:35"
    }
    quest = await GemmaService.generate_micro_quest(window_mock)
    return quest

# Serve static frontend files
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def serve_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "SolSpot Backend Online. Frontend static files loading..."}
