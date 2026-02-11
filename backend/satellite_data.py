import random

def get_ndvi(latitude, longitude):
    """
    Get NDVI (Normalized Difference Vegetation Index) for given coordinates.
    NDVI range: -1 to 1 (higher is better)
    """
    try:
        # Using a mock API response for demonstration
        # In production, integrate with actual satellite data providers
        # like Sentinel Hub, USGS Earth Explorer, or Google Earth Engine
        
        # Simulating satellite data retrieval
        ndvi_value = round(random.uniform(0.3, 0.9), 2)
        
        return {
            'ndvi': ndvi_value,
            'latitude': latitude,
            'longitude': longitude,
            'status': 'success'
        }
    except Exception as e:
        return {
            'ndvi': 0.0,
            'error': str(e),
            'status': 'error'
        }

def get_satellite_imagery(latitude, longitude, bands=None):
    """
    Get satellite imagery data for visualization
    """
    try:
        imagery_data = {
            'red_band': round(random.uniform(50, 200), 2),
            'green_band': round(random.uniform(50, 200), 2),
            'blue_band': round(random.uniform(50, 200), 2),
            'nir_band': round(random.uniform(100, 250), 2),
        }
        return imagery_data
    except Exception as e:
        return {'error': str(e)}
