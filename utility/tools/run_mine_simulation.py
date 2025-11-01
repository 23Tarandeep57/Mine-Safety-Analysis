
from typing import List, Dict
from helper_tools import generate_sensor_data, check_hazards

class RunMineSimulationTool:
    def __init__(self):
        self.name = "run_mine_simulation"
        self.description = "Simulates mine sensor data and checks for hazards, returning a list of detected alerts."

    def use(self, num_readings: int = 1) -> List[Dict]:
        print(f"Running mine simulation for {num_readings} readings...")
        df = generate_sensor_data(num_readings)
        df["hazard_flags"] = df.apply(check_hazards, axis=1)

        alerts = []
        for i, row in df.iterrows():
            if row["hazard_flags"] != "✅ Safe":
                alerts.append({
                    "reading_id": i + 1,
                    "temperature": row["temperature"],
                    "methane": row["methane"],
                    "vibration": row["vibration"],
                    "humidity": row["humidity"],
                    "hazard": row["hazard_flags"]
                })
        
        if alerts:
            print(f"Detected {len(alerts)} hazards during simulation.")
        else:
            print("No hazards detected during simulation.")

        return alerts
