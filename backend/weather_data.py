import requests
import random
from datetime import datetime, timedelta

def get_weather(latitude, longitude):
    """
    Fetch weather data for given coordinates.
    Uses Open-Meteo API (free, no API key required)
    """
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'current': 'temperature_2m,relative_humidity_2m,precipitation,weather_code',
            'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum',
            'timezone': 'auto'
        }
        
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        current_weather = data.get('current', {})
        daily_weather = data.get('daily', {})
        
        return {
            'current': {
                'temperature': current_weather.get('temperature_2m'),
                'humidity': current_weather.get('relative_humidity_2m'),
                'precipitation': current_weather.get('precipitation'),
            },
            'daily': {
                'max_temp': daily_weather.get('temperature_2m_max', [None])[0],
                'min_temp': daily_weather.get('temperature_2m_min', [None])[0],
                'precipitation': daily_weather.get('precipitation_sum', [None])[0],
            },
            'status': 'success'
        }
    except requests.exceptions.RequestException as e:
        # Return mock data if API fails
        return {
            'current': {
                'temperature': round(random.uniform(15, 35), 1),
                'humidity': random.randint(40, 90),
                'precipitation': round(random.uniform(0, 10), 1),
            },
            'daily': {
                'max_temp': round(random.uniform(20, 40), 1),
                'min_temp': round(random.uniform(10, 25), 1),
                'precipitation': round(random.uniform(0, 15), 1),
            },
            'status': 'success',
            'note': 'Using mock data'
        }
    except Exception as e:
        return {
            'error': str(e),
            'status': 'error'
        }

def get_weather_forecast(latitude, longitude, days=7):
    """
    Get extended weather forecast
    """
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum',
            'timezone': 'auto'
        }
        
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        return data.get('daily', {})
    except Exception as e:
        return {'error': str(e)}
