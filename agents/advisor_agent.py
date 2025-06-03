
# agents/advisor_agent.py
from adk import Agent
import google.generativeai as genai
import os
from dotenv import load_dotenv
import time


load_dotenv()
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

 
class AdvisorAgent(Agent):
    def __init__(self, name="AdvisorAgent"):
        super().__init__(name)
        self.model = genai.GenerativeModel("gemini-2.0-flash")

    def run(self, ctx):
        decision = ctx.get("decision", "No decision available")
        cost = round(ctx.get("expected_cost", 0.0), 2)

        prompt = f"""
        Based on the decision "{decision}" and an estimated cost of ${cost}, write a clear, concise, and user-friendly report
        explaining what the user should do and why, assuming they’re not energy experts.
        """
        time.sleep(5) 
        response = self.model.generate_content(prompt)
        # sleep 5 seconds between calls to avoid hitting the limit

        report = response.text.strip()
        print(f"[{self.name}] Gemini-generated report:\n{report}")

        return {"report": report}
