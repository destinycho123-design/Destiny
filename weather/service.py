"""Weather service - high-level interface for weather operations."""

from typing import Optional
from weather.api_client import WeatherClient, WeatherAPIError
from weather.models import CurrentWeather, Forecast
from weather.cache import WeatherCache


class WeatherService:
    """Service for fetching and caching weather data."""

    def __init__(self, client: WeatherClient, cache: Optional[WeatherCache] = None):
        """
        Initialize weather service.
        
        Args:
            client: Weather API client
            cache: Optional cache layer
        """
        self.client = client
        self.cache = cache or WeatherCache()

    def get_current_weather(self, location: str) -> CurrentWeather:
        """
        Get current weather for a location.
        
        Attempts to return cached data if available.
        """
        cache_key = f"weather_{location}"
        
        # Try cache first
        cached = self.cache.get(cache_key)
        if cached:
            return self._deserialize_current_weather(cached)
        
        # Fetch from API
        weather = self.client.get_current_weather(location)
        
        # Cache the result
        self.cache.set(cache_key, self._serialize_current_weather(weather))
        
        return weather

    def get_forecast(self, location: str, days: int = 5) -> Forecast:
        """
        Get weather forecast for a location.
        
        Attempts to return cached data if available.
        """
        cache_key = f"forecast_{location}_{days}"
        
        # Try cache first
        cached = self.cache.get(cache_key)
        if cached:
            return self._deserialize_forecast(cached)
        
        # Fetch from API
        forecast = self.client.get_forecast(location, days)
        
        # Cache the result
        self.cache.set(cache_key, self._serialize_forecast(forecast))
        
        return forecast

    @staticmethod
    def _serialize_current_weather(weather: CurrentWeather) -> dict:
        """Serialize CurrentWeather for caching."""
        return {
            "location": weather.location,
            "temperature": str(weather.temperature),
            "feels_like": str(weather.feels_like),
            "humidity": weather.humidity,
            "pressure": weather.pressure,
            "description": weather.description,
            "wind_speed": str(weather.wind_speed),
            "wind_direction": weather.wind_direction,
            "cloudiness": weather.cloudiness,
            "visibility": weather.visibility,
            "uv_index": str(weather.uv_index) if weather.uv_index else None,
            "sunrise": weather.sunrise.isoformat() if weather.sunrise else None,
            "sunset": weather.sunset.isoformat() if weather.sunset else None,
        }

    @staticmethod
    def _deserialize_current_weather(data: dict) -> CurrentWeather:
        """Deserialize CurrentWeather from cache."""
        from decimal import Decimal
        from datetime import datetime
        
        return CurrentWeather(
            location=data["location"],
            temperature=Decimal(data["temperature"]),
            feels_like=Decimal(data["feels_like"]),
            humidity=data["humidity"],
            pressure=data["pressure"],
            description=data["description"],
            wind_speed=Decimal(data["wind_speed"]),
            wind_direction=data["wind_direction"],
            cloudiness=data["cloudiness"],
            visibility=data["visibility"],
            uv_index=Decimal(data["uv_index"]) if data.get("uv_index") else None,
            sunrise=datetime.fromisoformat(data["sunrise"]) if data.get("sunrise") else None,
            sunset=datetime.fromisoformat(data["sunset"]) if data.get("sunset") else None,
        )

    @staticmethod
    def _serialize_forecast(forecast: Forecast) -> dict:
        """Serialize Forecast for caching."""
        return {
            "location": forecast.location,
            "days": [
                {
                    "date": day.date.isoformat(),
                    "max_temp": str(day.max_temp),
                    "min_temp": str(day.min_temp),
                    "avg_temp": str(day.avg_temp),
                    "description": day.description,
                    "precipitation": str(day.precipitation),
                    "precipitation_probability": day.precipitation_probability,
                    "humidity": day.humidity,
                    "wind_speed": str(day.wind_speed),
                    "cloudiness": day.cloudiness,
                    "uv_index": str(day.uv_index) if day.uv_index else None,
                }
                for day in forecast.days
            ],
        }

    @staticmethod
    def _deserialize_forecast(data: dict) -> Forecast:
        """Deserialize Forecast from cache."""
        from decimal import Decimal
        from datetime import datetime
        from weather.models import ForecastDay
        
        days = [
            ForecastDay(
                date=datetime.fromisoformat(day["date"]),
                max_temp=Decimal(day["max_temp"]),
                min_temp=Decimal(day["min_temp"]),
                avg_temp=Decimal(day["avg_temp"]),
                description=day["description"],
                precipitation=Decimal(day["precipitation"]),
                precipitation_probability=day["precipitation_probability"],
                humidity=day["humidity"],
                wind_speed=Decimal(day["wind_speed"]),
                cloudiness=day["cloudiness"],
                uv_index=Decimal(day["uv_index"]) if day.get("uv_index") else None,
            )
            for day in data["days"]
        ]
        
        return Forecast(location=data["location"], days=days)
