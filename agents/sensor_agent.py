from adk import Agent
from services.energy_data import insert_energy_record
from datetime import datetime

class SensorAgent(Agent):
    def __init__(self, name="SensorAgent"):
        super().__init__(name)

    def run(self, context):
        data = {
            "consumption_kWh": 12.5,
            "solar_generation_kWh": 4.2,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        print(f"[{self.name}] Collected sensor data: {data}")

        # Insert data into BigQuery using energy_data service
        insert_energy_record(
            timestamp=data["timestamp"],
            consumption_kWh=data["consumption_kWh"],
            solar_generation_kWh=data["solar_generation_kWh"]
        )

        return {"sensor_data": data}
# Register the agent
#Agent.register(SensorAgent)