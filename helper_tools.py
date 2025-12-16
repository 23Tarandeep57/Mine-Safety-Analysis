"""
Mine Safety Helper Tools

Provides utility functions for:
- Sensor data simulation and hazard detection
- Weather monitoring for mine locations
- OCR-based mine data extraction from images

Note: Weather API requires WEATHER_API_KEY in .env file.
"""

import os
import time
import random
from typing import Optional, List, Dict, Any

import requests
import pandas as pd
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

# Configuration
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
WEATHER_API_URL = "https://api.weatherapi.com/v1/current.json"

# Safety Thresholds
SAFE_LIMITS = {
    "temperature": 40,   # °C
    "methane": 1.5,      # %
    "vibration": 4.0,    # mm/s
    "humidity": 90       # %
}

INDIAN_STATES = {
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal", "Delhi",
    "Jammu and Kashmir"
}


# ==================== OCR Functions ====================

def extract_mine_data(image_path: str) -> List[Dict[str, str]]:
    """
    Uses pytesseract OCR to extract 'Mine' names from an image.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        List of dictionaries with mine names
    """
    try:
        import pytesseract
    except ImportError:
        print("Error: pytesseract not installed. Run: pip install pytesseract")
        return []
    
    if not os.path.exists(image_path):
        print(f"Error: Image file not found: {image_path}")
        return []
    
    image = Image.open(image_path)
    raw_text = pytesseract.image_to_string(image)
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    
    mines = []
    for line in lines:
        if line not in INDIAN_STATES:
            mines.append({"mine": line})

    print(f"Extracted {len(mines)} mine entries from image.")
    return mines


# ==================== Weather Functions ====================

def get_weather(city: str) -> Optional[Dict[str, Any]]:
    """
    Fetch current weather data for a city in India.
    
    Args:
        city: Name of the city/mine location
        
    Returns:
        Dictionary with weather data or None on error
    """
    if not WEATHER_API_KEY:
        print("Error: WEATHER_API_KEY not set in environment")
        return None
    
    query = f"{city},India"
    params = {"key": WEATHER_API_KEY, "q": query, "aqi": "no"}

    try:
        response = requests.get(WEATHER_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "location" not in data or "current" not in data:
            print(f"Warning: Unexpected response for {city}")
            return None

        return {
            "Mine": city,
            "Location": data["location"]["name"],
            "Temperature (°C)": data["current"]["temp_c"],
            "Condition": data["current"]["condition"]["text"],
            "Humidity (%)": data["current"]["humidity"]
        }

    except requests.RequestException as e:
        print(f"Error fetching weather for {city}: {e}")
        return None


def get_weather_for_mines(image_path: str) -> List[Dict[str, Any]]:
    """
    Extract mine names from image and fetch weather for each.
    
    Args:
        image_path: Path to image containing mine names
        
    Returns:
        List of weather data dictionaries
    """
    mines = extract_mine_data(image_path)
    all_weather = []
    
    print(f"Fetching weather for {len(mines)} mines...")
    for mine in mines:
        city = mine["mine"]
        weather = get_weather(city)
        if weather:
            all_weather.append(weather)
        time.sleep(1)  # Rate limiting

    return all_weather


# ==================== Sensor Simulation ====================

def generate_sensor_data(n: int = 50) -> pd.DataFrame:
    """
    Generate simulated mine sensor data.
    
    Args:
        n: Number of readings to generate
        
    Returns:
        DataFrame with temperature, methane, vibration, humidity readings
    """
    data = {
        "temperature": [random.uniform(25, 45) for _ in range(n)],
        "methane": [random.uniform(0.5, 3.0) for _ in range(n)],
        "vibration": [random.uniform(0.1, 6.0) for _ in range(n)],
        "humidity": [random.uniform(40, 95) for _ in range(n)]
    }
    return pd.DataFrame(data)


def check_hazards(row: pd.Series) -> str:
    """
    Check sensor reading for safety hazards.
    
    Args:
        row: DataFrame row with sensor readings
        
    Returns:
        String describing hazards or "✅ Safe"
    """
    hazards = []
    if row["temperature"] > SAFE_LIMITS["temperature"]:
        hazards.append("🔥 High temperature")
    if row["methane"] > SAFE_LIMITS["methane"]:
        hazards.append("💨 Methane concentration too high")
    if row["vibration"] > SAFE_LIMITS["vibration"]:
        hazards.append("🌋 Excessive ground vibration")
    if row["humidity"] > SAFE_LIMITS["humidity"]:
        hazards.append("💧 High humidity (ventilation issue)")
    return ", ".join(hazards) if hazards else "✅ Safe"


def monitor_mine_data(num_readings: int = 20) -> pd.DataFrame:
    """
    Monitor simulated mine sensor data and detect hazards.
    
    Args:
        num_readings: Number of sensor readings to simulate
        
    Returns:
        DataFrame with readings and hazard flags
    """
    print("⛏️ Starting Mine Safety Monitor...\n")
    df = generate_sensor_data(num_readings)
    df["hazard_flags"] = df.apply(check_hazards, axis=1)

    safe_count = (df["hazard_flags"] == "✅ Safe").sum()
    alert_count = len(df) - safe_count

    print(f"📊 Summary:")
    print(f"✅ Safe Readings: {safe_count}")
    print(f"🚨 Hazard Alerts: {alert_count}\n")

    alerts = df[df["hazard_flags"] != "✅ Safe"]
    if not alerts.empty:
        print("🚨 Alerts Generated:\n")
        for i, row in alerts.iterrows():
            print(f"Reading {i+1}: {row['hazard_flags']}")
    else:
        print("✅ No hazards detected")

    return df


def live_monitoring(interval: float = 2.0, total_cycles: int = 10) -> None:
    """
    Run live simulation of mine safety monitoring.
    
    Args:
        interval: Seconds between readings
        total_cycles: Number of monitoring cycles
    """
    print("Starting Live Mine Safety Monitoring...\n")
    for i in range(total_cycles):
        reading = generate_sensor_data(1)
        row = reading.iloc[0]
        hazard = check_hazards(row)
        print(f"Cycle {i+1}: Temp={row['temperature']:.1f}°C | "
              f"Methane={row['methane']:.2f}% | Vib={row['vibration']:.2f} | "
              f"Humidity={row['humidity']:.1f}% → {hazard}")
        time.sleep(interval)


if __name__ == "__main__":
    # Demo: Run monitoring simulation
    print("=" * 50)
    print("Mine Safety Monitoring Demo")
    print("=" * 50 + "\n")
    
    monitor_mine_data(num_readings=10)
    
    print("\n" + "-" * 50 + "\n")
    
    live_monitoring(interval=1.0, total_cycles=5)
