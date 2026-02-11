from flask import Flask, request, jsonify, render_template, send_from_directory, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
import os
from datetime import datetime, timedelta
import logging
import hashlib
import secrets
import json

# Use relative imports for backend modules
from .satellite_data import get_ndvi, get_satellite_imagery
from .weather_data import get_weather, get_weather_forecast
from .ai_model import predict_disease, get_health_score
from .alerts import send_disease_alert, send_health_alert

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app with proper template folder configuration
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'static', 'templates'))
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'static'))

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

# Enable CORS for all routes
CORS(app, resources={r"/*": {"origins": "*", "supports_credentials": True}})

# Configure Session
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Configure Database
db_dir = os.path.join(os.path.dirname(__file__), 'database')
os.makedirs(db_dir, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_dir}/crop_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    location = db.Column(db.String(200))
    phone = db.Column(db.String(15))
    crop_type = db.Column(db.String(100))
    field_area = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    def check_password(self, password):
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'location': self.location,
            'phone': self.phone,
            'crop_type': self.crop_type,
            'field_area': self.field_area,
            'created_at': self.created_at.isoformat()
        }

class CropData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    ndvi = db.Column(db.Float)
    health_status = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class DiseaseRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False)
    disease = db.Column(db.String(100))
    confidence = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Initialize Database
with app.app_context():
    try:
        reset_db = os.getenv('RESET_DB', 'false').lower() == 'true'

        if reset_db:
            db.drop_all()

        db.create_all()

        demo_exists = User.query.filter_by(username='demo').first() is not None
        if reset_db or not demo_exists:
            demo_user = User(
                username='demo',
                email='demo@farm.com',
                first_name='Demo',
                last_name='Farmer',
                crop_type='Wheat'
            )
            demo_user.set_password('demo123')
            db.session.add(demo_user)
            db.session.commit()

            logger.info("✅ Demo user created - Username: demo, Password: demo123")

        logger.info("✅ Database initialized successfully")
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Database initialization error: {e}")

# Routes

@app.route('/')
def home():
    """Serve the main HTML page"""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error loading index.html: {e}")
        return jsonify({'error': 'Failed to load page'}), 500

@app.route('/static/<path:path>')
def send_static(path):
    """Serve static files"""
    return send_from_directory(static_dir, path)

@app.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    return '', 204

@app.route('/health', methods=['GET'])
def health_check():
    """API health check endpoint"""
    return jsonify({
        'status': 'online',
        'service': 'Crop Health Monitoring System',
        'version': '1.0',
        'timestamp': datetime.utcnow().isoformat()
    })

# Authentication Routes

@app.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        if not data or not all(k in data for k in ['username', 'email', 'password']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        username = data.get('username').strip()
        email = data.get('email').strip()
        password = data.get('password')
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        
        if not username or not email or not password:
            return jsonify({'error': 'Username, email, and password cannot be empty'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already registered'}), 400
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        logger.info(f"✅ New user registered: {username}")
        
        return jsonify({
            'status': 'success',
            'message': 'Registration successful!',
            'user': new_user.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Registration error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Missing username or password'}), 400
        
        username = data.get('username').strip()
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid username or password'}), 401
        
        session['user_id'] = user.id
        session['username'] = user.username
        session.permanent = True
        app.permanent_session_lifetime = timedelta(days=30)
        
        logger.info(f"✅ User logged in: {username}")
        
        return jsonify({
            'status': 'success',
            'message': 'Login successful!',
            'user': user.to_dict()
        }), 200
    
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/logout', methods=['POST'])
def logout():
    """Logout user"""
    try:
        username = session.get('username')
        session.clear()
        logger.info(f"✅ User logged out: {username}")
        return jsonify({'status': 'success', 'message': 'Logout successful'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/session', methods=['GET'])
def check_session():
    """Check if user is logged in"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'status': 'not_authenticated', 'logged_in': False}), 200
        
        user = User.query.get(user_id)
        if not user:
            session.clear()
            return jsonify({'status': 'not_authenticated', 'logged_in': False}), 200
        
        return jsonify({
            'status': 'authenticated',
            'logged_in': True,
            'user': user.to_dict()
        }), 200
    
    except Exception as e:
        logger.error(f"Session check error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/profile', methods=['GET', 'PUT'])
def profile():
    """Get or update user profile"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if request.method == 'GET':
            return jsonify({
                'status': 'success',
                'user': user.to_dict()
            }), 200
        
        # PUT - Update profile
        data = request.get_json()
        
        if 'first_name' in data:
            user.first_name = data['first_name'].strip()
        if 'last_name' in data:
            user.last_name = data['last_name'].strip()
        if 'location' in data:
            user.location = data['location'].strip()
        if 'phone' in data:
            user.phone = data['phone'].strip()
        if 'crop_type' in data:
            user.crop_type = data['crop_type'].strip()
        if 'field_area' in data:
            user.field_area = float(data['field_area'])
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"✅ Profile updated: {user.username}")
        
        return jsonify({
            'status': 'success',
            'message': 'Profile updated!',
            'user': user.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Profile error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/ndvi', methods=['POST'])
def get_crop_health():
    """Get NDVI and crop health status"""
    try:
        data = request.get_json()
        
        if not data or 'latitude' not in data or 'longitude' not in data:
            return jsonify({'error': 'Missing required fields: latitude, longitude'}), 400
        
        latitude = float(data.get('latitude'))
        longitude = float(data.get('longitude'))
        email = data.get('email', 'unknown@example.com')
        
        # Get NDVI data
        ndvi_result = get_ndvi(latitude, longitude)
        
        if ndvi_result.get('status') != 'success':
            return jsonify(ndvi_result), 500
        
        ndvi_value = ndvi_result.get('ndvi', 0)
        
        # Get health score
        health_info = get_health_score(ndvi_value)
        
        # Save to database
        try:
            crop_data = CropData(
                email=email,
                latitude=latitude,
                longitude=longitude,
                ndvi=ndvi_value,
                health_status=health_info.get('score')
            )
            db.session.add(crop_data)
            db.session.commit()
        except Exception as e:
            logger.warning(f"Could not save to database: {e}")
            db.session.rollback()
        
        # Send alert if health is poor
        if ndvi_value < 0.2 and email != 'unknown@example.com':
            try:
                send_health_alert(health_info.get('score'), ndvi_value, email)
            except Exception as e:
                logger.warning(f"Could not send alert: {e}")
        
        return jsonify({
            'status': 'success',
            'ndvi': ndvi_value,
            'latitude': latitude,
            'longitude': longitude,
            'health': health_info
        })
    
    except ValueError as e:
        return jsonify({'error': f'Invalid input: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error in get_crop_health: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/weather', methods=['GET'])
def weather():
    """Get weather data"""
    try:
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        
        if not lat or not lon:
            return jsonify({'error': 'Missing required parameters: lat, lon'}), 400
        
        weather_data = get_weather(float(lat), float(lon))
        
        if weather_data.get('status') != 'success':
            return jsonify(weather_data), 500
        
        return jsonify(weather_data)
    
    except ValueError as e:
        return jsonify({'error': f'Invalid input: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error in weather: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/weather/forecast', methods=['GET'])
def weather_forecast():
    """Get weather forecast"""
    try:
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        days = request.args.get('days', 7, type=int)
        
        if not lat or not lon:
            return jsonify({'error': 'Missing required parameters: lat, lon'}), 400
        
        forecast_data = get_weather_forecast(float(lat), float(lon), days)
        return jsonify({'status': 'success', 'forecast': forecast_data})
    
    except ValueError as e:
        return jsonify({'error': f'Invalid input: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error in weather_forecast: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/predict', methods=['POST'])
def predict():
    """Predict crop disease from image"""
    try:
        data = request.get_json()
        
        if not data or 'image' not in data:
            return jsonify({'error': 'Missing required field: image'}), 400
        
        email = data.get('email', 'unknown@example.com')
        image_data = data.get('image')
        
        # Predict disease
        prediction = predict_disease(image_data)
        
        if prediction.get('status') != 'success':
            return jsonify(prediction), 500
        
        # Save to database
        try:
            disease_record = DiseaseRecord(
                email=email,
                disease=prediction.get('disease'),
                confidence=prediction.get('confidence')
            )
            db.session.add(disease_record)
            db.session.commit()
        except Exception as e:
            logger.warning(f"Could not save disease record: {e}")
            db.session.rollback()
        
        # Send alert if disease detected and email is valid
        if prediction.get('disease') != 'Healthy' and email != 'unknown@example.com':
            try:
                send_disease_alert(
                    prediction.get('disease'),
                    prediction.get('confidence'),
                    email
                )
            except Exception as e:
                logger.warning(f"Could not send disease alert: {e}")
        
        return jsonify(prediction)
    
    except Exception as e:
        logger.error(f"Error in predict: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/satellite', methods=['GET'])
def satellite():
    """Get satellite imagery data"""
    try:
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        
        if not lat or not lon:
            return jsonify({'error': 'Missing required parameters: lat, lon'}), 400
        
        imagery = get_satellite_imagery(float(lat), float(lon))
        return jsonify({'status': 'success', 'imagery': imagery})
    
    except ValueError as e:
        return jsonify({'error': f'Invalid input: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error in satellite: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/history', methods=['GET'])
def history():
    """Get user's crop data history"""
    try:
        email = request.args.get('email')
        
        if not email:
            return jsonify({'error': 'Missing required parameter: email'}), 400
        
        crop_records = CropData.query.filter_by(email=email).order_by(CropData.timestamp.desc()).all()
        disease_records = DiseaseRecord.query.filter_by(email=email).order_by(DiseaseRecord.timestamp.desc()).all()
        
        return jsonify({
            'status': 'success',
            'crop_data': [{
                'id': r.id,
                'ndvi': r.ndvi,
                'health_status': r.health_status,
                'latitude': r.latitude,
                'longitude': r.longitude,
                'timestamp': r.timestamp.isoformat()
            } for r in crop_records],
            'disease_records': [{
                'id': r.id,
                'disease': r.disease,
                'confidence': r.confidence,
                'timestamp': r.timestamp.isoformat()
            } for r in disease_records]
        })
    
    except Exception as e:
        logger.error(f"Error in history: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== CROP RECOMMENDATIONS ====================

@app.route('/crop-database', methods=['GET'])
def crop_database():
    """Get crop database with all available crops"""
    crops = {
        'Wheat': {
            'season': 'Winter',
            'ideal_temp': '15-25°C',
            'water_needed': '400-500mm',
            'soil_type': 'Well-drained loam',
            'ph_level': '6.0-7.5',
            'duration': '120-150 days',
            'yield': '4-5 tons/hectare',
            'benefits': 'High protein, long shelf-life, global demand',
            'spacing': '20x10 cm, 150-200 plants/m²'
        },
        'Rice': {
            'season': 'Summer/Monsoon',
            'ideal_temp': '20-30°C',
            'water_needed': '1000-1500mm',
            'soil_type': 'Clay/clayey loam',
            'ph_level': '5.5-7.5',
            'duration': '90-150 days',
            'yield': '4-6 tons/hectare',
            'benefits': 'High yield, stable crop, good market value',
            'spacing': '20x15 cm, planting 2-3 seedlings per hill'
        },
        'Maize': {
            'season': 'Spring/Summer',
            'ideal_temp': '21-27°C',
            'water_needed': '500-800mm',
            'soil_type': 'Well-drained loam',
            'ph_level': '5.5-7.0',
            'duration': '90-120 days',
            'yield': '5-8 tons/hectare',
            'benefits': 'Multiple uses (grain, fodder, silage), export crop',
            'spacing': '60x25 cm, 60-75 plants/m²'
        },
        'Cotton': {
            'season': 'Spring',
            'ideal_temp': '21-30°C',
            'water_needed': '500-750mm',
            'soil_type': 'Well-drained black soil',
            'ph_level': '6.0-7.5',
            'duration': '160-180 days',
            'yield': '1.5-2.5 tons/hectare',
            'benefits': 'High value crop, multiple byproducts',
            'spacing': '100-120 cm rows, 60-75 cm in row'
        },
        'Sugarcane': {
            'season': 'Year-round',
            'ideal_temp': '20-30°C',
            'water_needed': '1200-1500mm',
            'soil_type': 'Deep loam/clay loam',
            'ph_level': '5.5-8.0',
            'duration': '10-12 months',
            'yield': '50-60 tons/hectare',
            'benefits': 'High cash crop, by-products value, long season',
            'spacing': '75-100 cm row, 2 buds per sett'
        },
        'Soybean': {
            'season': 'Summer',
            'ideal_temp': '20-30°C',
            'water_needed': '450-650mm',
            'soil_type': 'Well-drained loam',
            'ph_level': '6.0-7.5',
            'duration': '90-110 days',
            'yield': '2-3 tons/hectare',
            'benefits': 'High protein, nitrogen fixation, export value',
            'spacing': '45x15 cm, 50-60 plants/m²'
        },
        'Tomato': {
            'season': 'Spring/Fall',
            'ideal_temp': '20-25°C',
            'water_needed': '400-600mm',
            'soil_type': 'Well-drained fertile loam',
            'ph_level': '6.0-6.8',
            'duration': '70-85 days',
            'yield': '30-50 tons/hectare',
            'benefits': 'High market value, multiple harvests, processing use',
            'spacing': '60x45 cm, staked system'
        },
        'Potato': {
            'season': 'Winter/Spring',
            'ideal_temp': '15-20°C',
            'water_needed': '400-600mm',
            'soil_type': 'Loose well-drained soil',
            'ph_level': '5.5-7.0',
            'duration': '70-90 days',
            'yield': '20-30 tons/hectare',
            'benefits': 'High nutritive value, staple food, fast returns',
            'spacing': '60x20 cm, 75cm rows'
        }
    }
    
    return jsonify({'status': 'success', 'crops': crops})

@app.route('/crop-recommendations', methods=['POST'])
def crop_recommendations():
    """Get crop recommendations based on location and climate"""
    try:
        data = request.get_json()
        latitude = float(data.get('latitude', 0))
        longitude = float(data.get('longitude', 0))
        
        # Determine recommendations based on latitude
        if latitude < 10:
            suitable_crops = ['Rice', 'Sugarcane', 'Cotton', 'Maize']
        elif latitude < 20:
            suitable_crops = ['Wheat', 'Maize', 'Cotton', 'Soybean']
        elif latitude < 30:
            suitable_crops = ['Wheat', 'Maize', 'Potato', 'Soybean']
        else:
            suitable_crops = ['Wheat', 'Potato', 'Barley', 'Maize']
        
        return jsonify({
            'status': 'success',
            'location': {'latitude': latitude, 'longitude': longitude},
            'suitable_crops': suitable_crops,
            'recommendation': f'Based on your location, we recommend growing {", ".join(suitable_crops[:-1])} or {suitable_crops[-1]}.'
        })
    
    except Exception as e:
        logger.error(f"Error in crop_recommendations: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/maintenance-guide/<crop_name>', methods=['GET'])
def maintenance_guide(crop_name):
    """Get crop maintenance guide"""
    try:
        guides = {
            'Wheat': {
                'name': 'Wheat',
                'stages': [
                    {'stage': 'Seedling (0-30 days)', 'care': 'Maintain soil moisture at 60-70%, protect seedlings from birds, thin excess shoots for 150-200 plants/m²'},
                    {'stage': 'Tillering (30-70 days)', 'care': 'First nitrogen split of 50kg/ha, first irrigation if no rain, control Phalaris and Avena weeds'},
                    {'stage': 'Heading (70-100 days)', 'care': 'Second nitrogen split 50kg/ha, second irrigation, monitor for rust diseases, spray fungicide if needed'},
                    {'stage': 'Grain maturation (100-150 days)', 'care': 'Third irrigation, reduce water gradually, monitor for grain maturity (hard dough stage), prepare harvesting equipment'}
                ],
                'fertilizer': 'NPK 120:60:40 kg/hectare spread in 3 splits: Basal, Tillering, Heading',
                'irrigation': '3-4 irrigations: CRI (Crown Root Initiation), Tillering, Heading, Grain filling',
                'pests_diseases': ['Stem rust (cover with sulfur spray)', 'Leaf rust (use Propiconazole)', 'Powdery mildew (spray Wettable Sulfur)', 'Armyworm (use Bt spray)'],
                'harvest_time': '140-150 days, Harvest at moisture 12-14%'
            },
            'Rice': {
                'name': 'Rice',
                'stages': [
                    {'stage': 'Nursery (30-40 days)', 'care': 'Keep seedbed flooded 5cm, apply 8kg NPK per 100m², watch for blast disease on leaves'},
                    {'stage': 'Transplanting (40-60 days)', 'care': 'Maintain 5-10cm standing water, apply first dose nitrogen, transplant 2-3 seedlings per hill'},
                    {'stage': 'Vegetative (60-90 days)', 'care': 'Keep field continuously flooded, second nitrogen application at 45 days, remove weeds manually'},
                    {'stage': 'Reproductive (90-150 days)', 'care': 'Maintain water for grain filling, third nitrogen at 70 days, monitor for stem borer, drain at maturity'}
                ],
                'fertilizer': 'NPK 120:60:60 kg/hectare in 3 splits: Transplanting, 45 days, 70 days',
                'irrigation': 'Continuous flooding except for draining 7-10 days before harvest',
                'pests_diseases': ['Blast disease (spray Tricyclazole)', 'Brown spot (use Carbendazim)', 'Stem borer (pheromone trap)', 'Leafhopper (spray Imidacloprid)'],
                'harvest_time': '120-150 days, Harvest when 70% grains turned golden yellow'
            },
            'Maize': {
                'name': 'Maize',
                'stages': [
                    {'stage': 'Vegetation (0-30 days)', 'care': 'Thin to 50-60 plants/m² at 4 leaves stage, apply herbicide for weed control, light irrigation'},
                    {'stage': 'Vegetative (30-60 days)', 'care': 'First nitrogen split 75kg/ha, first earthing-up, second irrigation, remove lower leaves for ventilation'},
                    {'stage': 'Reproductive (60-100 days)', 'care': 'Second nitrogen split 75kg/ha at tassel emergence, third irrigation critical during silking, monitor pollen shed'},
                    {'stage': 'Maturation (100-120 days)', 'care': 'Reduce water gradually, allow cob to dry, monitor for physiological maturity, prepare for harvest'}
                ],
                'fertilizer': 'NPK 150:75:75 kg/hectare spread in 2-3 splits: Basal, 30 days, 60 days',
                'irrigation': '3-4 irrigations with critical irrigation at tasseling and silking stages',
                'pests_diseases': ['Armyworm (spray Chlorpyrifos)', 'Stem borer (release parasitoid)', 'Turcicum leaf blight (spray Mancozeb)', 'Rust (remove affected leaves)'],
                'harvest_time': '120-130 days at 20-25% grain moisture'
            },
            'Cotton': {
                'name': 'Cotton',
                'stages': [
                    {'stage': 'Seedling (0-45 days)', 'care': 'Thin to 1 plant per hill (60-75cm spacing), light irrigation to maintain 60-70% soil moisture, mulch to retain moisture'},
                    {'stage': 'Vegetative (45-90 days)', 'care': 'Heavy irrigation 8-10cm water, apply nitrogen 60kg/ha at 45 days, topping at 80-90 days, remove lower leaves at 90 days'},
                    {'stage': 'Flowering (90-140 days)', 'care': 'Critical water period, maintain 15cm soil moisture, apply potassium 60kg/ha, open bolls inspection, pesticide spray weekly'},
                    {'stage': 'Boll maturation (140-180 days)', 'care': 'Reduce irrigation, apply harvest aid at 85% boll opening, defoliate mechanically/chemically, begin picking'}
                ],
                'fertilizer': 'NPK 120:60:90 kg/hectare: 60kg N+P at 45 days, 60kg N+60kg K at 90 days',
                'irrigation': '10-12 flood/furrow irrigations with emphasis on flowering to boll opening',
                'pests_diseases': ['Bollworm (spray Bt-cotton approved insecticide)', 'Jassid (use Yellow sticky traps)', 'Whitefly (spray Neem oil)', 'Bacterial blight (remove infected plants)'],
                'harvest_time': '160-180 days, Stagger picking for 4-5 weeks'
            },
            'Potato': {
                'name': 'Potato',
                'stages': [
                    {'stage': 'Sprouting (0-15 days)', 'care': 'Soil temperature 15-16°C optimal, light irrigation 25-30mm, cover seed pieces with 5cm soil to prevent greening'},
                    {'stage': 'Growth (15-45 days)', 'care': 'First ridging at 30 days with 150kg/ha nitrogen, two irrigations of 50-60mm each, monitor for early blight'},
                    {'stage': 'Tuber formation (45-75 days)', 'care': 'THIS IS CRITICAL: consistent water 60-70mm bi-weekly, second nitrogen 150kg/ha, fungicide spray for late blight'},
                    {'stage': 'Maturation (75-90 days)', 'care': 'Reduce irrigation gradually, top-dressing cease, allow skins to harden, harvest when 80% soil removed tubers visible'}
                ],
                'fertilizer': 'NPK 60:120:120 kg/hectare: 150kg N (3 splits), full P+K basal, plus 40kg/ha MgSO4',
                'irrigation': 'Sprinkler preferred, 4-6 irrigations of 50-60mm at 10-15 days interval',
                'pests_diseases': ['Late blight (spray Mancozeb or Metalaxyl)', 'Early blight (spray Chlorothalonil)', 'Wireworm (use Carbofuran)', 'Aphids (spray Imidacloprid)'],
                'harvest_time': '70-90 days depending on variety, Harvest at 12-14% soil moisture'
            },
            'Tomato': {
                'name': 'Tomato',
                'stages': [
                    {'stage': 'Seedling (0-30 days)', 'care': 'Controlled greenhouse at 20-25°C, maintain 60-70% humidity, water mist 2-3 times daily, shade if needed'},
                    {'stage': 'Transplanting (30-45 days)', 'care': 'Harden seedlings gradually, transplant at 45 days (4-5 true leaves), spacing 60x45cm, mulch immediately'},
                    {'stage': 'Flowering (45-60 days)', 'care': 'Install support structure/staking, prune lower leaves, remove suckers, nutrient spray (B+Zn), bee activity check'},
                    {'stage': 'Fruiting (60-85 days)', 'care': 'Regular drip irrigation (5-6cm water weekly), harvest when breaker stage color shows, continue picking for 8-10 weeks'}
                ],
                'fertilizer': 'NPK 100:150:100 kg/hectare: Full P+K basal, N split in 4-5 doses at 15-20 days interval',
                'irrigation': 'Drip preferred, daily irrigation to maintain moisture 70-80%, avoid wetting foliage',
                'pests_diseases': ['Early blight (spray Chlorothalonil)', 'Late blight (spray Mancozeb)', 'Whitefly (use Yellow traps)', 'Fruit borer (install pheromone trap)'],
                'harvest_time': '60-85 days from transplanting, Multiple harvests over 8-10 weeks'
            },
            'Sugarcane': {
                'name': 'Sugarcane',
                'stages': [
                    {'stage': 'Germination (0-60 days)', 'care': 'Plant setts 2-3 buds deep, 75cm row spacing, irrigation at 3-4 days interval, mulch with straw to keep 70% moisture'},
                    {'stage': 'Tillering (60-180 days)', 'care': 'First irrigation at 30 days, dense canopy formation, first nitrogen split 80kg/ha, light cultivation to remove weeds'},
                    {'stage': 'Elongation (180-270 days)', 'care': 'Critical growth period, furrow irrigation, second nitrogen 80kg/ha, trashing (lower leaf removal), no stagnant water'},
                    {'stage': 'Maturation (270-360 days)', 'care': 'Reduce nitrogen, final irrigation 2-3 months before harvest, trash completely, monitor sucrose accumulation'}
                ],
                'fertilizer': 'NPK 200:120:120 kg/hectare: 100kg N at 30 days, 100kg N at 150 days, full K+P basal with FYM 20-25 tons/ha',
                'irrigation': 'Furrow irrigation 8-12 times, first at 30 days, avoid waterlogging during initiation phase',
                'pests_diseases': ['Shoot borer (use Neem oil spray)', 'Scale insect (release parasitoid)', 'Red rot (use resistant varieties)', 'Smut (hot water treatment for seeds)'],
                'harvest_time': '12-14 months, Harvest when mature stalks are 9-10 months old'
            },
            'Soybean': {
                'name': 'Soybean',
                'stages': [
                    {'stage': 'Germination (0-10 days)', 'care': 'Seed treated with Rhizobium culture, sow when soil temp 20-25°C, light irrigation after sowing, ensure 70% field capacity'},
                    {'stage': 'Vegetative (10-45 days)', 'care': 'Thin to optimal plant population 50-60 plants/m², one irrigation at 30 days if needed, hand weeding 2-3 times'},
                    {'stage': 'Reproductive (45-80 days)', 'care': 'Critical water period during flowering & pod filling (60-80 days), 1-2 irrigations of 50mm, no water stress, monitor for pests'},
                    {'stage': 'Maturation (80-110 days)', 'care': 'Reduce water 30 days before harvest, monitor pod color change to brown, remove lower third of leaves for harvesting'}
                ],
                'fertilizer': 'NPK 0:60:40 kg/hectare (N from Rhizobium symbiosis), apply full P+K basal, Seed inoculation with Rhizobium bacteira essential',
                'irrigation': '1-2 irrigations, critical at flowering and early pod formation stages',
                'pests_diseases': ['Pod borer (spray Formothion)', 'Yellow mosaic virus (use resistant variety)', 'Anthracnose (spray Carbendazim)', 'Leaf roller (hand pick)'],
                'harvest_time': '100-120 days, Harvest when 80% pods turned brown and seed rattles'
            }
        }
        
        if crop_name not in guides:
            return jsonify({'error': f'No guide found for {crop_name}'}), 404
        
        return jsonify({'status': 'success', 'guide': guides[crop_name]})
    
    except Exception as e:
        logger.error(f"Error in maintenance_guide: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/soil-health', methods=['POST'])
def soil_health():
    """Get soil health recommendations"""
    try:
        data = request.get_json()
        ph_value = float(data.get('ph_value', 7))
        
        recommendations = {
            'ph_status': '',
            'actions': [],
            'suitable_crops': []
        }
        
        if ph_value < 5.5:
            recommendations['ph_status'] = 'Very Acidic'
            recommendations['actions'] = [
                'Add lime to increase pH',
                'Apply 2-3 tons/hectare calcium carbonate',
                'Avoid acid-loving species initially'
            ]
            recommendations['suitable_crops'] = ['Potato', 'Strawberry']
        elif ph_value < 6.0:
            recommendations['ph_status'] = 'Acidic'
            recommendations['actions'] = [
                'Apply 1-2 tons/hectare lime',
                'Monitor soil annually',
                'Good drainage needed'
            ]
            recommendations['suitable_crops'] = ['Wheat', 'Potato', 'Rye']
        elif ph_value < 7.0:
            recommendations['ph_status'] = 'Slightly Acidic (Good)'
            recommendations['actions'] = [
                'Maintain current pH',
                'Regular soil testing',
                'Add organic matter'
            ]
            recommendations['suitable_crops'] = ['Most crops']
        elif ph_value < 8.0:
            recommendations['ph_status'] = 'Neutral to Slightly Alkaline (Ideal)'
            recommendations['actions'] = [
                'Excellent for most crops',
                'Monitor micronutrient availability',
                'Maintain with organic matter'
            ]
            recommendations['suitable_crops'] = ['Wheat', 'Rice', 'Maize', 'Sugarcane']
        else:
            recommendations['ph_status'] = 'Alkaline'
            recommendations['actions'] = [
                'Add sulfur to lower pH',
                'Incorporate organic matter',
                'Improve drainage'
            ]
            recommendations['suitable_crops'] = ['Bajra', 'Gram']
        
        return jsonify({'status': 'success', 'recommendations': recommendations})
    
    except Exception as e:
        logger.error(f"Error in soil_health: {e}")
        return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Route not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info("🌾 Starting Crop Health Monitoring System...")
    logger.info(f"📁 Template folder: {template_dir}")
    logger.info(f"📁 Static folder: {static_dir}")
    app.run(debug=True, host='0.0.0.0', port=5000)
