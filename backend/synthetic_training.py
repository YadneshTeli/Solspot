"""
Atmospheric and Chronobiological calibration dataset for TabPFN.
Synthesizes scientific domain data on circadian light exposure,
UV risk curves, and thermal outdoor comfort indices.
"""
import numpy as np

def generate_circadian_training_dataset(n_samples=250, seed=42):
    """
    Generates realistic atmospheric conditions mapped to optimal outdoor light scores.
    Features:
      0: hour_of_day (0 to 23)
      1: solar_elevation (degrees, -50 to +80)
      2: ghi_irradiance (W/m^2, 0 to 1100)
      3: uv_index (0 to 12)
      4: cloud_cover (pct, 0 to 100)
      5: temp_c (celsius, -10 to 45)
      6: wind_speed (km/h, 0 to 60)
    Target:
      circadian_wellness_score (0 to 100)
    """
    np.random.seed(seed)
    
    # Hours
    hours = np.random.uniform(5, 21, n_samples)
    
    # Solar elevation roughly tied to hour
    solar_elev = np.sin((hours - 6) / 14 * np.pi) * np.random.uniform(40, 75, n_samples)
    solar_elev = np.clip(solar_elev, -10, 85)
    
    # GHI irradiance correlated with elevation and clouds
    clouds = np.random.uniform(0, 100, n_samples)
    base_ghi = np.maximum(0, np.sin(np.maximum(0, solar_elev) * np.pi / 180)) * 1000
    ghi = base_ghi * (1.0 - (clouds / 100.0) * 0.75) + np.random.normal(0, 20, n_samples)
    ghi = np.clip(ghi, 0, 1100)
    
    # UV Index
    uv = np.maximum(0, (ghi / 100.0) * np.random.uniform(0.9, 1.2, n_samples))
    uv = np.clip(uv, 0, 12)
    
    # Temperature
    temp = 12 + 10 * np.sin((hours - 8) / 12 * np.pi) + np.random.normal(0, 5, n_samples)
    temp = np.clip(temp, -5, 40)
    
    # Wind speed
    wind = np.random.gamma(2, 5, n_samples)
    wind = np.clip(wind, 0, 50)
    
    # Calculate Ground-truth Circadian Wellness Score based on chronobiology:
    # 1. Morning light bonus (7:00 - 10:30): Essential for cortisol peak & melatonin suppression
    morning_mask = (hours >= 7.0) & (hours <= 10.5)
    morning_bonus = np.where(morning_mask, 35 * (ghi / 600.0).clip(0, 1), 0)
    
    # 2. Golden hour / afternoon light bonus (16:30 - 18:45): Melatonin preparation & sunset reset
    evening_mask = (hours >= 16.5) & (hours <= 19.0)
    evening_bonus = np.where(evening_mask, 30 * (1 - clouds / 100.0), 0)
    
    # 3. Midday light (11:00 - 15:00): Good for Vitamin D, but penalize harsh UV (> 6.0)
    midday_mask = (hours > 10.5) & (hours < 16.5)
    midday_score = np.where(midday_mask, 25 + 20 * (ghi / 800.0).clip(0, 1) - np.maximum(0, uv - 6.0) * 8, 0)
    
    # 4. Thermal comfort penalty (too cold < 10C or too hot > 32C, high wind > 30km/h)
    thermal_penalty = np.maximum(0, 12 - temp) * 1.2 + np.maximum(0, temp - 30) * 2.0 + np.maximum(0, wind - 25) * 0.8
    
    # Base score
    base_score = 15 + morning_bonus + evening_bonus + midday_score - thermal_penalty
    scores = np.clip(base_score + np.random.normal(0, 3, n_samples), 5, 100)
    
    X = np.column_stack([hours, solar_elev, ghi, uv, clouds, temp, wind])
    y = scores
    
    return X, y
