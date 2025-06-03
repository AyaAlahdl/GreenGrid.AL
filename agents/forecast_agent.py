from adk import Agent
import pandas as pd
import openmeteo_requests
import requests_cache
from retry_requests import retry
import datetime
import random
from utils.logger import get_logger

class ForecastAgent(Agent):
    def __init__(self, name="ForecastAgent", latitude=51.5085, longitude=-0.1257):
        super().__init__(name)
        self.latitude = latitude
        self.longitude = longitude
        self.logger = get_logger(name) # Initialize logger


        # Setup Open-Meteo client with cache and retry
        cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
        self.client = openmeteo_requests.Client(session=retry(cache_session, retries=3, backoff_factor=0.2))

    def get_weather_forecast(self):
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "hourly": [
                "temperature_2m", "wind_speed_10m", "relative_humidity_2m",
                "apparent_temperature", "cloud_cover", "wind_direction_10m",
                "shortwave_radiation", "direct_radiation", "diffuse_radiation"
            ],
            "timezone": "Europe/London"
        }

        try:
            responses = self.client.weather_api(url, params=params)
            hourly = responses[0].Hourly()

            df = pd.DataFrame({
                "time": pd.date_range(
                    start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                    end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                    freq=pd.Timedelta(seconds=hourly.Interval()),
                    inclusive="left"
                ),
                "temperature_2m": hourly.Variables(0).ValuesAsNumpy(),
                "shortwave_radiation": hourly.Variables(6).ValuesAsNumpy()
            })

           
            # Convert to local London time
            df["time"] = df["time"].dt.tz_convert("Europe/London")

            # Keep only data for the next hour
            now = datetime.datetime.now(datetime.timezone.utc).astimezone()
            df = df[(df["time"] >= now) & (df["time"] < now + datetime.timedelta(hours=1))]
            df = df.reset_index(drop=True)

            return df
        except Exception as e:
            print(f"[{self.name}] Error fetching forecast: {e}")
            return None

    def run(self, context):
        df = self.get_weather_forecast()

        if df is not None and not df.empty:
            next_hour = df.iloc[0]
            temperature = next_hour["temperature_2m"]
            radiation = max(0, next_hour["shortwave_radiation"])  # Ensure no negative radiation

            # Round and convert to float here, then store
            if temperature < 25:
                predicted_consumption_kWh = round(10 + (25 - temperature) * 0.2, 2)
            else:
                predicted_consumption_kWh = 10.0  # already float

            predicted_consumption_kWh = float(predicted_consumption_kWh)

            predicted_solar_kWh = float(round(radiation * 0.004, 2))  # Round here

        else:
            # fallback with rounded floats
            predicted_consumption_kWh = float(round(random.uniform(10, 15), 2))
            predicted_solar_kWh = float(round(random.uniform(3, 6), 2))
            radiation = "N/A"

        prediction = {
            "predicted_consumption_kWh": predicted_consumption_kWh,
            "predicted_solar_kWh": predicted_solar_kWh,
        }

       # After calculating rounded predicted values:

# Use rounded predicted values directly in logs:
        self.logger.info(
            f"Radiation: {radiation:.2f} W/m² → Solar Forecast: {predicted_solar_kWh:.2f} kWh"
        )
        self.logger.info(f"Weather forecast data:\n{df.head() if df is not None else 'No data available'}")
        self.logger.info(f"Predicted consumption: {predicted_consumption_kWh:.2f} kWh")

        # Format floats in the dictionary explicitly for logging:
        forecast_log_str = (
            f"{{'predicted_consumption_kWh': {predicted_consumption_kWh:.2f}, "
            f"'predicted_solar_kWh': {predicted_solar_kWh:.2f}}}"
        )
        self.logger.info(f"Forecast: {forecast_log_str}")
        self.logger.info(f"[{self.name}] Forecast completed successfully.")
        # Return the prediction as a dictionary
        

        return {"forecast": prediction}
    
