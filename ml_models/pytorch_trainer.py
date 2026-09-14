import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import logging

logger = logging.getLogger(__name__)

class CoastalAlertNet(nn.Module):
    def __init__(self, input_dim=6, num_classes=4):
        super(CoastalAlertNet, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.BatchNorm1d(64),
            nn.Dropout(0.3),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.BatchNorm1d(32),
            nn.Dropout(0.3),
            nn.Linear(32, num_classes)
        )
    
    def forward(self, x):
        return self.net(x)

class PyTorchModelTrainer:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
        self.model = None
        
        logger.info(f"PyTorch Device: {self.device}")
        if torch.cuda.is_available():
            logger.info(f"🚀 Acceleration: CUDA GPU -> {self.gpu_name}")
        else:
            logger.info("Running on CPU")

    def build_model(self, input_dim=6, num_classes=4):
        model = CoastalAlertNet(input_dim, num_classes).to(self.device)
        logger.info(f"PyTorch model initialized on {self.device}")
        return model

    def train_model(self, X_train, y_train, X_val=None, y_val=None, epochs=50, batch_size=32, lr=0.001):
        X_train_t = torch.tensor(X_train, dtype=torch.float32).to(self.device)
        y_train_t = torch.tensor(y_train, dtype=torch.long).to(self.device)
        
        train_dataset = TensorDataset(X_train_t, y_train_t)
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(self.model.parameters(), lr=lr)
        
        logger.info(f"Starting PyTorch model training on {self.gpu_name} ({epochs} epochs)...")
        
        for epoch in range(1, epochs + 1):
            self.model.train()
            total_loss = 0.0
            correct = 0
            total = 0
            
            for X_batch, y_batch in train_loader:
                optimizer.zero_grad()
                outputs = self.model(X_batch)
                loss = criterion(outputs, y_batch)
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item() * X_batch.size(0)
                _, predicted = torch.max(outputs, 1)
                total += y_batch.size(0)
                correct += (predicted == y_batch).sum().item()
            
            epoch_loss = total_loss / total
            epoch_acc = correct / total
            
            val_info = ""
            if X_val is not None and y_val is not None:
                val_loss, val_acc = self.evaluate_loss_acc(X_val, y_val, criterion)
                val_info = f" - val_loss: {val_loss:.4f} - val_acc: {val_acc:.4f}"
            
            if epoch % 5 == 0 or epoch == epochs or epoch == 1:
                logger.info(f"Epoch {epoch:2d}/{epochs} - loss: {epoch_loss:.4f} - acc: {epoch_acc:.4f}{val_info}")

        logger.info("✓ PyTorch training complete on GPU")

    def evaluate_loss_acc(self, X_val, y_val, criterion):
        self.model.eval()
        with torch.no_grad():
            X_val_t = torch.tensor(X_val, dtype=torch.float32).to(self.device)
            y_val_t = torch.tensor(y_val, dtype=torch.long).to(self.device)
            outputs = self.model(X_val_t)
            loss = criterion(outputs, y_val_t).item()
            _, predicted = torch.max(outputs, 1)
            acc = (predicted == y_val_t).float().mean().item()
        return loss, acc

    def evaluate_model(self, X_test, y_test):
        self.model.eval()
        with torch.no_grad():
            X_test_t = torch.tensor(X_test, dtype=torch.float32).to(self.device)
            outputs = self.model(X_test_t)
            probs = torch.softmax(outputs, dim=1).cpu().numpy()
            y_pred = np.argmax(probs, axis=1)
            
        accuracy = accuracy_score(y_test, y_pred)
        logger.info(f"Accuracy: {accuracy:.4f}")
        
        class_names = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        report = classification_report(
            y_test, y_pred, labels=[0, 1, 2, 3], target_names=class_names,
            zero_division=0, output_dict=True
        )
        logger.info(f"Classification Report:\n{report}")
        
        cm = confusion_matrix(y_test, y_pred)
        logger.info(f"Confusion Matrix:\n{cm}")
        
        return {
            "accuracy": accuracy,
            "classification_report": report,
            "confusion_matrix": cm.tolist(),
            "y_pred": y_pred,
            "y_pred_probs": probs,
        }

    def save_model(self, model_path):
        os.makedirs(os.path.dirname(model_path) or ".", exist_ok=True)
        torch.save(self.model.state_dict(), model_path)
        logger.info(f"PyTorch model weights saved to {model_path}")
