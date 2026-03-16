# ==============================
# CyberTrust Africa
# Entrainement du modèle IA
# ==============================

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib

# 1️⃣ Charger les deux fichiers
train_data = pd.read_csv("dataset/train.csv")
test_data = pd.read_csv("dataset/test.csv")

# 2️⃣ Combiner les deux fichiers
data = pd.concat([train_data, test_data], ignore_index=True)

# 3️⃣ Sélectionner les variables
features = [
    "profile pic",
    "nums/length username",
    "fullname words",
    "nums/length fullname",
    "name==username",
    "description length",
    "external URL",
    "private",
    "#posts",
    "#followers",
    "#follows"
]

X = data[features]

# Variable cible
# 0 = vrai compte
# 1 = faux compte
y = data["fake"]

# 4️⃣ Séparer les données
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42
)

# 5️⃣ Créer le modèle IA
model = RandomForestClassifier(
    n_estimators=200,
    max_depth=10,
    random_state=42
)

# 6️⃣ Entraîner le modèle
model.fit(X_train, y_train)

# 7️⃣ Tester le modèle
predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)
print("Précision du modèle :", round(accuracy * 100, 2), "%")

# 8️⃣ Sauvegarder le modèle
joblib.dump(model, "models/cybertrust_model.pkl")
print("Modèle sauvegardé avec succès !")