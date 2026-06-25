"""Tests for weather models."""

import unittest
from decimal import Decimal
from datetime import datetime
from weather.models import CurrentWeather, ForecastDay, Forecast, PositionSnapshot


class TestCurrentWeather(unittest.TestCase):
    """Test CurrentWeather model."""

    def test_current_weather_creation(self):
        """Test creating CurrentWeather instance."""
        weather = CurrentWeather(
            location="London, GB",
            temperature=Decimal("15.5"),
            feels_like=Decimal("14.0"),
            humidity=75,
            pressure=1013,
            description="Cloudy",
            wind_speed=Decimal("5.2"),
            wind_direction=180,
            cloudiness=65,
            visibility=10
        )
        
        self.assertEqual(weather.location, "London, GB")
        self.assertEqual(weather.temperature, Decimal("15.5"))
        self.assertEqual(weather.humidity, 75)
        self.assertIsNotNone(weather.last_updated)

    def test_current_weather_string_representation(self):
        """Test string representation of CurrentWeather."""
        weather = CurrentWeather(
            location="Paris, FR",
            temperature=Decimal("18.0"),
            feels_like=Decimal("17.5"),
            humidity=60,
            pressure=1013,
            description="Sunny",
            wind_speed=Decimal("3.0"),
            wind_direction=90,
            cloudiness=20,
            visibility=15
        )
        
        weather_str = str(weather)
        self.assertIn("Paris, FR", weather_str)
        self.assertIn("18.0", weather_str)
        self.assertIn("Sunny", weather_str)


class TestForecastDay(unittest.TestCase):
    """Test ForecastDay model."""

    def test_forecast_day_creation(self):
        """Test creating ForecastDay instance."""
        now = datetime.now()
        day = ForecastDay(
            date=now,
            max_temp=Decimal("20.0"),
            min_temp=Decimal("15.0"),
            avg_temp=Decimal("17.5"),
            description="Partly Cloudy",
            precipitation=Decimal("2.5"),
            precipitation_probability=30,
            humidity=70,
            wind_speed=Decimal("4.5"),
            cloudiness=50
        )
        
        self.assertEqual(day.max_temp, Decimal("20.0"))
        self.assertEqual(day.min_temp, Decimal("15.0"))
        self.assertEqual(day.precipitation_probability, 30)

    def test_forecast_day_string_representation(self):
        """Test string representation of ForecastDay."""
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
        
        day_str = str(day)
        self.assertIn("20.0", day_str)
        self.assertIn("15.0", day_str)
        self.assertIn("Sunny", day_str)


class TestForecast(unittest.TestCase):
    """Test Forecast model."""

    def test_forecast_creation(self):
        """Test creating Forecast instance."""
        now = datetime.now()
        days = [
            ForecastDay(
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
        ]
        
        forecast = Forecast(location="London, GB", days=days)
        
        self.assertEqual(forecast.location, "London, GB")
        self.assertEqual(len(forecast.days), 1)
        self.assertIsNotNone(forecast.generated_at)


if __name__ == "__main__":
    unittest.main()
