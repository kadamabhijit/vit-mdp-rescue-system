import random
from collections import Counter

from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

from intelligence.priority_model import (
    FEATURE_NAMES,
    MODEL_PATH,
)
from intelligence.sensor_fusion import SENSOR_RANGES, assess_situation


RANDOM_SEED = 42
SAMPLE_COUNT = 3000
MODEL_CLASSES = ("LOW", "MEDIUM", "HIGH")


def generate_sample(rng):
    sensor_data = {}
    status = {}

    for name, (minimum, maximum) in SENSOR_RANGES.items():
        state = rng.choices(
            ["VALID", "MISSING", "STALE"],
            weights=[80, 10, 10],
            k=1,
        )[0]

        status[name] = state

        if state == "VALID":
            if name == "temperature":
                value = round(rng.uniform(minimum, maximum), 1)
            else:
                value = rng.randint(minimum, maximum)

            sensor_data[name] = value
        else:
            sensor_data[name] = None

    cv_detected = rng.choice([0, 1])
    cv_confidence = (
        round(rng.uniform(0.50, 1.0), 3)
        if cv_detected
        else 0.0
    )

    assessment = assess_situation(sensor_data)

    valid_count = sum(
        state == "VALID" for state in status.values()
    )
    stale_count = sum(
        state == "STALE" for state in status.values()
    )
    missing_count = 3 - valid_count - stale_count

    features = {
        "gas_level": (
            sensor_data["gas_level"]
            if status["gas_level"] == "VALID"
            else 0
        ),
        "temperature": (
            sensor_data["temperature"]
            if status["temperature"] == "VALID"
            else 0
        ),
        "distance": (
            sensor_data["distance"]
            if status["distance"] == "VALID"
            else 0
        ),
        "sensors_valid": valid_count,
        "sensors_missing": missing_count,
        "sensors_stale": stale_count,
        "obstacle_detected": int(
            bool(assessment["obstacles"])
        ),
        "hazard_detected": int(
            assessment["hazard_detected"]
        ),
        "cv_person_detected": cv_detected,
        "cv_confidence": cv_confidence,
    }

    hazard = features["hazard_detected"]
    obstacle = features["obstacle_detected"]

    # Synthetic labels are illustrative rules,
    # not real-world ground truth.
    severe_gas = (
        status["gas_level"] == "VALID"
        and features["gas_level"] >= 800
    )

    severe_temperature = (
        status["temperature"] == "VALID"
        and features["temperature"] >= 75
    )

    # A detected hazard and nearby obstacle together
    # always receive HIGH priority.
    if hazard and obstacle:
        label = "HIGH"

    elif (
        severe_gas
        or severe_temperature
        or (hazard and cv_detected)
        or (obstacle and cv_detected)
    ):
        label = "HIGH"

    elif (
        hazard
        or obstacle
        or cv_detected
        or valid_count < 3
    ):
        label = "MEDIUM"

    else:
        label = "LOW"

    return features, label


def main():
    rng = random.Random(RANDOM_SEED)

    samples = [
        generate_sample(rng)
        for _ in range(SAMPLE_COUNT)
    ]

    class_counts = Counter(
        label for _, label in samples
    )

    print("Training data: SYNTHETIC")
    print("Class distribution:")

    for label in MODEL_CLASSES:
        print(f"  {label}: {class_counts.get(label, 0)}")

    missing_classes = set(MODEL_CLASSES) - set(class_counts)

    if missing_classes:
        raise ValueError(
            f"Training data is missing priority classes: "
            f"{sorted(missing_classes)}"
        )

    print()

    X = [
        [features[name] for name in FEATURE_NAMES]
        for features, _ in samples
    ]

    y = [
        label for _, label in samples
    ]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=RANDOM_SEED,
        stratify=y,
    )

    model = DecisionTreeClassifier(
        max_depth=3,
        min_samples_leaf=10,
        class_weight="balanced",
        random_state=RANDOM_SEED,
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    print(f"Total samples: {len(samples)}")
    print(f"Training samples: {len(X_train)}")
    print(f"Test samples: {len(X_test)}")

    print(
        f"Test accuracy: "
        f"{accuracy_score(y_test, predictions):.3f}"
    )

    print()

    print(
        classification_report(
            y_test,
            predictions,
            labels=list(MODEL_CLASSES),
            zero_division=0,
        )
    )

    import joblib

    joblib.dump(model, MODEL_PATH)

    print(f"Model saved to: {MODEL_PATH}")


if __name__ == "__main__":
    main()