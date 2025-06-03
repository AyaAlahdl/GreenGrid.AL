from adk import Agent

class OptimizerAgent(Agent):
    def __init__(self, name="OptimizerAgent"):
        super().__init__(name)
        # Initialize battery state (could be dynamic)
        self.battery_capacity_kWh = 20
        self.battery_current_charge = 10
        self.battery_charge_efficiency = 0.9
        self.battery_discharge_efficiency = 0.9

    def run(self, context):
        forecast = context.get("forecast", {})
        price = context.get("price_kWh", 0)

        predicted_consumption = forecast.get("predicted_consumption_kWh", 0)
        predicted_solar = forecast.get("predicted_solar_kWh", 0)
        user_consumption = predicted_consumption
        simulated_solar_kWh = predicted_solar
        grid_price = price

        # Battery decision threshold (example, can be dynamic)
        price_threshold = 0.15  # currency units per kWh

        # Decide battery action based on price and solar/consumption forecast
        if grid_price > price_threshold and self.battery_current_charge > 0:
            battery_action = "discharge"
            battery_change = min(self.battery_current_charge, user_consumption) * self.battery_discharge_efficiency
        else:
            battery_action = "charge"
            battery_change = min(self.battery_capacity_kWh - self.battery_current_charge, simulated_solar_kWh) * self.battery_charge_efficiency

        # Update battery state
        if battery_action == "charge":
            self.battery_current_charge += battery_change
            effective_solar = simulated_solar_kWh - battery_change
            effective_consumption = user_consumption
        else:  # discharge
            self.battery_current_charge -= battery_change
            effective_consumption = user_consumption - battery_change
            effective_solar = simulated_solar_kWh

        # Calculate net demand after battery impact
        net_demand = max(0, effective_consumption - effective_solar)

        # Make a high-level decision string
        if simulated_solar_kWh > user_consumption:
            decision = "store surplus" if battery_action == "charge" else "use battery"
        elif simulated_solar_kWh > 0:
            decision = "use solar, buy rest"
        else:
            decision = "buy energy"

        expected_cost = round(net_demand * grid_price, 2)

        print(f"[{self.name}] Decision: {decision}, Battery action: {battery_action}, Expected cost: {expected_cost}")
        print(f"[{self.name}] Battery charge level: {self.battery_current_charge:.2f} kWh")

        return {
            "decision": decision,
            "battery_action": battery_action,
            "battery_charge_kWh": self.battery_current_charge,
            "expected_cost": expected_cost,
            "net_demand_kWh": net_demand,
            "effective_consumption_kWh": effective_consumption,
            "effective_solar_kWh": effective_solar
        }
