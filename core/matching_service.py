"""
Core face-matching service layer for VanishVault.

This module wraps the lower-level utilities in ``face_recognition_utils``
and the Django models into clean, reusable functions that can be called
from:
- regular Django views
- DRF API views
- your chatbot backend handlers

Key functions exposed for the rest of the app:
- generate_face_embedding()
- match_faces()
- create_report()
- check_for_matches()
"""

from typing import List, Dict, Optional, Tuple, Union
import json
import numpy as np
from django.utils import timezone
from django.db import transaction
from django.core.files.uploadedfile import InMemoryUploadedFile

from . import face_recognition_utils as fr_utils
from .models import MissingPerson, FoundPerson, PotentialMatch


# ---------------------------------------------------------------------------
# Helper utilities for (de)serializing embeddings
# ---------------------------------------------------------------------------

def _serialize_embedding(embedding: np.ndarray) -> str:
    """
    Convert a numpy embedding array to JSON text for storage in TextField.
    """
    return json.dumps(embedding.tolist())


def _deserialize_embedding(embedding_text: Optional[str]) -> Optional[np.ndarray]:
    """
    Convert JSON text from the database back into a numpy array.
    """
    if not embedding_text:
        return None
    try:
        data = json.loads(embedding_text)
        return np.array(data, dtype=float)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Public API: generate_face_embedding
# ---------------------------------------------------------------------------

def generate_face_embedding(
    image: Union[str, InMemoryUploadedFile],
    *,
    from_upload: bool = True,
    use_deepface: bool = True,
) -> Optional[np.ndarray]:
    """
    Generate a face embedding from an image.

    This is a light wrapper around ``face_recognition_utils`` that hides
    the distinction between uploaded files and file paths.

    Args:
        image: Either a Django ``InMemoryUploadedFile`` (when handling
               a newly uploaded photo) or a filesystem path to an image.
        from_upload: Set to True when ``image`` is an uploaded file;
                     False when it is a filesystem path.
        use_deepface: Prefer DeepFace if available for better accuracy.

    Returns:
        Numpy array with the face embedding, or ``None`` if no face
        could be detected.
    """
    if from_upload:
        if not isinstance(image, InMemoryUploadedFile):
            raise TypeError("from_upload=True requires an InMemoryUploadedFile.")
        return fr_utils.extract_face_encoding_from_upload(
            uploaded_file=image,
            use_deepface=use_deepface and fr_utils.DEEPFACE_AVAILABLE,
        )

    # Image is a filesystem path
    if not isinstance(image, str):
        raise TypeError("from_upload=False requires a string file path.")
    return fr_utils.extract_face_encoding(
        image_path=image,
        use_deepface=use_deepface and fr_utils.DEEPFACE_AVAILABLE,
    )


# ---------------------------------------------------------------------------
# Public API: match_faces
# ---------------------------------------------------------------------------

def match_faces(
    query_embedding: np.ndarray,
    database_items: List[Tuple[Union[MissingPerson, FoundPerson], np.ndarray]],
    *,
    confidence_threshold: float = 0.6,
) -> List[Dict]:
    """
    Match a query embedding against a list of stored embeddings.

    Args:
        query_embedding: Embedding of the face we want to search for.
        database_items: List of (person_instance, person_embedding_array).
        confidence_threshold: Minimum confidence (0.0–1.0) for a result
                              to be returned as a potential match.

    Returns:
        List of dictionaries with:
        - person: model instance (MissingPerson or FoundPerson)
        - confidence: confidence percentage (0–100)
        - distance: numeric distance (lower = more similar)
    """
    # Decide which model type we are using for distance → confidence mapping
    if fr_utils.DEEPFACE_AVAILABLE:
        model_type = "deepface"
    elif fr_utils.FACE_RECOGNITION_AVAILABLE:
        model_type = "face_recognition"
    else:
        model_type = "fallback"

    # Reuse the existing high-level matcher
    return fr_utils.find_matches(
        query_encoding=query_embedding,
        database_encodings=database_items,
        threshold=confidence_threshold,
        max_results=50,
        model_type=model_type,
    )


# ---------------------------------------------------------------------------
# Public API: create_report
# ---------------------------------------------------------------------------

def _save_embedding_to_instance(
    instance: Union[MissingPerson, FoundPerson],
    embedding: Optional[np.ndarray],
) -> None:
    """
    Persist an embedding onto a MissingPerson or FoundPerson instance.
    """
    if embedding is None:
        return

    instance.face_embedding = _serialize_embedding(embedding)

    # Record which AI model was used for this embedding
    if fr_utils.DEEPFACE_AVAILABLE:
        instance.face_embedding_model = fr_utils.DEEPFACE_MODEL
    elif fr_utils.FACE_RECOGNITION_AVAILABLE:
        instance.face_embedding_model = "face_recognition"
    else:
        instance.face_embedding_model = "fallback"

    instance.face_embedding_created_at = timezone.now()
    instance.save(update_fields=["face_embedding", "face_embedding_model", "face_embedding_created_at"])


def create_report(
    *,
    report_type: str,
    instance: Union[MissingPerson, FoundPerson],
    uploaded_photo: Optional[InMemoryUploadedFile] = None,
    confidence_threshold: float = 0.6,
) -> Union[MissingPerson, FoundPerson]:
    """
    Post-processing pipeline for a newly created report.

    This function is designed to be called from your view **after**
    a MissingPerson or FoundPerson instance has been created and saved.
    It will:
    1. Generate and save a face embedding (if photo is present).
    2. Run AI matching against the opposite report type.
    3. Persist PotentialMatch rows for any matches above the threshold.

    Args:
        report_type: Either ``\"missing\"`` or ``\"found\"``.
        instance: A saved ``MissingPerson`` or ``FoundPerson`` instance.
        uploaded_photo: Optional uploaded file for this report; if not
                        provided, the function will fall back to
                        ``instance.photo.path`` (if available).
        confidence_threshold: Minimum confidence (0.0–1.0) to store a
                              PotentialMatch.

    Returns:
        The same instance, after embeddings and matches have been handled.
    """
    if report_type not in ("missing", "found"):
        raise ValueError("report_type must be 'missing' or 'found'.")

    # Step 1 – Generate embedding for this report, if possible
    embedding: Optional[np.ndarray] = None
    if uploaded_photo is not None:
        embedding = generate_face_embedding(
            uploaded_photo,
            from_upload=True,
            use_deepface=True,
        )
    elif getattr(instance, "photo", None) and instance.photo:
        embedding = generate_face_embedding(
            instance.photo.path,
            from_upload=False,
            use_deepface=True,
        )

    _save_embedding_to_instance(instance, embedding)

    # Step 2 – Check for matches on the opposite side
    if embedding is not None:
        check_for_matches(
            report_type=report_type,
            instance=instance,
            query_embedding=embedding,
            confidence_threshold=confidence_threshold,
        )

    return instance


# ---------------------------------------------------------------------------
# Public API: check_for_matches
# ---------------------------------------------------------------------------

@transaction.atomic
def check_for_matches(
    *,
    report_type: str,
    instance: Union[MissingPerson, FoundPerson],
    query_embedding: Optional[np.ndarray] = None,
    confidence_threshold: float = 0.6,
) -> List[PotentialMatch]:
    """
    Compare a new report against all opposite-type reports and create
    ``PotentialMatch`` records for any strong AI suggestions.

    Matching rules:
    - If a new MISSING report is added, compare with all FOUND reports.
    - If a new FOUND report is added, compare with all MISSING reports.
    - Uses cosine-based distance + threshold logic from ``face_recognition_utils``.
    - Does **not** auto-confirm matches. All results are stored with
      status = ``pending`` for human review.

    Args:
        report_type: ``\"missing\"`` or ``\"found\"`` – which side is new.
        instance: The new ``MissingPerson`` or ``FoundPerson`` instance.
        query_embedding: Pre-computed embedding for this instance; if
                         omitted, it will be loaded from the instance.
        confidence_threshold: Minimum confidence (0.0–1.0) to store a
                              potential match.

    Returns:
        List of ``PotentialMatch`` instances that were created or found.
    """
    if report_type not in ("missing", "found"):
        raise ValueError("report_type must be 'missing' or 'found'.")

    # Load embedding from instance if not provided
    if query_embedding is None:
        query_embedding = _deserialize_embedding(getattr(instance, "face_embedding", None))

    if query_embedding is None:
        # Nothing to match if we have no embedding
        return []

    # Decide which queryset to compare against
    if report_type == "missing":
        # New MISSING report -> check against all FOUND reports
        opposite_qs = FoundPerson.objects.filter(
            photo__isnull=False,
        ).exclude(face_embedding__isnull=True).exclude(face_embedding="")
        triggered_by = "missing"
    else:
        # New FOUND report -> check against all MISSING reports
        opposite_qs = MissingPerson.objects.filter(
            photo__isnull=False,
        ).exclude(face_embedding__isnull=True).exclude(face_embedding="")
        triggered_by = "found"

    # Build list of (person, embedding_array)
    database_items: List[Tuple[Union[MissingPerson, FoundPerson], np.ndarray]] = []
    for person in opposite_qs:
        db_emb = _deserialize_embedding(person.face_embedding)
        if db_emb is not None:
            database_items.append((person, db_emb))

    if not database_items:
        return []

    # Run AI-based face matching
    matches = match_faces(
        query_embedding=query_embedding,
        database_items=database_items,
        confidence_threshold=confidence_threshold,
    )

    potential_matches: List[PotentialMatch] = []

    # Map model type string for storing
    if fr_utils.DEEPFACE_AVAILABLE:
        ai_model_name = fr_utils.DEEPFACE_MODEL
    elif fr_utils.FACE_RECOGNITION_AVAILABLE:
        ai_model_name = "face_recognition"
    else:
        ai_model_name = "fallback"

    for match in matches:
        person = match["person"]
        confidence = float(match["confidence"])
        distance = float(match["distance"])

        # Determine which side is missing/found based on report_type
        if report_type == "missing":
            missing_person = instance  # new MissingPerson
            found_person = person      # existing FoundPerson
        else:
            missing_person = person    # existing MissingPerson
            found_person = instance    # new FoundPerson

        # Ensure we don't create duplicate PotentialMatch rows for
        # the same pair + trigger type.
        potential_match, created = PotentialMatch.objects.get_or_create(
            missing_person=missing_person,
            found_person=found_person,
            triggered_by=triggered_by,
            defaults={
                "distance": distance,
                "confidence": confidence,
                "ai_model": ai_model_name,
                "status": "pending",
            },
        )

        if not created:
            # If we already had a record, update it with better data
            potential_match.distance = distance
            potential_match.confidence = confidence
            potential_match.ai_model = ai_model_name
            potential_match.updated_at = timezone.now()
            potential_match.save(
                update_fields=["distance", "confidence", "ai_model", "updated_at"]
            )

        potential_matches.append(potential_match)

    return potential_matches


__all__ = [
    "generate_face_embedding",
    "match_faces",
    "create_report",
    "check_for_matches",
]


