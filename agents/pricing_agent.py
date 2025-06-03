
# agents/pricing_agent.py
from adk import Agent
import pandas as pd
import requests

class PricingAgent(Agent):
    def __init__(self, name="PricingAgent"):
        super().__init__(name)

    def get_current_price(self):
        url = r"https://api.octopus.energy/v1/products/AGILE-18-02-21/electricity-tariffs/E-1R-AGILE-18-02-21-L/standard-unit-rates/"
        response = requests.get(url)
        data = response.json()
        if "results" in data and data["results"]:
            price = data["results"][0]["value_inc_vat"]  # pence per kWh
            return price
        return None

    def run(self, context):
        # Get current UTC time rounded to the hour
        now_utc = pd.Timestamp.now(tz="UTC").floor("h")

        # Fetch the current price
        price_kWh = self.get_current_price()

        if price_kWh is None:
            print(f"[{self.name}] ⚠️ No current price available. Using fallback price.")
            price_kWh = 0.18

        print(f"[{self.name}] Current price: {price_kWh} p/kWh at {now_utc}")

        # Return the price in the context dictionary
        return {"price_kWh": price_kWh}



