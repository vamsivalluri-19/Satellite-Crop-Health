import numpy as np
from PIL import Image
import io
import base64
import random

class CropDiseasePredictor:
    """
    Simple crop disease prediction model.
    In production, this would use a trained CNN or similar model.
    """
    
    diseases = [
        'Healthy',
        'Powdery Mildew',
        'Leaf Spot',
        'Rust',
        'Blight',
        'Septoria'
    ]
    
    def __init__(self):
        self.model_loaded = True
    
    def preprocess_image(self, image_data):
        """
        Preprocess image for model prediction
        """
        try:
            if isinstance(image_data, str):
                # Handle base64 encoded image
                image_array = base64.b64decode(image_data.split(',')[1])
                image = Image.open(io.BytesIO(image_array))
            else:
                image = image_data
            
            # Resize to standard size
            image = image.resize((224, 224))
            image_array = np.array(image) / 255.0
            
            return image_array
        except Exception as e:
            return None
    
    def predict(self, image_data):
        """
        Predict crop disease from image
        """
        try:
            preprocessed = self.preprocess_image(image_data)
            if preprocessed is None:
                return {
                    'disease': 'Unknown',
                    'confidence': 0.0,
                    'error': 'Could not process image'
                }
            
            # Simulate model prediction
            # In production, use actual trained model
            disease_idx = random.randint(0, len(self.diseases) - 1)
            disease = self.diseases[disease_idx]
            confidence = round(random.uniform(0.7, 0.99), 3)
            
            # Generate treatment recommendations
            recommendations = self.get_treatments(disease)
            
            return {
                'disease': disease,
                'confidence': confidence,
                'recommendations': recommendations,
                'status': 'success'
            }
        except Exception as e:
            return {
                'disease': 'Error',
                'confidence': 0.0,
                'error': str(e),
                'status': 'error'
            }
    
    @staticmethod
    def get_treatments(disease):
        """
        Get treatment recommendations for identified disease
        """
        treatments = {
            'Healthy': ['Continue regular maintenance', 'Monitor crop regularly'],
            'Powdery Mildew': ['Apply fungicide spray', 'Improve air circulation', 'Reduce humidity'],
            'Leaf Spot': ['Remove affected leaves', 'Apply copper fungicide', 'Ensure proper spacing'],
            'Rust': ['Use sulfur-based treatments', 'Improve air drainage', 'Remove infected leaves'],
            'Blight': ['Apply systemic fungicide immediately', 'Increase drainage', 'Isolate infected plants'],
            'Septoria': ['Remove infected foliage', 'Apply fungicide', 'Reduce leaf wetness'],
            'Unknown': ['Consult agricultural expert', 'Take multiple photos from different angles']
        }
        return treatments.get(disease, treatments['Unknown'])

# Initialize predictor
predictor = CropDiseasePredictor()

def predict_disease(image_data):
    """
    Public function to predict disease from image
    """
    return predictor.predict(image_data)

def get_health_score(ndvi_value):
    """
    Calculate overall crop health score from NDVI
    """
    if ndvi_value < 0.2:
        return {'score': 'Poor', 'color': 'red', 'action': 'Immediate intervention required'}
    elif ndvi_value < 0.4:
        return {'score': 'Fair', 'color': 'orange', 'action': 'Monitor and treat'}
    elif ndvi_value < 0.6:
        return {'score': 'Good', 'color': 'yellow', 'action': 'Continue monitoring'}
    else:
        return {'score': 'Excellent', 'color': 'green', 'action': 'Maintain current practices'}
