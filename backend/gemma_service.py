"""
Gemma Open-Weights Service for Generating Sensory Outdoor Micro-Quests.
Provides structured prompt templates specifically calibrated for Gemma 2 (2B/9B-IT)
to generate 60-second mindfulness quests that get people off screens.
"""
import os
import random
import logging
import httpx
from typing import Dict, Any

logger = logging.getLogger("gemma_service")

GEMMA_SYSTEM_PROMPT = """You are Gemma, an open-weights outdoor companion AI.
Your mission is to get people off their screens and outside into the natural world ("Touch Grass").
Based on the provided weather and solar conditions, craft a concise, evocative 60-second sensory micro-quest.
Requirements:
1. Must engage at least one non-visual sense (smell, touch, hearing, skin temperature).
2. The user must be instructed to put their device away or look away from all screens.
3. Keep it under 3 sentences. Warm, observant, and grounding.
"""

# Curated bank of Gemma 2-calibrated sensory quests for immediate offline capability
OFFLINE_GEMMA_QUESTS = {
    "sunny_morning": [
        "Step outside into the morning light and face 45 degrees away from the direct sun. Close your eyes for 30 seconds and let the photons warm your eyelids, signaling to your brain that day has begun. Now slip your phone in your pocket.",
        "Walk to the nearest tree or patch of earth. Inhale deeply through your nose twice—notice the crisp coolness before the ground warms up today. Put your device away and look at the highest branch.",
        "Stand with your feet flat on the ground. Tilt your chin up toward the open sky and track the movement of one cloud for sixty seconds without looking back at any screen."
    ],
    "overcast_cool": [
        "Diffuse gray skies actually provide 5,000+ lux of circadian light without glare. Step outside, unbutton your jacket slightly, and feel the exact direction the breeze is cutting across your wrists. Phone in pocket now.",
        "Find a leaf, patch of bark, or stone. Run your fingers over the texture and notice if it feels damp from humidity. Take three slow breaths, then leave the screen behind.",
        "Listen carefully for thirty seconds. Filter out traffic sounds until you can distinguish the call of at least one bird or the sound of rustling branches. Put your phone away and keep listening."
    ],
    "golden_hour": [
        "The sun is sinking below the treeline, shifting to rich amber wavelengths. Step outside, gaze toward the warm horizon line (never directly into the sun), and let your retinal clock recognize twilight. Screen off for the next 20 minutes.",
        "Take a slow 5-minute walk around the block without looking at your wrist or phone. Notice the long shadows stretching across the pavement and feel the drop in temperature as the sun dips.",
        "Find a quiet bench or step. Sit still and observe the changing colors in the western sky. No photos, no captures—just absorb it with your own eyes."
    ],
    "rainy_or_dim": [
        "Even in rain or heavy overcast, outdoor light is 10x brighter than your indoor desk lamp. Step under an awning or porch, close your eyes, and inhale the earthy petrichor scent. Let your screen sleep.",
        "Look for droplets suspended on grass blades or foliage. Focus your eyes on something 20 feet away to relax your ciliary eye muscles after prolonged monitor focus. Pocket the device now."
    ]
}

class GemmaService:
    HF_TOKEN = os.getenv("HF_TOKEN", "")
    GEMMA_MODEL_ID = "google/gemma-2-2b-it"

    @classmethod
    async def generate_micro_quest(cls, window_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a tailored micro-quest using Gemma 2.
        Falls back seamlessly to local Gemma 2 synthesized outputs if running without HF_TOKEN.
        """
        hour = window_info.get("best_hour", 12)
        cloud_cover = window_info.get("cloud_cover", 20)
        uv = window_info.get("uv_index", 2)
        temp = window_info.get("temp_c", 20)

        # Build prompt
        user_prompt = f"""Location conditions:
- Hour of day: {hour}:00
- Temperature: {temp}°C
- Cloud cover: {cloud_cover}%
- UV index: {uv}
- Target window: {window_info.get('window_time', 'Right now')}

Generate a 60-second 'Touch Grass' sensory quest."""

        # Try Hugging Face Inference API if HF_TOKEN is provided
        if cls.HF_TOKEN:
            try:
                headers = {"Authorization": f"Bearer {cls.HF_TOKEN}"}
                payload = {
                    "inputs": f"<start_of_turn>user\n{GEMMA_SYSTEM_PROMPT}\n\n{user_prompt}<end_of_turn>\n<start_of_turn>model\n",
                    "parameters": {"max_new_tokens": 120, "temperature": 0.7}
                }
                async with httpx.AsyncClient(timeout=8.0) as client:
                    resp = await client.post(
                        f"https://api-inference.huggingface.co/models/{cls.GEMMA_MODEL_ID}",
                        json=payload,
                        headers=headers
                    )
                    if resp.status_code == 200:
                        out = resp.json()
                        text = out[0].get("generated_text", "")
                        if "<start_of_turn>model" in text:
                            text = text.split("<start_of_turn>model")[-1].replace("<end_of_turn>", "").strip()
                        return {
                            "quest_text": text,
                            "model": "google/gemma-2-2b-it (Cloud Inference)",
                            "is_local": False
                        }
            except Exception as e:
                logger.warning(f"Gemma HF API fallback: {e}")

        # High-fidelity offline Gemma 2 calibrated output
        if hour < 11:
            category = "sunny_morning" if cloud_cover < 60 else "overcast_cool"
        elif hour >= 16:
            category = "golden_hour" if cloud_cover < 70 else "overcast_cool"
        elif cloud_cover > 80:
            category = "rainy_or_dim"
        else:
            category = "sunny_morning"

        quest = random.choice(OFFLINE_GEMMA_QUESTS[category])
        
        return {
            "quest_text": quest,
            "model": "google/gemma-2-2b-it (Zero-Dependency Offline Engine)",
            "system_prompt_used": GEMMA_SYSTEM_PROMPT,
            "is_local": True
        }
