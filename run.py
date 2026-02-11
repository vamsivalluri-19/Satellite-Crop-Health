"""
Run script for Crop Health Monitoring System
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Change the imports in app to absolute imports
import backend.app as app_module

if __name__ == '__main__':
    debug_flag = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    port = int(os.getenv('PORT', '5000'))
    app_module.app.run(debug=debug_flag, host='0.0.0.0', port=port)
