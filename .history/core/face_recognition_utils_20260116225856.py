"""
Face Recognition Utilities for VanishVault
Handles AI-powered face matching between uploaded images and database photos
Supports multiple AI models: DeepFace (recommended), face_recognition, and fallback mode
"""
import os
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import io
import tempfile
from typing import List, Dict, Tuple, Optional
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.conf import settings

# Try to import DeepFace (most accurate, supports multiple models)
try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False
    print("Info: DeepFace not installed. Install with: pip install deepface")

# Try to import face_recognition library (fallback)
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("Info: face_recognition library not installed. Install with: pip install face_recognition")

# Determine which library to use (DeepFace preferred)
AI_MODEL_AVAILABLE = DEEPFACE_AVAILABLE or FACE_RECOGNITION_AVAILABLE

# DeepFace model options (in order of preference)
# VGG-Face: Best accuracy, slower
# Facenet: Good balance
# OpenFace: Fast, good for real-time
# ArcFace: State-of-the-art accuracy
DEEPFACE_MODEL = getattr(settings, 'DEEPFACE_MODEL', 'VGG-Face')  # Can be: VGG-Face, Facenet, OpenFace, ArcFace


def extract_face_encoding(image_path: str, use_deepface: bool = True) -> Optional[np.ndarray]:
    """
    Extract face encoding from an image file using AI.
    Uses DeepFace if available (more accurate), otherwise falls back to face_recognition.
    
    Args:
        image_path: Path to the image file
        use_deepface: Whether to prefer DeepFace (default: True)
        
    Returns:
        Face encoding array or None if no face detected
    """
    if not os.path.exists(image_path):
        return None
    
    # Try DeepFace first (more accurate)
    if use_deepface and DEEPFACE_AVAILABLE:
        try:
            # DeepFace returns a dictionary with embedding
            result = DeepFace.represent(
                img_path=image_path,
                model_name=DEEPFACE_MODEL,
                enforce_detection=False,  # Don't fail if face detection is uncertain
                detector_backend='opencv'  # Can also use: 'ssd', 'dlib', 'mtcnn', 'retinaface'
            )
            
            if result and len(result) > 0:
                # Get the first face embedding
                embedding = result[0]['embedding']
                return np.array(embedding)
        except Exception as e:
            print(f"DeepFace extraction failed, trying fallback: {e}")
            # Fall through to face_recognition
    
    # Fallback to face_recognition
    if FACE_RECOGNITION_AVAILABLE:
        try:
            # Load image
            image = face_recognition.load_image_file(image_path)
            
            # Find face locations
            face_locations = face_recognition.face_locations(image, model='hog')  # 'hog' is faster, 'cnn' is more accurate
            
            if not face_locations:
                return None
            
            # Get face encodings (use first face if multiple)
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            if face_encodings:
                return face_encodings[0]
        except Exception as e:
            print(f"Error extracting face encoding with face_recognition: {e}")
    
    # Final fallback for development
    if not AI_MODEL_AVAILABLE:
        print("Warning: No AI library available. Using dummy encoding for development.")
        return np.random.rand(128) if os.path.exists(image_path) else None
    
    return None


def extract_face_encoding_from_upload(uploaded_file: InMemoryUploadedFile, use_deepface: bool = True) -> Optional[np.ndarray]:
    """
    Extract face encoding from an uploaded file.
    Preprocesses image for better recognition (handles sketches, pixelated images).
    
    Args:
        uploaded_file: Django InMemoryUploadedFile
        use_deepface: Whether to prefer DeepFace (default: True)
        
    Returns:
        Face encoding array or None if no face detected
    """
    try:
        # Read file into memory
        uploaded_file.seek(0)  # Reset file pointer
        image_data = uploaded_file.read()
        image = Image.open(io.BytesIO(image_data))
        
        # Preprocess image for better AI recognition
        image = preprocess_image_pil(image)
        
        # Save to temporary file for DeepFace/face_recognition
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
            image.save(tmp_file.name, 'JPEG', quality=95)
            tmp_path = tmp_file.name
        
        try:
            # Extract encoding using the saved temp file
            encoding = extract_face_encoding(tmp_path, use_deepface=use_deepface)
            return encoding
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except:
                pass
        
    except Exception as e:
        print(f"Error extracting face encoding from upload: {e}")
        return None


def calculate_face_distance(encoding1: np.ndarray, encoding2: np.ndarray) -> float:
    """
    Calculate the distance between two face encodings using cosine similarity.
    Lower distance = more similar faces.
    
    Args:
        encoding1: First face encoding
        encoding2: Second face encoding
        
    Returns:
        Distance value (0.0 = identical, higher = more different)
    """
    try:
        # Normalize encodings for better comparison
        encoding1_norm = encoding1 / (np.linalg.norm(encoding1) + 1e-10)
        encoding2_norm = encoding2 / (np.linalg.norm(encoding2) + 1e-10)
        
        # Calculate cosine distance (1 - cosine similarity)
        # Cosine similarity ranges from -1 to 1, distance from 0 to 2
        cosine_similarity = np.dot(encoding1_norm, encoding2_norm)
        cosine_distance = 1 - cosine_similarity
        
        # Also calculate Euclidean distance as fallback
        euclidean_distance = np.linalg.norm(encoding1 - encoding2)
        
        # Use cosine distance (better for face recognition) but normalize
        # Convert to 0-1 range for consistency
        normalized_distance = min(cosine_distance / 2.0, euclidean_distance / 10.0)
        
        return float(normalized_distance)
    except Exception as e:
        print(f"Error calculating face distance: {e}")
        # Fallback to simple Euclidean distance
        try:
            return float(np.linalg.norm(encoding1 - encoding2))
        except:
            return 1.0


def distance_to_confidence(distance: float, model_type: str = 'deepface') -> float:
    """
    Convert face distance to confidence percentage.
    Uses different thresholds based on the AI model used.
    
    Args:
        distance: Face distance (0.0 to ~1.0)
        model_type: Type of model used ('deepface' or 'face_recognition')
        
    Returns:
        Confidence percentage (0-100)
    """
    # DeepFace typically has better separation, so thresholds are different
    if model_type == 'deepface':
        # DeepFace distances are typically lower and more accurate
        if distance <= 0.2:
            # Very similar (high confidence)
            confidence = 100 - (distance * 200)  # 100% at 0.0, ~60% at 0.2
        elif distance <= 0.4:
            # Somewhat similar (medium confidence)
            confidence = 60 - ((distance - 0.2) * 100)  # 60% at 0.2, ~40% at 0.4
        elif distance <= 0.6:
            # Low similarity (low confidence)
            confidence = 40 - ((distance - 0.4) * 100)  # 40% at 0.4, ~20% at 0.6
        else:
            # Not very similar
            confidence = max(0, 20 - ((distance - 0.6) * 50))
    else:
        # face_recognition model thresholds
        if distance <= 0.4:
            confidence = 100 - (distance * 150)  # 100% at 0.0, ~40% at 0.4
        elif distance <= 0.6:
            confidence = 40 - ((distance - 0.4) * 100)  # 40% at 0.4, ~20% at 0.6
        else:
            confidence = max(0, 20 - ((distance - 0.6) * 50))
    
    return max(0, min(100, confidence))


def find_matches(
    query_encoding: np.ndarray,
    database_encodings: List[Tuple[object, np.ndarray]],
    threshold: float = 0.6,
    max_results: int = 20,
    model_type: str = 'deepface'
) -> List[Dict]:
    """
    Find matching faces in the database using AI-powered comparison.
    
    Args:
        query_encoding: Face encoding from uploaded image
        database_encodings: List of (person_object, encoding) tuples
        threshold: Confidence threshold (0.0-1.0, converted to distance)
        max_results: Maximum number of results to return
        model_type: Type of AI model used ('deepface' or 'face_recognition')
        
    Returns:
        List of match dictionaries with person, confidence, and distance
    """
    matches = []
    
    # Convert threshold to distance (inverse relationship)
    # For DeepFace: threshold 0.6 = 60% confidence ≈ 0.3-0.4 distance
    # For face_recognition: threshold 0.6 = 60% confidence ≈ 0.4 distance
    if model_type == 'deepface':
        max_distance = 1.0 - (threshold * 0.7)  # More lenient for DeepFace
    else:
        max_distance = 1.0 - (threshold * 0.6)
    
    for person, db_encoding in database_encodings:
        if db_encoding is None:
            continue
        
        try:
            # Calculate distance
            distance = calculate_face_distance(query_encoding, db_encoding)
            
            # Convert to confidence
            confidence = distance_to_confidence(distance, model_type=model_type)
            
            # Check if above threshold (both distance and confidence)
            if distance <= max_distance and confidence >= (threshold * 100):
                matches.append({
                    'person': person,
                    'confidence': round(confidence, 1),
                    'distance': round(distance, 4),
                })
        except Exception as e:
            print(f"Error matching with person {person.pk}: {e}")
            continue
    
    # Sort by confidence (highest first), then by distance (lowest first)
    matches.sort(key=lambda x: (-x['confidence'], x['distance']))
    
    # Return top results
    return matches[:max_results]


def preprocess_image_for_ai(image_path: str) -> Optional[str]:
    """
    Preprocess image for better AI recognition (handles sketches, pixelated images).
    
    Args:
        image_path: Path to image file
        
    Returns:
        Path to processed image or None
    """
    try:
        image = Image.open(image_path)
        
        # Convert to RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Enhance contrast for sketches/pixelated images
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.2)
        
        # Save processed image
        processed_path = image_path.replace('.', '_processed.')
        image.save(processed_path, 'JPEG', quality=90)
        
        return processed_path
    except Exception as e:
        print(f"Error preprocessing image: {e}")
        return image_path  # Return original if processing fails

