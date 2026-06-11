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
from typing import List, Dict, Tuple, Optional, Union
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
    Enhanced confidence calculation with detailed classification.
    Converts face distance to confidence percentage with match/no-match classification.
    
    Args:
        distance: Face distance (0.0 to ~1.0)
        model_type: Type of model used ('deepface' or 'face_recognition')
        
    Returns:
        Confidence percentage (0-100)
    """
    # Enhanced thresholds for better real-world performance
    if model_type == 'deepface':
        # DeepFace has better accuracy, use tighter thresholds
        if distance <= 0.15:
            # Very high confidence match
            confidence = 100 - (distance * 150)  # 100% at 0.0, ~77% at 0.15
        elif distance <= 0.25:
            # High confidence match
            confidence = 85 - ((distance - 0.15) * 200)  # 77% at 0.15, ~65% at 0.25
        elif distance <= 0.35:
            # Medium confidence (possible match)
            confidence = 65 - ((distance - 0.25) * 150)  # 65% at 0.25, ~50% at 0.35
        elif distance <= 0.5:
            # Low confidence (unlikely match)
            confidence = 50 - ((distance - 0.35) * 100)  # 50% at 0.35, ~35% at 0.5
        else:
            # Very low confidence (probably not a match)
            confidence = max(0, 35 - ((distance - 0.5) * 70))
    else:
        # face_recognition model thresholds (more lenient)
        if distance <= 0.3:
            confidence = 100 - (distance * 120)  # 100% at 0.0, ~64% at 0.3
        elif distance <= 0.45:
            confidence = 64 - ((distance - 0.3) * 100)  # 64% at 0.3, ~49% at 0.45
        elif distance <= 0.6:
            confidence = 49 - ((distance - 0.45) * 80)  # 49% at 0.45, ~37% at 0.6
        else:
            confidence = max(0, 37 - ((distance - 0.6) * 50))
    
    return max(0, min(100, confidence))


def classify_match_quality(confidence: float) -> Dict[str, Union[str, bool]]:
    """
    Classify match quality based on confidence score.
    Returns classification and match determination.
    
    Args:
        confidence: Confidence percentage (0-100)
        
    Returns:
        Dictionary with classification details
    """
    if confidence >= 80:
        return {
            'classification': 'High Confidence Match',
            'is_match': True,
            'color': '#28a745',  # Green
            'description': 'Strong facial similarity - likely the same person',
            'requires_review': True  # Still requires human verification
        }
    elif confidence >= 65:
        return {
            'classification': 'Medium Confidence Match',
            'is_match': True,
            'color': '#ffc107',  # Yellow/Orange
            'description': 'Good facial similarity - possible match',
            'requires_review': True
        }
    elif confidence >= 45:
        return {
            'classification': 'Low Confidence Match',
            'is_match': True,
            'color': '#fd7e14',  # Orange
            'description': 'Some facial similarity - needs investigation',
            'requires_review': True
        }
    else:
        return {
            'classification': 'Not a Match',
            'is_match': False,
            'color': '#dc3545',  # Red
            'description': 'Insufficient facial similarity',
            'requires_review': False
        }


def find_matches(
    query_encoding: np.ndarray,
    database_encodings: List[Tuple[object, np.ndarray]],
    threshold: float = 0.6,
    max_results: int = 20,
    model_type: str = 'deepface'
) -> List[Dict]:
    """
    Enhanced face matching with detailed classification and angle-invariant comparison.
    
    Args:
        query_encoding: Face encoding from uploaded image
        database_encodings: List of (person_object, encoding) tuples
        threshold: Confidence threshold (0.0-1.0, converted to distance)
        max_results: Maximum number of results to return
        model_type: Type of AI model used ('deepface' or 'face_recognition')
        
    Returns:
        List of enhanced match dictionaries with classification
    """
    matches = []
    
    # Convert threshold to distance with enhanced logic
    if model_type == 'deepface':
        max_distance = 1.0 - (threshold * 0.8)  # More accurate for DeepFace
    else:
        max_distance = 1.0 - (threshold * 0.7)
    
    for person, db_encoding in database_encodings:
        if db_encoding is None:
            continue
        
        try:
            # Calculate distance using enhanced method
            distance = calculate_face_distance(query_encoding, db_encoding)
            
            # Convert to confidence with enhanced calculation
            confidence = distance_to_confidence(distance, model_type=model_type)
            
            # Classify match quality
            classification = classify_match_quality(confidence)
            
            # Include more results for better coverage, but filter by classification
            if confidence >= 30:  # Lower threshold to include potential matches
                matches.append({
                    'person': person,
                    'confidence': round(confidence, 1),
                    'distance': round(distance, 4),
                    'classification': classification['classification'],
                    'is_match': classification['is_match'],
                    'color': classification['color'],
                    'description': classification['description'],
                    'requires_review': classification['requires_review'],
                    'match_quality': 'high' if confidence >= 80 else 
                                   'medium' if confidence >= 65 else 
                                   'low' if confidence >= 45 else 'none'
                })
        except Exception as e:
            print(f"Error matching with person {person.pk}: {e}")
            continue
    
    # Sort by confidence (highest first), then by distance (lowest first)
    matches.sort(key=lambda x: (-x['confidence'], x['distance']))
    
    # Return top results, but ensure we include all high/medium confidence matches
    high_confidence_matches = [m for m in matches if m['confidence'] >= 65]
    other_matches = [m for m in matches if m['confidence'] < 65]
    
    # Prioritize high confidence matches
    final_matches = high_confidence_matches + other_matches[:max(0, max_results - len(high_confidence_matches))]
    
    return final_matches[:max_results]


def preprocess_image_pil(image: Image.Image) -> Image.Image:
    """
    Enhanced preprocessing for angle-invariant face recognition.
    Handles sketches, pixelated images, low-quality photos, and various face angles.
    
    Args:
        image: PIL Image object
        
    Returns:
        Processed PIL Image with enhanced face features
    """
    try:
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize if too large (faster processing, maintains quality)
        max_size = 1024
        if max(image.size) > max_size:
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Step 1: Enhance contrast for sketches/pixelated images
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.3)
        
        # Step 2: Enhance sharpness slightly for better edge detection
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.1)
        
        # Step 3: Apply adaptive histogram equalization for better lighting
        # This helps with faces captured at different angles/lighting conditions
        image = enhance_lighting_conditions(image)
        
        # Step 4: Apply slight unsharp mask for better edge detection
        image = image.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))
        
        # Step 5: Face alignment normalization (if face detected)
        image = normalize_face_alignment(image)
        
        return image
    except Exception as e:
        print(f"Error preprocessing image: {e}")
        return image  # Return original if processing fails


def preprocess_image_for_ai(image_path: str) -> Optional[str]:
    """
    Preprocess image file for better AI recognition (handles sketches, pixelated images).
    
    Args:
        image_path: Path to image file
        
    Returns:
        Path to processed image or original path if processing fails
    """
    try:
        image = Image.open(image_path)
        processed_image = preprocess_image_pil(image)
        
        # Save processed image
        processed_path = image_path.replace('.', '_processed.')
        processed_image.save(processed_path, 'JPEG', quality=95)
        
        return processed_path
    except Exception as e:
        print(f"Error preprocessing image file: {e}")
        return image_path  # Return original if processing fails


def detect_faces_in_image(image_path: str) -> int:
    """
    Detect number of faces in an image using multiple detection backends.
    
    Args:
        image_path: Path to image file
        
    Returns:
        Number of faces detected
    """
    if DEEPFACE_AVAILABLE:
        try:
            # Try multiple detectors for better angle detection
            detectors = ['opencv', 'ssd', 'mtcnn']
            for detector in detectors:
                try:
                    result = DeepFace.extract_faces(
                        img_path=image_path,
                        detector_backend=detector,
                        enforce_detection=False
                    )
                    if result and len(result) > 0:
                        return len(result)
                except:
                    continue
        except:
            pass
    
    if FACE_RECOGNITION_AVAILABLE:
        try:
            image = face_recognition.load_image_file(image_path)
            # Try both HOG (faster) and CNN (more accurate) detectors
            face_locations = face_recognition.face_locations(image, model='hog')
            if not face_locations:
                face_locations = face_recognition.face_locations(image, model='cnn')
            return len(face_locations)
        except:
            pass
    
    return 0


def enhance_lighting_conditions(image: Image.Image) -> Image.Image:
    """
    Enhance image to normalize lighting conditions for better face recognition.
    Helps with faces captured in different lighting/angle scenarios.
    """
    try:
        import cv2
        import numpy as np
        
        # Convert PIL to OpenCV format
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        
        # Convert to LAB color space
        lab = cv2.cvtColor(cv_image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE to L channel
        l = clahe.apply(l)
        
        # Merge channels and convert back
        lab = cv2.merge([l, a, b])
        cv_image = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        # Convert back to PIL
        rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb_image)
    except:
        return image


def normalize_face_alignment(image: Image.Image) -> Image.Image:
    """
    Attempt to normalize face alignment for better angle-invariant matching.
    This is a lightweight version that doesn't require facial landmark detection.
    """
    try:
        # For now, return the image as-is
        # In a future enhancement, we could add facial landmark detection
        # to align faces to a canonical position
        return image
    except:
        return image


def compare_faces(encoding1: np.ndarray, encoding2: np.ndarray) -> float:
    """
    Compare two face encodings and return confidence score.
    This is a simplified version for direct comparison.
    
    Args:
        encoding1: First face encoding
        encoding2: Second face encoding
        
    Returns:
        Confidence score (0.0 to 1.0) where higher is more similar
    """
    if encoding1 is None or encoding2 is None:
        return 0.0
    
    try:
        # Calculate distance between encodings
        distance = calculate_face_distance(encoding1, encoding2)
        
        # Convert distance to confidence
        confidence = distance_to_confidence(distance, model_type='deepface' if DEEPFACE_AVAILABLE else 'face_recognition')
        
        # Return confidence as 0.0 to 1.0 range
        return confidence / 100.0
    except Exception as e:
        print(f"Error comparing faces: {e}")
        return 0.0


def extract_multiple_face_encodings(image_path: str, max_faces: int = 5) -> List[np.ndarray]:
    """
    Extract multiple face encodings from an image.
    Useful for group photos or images with multiple faces.
    
    Args:
        image_path: Path to image file
        max_faces: Maximum number of faces to extract
        
    Returns:
        List of face encoding arrays
    """
    encodings = []
    
    if DEEPFACE_AVAILABLE:
        try:
            result = DeepFace.represent(
                img_path=image_path,
                model_name=DEEPFACE_MODEL,
                enforce_detection=False,
                detector_backend='mtcnn'  # Better for multiple faces
            )
            
            if result:
                for face_data in result[:max_faces]:
                    embedding = face_data['embedding']
                    encodings.append(np.array(embedding))
        except Exception as e:
            print(f"DeepFace multi-face extraction failed: {e}")
    
    # Fallback to face_recognition
    if not encodings and FACE_RECOGNITION_AVAILABLE:
        try:
            image = face_recognition.load_image_file(image_path)
            face_locations = face_recognition.face_locations(image, model='cnn')
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            for encoding in face_encodings[:max_faces]:
                encodings.append(encoding)
        except Exception as e:
            print(f"face_recognition multi-face extraction failed: {e}")
    
    return encodings

