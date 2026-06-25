# Weather Dashboard

A comprehensive weather dashboard application that fetches real-time weather data from public APIs with caching, CLI interface, and REST API.

## Features

✅ **Multiple API Providers**
- OpenWeatherMap API integration
- WeatherAPI.com integration

✅ **Smart Caching**
- In-memory cache with configurable TTL
- Optional file-based persistent cache
- Automatic cache expiration

✅ **Command Line Interface**
- Get current weather for any location
- View 5-16 day forecasts
- Compare weather across multiple locations
- Formatted terminal output

✅ **REST API**
- Flask-based REST API
- JSON responses
- Current weather endpoint
- Forecast endpoint
- Location comparison endpoint

✅ **Data Models**
- Type-safe weather data models
- Decimal precision for temperatures
- Comprehensive weather attributes

✅ **Error Handling**
- Custom exceptions for API errors
- Graceful error handling
- Helpful error messages

## Installation

```bash
pip install requests flask
```

## Configuration

### API Keys

You'll need an API key from one of these services:

1. **OpenWeatherMap** - https://openweathermap.org/api
   - Sign up for a free account
   - Generate API key from settings

2. **WeatherAPI.com** - https://www.weatherapi.com/
   - Sign up for free tier
   - API key available immediately

## Usage

### Command Line Interface

#### Get Current Weather

```bash
python -m weather.cli --api-key YOUR_API_KEY current London
```

#### Get Weather Forecast

```bash
python -m weather.cli --api-key YOUR_API_KEY forecast "New York" --days 7
```

#### Compare Weather Across Locations

```bash
python -m weather.cli --api-key YOUR_API_KEY compare London Paris Tokyo
```

#### Using Different Provider

```bash
python -m weather.cli --api-key YOUR_API_KEY --provider weatherapi current London
```

#### With Caching

```bash
python -m weather.cli --api-key YOUR_API_KEY --cache-dir /tmp/weather current London
```

### Python API

```python
from weather.api_client import WeatherAPIClient
from weather.service import WeatherService
from weather.cache import WeatherCache

# Initialize
client = WeatherAPIClient(api_key="your_api_key")
cache = WeatherCache(cache_dir="/tmp/weather_cache")
service = WeatherService(client, cache)

# Get current weather
weather = service.get_current_weather("London")
print(f"Temperature: {weather.temperature}°C")
print(f"Conditions: {weather.description}")

# Get forecast
forecast = service.get_forecast("London", days=5)
for day in forecast.days:
    print(f"{day.date}: {day.description} ({day.min_temp}°C - {day.max_temp}°C)")
```

### REST API

#### Start Server

```bash
export WEATHER_API_KEY="your_api_key"
python -m weather.flask_app
```

Server will run on `http://localhost:5000`

#### Get Current Weather

```bash
curl "http://localhost:5000/api/v1/current?location=London"
```

**Response:**

```json
{
  "location": "London, GB",
  "temperature": 15.5,
  "feels_like": 14.0,
  "humidity": 75,
  "pressure": 1013,
  "description": "Cloudy",
  "wind_speed": 5.2,
  "wind_direction": 180,
  "cloudiness": 65,
  "visibility": 10,
  "uv_index": 3.5,
  "sunrise": "2024-01-15T07:30:00",
  "sunset": "2024-01-15T17:45:00",
  "last_updated": "2024-01-15T12:00:00"
}
```

#### Get Forecast

```bash
curl "http://localhost:5000/api/v1/forecast?location=London&days=5"
```

#### Compare Locations

```bash
curl "http://localhost:5000/api/v1/compare?locations=London,Paris,Tokyo"
```

## File Structure

```
weather/
├── __init__.py              # Package exports
├── models.py                # Data models (CurrentWeather, Forecast, etc.)
├── api_client.py            # API client implementations
├── cache.py                 # Caching layer
├── service.py               # High-level weather service
├── cli.py                   # Command-line interface
└── flask_app.py             # REST API (Flask)

tests/
├── __init__.py
├── test_models.py           # Model tests
├── test_cache.py            # Cache tests
└── test_service.py          # Service tests
```

## Running Tests

```bash
python -m pytest tests/

# Or with unittest
python -m unittest discover tests
```

## Data Models

### CurrentWeather

```python
@dataclass
class CurrentWeather:
    location: str                    # e.g., "London, GB"
    temperature: Decimal             # in Celsius
    feels_like: Decimal              # perceived temperature
    humidity: int                    # 0-100%
    pressure: int                    # in hPa
    description: str                 # e.g., "Cloudy"
    wind_speed: Decimal              # in m/s
    wind_direction: int              # 0-360 degrees
    cloudiness: int                  # 0-100%
    visibility: int                  # in km
    uv_index: Optional[Decimal]      # 0-11+
    sunrise: Optional[datetime]      # sunrise time
    sunset: Optional[datetime]       # sunset time
    last_updated: datetime           # when data was fetched
```

### ForecastDay

```python
@dataclass
class ForecastDay:
    date: datetime                   # forecast date
    max_temp: Decimal                # maximum temperature
    min_temp: Decimal                # minimum temperature
    avg_temp: Decimal                # average temperature
    description: str                 # weather description
    precipitation: Decimal           # in mm
    precipitation_probability: int   # 0-100%
    humidity: int                    # 0-100%
    wind_speed: Decimal              # in m/s
    cloudiness: int                  # 0-100%
    uv_index: Optional[Decimal]      # UV index
```

## Caching Strategy

The weather dashboard uses a two-tier caching strategy:

1. **In-Memory Cache**
   - Fastest access
   - Per-process (not shared between processes)
   - Lost on restart

2. **File-Based Cache** (optional)
   - Persistent across restarts
   - JSON format
   - Configurable directory
   - Useful for background jobs

**Cache TTL** (Time To Live):
- Default: 3600 seconds (1 hour)
- Configurable per use case
- Expired entries are automatically cleaned up

## Error Handling

The service handles various error scenarios:

```python
from weather.api_client import WeatherAPIError

try:
    weather = service.get_current_weather("InvalidLocation")
except WeatherAPIError as e:
    print(f"Weather API Error: {e}")
```

## Performance Considerations

- **API Rate Limiting**: Check your API provider's rate limits
- **Cache Duration**: Increase TTL for less frequent updates
- **Concurrent Requests**: File cache is thread-safe
- **File Operations**: Cache directory I/O may be slow on network drives

## Future Enhancements

- [ ] Webhook support for real-time updates
- [ ] Database backend for historical data
- [ ] Advanced visualization dashboard
- [ ] Weather alerts and notifications
- [ ] Multi-language support
- [ ] Weather data export (CSV, PDF)
- [ ] Machine learning-based predictions
- [ ] Integration with home automation systems

## License

MIT
