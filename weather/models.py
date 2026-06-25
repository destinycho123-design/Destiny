"""Weather data models."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, List
from datetime import datetime


@dataclass
class CurrentWeather:
    """Current weather conditions."""
    location: str
    temperature: Decimal
    feels_like: Decimal
    humidity: int
    pressure: int
    description: str
    wind_speed: Decimal
    wind_direction: int
    cloudiness: int
    visibility: int
    uv_index: Optional[Decimal] = None
    sunrise: Optional[datetime] = None
    sunset: Optional[datetime] = None
    last_updated: datetime = None

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()

    def __str__(self):
        return (
            f"{self.location}: {self.temperature}°C, {self.description}\n"
            f"Feels like: {self.feels_like}°C | Humidity: {self.humidity}% | Wind: {self.wind_speed} m/s"
        )


@dataclass
class ForecastDay:
    """Weather forecast for a single day."""
    date: datetime
    max_temp: Decimal
    min_temp: Decimal
    avg_temp: Decimal
    description: str
    precipitation: Decimal
    precipitation_probability: int
    humidity: int
    wind_speed: Decimal
    cloudiness: int
    uv_index: Optional[Decimal] = None

    def __str__(self):
        return (
            f"{self.date.strftime('%Y-%m-%d')}: {self.min_temp}°C - {self.max_temp}°C, {self.description}\n"
            f"Chance of rain: {self.precipitation_probability}% | Wind: {self.wind_speed} m/s"
        )


@dataclass
class Forecast:
    """Weather forecast for multiple days."""
    location: str
    days: List[ForecastDay]
    generated_at: datetime = None

    def __post_init__(self):
        if self.generated_at is None:
            self.generated_at = datetime.now()

    def __str__(self):
        forecast_str = f"Weather Forecast for {self.location}:\n"
        forecast_str += "=" * 50 + "\n"
        for day in self.days:
            forecast_str += f"{day}\n\n"
        return forecast_str
