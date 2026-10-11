"""
Solar and atmospheric data service using Open-Meteo's open solar and weather API.
Requires no proprietary API keys, honoring the open-source philosophy of the challenge.
"""
import httpx
from datetime import datetime, date
from typing import Dict, Any, List

class SolarService:
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"

    @classmethod
    async def search_city(cls, query: str) -> List[Dict[str, Any]]:
        """Search for cities/coordinates worldwide without API keys."""
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(cls.GEO_URL, params={"name": query, "count": 5, "language": "en", "format": "json"})
            if resp.status_code != 200:
                return []
            data = resp.json()
            results = []
            for item in data.get("results", []):
                results.append({
                    "name": item.get("name"),
                    "country": item.get("country", ""),
                    "admin1": item.get("admin1", ""),
                    "latitude": item.get("latitude"),
                    "longitude": item.get("longitude"),
                    "timezone": item.get("timezone", "UTC")
                })
            return results

    @classmethod
    async def get_solar_forecast(cls, lat: float, lon: float, timezone: str = "auto") -> Dict[str, Any]:
        """
        Fetches hourly solar irradiance, UV, cloud cover, and daily ephemeris (sunrise/sunset).
        """
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": [
                "temperature_2m",
                "relative_humidity_2m",
                "cloud_cover",
                "direct_normal_irradiance",
                "global_tilted_irradiance",
                "uv_index",
                "wind_speed_10m"
            ],
            "daily": ["sunrise", "sunset", "uv_index_max"],
            "timezone": timezone,
            "forecast_days": 1
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(cls.BASE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        hourly = data.get("hourly", {})
        daily = data.get("daily", {})
        
        # Flatten hourly data into record objects
        times = hourly.get("time", [])
        temps = hourly.get("temperature_2m", [])
        humidity = hourly.get("relative_humidity_2m", [])
        clouds = hourly.get("cloud_cover", [])
        dni = hourly.get("direct_normal_irradiance", [])
        ghi = hourly.get("global_tilted_irradiance", [])
        uv = hourly.get("uv_index", [])
        wind = hourly.get("wind_speed_10m", [])

        hourly_records = []
        for i in range(len(times)):
            iso_str = times[i]
            dt = datetime.fromisoformat(iso_str)
            hour_val = dt.hour + dt.minute / 60.0
            
            hourly_records.append({
                "time_iso": iso_str,
                "hour": hour_val,
                "temperature_c": temps[i] if i < len(temps) else 20.0,
                "humidity_pct": humidity[i] if i < len(humidity) else 50.0,
                "cloud_cover_pct": clouds[i] if i < len(clouds) else 0.0,
                "dni_w_m2": dni[i] if i < len(dni) else 0.0,
                "ghi_w_m2": ghi[i] if i < len(ghi) else 0.0,
                "uv_index": uv[i] if i < len(uv) else 0.0,
                "wind_speed_kmh": wind[i] if i < len(wind) else 10.0,
            })

        return {
            "latitude": lat,
            "longitude": lon,
            "timezone": data.get("timezone", timezone),
            "elevation": data.get("elevation", 0),
            "sunrise": daily.get("sunrise", [None])[0],
            "sunset": daily.get("sunset", [None])[0],
            "uv_index_max": daily.get("uv_index_max", [None])[0],
            "hourly": hourly_records
        }
