"""Flask REST API for weather dashboard."""

from flask import Flask, request, jsonify
from typing import Optional, Tuple
from weather.api_client import OpenWeatherMapClient, WeatherAPIClient, WeatherAPIError
from weather.service import WeatherService
from weather.cache import WeatherCache
from decimal import Decimal


def create_app(api_key: str, provider: str = "openweathermap", cache_dir: Optional[str] = None) -> Flask:
    """
    Create and configure Flask application.
    
    Args:
        api_key: Weather API key
        provider: "openweathermap" or "weatherapi"
        cache_dir: Optional cache directory
    
    Returns:
        Configured Flask app
    """
    app = Flask(__name__)
    
    # Initialize weather service
    if provider.lower() == "openweathermap":
        client = OpenWeatherMapClient(api_key)
    elif provider.lower() == "weatherapi":
        client = WeatherAPIClient(api_key)
    else:
        raise ValueError(f"Unknown provider: {provider}")
    
    cache = WeatherCache(cache_dir=cache_dir, ttl_seconds=3600)
    service = WeatherService(client, cache)
    
    @app.route("/", methods=["GET"])
    def health():
        """Health check endpoint."""
        return jsonify({"status": "ok", "service": "weather-dashboard"}), 200
    
    @app.route("/api/v1/current", methods=["GET"])
    def get_current_weather():
        """
        Get current weather for a location.
        
        Query parameters:
            location: Location name (required)
        
        Returns:
            JSON with current weather data
        """
        location = request.args.get("location")
        if not location:
            return jsonify({"error": "location parameter is required"}), 400
        
        try:
            weather = service.get_current_weather(location)
            return jsonify({
                "location": weather.location,
                "temperature": float(weather.temperature),
                "feels_like": float(weather.feels_like),
                "humidity": weather.humidity,
                "pressure": weather.pressure,
                "description": weather.description,
                "wind_speed": float(weather.wind_speed),
                "wind_direction": weather.wind_direction,
                "cloudiness": weather.cloudiness,
                "visibility": weather.visibility,
                "uv_index": float(weather.uv_index) if weather.uv_index else None,
                "sunrise": weather.sunrise.isoformat() if weather.sunrise else None,
                "sunset": weather.sunset.isoformat() if weather.sunset else None,
                "last_updated": weather.last_updated.isoformat(),
            }), 200
        except WeatherAPIError as e:
            return jsonify({"error": str(e)}), 503
        except Exception as e:
            return jsonify({"error": "Internal server error"}), 500
    
    @app.route("/api/v1/forecast", methods=["GET"])
    def get_forecast():
        """
        Get weather forecast for a location.
        
        Query parameters:
            location: Location name (required)
            days: Number of days (optional, default: 5)
        
        Returns:
            JSON with forecast data
        """
        location = request.args.get("location")
        if not location:
            return jsonify({"error": "location parameter is required"}), 400
        
        days = request.args.get("days", default=5, type=int)
        if days < 1 or days > 16:
            return jsonify({"error": "days must be between 1 and 16"}), 400
        
        try:
            forecast = service.get_forecast(location, days=days)
            return jsonify({
                "location": forecast.location,
                "generated_at": forecast.generated_at.isoformat(),
                "forecast": [
                    {
                        "date": day.date.isoformat(),
                        "max_temp": float(day.max_temp),
                        "min_temp": float(day.min_temp),
                        "avg_temp": float(day.avg_temp),
                        "description": day.description,
                        "precipitation": float(day.precipitation),
                        "precipitation_probability": day.precipitation_probability,
                        "humidity": day.humidity,
                        "wind_speed": float(day.wind_speed),
                        "cloudiness": day.cloudiness,
                        "uv_index": float(day.uv_index) if day.uv_index else None,
                    }
                    for day in forecast.days
                ]
            }), 200
        except WeatherAPIError as e:
            return jsonify({"error": str(e)}), 503
        except Exception as e:
            return jsonify({"error": "Internal server error"}), 500
    
    @app.route("/api/v1/compare", methods=["GET"])
    def compare_locations():
        """
        Compare weather across multiple locations.
        
        Query parameters:
            locations: Comma-separated location names (required)
        
        Returns:
            JSON with comparison data
        """
        locations_param = request.args.get("locations")
        if not locations_param:
            return jsonify({"error": "locations parameter is required"}), 400
        
        locations = [loc.strip() for loc in locations_param.split(",")]
        if len(locations) < 2:
            return jsonify({"error": "at least 2 locations required for comparison"}), 400
        
        results = []
        errors = []
        
        for location in locations:
            try:
                weather = service.get_current_weather(location)
                results.append({
                    "location": weather.location,
                    "temperature": float(weather.temperature),
                    "humidity": weather.humidity,
                    "description": weather.description,
                    "wind_speed": float(weather.wind_speed),
                })
            except WeatherAPIError as e:
                errors.append({"location": location, "error": str(e)})
        
        return jsonify({
            "comparison": results,
            "errors": errors,
        }), 200 if not errors else 206
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return jsonify({"error": "Endpoint not found"}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        return jsonify({"error": "Internal server error"}), 500
    
    return app


if __name__ == "__main__":
    import os
    
    api_key = os.environ.get("WEATHER_API_KEY")
    if not api_key:
        raise ValueError("WEATHER_API_KEY environment variable not set")
    
    app = create_app(api_key, provider="weatherapi")
    app.run(debug=True, host="0.0.0.0", port=5000)
