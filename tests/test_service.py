"""Tests for weather service."""

import unittest
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, patch
from weather.service import WeatherService
from weather.models import CurrentWeather, Forecast, ForecastDay
from weather.cache import WeatherCache


class TestWeatherService(unittest.TestCase):
    """Test WeatherService."""

    def setUp(self):
        """Set up test service."""
        self.mock_client = Mock()
        self.cache = WeatherCache(ttl_seconds=3600)
        self.service = WeatherService(self.mock_client, self.cache)

    def test_get_current_weather_from_api(self):
        """Test fetching current weather from API."""
        mock_weather = CurrentWeather(
            location="London, GB",
            temperature=Decimal("15.0"),
            feels_like=Decimal("14.0"),
            humidity=75,
            pressure=1013,
            description="Cloudy",
            wind_speed=Decimal("5.0"),
            wind_direction=180,
            cloudiness=65,
            visibility=10
        )
        
        self.mock_client.get_current_weather.return_value = mock_weather
        
        result = self.service.get_current_weather("London")
        
        self.assertEqual(result.location, "London, GB")
        self.mock_client.get_current_weather.assert_called_once_with("London")

    def test_get_current_weather_from_cache(self):
        """Test fetching current weather from cache."""
        mock_weather = CurrentWeather(
            location="London, GB",
            temperature=Decimal("15.0"),
            feels_like=Decimal("14.0"),
            humidity=75,
            pressure=1013,
            description="Cloudy",
            wind_speed=Decimal("5.0"),
            wind_direction=180,
            cloudiness=65,
            visibility=10
        )
        
        self.mock_client.get_current_weather.return_value = mock_weather
        
        # First call - from API
        self.service.get_current_weather("London")
        
        # Second call - from cache
        result = self.service.get_current_weather("London")
        
        # Client should only be called once
        self.mock_client.get_current_weather.assert_called_once()
        self.assertEqual(result.location, "London, GB")

    def test_get_forecast_from_api(self):
        """Test fetching forecast from API."""
        now = datetime.now()
        day = ForecastDay(
            date=now,
            max_temp=Decimal("20.0"),
            min_temp=Decimal("15.0"),
            avg_temp=Decimal("17.5"),
            description="Sunny",
            precipitation=Decimal("0.0"),
            precipitation_probability=0,
            humidity=65,
            wind_speed=Decimal("3.0"),
            cloudiness=10
        )
        
        mock_forecast = Forecast(location="London, GB", days=[day])
        self.mock_client.get_forecast.return_value = mock_forecast
        
        result = self.service.get_forecast("London", days=5)
        
        self.assertEqual(result.location, "London, GB")
        self.assertEqual(len(result.days), 1)
        self.mock_client.get_forecast.assert_called_once_with("London", 5)


if __name__ == "__main__":
    unittest.main()
