import asyncio
from backend.solar_service import SolarService
from backend.tabpfn_engine import TabPFNEngine
from backend.gemma_service import GemmaService

async def main():
    print("Testing Solar Service...")
    data = await SolarService.get_solar_forecast(37.7749, -122.4194)
    print("Hourly records received:", len(data["hourly"]))
    
    print("Running TabPFN inference...")
    engine = TabPFNEngine()
    scored = engine.predict_hourly_scores(data["hourly"])
    best = engine.find_best_window(scored)
    print("Best window:", best["window_time"], "Peak score:", best["peak_score"])
    print("Conditions: Temp", best["temp_c"], "C, UV:", best["uv_index"], "Lux:", best["lux_estimate"])
    
    print("Running Gemma 2 Micro-Quest...")
    quest = await GemmaService.generate_micro_quest(best)
    print("Gemma Model:", quest["model"])
    print("Quest:", quest["quest_text"])
    print("All Pipeline Tests PASSED!")

if __name__ == "__main__":
    asyncio.run(main())
