import numpy as np
from sklearn.preprocessing import StandardScaler
from . import Model
from datetime import datetime

class KNN(Model):
    """Model class untuk K-Nearest Neighbors"""

    @staticmethod
    def euclidean_distance(x1, x2, weights=None):
        """Calculate Euclidean distance with optional feature weights"""
        if weights is None:
            weights = np.ones(len(x1))
        return np.sqrt(np.sum(weights * (x1 - x2) ** 2))

    @classmethod
    def predict(cls, X_train, y_train, X_test, k=3, weights=None):
        """
        Predict status gizi using KNN algorithm
        
        Parameters:
        -----------
        X_train : array-like of shape (n_samples, n_features)
            Training data
        y_train : array-like of shape (n_samples,)
            Target values for training data
        X_test : array-like of shape (n_samples, n_features)
            Test data
        k : int, default=3
            Number of neighbors
        weights : array-like of shape (n_features,), default=None
            Feature weights for distance calculation
            
        Returns:
        --------
        predictions : array of shape (n_samples,)
            Predicted classes
        """
        if weights is None:
            weights = np.ones(X_train.shape[1])
            
        # Normalize feature weights
        weights = np.array(weights) / np.sum(weights)
        
        # Initialize scaler
        scaler = StandardScaler()
        
        # Fit and transform training data
        X_train_scaled = scaler.fit_transform(X_train)
        
        # Transform test data
        X_test_scaled = scaler.transform(X_test)
        
        # Initialize predictions array
        predictions = []
        
        # For each test instance
        for x_test in X_test_scaled:
            # Calculate distances to all training instances
            distances = []
            for x_train in X_train_scaled:
                dist = cls.euclidean_distance(x_test, x_train, weights)
                distances.append(dist)
            
            # Get k nearest neighbors
            k_indices = np.argsort(distances)[:k]
            k_nearest_labels = [y_train[i] for i in k_indices]
            
            # Predict class by majority vote
            prediction = max(set(k_nearest_labels), key=k_nearest_labels.count)
            predictions.append(prediction)
        
        return np.array(predictions)

    @classmethod
    def get_parameters(cls):
        """Get current KNN parameters from database"""
        query = "SELECT * FROM parameter_knn ORDER BY id DESC LIMIT 1"
        return cls.query_db(query, one=True)

    @classmethod
    def save_parameters(cls, nilai_k, bobot_berat, bobot_tinggi, bobot_lila):
        """Save KNN parameters to database"""
        data = {
            'nilai_k': nilai_k,
            'bobot_berat': bobot_berat,
            'bobot_tinggi': bobot_tinggi,
            'bobot_lila': bobot_lila,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        return cls.insert_db('parameter_knn', data)

    @classmethod
    def evaluate(cls, X_train, y_train, X_val, y_val, k=3, weights=None):
        """
        Evaluate KNN model performance
        
        Returns accuracy and confusion matrix
        """
        # Get predictions
        y_pred = cls.predict(X_train, y_train, X_val, k, weights)
        
        # Calculate accuracy
        accuracy = np.mean(y_pred == y_val)
        
        # Calculate confusion matrix
        classes = sorted(set(y_train))
        conf_matrix = np.zeros((len(classes), len(classes)))
        
        for true, pred in zip(y_val, y_pred):
            i = classes.index(true)
            j = classes.index(pred)
            conf_matrix[i][j] += 1
            
        return {
            'accuracy': accuracy,
            'confusion_matrix': conf_matrix,
            'classes': classes
        }

    @classmethod
    def save_accuracy(cls, accuracy, parameter_id):
        """Save model accuracy to database"""
        data = {
            'accuracy': accuracy,
            'parameter_id': parameter_id,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        return cls.insert_db('accuracy_history', data)

    @classmethod
    def get_accuracy_history(cls):
        """Get accuracy history with parameters"""
        query = """
            SELECT a.*, p.nilai_k, p.bobot_berat, p.bobot_tinggi, p.bobot_lila
            FROM accuracy_history a
            JOIN parameter_knn p ON a.parameter_id = p.id
            ORDER BY a.created_at DESC
            LIMIT 10
        """
        return cls.query_db(query)