"""Command-line interface for the weather dashboard."""

import argparse
import sys
from typing import Optional
from weather.api_client import OpenWeatherMapClient, WeatherAPIClient, WeatherAPIError
from weather.service import WeatherService
from weather.cache import WeatherCache


class WeatherCLI:
    """CLI for weather dashboard."""

    def __init__(self, api_key: str, provider: str = "openweathermap", cache_dir: Optional[str] = None):
        """
        Initialize weather CLI.
        
        Args:
            api_key: API key for weather service
            provider: "openweathermap" or "weatherapi"
            cache_dir: Optional cache directory
        """
        if provider.lower() == "openweathermap":
            client = OpenWeatherMapClient(api_key)
        elif provider.lower() == "weatherapi":
            client = WeatherAPIClient(api_key)
        else:
            raise ValueError(f"Unknown provider: {provider}")
        
        cache = WeatherCache(cache_dir=cache_dir, ttl_seconds=3600)
        self.service = WeatherService(client, cache)

    def get_current(self, location: str, verbose: bool = False) -> None:
        """Get and display current weather."""
        try:
            weather = self.service.get_current_weather(location)
            print(f"\n{'='*60}")
            print(f"Current Weather: {weather.location}")
            print(f"{'='*60}")
            print(f"Temperature:    {weather.temperature}°C (feels like {weather.feels_like}°C)")
            print(f"Conditions:     {weather.description}")
            print(f"Humidity:       {weather.humidity}%")
            print(f"Pressure:       {weather.pressure} hPa")
            print(f"Wind Speed:     {weather.wind_speed} m/s (direction: {weather.wind_direction}°)")
            print(f"Cloudiness:     {weather.cloudiness}%")
            print(f"Visibility:     {weather.visibility} km")
            
            if weather.uv_index is not None:
                print(f"UV Index:       {weather.uv_index}")
            
            if weather.sunrise:
                print(f"Sunrise:        {weather.sunrise.strftime('%H:%M:%S')}")
            
            if weather.sunset:
                print(f"Sunset:         {weather.sunset.strftime('%H:%M:%S')}")
            
            print(f"{'='*60}\n")
        except WeatherAPIError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    def get_forecast(self, location: str, days: int = 5, verbose: bool = False) -> None:
        """Get and display weather forecast."""
        try:
            forecast = self.service.get_forecast(location, days=days)
            print(f"\n{'='*70}")
            print(f"Weather Forecast: {forecast.location}")
            print(f"{'='*70}\n")
            
            for day in forecast.days:
                print(f"Date: {day.date.strftime('%A, %Y-%m-%d')}")
                print(f"  Conditions:     {day.description}")
                print(f"  Temperature:    {day.min_temp}°C - {day.max_temp}°C (avg: {day.avg_temp}°C)")
                print(f"  Precipitation:  {day.precipitation}mm (probability: {day.precipitation_probability}%)")
                print(f"  Humidity:       {day.humidity}%")
                print(f"  Wind Speed:     {day.wind_speed} m/s")
                print(f"  Cloudiness:     {day.cloudiness}%")
                
                if day.uv_index is not None:
                    print(f"  UV Index:       {day.uv_index}")
                
                print()
            
            print(f"{'='*70}\n")
        except WeatherAPIError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    def compare_locations(self, locations: list) -> None:
        """Compare weather across multiple locations."""
        print(f"\n{'='*80}")
        print(f"Weather Comparison")
        print(f"{'='*80}")
        print(f"{'Location':<25} {'Temp':<12} {'Conditions':<25} {'Humidity':<12}")
        print(f"{'-'*80}")
        
        for location in locations:
            try:
                weather = self.service.get_current_weather(location)
                loc_name = weather.location[:25]
                temp = f"{weather.temperature}°C"
                conditions = weather.description[:25]
                humidity = f"{weather.humidity}%"
                print(f"{loc_name:<25} {temp:<12} {conditions:<25} {humidity:<12}")
            except WeatherAPIError as e:
                print(f"{location[:25]:<25} Error fetching data", file=sys.stderr)
        
        print(f"{'='*80}\n")


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Weather Dashboard - Fetch weather data from public APIs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  %(prog)s current London
  %(prog)s forecast New York --days 7
  %(prog)s compare London Paris Tokyo
        """
    )
    
    parser.add_argument(
        "--api-key",
        required=True,
        help="API key for weather service"
    )
    parser.add_argument(
        "--provider",
        default="openweathermap",
        choices=["openweathermap", "weatherapi"],
        help="Weather service provider (default: openweathermap)"
    )
    parser.add_argument(
        "--cache-dir",
        help="Cache directory for weather data"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Current weather command
    current_parser = subparsers.add_parser("current", help="Get current weather")
    current_parser.add_argument("location", help="Location name")
    current_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    # Forecast command
    forecast_parser = subparsers.add_parser("forecast", help="Get weather forecast")
    forecast_parser.add_argument("location", help="Location name")
    forecast_parser.add_argument("--days", type=int, default=5, help="Number of days (default: 5)")
    forecast_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Compare weather across locations")
    compare_parser.add_argument("locations", nargs="+", help="Locations to compare")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Initialize CLI
    cli = WeatherCLI(
        api_key=args.api_key,
        provider=args.provider,
        cache_dir=args.cache_dir
    )
    
    # Execute command
    if args.command == "current":
        cli.get_current(args.location, verbose=args.verbose)
    elif args.command == "forecast":
        cli.get_forecast(args.location, days=args.days, verbose=args.verbose)
    elif args.command == "compare":
        cli.compare_locations(args.locations)


if __name__ == "__main__":
    main()
