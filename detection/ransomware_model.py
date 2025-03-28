import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import StandardScaler
import joblib

# Load the dataset
def load_dataset(file_path):
    return pd.read_csv(file_path)

# Train a RandomForest model with hyperparameter tuning and feature scaling
def train_model(dataset):
    X = dataset.drop('label', axis=1)
    y = dataset['label']

    # Feature scaling
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.3, random_state=42)

    # Hyperparameter tuning
    param_grid = {
        'n_estimators': [100, 150, 200],
        'max_depth': [10, 20, 30],
        'min_samples_split': [2, 5, 10]
    }
    model = RandomForestClassifier(random_state=42)
    grid_search = GridSearchCV(model, param_grid, cv=5, n_jobs=-1, scoring='accuracy')
    grid_search.fit(X_train, y_train)

    best_model = grid_search.best_estimator_

    # Save the trained model
    joblib.dump(best_model, 'ransomware_detection_model.pkl')

    # Evaluate the model
    y_pred = best_model.predict(X_test)
    print("Accuracy: ", accuracy_score(y_test, y_pred))
    print("Classification Report:\n", classification_report(y_test, y_pred))

# Detection function using the trained model
def detect_ransomware(features):
    model = joblib.load('ransomware_detection_model.pkl')
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform([features])
    prediction = model.predict(features_scaled)

    if prediction[0] == 1:
        print("Ransomware detected!")
        return True
    else:
        print("No ransomware detected.")
        return False

if __name__ == "__main__":
    # Train model with dataset
    dataset_path = 'ransomware_data.csv'
    dataset = load_dataset(dataset_path)
    train_model(dataset)

    # Simulate new data for detection
    test_features = [0.2, 0.4, 0.1, 100, 1500, 0.2]
    detect_ransomware(test_features)