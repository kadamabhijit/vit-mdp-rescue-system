import math
from pathlib import Path

MODEL_PATH = Path(__file__).with_name("priority_model.joblib")

FEATURE_NAMES = (
    "gas_level",
    "temperature",
    "distance",
    "sensors_valid",
    "sensors_missing",
    "sensors_stale",
    "obstacle_detected",
    "hazard_detected",
    "cv_person_detected",
    "cv_confidence",
)

MODEL_CLASSES = ("LOW", "MEDIUM", "HIGH")

_model = None
_model_load_attempted = False


def _validate_features(features):
    if not isinstance(features, dict):
        raise ValueError("features must be a dictionary.")

    missing = set(FEATURE_NAMES) - set(features)
    if missing:
        raise ValueError(
            f"Missing model features: {sorted(missing)}"
        )

    values = []

    for name in FEATURE_NAMES:
        value = features[name]

        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise ValueError(
                f"{name} must be a finite numeric value."
            )

        values.append(float(value))

    for name in (
        "sensors_valid",
        "sensors_missing",
        "sensors_stale",
    ):
        value = features[name]

        if not isinstance(value, int) or value < 0:
            raise ValueError(
                f"{name} must be a non-negative integer."
            )

    for name in (
        "obstacle_detected",
        "hazard_detected",
        "cv_person_detected",
    ):
        if features[name] not in (0, 1):
            raise ValueError(f"{name} must be 0 or 1.")

    if not 0.0 <= features["cv_confidence"] <= 1.0:
        raise ValueError("cv_confidence must be between 0 and 1.")

    return values


def _load_model():
    global _model, _model_load_attempted

    if _model_load_attempted:
        return _model

    _model_load_attempted = True

    if not MODEL_PATH.is_file():
        return None

    try:
        import joblib

        _model = joblib.load(MODEL_PATH)

    except (ImportError, OSError, ValueError, EOFError):
        _model = None

    return _model


def predict_priority(features):
    values = _validate_features(features)

    model = _load_model()

    valid_count = features["sensors_valid"]
    stale_count = features["sensors_stale"]
    missing_count = features["sensors_missing"]

    if (
        valid_count >= 3
        and stale_count == 0
        and missing_count == 0
    ):
        quality_confidence = "HIGH"
    elif valid_count >= 2 and stale_count == 0:
        quality_confidence = "MEDIUM"
    else:
        quality_confidence = "LOW"

    if model is None:
        return {
            "priority": None,
            "model_prediction": None,
            "model_confidence": None,
            "priority_override_applied": False,
            "data_quality_confidence": quality_confidence,
            "status": "MODEL_NOT_TRAINED",
            "training_data": "synthetic",
            "advisory_only": True,
        }

    model_prediction = str(model.predict([values])[0])

    probabilities = model.predict_proba([values])[0]
    probability_by_class = {
        str(label): float(probability)
        for label, probability in zip(
            model.classes_,
            probabilities,
        )
    }

    # This probability belongs to the model's original prediction.
    model_confidence = probability_by_class.get(
        model_prediction, 0.0
    )

    # The safety-priority rule can override the model's prediction.
    priority = model_prediction

    priority_override_applied = (
        features["hazard_detected"] == 1
        and features["obstacle_detected"] == 1
    )

    if priority_override_applied:
        priority = "HIGH"

    return {
        "priority": priority,
        "model_prediction": model_prediction,
        "model_confidence": model_confidence,
        "priority_override_applied": priority_override_applied,
        "data_quality_confidence": quality_confidence,
        "status": "OK",
        "training_data": "synthetic",
        "advisory_only": True,
    }