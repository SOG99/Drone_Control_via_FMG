import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
from sklearn.preprocessing import MinMaxScaler
import pickle

# Load the data
df = pd.read_excel("./shuffled_file.xlsx")

# Separate features and target labels
X = df.iloc[:, 1:-1].values    
y = df.iloc[:, -1].values    

# Split data into training and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Initialize the KNeighborsClassifier
clf = KNeighborsClassifier(n_neighbors=5)

# Train the classifier
clf.fit(X_train, y_train)

# Predictions on the test set
y_pred = clf.predict(X_test)

# Save the trained model to a file
with open('knn_model.pkl', 'wb') as f:
    pickle.dump(clf, f)

# Evaluate accuracy
accuracy = accuracy_score(y_test, y_pred)
print("Accuracy:", accuracy)

# Additional metrics
precision = precision_score(y_test, y_pred, average='weighted')
recall = recall_score(y_test, y_pred, average='weighted')
f1 = f1_score(y_test, y_pred, average='weighted')

print("Weighted Precision:", precision)
print("Weighted Recall:", recall)
print("Weighted F1-Score:", f1)

# Classification report
print("Classification Report:")
print(classification_report(y_test, y_pred))
