import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
import pickle
import os

print("=" * 50)
print("  CropSense AI — ML Model Training")
print("=" * 50)

# ── STEP 1: Load Dataset ──────────────────────────
print("\nLoading dataset...")
df = pd.read_csv(os.path.join(os.path.dirname(__file__), 'Crop_recommendation.csv'))
print(f"Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")
print(f"Columns: {list(df.columns)}")
print(f"Crops: {df['label'].nunique()} unique crops")
print(f"   {list(df['label'].unique())}")

# ── STEP 2: Explore Data ─────────────────────────
print("\nDataset Statistics:")
print(df.describe().round(2))

# ── STEP 3: Prepare Features ─────────────────────
print("\nPreparing features...")
X = df[['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']]
y = df['label']

print(f"Features: {list(X.columns)}")
print(f"Target: crop label")

# Label Encoding
le = LabelEncoder()
y_encoded = le.fit_transform(y)
print(f"Labels encoded: {len(le.classes_)} crops")

# ── STEP 4: Split Data ───────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)
print(f"\nTrain size: {len(X_train)} | Test size: {len(X_test)}")

# ── STEP 5: Train Model ──────────────────────────
print("\nTraining Random Forest model...")
model = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    random_state=42,
    n_jobs=-1
)
model.fit(X_train, y_train)
print("Model trained!")

# ── STEP 6: Evaluate ─────────────────────────────
print("\nModel Evaluation:")
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Accuracy: {accuracy * 100:.2f}%")

# Top 5 important features
feature_names = ['Nitrogen(N)', 'Phosphorus(P)', 'Potassium(K)',
                 'Temperature', 'Humidity', 'pH', 'Rainfall']
importances = model.feature_importances_
print("\nFeature Importance:")
for name, imp in sorted(zip(feature_names, importances),
                         key=lambda x: x[1], reverse=True):
    bar = '█' * int(imp * 40)
    print(f"   {name:15} {bar} {imp:.3f}")

# ── STEP 7: Save Model ───────────────────────────
print("\nSaving model files...")
model_dir = os.path.dirname(__file__)

# Save model
with open(os.path.join(model_dir, 'crop_model.pkl'), 'wb') as f:
    pickle.dump(model, f)
print("crop_model.pkl saved!")

# Save label encoder
with open(os.path.join(model_dir, 'label_encoder.pkl'), 'wb') as f:
    pickle.dump(le, f)
print("label_encoder.pkl saved!")

# Save crop info
with open(os.path.join(model_dir, 'crop_info.pkl'), 'wb') as f:
    pickle.dump({
        'crops': list(le.classes_),
        'features': list(X.columns),
        'accuracy': accuracy
    }, f)
print("crop_info.pkl saved!")

# ── STEP 8: Test Prediction ──────────────────────
print("\nTest Prediction:")
test_input = pd.DataFrame([[90, 42, 43, 20.87, 82.0, 6.5, 202.9]],
                           columns=['N', 'P', 'K', 'temperature',
                                   'humidity', 'ph', 'rainfall'])
pred = model.predict(test_input)
crop = le.inverse_transform(pred)[0]
proba = model.predict_proba(test_input)[0]
top3_idx = proba.argsort()[-3:][::-1]
print(f"   Input: N=90, P=42, K=43, Temp=20.87°C, Humidity=82%, pH=6.5, Rainfall=202mm")
print(f"   Predicted Crop: {crop.upper()}")
print(f"   Top 3 recommendations:")
for idx in top3_idx:
    print(f"   - {le.classes_[idx]:15} {proba[idx]*100:.1f}%")

print("\n" + "=" * 50)
print("  MODEL TRAINING COMPLETE!")
print(f"  Final Accuracy: {accuracy * 100:.2f}%")
print("=" * 50)