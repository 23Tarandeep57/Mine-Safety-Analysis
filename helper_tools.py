import os
import time
import requests
import pytesseract
from dotenv import load_dotenv
from PIL import Image
import random 
import pandas as pd 

load_dotenv()
API_KEY = os.getenv("WEATHER_API_KEY")

if not API_KEY:
    raise ValueError(" Missing WEATHER_API_KEY in .env file!")

INDIAN_STATES = {
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal", "Delhi",
    "Jammu and Kashmir"
}


def extract_mine_data(image_path):
    """
    Uses pytesseract OCR to extract 'Mine' and 'State' pairs from the image.
    """
    image = Image.open(image_path)
    raw_text = pytesseract.image_to_string(image)
    print("raw_text: ",raw_text)
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    #print("lines: ",lines)
    mines = []
    current_mine = None

    for i in range(0, len(lines), 1):
        if i < len(lines):
            mine = lines[i]
            if mine in INDIAN_STATES:
                continue 
            mines.append({"mine": mine})

    print(f"Extracted {len(mines)} mine entries from image.\n")
    return mines


def get_weather(city):
    url = "https://api.weatherapi.com/v1/current.json"
    query = f"{city},India"
    params = {"key": API_KEY, "q": query, "aqi": "no"}

    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()

        if "location" not in data or "current" not in data:
            print(f"⚠️ Unexpected response for {city}: {data}")
            return None

        loc = data["location"]["name"]
        temp = data["current"]["temp_c"]
        condition = data["current"]["condition"]["text"]
        humidity = data["current"]["humidity"]

        return {
            "Mine": city,
            "Location": loc,
            "Temperature (°C)": temp,
            "Condition": condition,
            "Humidity (%)": humidity
        }

    except Exception as e:
        print(f"Error fetching weather for {city}: {e}")
        return None


def get_weather_for_all(image_path):
    mines = extract_mine_data(image_path)
    all_weather = []
    print("Fetching weather for all extracted mines...\n")
    for mine in mines:
        city = mine["mine"]
        print(f"🔍 {city}")
        weather = get_weather(city)
        if weather:
            all_weather.append(weather)
        time.sleep(1)

    print("\n---Mine Weather Report ---\n")
    for w in all_weather:
        print(f"{w['Mine']}) → {w['Condition']}, "
              f"{w['Temperature (°C)']}°C, Humidity: {w['Humidity (%)']}%")

    return all_weather



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
    IMAGE_PATH = r"/Users/ajaypillai/Desktop/mine_agent/Screenshot 2025-11-01 at 9.09.13 AM.png"  
    get_weather_for_all(IMAGE_PATH)
    monitor_mine_data()

    print("\n---------------------------------------------\n")
    live_monitoring(interval=1.5, total_cycles=8)
