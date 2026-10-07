"""
Fire and Smoke Detection — Model Training Module
==================================================
Trains a CNN to classify images as 'fire' or 'non_fire' using a wildfire dataset.

Dataset structure expected:
    dataset/
    ├── fire/        (images containing fire/smoke)
    └── non_fire/    (images without fire/smoke)

Usage:
    python train_model.py --dataset <path_to_dataset>
"""

import os
import argparse
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import (
    Conv2D, MaxPooling2D, Flatten, Dense, Dropout, BatchNormalization
)
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────
IMG_SIZE = 128          # Resize all images to 128x128
BATCH_SIZE = 32
EPOCHS = 20
MODEL_SAVE_PATH = os.path.join(os.path.dirname(__file__), "fire_detection_model.h5")


def load_dataset(dataset_path: str):
    """
    Load images from fire/ and non_fire/ subdirectories.
    Returns numpy arrays: (images, labels)
        label 1 = fire, 0 = non-fire
    """
    images = []
    labels = []

    # Map folder names to labels
    class_map = {"fire": 1, "non_fire": 0, "nofire": 0, "no_fire": 0, "nonfire": 0}

    found_classes = []
    for folder_name in os.listdir(dataset_path):
        folder_path = os.path.join(dataset_path, folder_name)
        if not os.path.isdir(folder_path):
            continue

        label_key = folder_name.lower().replace(" ", "_").replace("-", "_")
        if label_key not in class_map:
            print(f"[WARN] Skipping unknown folder: '{folder_name}'")
            continue

        label = class_map[label_key]
        found_classes.append((folder_name, label))
        file_list = os.listdir(folder_path)
        print(f"[LOAD] Loading '{folder_name}/' -> label={label}  ({len(file_list)} files)")

        for filename in file_list:
            filepath = os.path.join(folder_path, filename)
            try:
                img = load_img(filepath, target_size=(IMG_SIZE, IMG_SIZE))
                img_array = img_to_array(img) / 255.0   # normalize to [0, 1]
                images.append(img_array)
                labels.append(label)
            except Exception as e:
                # Skip corrupt or non-image files silently
                pass

    if len(found_classes) < 2:
        raise ValueError(
            f"Expected at least 2 class folders (fire, non_fire) in '{dataset_path}'. "
            f"Found: {[c[0] for c in found_classes]}"
        )

    images = np.array(images, dtype="float32")
    labels = np.array(labels, dtype="float32")
    print(f"\n[OK] Loaded {len(images)} images  |  fire={int(labels.sum())}  non-fire={int(len(labels) - labels.sum())}")
    return images, labels


def build_model():
    """
    Build a CNN for binary classification (fire vs non-fire).
    Architecture: 3 × (Conv2D → BatchNorm → MaxPool → Dropout) → Dense → Output
    """
    model = Sequential([
        # Block 1
        Conv2D(32, (3, 3), activation="relu", input_shape=(IMG_SIZE, IMG_SIZE, 3)),
        BatchNormalization(),
        MaxPooling2D(pool_size=(2, 2)),
        Dropout(0.25),

        # Block 2
        Conv2D(64, (3, 3), activation="relu"),
        BatchNormalization(),
        MaxPooling2D(pool_size=(2, 2)),
        Dropout(0.25),

        # Block 3
        Conv2D(128, (3, 3), activation="relu"),
        BatchNormalization(),
        MaxPooling2D(pool_size=(2, 2)),
        Dropout(0.25),

        # Classifier head
        Flatten(),
        Dense(256, activation="relu"),
        Dropout(0.5),
        Dense(1, activation="sigmoid"),   # binary output
    ])

    model.compile(
        optimizer="adam",
        loss="binary_crossentropy",
        metrics=["accuracy"],
    )
    return model


def plot_training_history(history, save_path="training_history.png"):
    """Save accuracy & loss curves to a PNG file."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Accuracy
    ax1.plot(history.history["accuracy"], label="Train Accuracy", linewidth=2)
    ax1.plot(history.history["val_accuracy"], label="Val Accuracy", linewidth=2)
    ax1.set_title("Model Accuracy", fontsize=14, fontweight="bold")
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Accuracy")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Loss
    ax2.plot(history.history["loss"], label="Train Loss", linewidth=2)
    ax2.plot(history.history["val_loss"], label="Val Loss", linewidth=2)
    ax2.set_title("Model Loss", fontsize=14, fontweight="bold")
    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("Loss")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plot_path = os.path.join(os.path.dirname(__file__), save_path)
    plt.savefig(plot_path, dpi=150)
    plt.close()
    print(f"[PLOT] Training curves saved to: {plot_path}")


def train(dataset_path: str):
    """Full training pipeline."""
    print("=" * 60)
    print("   [FIRE] FIRE & SMOKE DETECTION - MODEL TRAINING")
    print("=" * 60)

    # 1. Load data
    images, labels = load_dataset(dataset_path)

    # 2. Train/validation split (80/20)
    X_train, X_val, y_train, y_val = train_test_split(
        images, labels, test_size=0.2, random_state=42, stratify=labels
    )
    print(f"[DATA] Train: {len(X_train)}  |  Validation: {len(X_val)}")

    # 3. Build model
    model = build_model()
    model.summary()

    # 4. Callbacks
    callbacks = [
        EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True),
        ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=3, min_lr=1e-6),
    ]

    # 5. Train
    print("\n[START] Starting training...\n")
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=callbacks,
        verbose=1,
    )

    # 6. Evaluate
    val_loss, val_acc = model.evaluate(X_val, y_val, verbose=0)
    print(f"\n{'=' * 60}")
    print(f"   [DONE] TRAINING COMPLETE")
    print(f"   Validation Accuracy : {val_acc * 100:.2f}%")
    print(f"   Validation Loss     : {val_loss:.4f}")
    print(f"{'=' * 60}")

    # 7. Save model
    model.save(MODEL_SAVE_PATH)
    print(f"[SAVE] Model saved to: {MODEL_SAVE_PATH}")

    # 8. Plot history
    plot_training_history(history)

    return model


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train fire/smoke detection CNN model")
    parser.add_argument(
        "--dataset", type=str, required=True,
        help="Path to dataset folder containing 'fire/' and 'non_fire/' subfolders"
    )
    args = parser.parse_args()

    if not os.path.isdir(args.dataset):
        print(f"[ERROR] Dataset path not found: {args.dataset}")
        exit(1)

    train(args.dataset)
