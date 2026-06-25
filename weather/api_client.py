"""Weather API clients for different weather services."""

import requests
from decimal import Decimal
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import json
from abc import ABC, abstractmethod

from weather.models import CurrentWeather, Forecast, ForecastDay


class WeatherClient(ABC):
    """Abstract base class for weather API clients."""

    @abstractmethod
    def get_current_weather(self, location: str) -> CurrentWeather:
        """Fetch current weather for a location."""
        pass

    @abstractmethod
    def get_forecast(self, location: str, days: int = 5) -> Forecast:
        """Fetch weather forecast for a location."""
        pass


class OpenWeatherMapClient(WeatherClient):
    """OpenWeatherMap API client."""

    BASE_URL = "https://api.openweathermap.org/data/2.5"

    def __init__(self, api_key: str):
        """
        Initialize OpenWeatherMap client.
        
        Args:
            api_key: OpenWeatherMap API key
        """
        if not api_key:
            raise ValueError("API key is required")
        self.api_key = api_key
        self.session = requests.Session()

    def get_current_weather(self, location: str) -> CurrentWeather:
        """Fetch current weather from OpenWeatherMap."""
        try:
            url = f"{self.BASE_URL}/weather"
            params = {
                "q": location,
                "appid": self.api_key,
                "units": "metric"
            }
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return self._parse_current_weather(data, location)
        except requests.RequestException as e:
            raise WeatherAPIError(f"Failed to fetch weather for {location}: {e}")
        except (KeyError, ValueError) as e:
            raise WeatherAPIError(f"Failed to parse weather data: {e}")

    def get_forecast(self, location: str, days: int = 5) -> Forecast:
        """Fetch weather forecast from OpenWeatherMap."""
        try:
            url = f"{self.BASE_URL}/forecast"
            params = {
                "q": location,
                "appid": self.api_key,
                "units": "metric",
                "cnt": days * 8  # 8 forecasts per day (3-hour intervals)
            }
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return self._parse_forecast(data, location)
        except requests.RequestException as e:
            raise WeatherAPIError(f"Failed to fetch forecast for {location}: {e}")
        except (KeyError, ValueError) as e:
            raise WeatherAPIError(f"Failed to parse forecast data: {e}")

    @staticmethod
    def _parse_current_weather(data: Dict[str, Any], location: str) -> CurrentWeather:
        """Parse OpenWeatherMap current weather response."""
        main = data["main"]
        weather = data["weather"][0]
        wind = data["wind"]
        clouds = data["clouds"]
        sys = data["sys"]

        return CurrentWeather(
            location=f"{data['name']}, {data['sys']['country']}",
            temperature=Decimal(str(main["temp"])),
            feels_like=Decimal(str(main["feels_like"])),
            humidity=main["humidity"],
            pressure=main["pressure"],
            description=weather["main"],
            wind_speed=Decimal(str(wind.get("speed", 0))),
            wind_direction=wind.get("deg", 0),
            cloudiness=clouds["all"],
            visibility=data.get("visibility", 0) // 1000,  # Convert to km
            sunrise=datetime.fromtimestamp(sys["sunrise"]),
            sunset=datetime.fromtimestamp(sys["sunset"])
        )

    @staticmethod
    def _parse_forecast(data: Dict[str, Any], location: str) -> Forecast:
        """Parse OpenWeatherMap forecast response."""
        forecast_data = {}
        
        # Group by day
        for item in data["list"]:
            dt = datetime.fromtimestamp(item["dt"])
            date_key = dt.date()
            
            if date_key not in forecast_data:
                forecast_data[date_key] = []
            forecast_data[date_key].append(item)
        
        # Generate daily forecasts
        forecast_days = []
        for date in sorted(forecast_data.keys()):
            day_data = forecast_data[date]
            temps = [Decimal(str(item["main"]["temp"])) for item in day_data]
            precip = sum([Decimal(str(item.get("rain", {}).get("3h", 0))) for item in day_data])
            
            forecast_day = ForecastDay(
                date=datetime.combine(date, datetime.min.time()),
                max_temp=max(temps),
                min_temp=min(temps),
                avg_temp=sum(temps) / len(temps),
                description=day_data[0]["weather"][0]["main"],
                precipitation=precip,
                precipitation_probability=50,  # OpenWeatherMap doesn't provide this in free tier
                humidity=int(sum([item["main"]["humidity"] for item in day_data]) / len(day_data)),
                wind_speed=Decimal(str(day_data[0]["wind"]["speed"])),
                cloudiness=int(sum([item["clouds"]["all"] for item in day_data]) / len(day_data))
            )
            forecast_days.append(forecast_day)
        
        return Forecast(
            location=f"{data['city']['name']}, {data['city']['country']}",
            days=forecast_days
        )


class WeatherAPIClient(WeatherClient):
    """WeatherAPI.com client."""

    BASE_URL = "https://api.weatherapi.com/v1"

    def __init__(self, api_key: str):
        """
        Initialize WeatherAPI client.
        
        Args:
            api_key: WeatherAPI.com API key
        """
        if not api_key:
            raise ValueError("API key is required")
        self.api_key = api_key
        self.session = requests.Session()

    def get_current_weather(self, location: str) -> CurrentWeather:
        """Fetch current weather from WeatherAPI."""
        try:
            url = f"{self.BASE_URL}/current.json"
            params = {
                "key": self.api_key,
                "q": location,
                "aqi": "yes"
            }
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return self._parse_current_weather(data)
        except requests.RequestException as e:
            raise WeatherAPIError(f"Failed to fetch weather for {location}: {e}")
        except (KeyError, ValueError) as e:
            raise WeatherAPIError(f"Failed to parse weather data: {e}")

    def get_forecast(self, location: str, days: int = 5) -> Forecast:
        """Fetch weather forecast from WeatherAPI."""
        try:
            url = f"{self.BASE_URL}/forecast.json"
            params = {
                "key": self.api_key,
                "q": location,
                "days": min(days, 10),  # WeatherAPI free tier supports up to 10 days
                "aqi": "yes"
            }
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return self._parse_forecast(data)
        except requests.RequestException as e:
            raise WeatherAPIError(f"Failed to fetch forecast for {location}: {e}")
        except (KeyError, ValueError) as e:
            raise WeatherAPIError(f"Failed to parse forecast data: {e}")

    @staticmethod
    def _parse_current_weather(data: Dict[str, Any]) -> CurrentWeather:
        """Parse WeatherAPI current weather response."""
        current = data["current"]
        location = data["location"]

        return CurrentWeather(
            location=f"{location['name']}, {location['country']}",
            temperature=Decimal(str(current["temp_c"])),
            feels_like=Decimal(str(current["feelslike_c"])),
            humidity=current["humidity"],
            pressure=current["pressure_mb"],
            description=current["condition"]["text"],
            wind_speed=Decimal(str(current["wind_kph"])) / Decimal("3.6"),  # Convert to m/s
            wind_direction=current["wind_degree"],
            cloudiness=current["cloud"],
            visibility=current["vis_km"],
            uv_index=Decimal(str(current.get("uv", 0)))
        )

    @staticmethod
    def _parse_forecast(data: Dict[str, Any]) -> Forecast:
        """Parse WeatherAPI forecast response."""
        forecast_days = []
        location = data["location"]

        for day_data in data["forecast"]["forecastday"]:
            forecast_day = ForecastDay(
                date=datetime.strptime(day_data["date"], "%Y-%m-%d"),
                max_temp=Decimal(str(day_data["day"]["maxtemp_c"])),
                min_temp=Decimal(str(day_data["day"]["mintemp_c"])),
                avg_temp=Decimal(str(day_data["day"]["avgtemp_c"])),
                description=day_data["day"]["condition"]["text"],
                precipitation=Decimal(str(day_data["day"]["totalprecip_mm"])),
                precipitation_probability=day_data["day"]["daily_chance_of_rain"],
                humidity=day_data["day"]["avghumidity"],
                wind_speed=Decimal(str(day_data["day"]["maxwind_kph"])) / Decimal("3.6"),  # Convert to m/s
                cloudiness=day_data["day"]["avgcloud"],
                uv_index=Decimal(str(day_data["day"]["uv"]))
            )
            forecast_days.append(forecast_day)

        return Forecast(
            location=f"{location['name']}, {location['country']}",
            days=forecast_days
        )


class WeatherAPIError(Exception):
    """Weather API error."""
    pass
