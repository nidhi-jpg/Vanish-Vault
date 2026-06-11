# AI Face Search Implementation Guide

## Overview

The face search system uses AI-powered facial recognition to match uploaded images (photos, sketches, or pixelated images) against faces in the VanishVault database.

## How It Works

### 1. **Image Upload & Processing**
- User uploads an image (photo, sketch, or pixelated image)
- The system accepts: JPG, PNG formats (up to 5MB)
- Image is processed to enhance recognition (especially for sketches/pixelated images)

### 2. **Face Detection**
- AI system detects faces in the uploaded image
- Extracts facial features and creates a unique "face encoding" (128-dimensional vector)
- This encoding represents the unique characteristics of the face

### 3. **Database Search**
- System searches through all verified missing persons and found persons with photos
- For each database photo:
  - Extracts face encoding
  - Compares with uploaded image's encoding
  - Calculates similarity score (distance)

### 4. **Matching Algorithm**
- Uses Euclidean distance between face encodings
- Lower distance = more similar faces
- Converts distance to confidence percentage (0-100%)
- Filters results based on confidence threshold

### 5. **Results Display**
- Returns matches sorted by confidence (highest first)
- Shows match percentage, case details, and photos
- User can view full details or report a sighting

## Technical Implementation

### Backend (`core/face_recognition_utils.py`)

**Key Functions:**
- `extract_face_encoding()` - Extracts face encoding from image file
- `extract_face_encoding_from_upload()` - Handles uploaded files
- `calculate_face_distance()` - Computes similarity between two faces
- `distance_to_confidence()` - Converts distance to percentage
- `find_matches()` - Main matching function

**Face Recognition Library:**
- Uses `face_recognition` library (built on dlib)
- Fallback mode available if library not installed
- Supports sketches and pixelated images through preprocessing

### Frontend (`templates/core/face_search.html`)

**JavaScript Functions:**
- `startFaceSearch()` - Initiates search with uploaded image
- `updateProgress()` - Shows search progress
- `displayResults()` - Renders match results
- Real-time progress updates during processing

### API Endpoint

**POST `/face-search/`**
- Accepts: `image` (file), `search_type`, `confidence_threshold`
- Returns: JSON with matches array
- Each match includes: person details, confidence score, photo URL

## Installation Requirements

To enable full AI face recognition:

```bash
pip install face_recognition
pip install dlib
pip install opencv-python
```

**Note:** `dlib` requires C++ build tools on Windows.

## Alternative Options

If `face_recognition` library is not available, you can use:

1. **Cloud APIs:**
   - AWS Rekognition
   - Azure Face API
   - Google Cloud Vision API

2. **Other Libraries:**
   - DeepFace
   - InsightFace
   - MediaPipe

## Current Status

- ✅ Backend structure implemented
- ✅ Frontend integration ready
- ✅ Handles photos, sketches, pixelated images
- ⚠️ Requires face_recognition library for full functionality
- ✅ Fallback mode available for development

## How to Use

1. User uploads image (photo/sketch/pixelated)
2. System detects face and extracts encoding
3. Compares with all database photos
4. Returns matches above confidence threshold
5. User reviews results and can take action

## Privacy & Security

- Uploaded images are processed but not stored
- Face encodings are computed on-the-fly
- No personal data is exposed in the matching process
- All processing happens server-side

