# Dependency Notes

## Known Dependency Conflicts

### Protobuf Version Conflict

**Issue**: TensorFlow 2.11.0 requires `protobuf<3.20`, while Streamlit 1.23.1 requires `protobuf>=3.20`.

**Current Status**: 
- Protobuf is set to 3.19.6 (for TensorFlow compatibility)
- Streamlit will show a warning but may still work
- **Face matching system is NOT affected** - it doesn't require Streamlit

### Solutions

#### Option 1: Use Virtual Environments (Recommended)
Create separate environments for different projects:

```bash
# For face matching (with TensorFlow/DeepFace)
python -m venv venv_face_matching
venv_face_matching\Scripts\activate
pip install deepface tensorflow opencv-python

# For Streamlit projects (separate environment)
python -m venv venv_streamlit
venv_streamlit\Scripts\activate
pip install streamlit
```

#### Option 2: Upgrade Python and TensorFlow
If you upgrade to Python 3.8+, you can use TensorFlow 2.13+ which supports protobuf 3.20+:

```bash
# Requires Python 3.8+
pip install tensorflow>=2.13.0
pip install protobuf>=3.20
```

#### Option 3: Accept the Warning
The conflict warning may not break functionality. Both packages might work despite the warning, but this is not guaranteed.

### For Face Matching System

The AI face matching system works correctly with:
- ✅ protobuf 3.19.6 (current)
- ✅ TensorFlow 2.11.0 (current)
- ✅ DeepFace (if installed)
- ✅ face_recognition (if installed)

**Streamlit is NOT required** for the face matching functionality.

## Recommended Setup for Face Matching

```bash
# Install core dependencies
pip install deepface tensorflow opencv-python numpy pillow

# OR use face_recognition instead
pip install face_recognition dlib

# Current protobuf version (3.19.6) is fine for face matching
```

## Checking Dependencies

To check current versions:
```bash
pip list | findstr "protobuf tensorflow streamlit"
```

To verify face matching works:
```python
# Test DeepFace
from deepface import DeepFace
print("DeepFace available")

# Test face_recognition
import face_recognition
print("face_recognition available")
```

