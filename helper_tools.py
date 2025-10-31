import requests
from dotenv import load_dotenv
import os

# --- Load environment variables ---
load_dotenv()
API_KEY = os.getenv("WEATHER_API_KEY")

if not API_KEY:
    raise ValueError("❌ Missing WEATHER_API_KEY in .env file!")

def get_weather(city):
    url = "https://api.weatherapi.com/v1/current.json"
    params = {
        "key": API_KEY,
        "q": city,
        "aqi": "no"
    }

    r = requests.get(url, params=params)

    # --- Handle HTTP errors ---
    if r.status_code != 200:
        print(f"❌ API Error {r.status_code}: {r.text}")
        return None

    data = r.json()

    # --- Check for expected structure ---
    if "location" not in data or "current" not in data:
        print("⚠️ Unexpected response format:", data)
        return None

    location = data["location"]["name"]
    region = data["location"]["region"]
    country = data["location"]["country"]
    temp_c = data["current"]["temp_c"]
    condition = data["current"]["condition"]["text"]
    humidity = data["current"]["humidity"]

    print(f"🌦️ Weather in {location}, {region}, {country}:")
    print(f"   Condition: {condition}")
    print(f"   Temperature: {temp_c}°C")
    print(f"   Humidity: {humidity}%")

# --- Example ---
get_weather("Dhanbad")


import random
import pandas as pd
import time

# --- STEP 1: Create Dummy Sensor Data ---
def generate_sensor_data(n=50):
    data = {
        "temperature": [random.uniform(25, 45) for _ in range(n)],  # °C
        "methane": [random.uniform(0.5, 3.0) for _ in range(n)],    # %
        "vibration": [random.uniform(0.1, 6.0) for _ in range(n)],  # mm/s
        "humidity": [random.uniform(40, 95) for _ in range(n)]      # %
    }
    return pd.DataFrame(data)

# --- STEP 2: Define Safety Thresholds ---
SAFE_LIMITS = {
    "temperature": 40,   # °C
    "methane": 1.5,      # %
    "vibration": 4.0,    # mm/s
    "humidity": 90       # %
}

# --- STEP 3: Hazard Detection Logic ---
def check_hazards(row):
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

# --- STEP 4: Monitor and Generate Alerts ---
def monitor_mine_data():
    print("⛏️ Starting Mine Safety Monitor...\n")
    df = generate_sensor_data(20)  # simulate 20 readings
    df["hazard_flags"] = df.apply(check_hazards, axis=1)

    safe_count = (df["hazard_flags"] == "✅ Safe").sum()
    alert_count = len(df) - safe_count

    print("📊 Summary:")
    print(f"✅ Safe Readings: {safe_count}")
    print(f"🚨 Hazard Alerts: {alert_count}\n")

    # Show flagged alerts
    alerts = df[df["hazard_flags"] != "✅ Safe"]
    if not alerts.empty:
        print("🚨 Alerts Generated:\n")
        for i, row in alerts.iterrows():
            print(f"Reading {i+1}: {row['hazard_flags']}")
    else:
        print("✅ No hazards detected")

    # Optional: display the entire table
    print("\n📋 All Sensor Readings:\n")
    print(df.to_string(index=False))

# --- STEP 5: Real-Time Simulation (optional) ---
def live_monitoring(interval=2, total_cycles=10):
    print("🟢 Starting Live Mine Safety Monitoring...\n")
    for i in range(total_cycles):
        reading = generate_sensor_data(1)
        row = reading.iloc[0]
        hazard = check_hazards(row)
        print(f"Cycle {i+1}: Temp={row['temperature']:.1f}°C | "
              f"Methane={row['methane']:.2f}% | Vib={row['vibration']:.2f} | "
              f"Humidity={row['humidity']:.1f}% → {hazard}")
        time.sleep(interval)

if __name__ == "__main__":
    monitor_mine_data()

    print("\n---------------------------------------------\n")
    live_monitoring(interval=1.5, total_cycles=8)
