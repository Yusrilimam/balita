import numpy as np
from sklearn.preprocessing import StandardScaler
from . import Model
from datetime import datetime

class LVQ(Model):
    """Model class untuk Learning Vector Quantization"""

    def __init__(self, n_epochs=100, learning_rate=0.1):
        """
        Initialize LVQ model
        
        Parameters:
        -----------
        n_epochs : int, default=100
            Number of training epochs
        learning_rate : float, default=0.1
            Initial learning rate
        """
        self.n_epochs = n_epochs
        self.learning_rate = learning_rate
        self.codebook_vectors = None
        self.codebook_labels = None
        self.scaler = StandardScaler()

    def initialize_codebook(self, X, y):
        """Initialize codebook vectors"""
        classes = np.unique(y)
        self.codebook_vectors = []
        self.codebook_labels = []
        
        # For each class, select first instance as initial codebook vector
        for c in classes:
            idx = np.where(y == c)[0][0]
            self.codebook_vectors.append(X[idx])
            self.codebook_labels.append(c)
            
        self.codebook_vectors = np.array(self.codebook_vectors)
        self.codebook_labels = np.array(self.codebook_labels)

    def euclidean_distance(self, x1, x2):
        """Calculate Euclidean distance between two vectors"""
        return np.sqrt(np.sum((x1 - x2) ** 2))

    def fit(self, X, y):
        """
        Train LVQ model
        
        Parameters:
        -----------
        X : array-like of shape (n_samples, n_features)
            Training data
        y : array-like of shape (n_samples,)
            Target values
        """
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Initialize codebook vectors
        self.initialize_codebook(X_scaled, y)
        
        # Training loop
        for epoch in range(self.n_epochs):
            # Decrease learning rate
            current_lr = self.learning_rate * (1 - epoch/self.n_epochs)
            
            # Shuffle training data
            indices = np.random.permutation(len(X_scaled))
            X_shuffled = X_scaled[indices]
            y_shuffled = y[indices]
            
            # Update codebook vectors
            for x, target in zip(X_shuffled, y_shuffled):
                # Find closest codebook vector
                distances = [self.euclidean_distance(x, w) for w in self.codebook_vectors]
                winner_idx = np.argmin(distances)
                winner = self.codebook_vectors[winner_idx]
                winner_label = self.codebook_labels[winner_idx]
                
                # Update winner vector
                if winner_label == target:
                    # Move closer
                    self.codebook_vectors[winner_idx] += current_lr * (x - winner)
                else:
                    # Move away
                    self.codebook_vectors[winner_idx] -= current_lr * (x - winner)

    def predict(self, X):
        """
        Predict using trained LVQ model
        
        Parameters:
        -----------
        X : array-like of shape (n_samples, n_features)
            Test data
            
        Returns:
        --------
        predictions : array of shape (n_samples,)
            Predicted classes
        """
        # Scale features
        X_scaled = self.scaler.transform(X)
        
        predictions = []
        for x in X_scaled:
            # Find closest codebook vector
            distances = [self.euclidean_distance(x, w) for w in self.codebook_vectors]
            winner_idx = np.argmin(distances)
            predictions.append(self.codebook_labels[winner_idx])
            
        return np.array(predictions)

    def evaluate(self, X_test, y_test):
        """
        Evaluate LVQ model performance
        
        Returns accuracy and confusion matrix
        """
        # Get predictions
        y_pred = self.predict(X_test)
        
        # Calculate accuracy
        accuracy = np.mean(y_pred == y_test)
        
        # Calculate confusion matrix
        classes = sorted(set(self.codebook_labels))
        conf_matrix = np.zeros((len(classes), len(classes)))
        
        for true, pred in zip(y_test, y_pred):
            i = classes.index(true)
            j = classes.index(pred)
            conf_matrix[i][j] += 1
            
        return {
            'accuracy': accuracy,
            'confusion_matrix': conf_matrix,
            'classes': classes
        }

    @classmethod
    def save_accuracy(cls, accuracy, model_params):
        """Save model accuracy and parameters to database"""
        data = {
            'algorithm': 'LVQ',
            'accuracy': accuracy,
            'parameters': str(model_params),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        return cls.insert_db('model_performance', data)

    @classmethod
    def get_performance_history(cls):
        """Get LVQ performance history"""
        query = """
            SELECT *
            FROM model_performance
            WHERE algorithm = 'LVQ'
            ORDER BY created_at DESC
            LIMIT 10
        """
        return cls.query_db(query)