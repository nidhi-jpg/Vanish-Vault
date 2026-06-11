#!/usr/bin/env python
"""Check which AI face recognition libraries are available"""

print("Checking AI face recognition libraries...\n")

# Check DeepFace
try:
    import deepface
    print("[OK] DeepFace: INSTALLED")
except ImportError:
    print("[X] DeepFace: NOT INSTALLED")

# Check face_recognition
try:
    import face_recognition
    print("[OK] face_recognition: INSTALLED")
except ImportError:
    print("[X] face_recognition: NOT INSTALLED")

# Check numpy
try:
    import numpy as np
    print("[OK] numpy: INSTALLED")
except ImportError:
    print("[X] numpy: NOT INSTALLED")

# Check PIL
try:
    from PIL import Image
    print("[OK] Pillow: INSTALLED")
except ImportError:
    print("[X] Pillow: NOT INSTALLED")

print("\n" + "="*50)
print("Summary:")
print("The face search will work with any available library.")
print("If none are installed, it will use fallback mode (dummy data).")

