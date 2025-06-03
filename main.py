# main.py
from agents.coordinator_agent import CoordinatorAgent

if __name__ == '__main__':
    coordinator = CoordinatorAgent()
    result = coordinator.run({})
        # ✅ Round numeric values before printing
    result["forecast"]["predicted_consumption_kWh"] = round(result["forecast"]["predicted_consumption_kWh"], 2)
    result["forecast"]["predicted_solar_kWh"] = round(result["forecast"]["predicted_solar_kWh"], 2)
    result["expected_cost"] = round(result["expected_cost"], 2)
    print("\n[GreenGrid.AI Result]", result)