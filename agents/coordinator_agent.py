from adk import Agent
from agents.sensor_agent import SensorAgent
from agents.forecast_agent import ForecastAgent
from agents.pricing_agent import PricingAgent
from agents.optimizer_agent import OptimizerAgent
from agents.advisor_agent import AdvisorAgent

class CoordinatorAgent(Agent):
    def __init__(self, name="CoordinatorAgent"):
        super().__init__(name)
        self.sensor = SensorAgent()
        self.forecast = ForecastAgent()
        self.pricing = PricingAgent()
        self.optimizer = OptimizerAgent()
        self.advisor = AdvisorAgent()

    def run(self, context):
        ctx = {}
        ctx.update(self.sensor.run(ctx))
        ctx.update(self.forecast.run(ctx))
        ctx.update(self.pricing.run(ctx))
        ctx.update(self.optimizer.run(ctx))
        ctx.update(self.advisor.run(ctx))
        return ctx