"""
Train RNN, LSTM, biLSTM models for user behavior classification.
Input: data/data_user500.csv (500 users × 8 behaviors)
Output: Trained models + evaluation metrics + plots

Usage: python ai_service/scripts/train_behavior_models.py
"""
import os, sys, json
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report, confusion_matrix
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from ai_service.models.behavior_models import RNNClassifier, LSTMClassifier, BiLSTMClassifier

DATA_PATH = os.path.join("data", "data_user500.csv")
MODEL_DIR = os.path.join("data", "models", "behavior")
PLOT_DIR = os.path.join("docs", "plots")
SEED = 42
EPOCHS = 50
BATCH_SIZE = 32
HIDDEN_DIM = 64
LR = 1e-3
SEQ_LEN = 8  # 8 behaviors as sequence

class RNNClassifier(nn.Module):
    def __init__(self, input_size, hidden_size, num_classes):
        super().__init__()
        self.rnn = nn.RNN(input_size, hidden_size, batch_first=True)
        self.fc = nn.Linear(hidden_size, num_classes)

    def forward(self, x):
        _, h = self.rnn(x)
        return self.fc(h.squeeze(0))


class LSTMClassifier(nn.Module):
    def __init__(self, input_size, hidden_size, num_classes):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True)
        self.fc = nn.Linear(hidden_size, num_classes)

    def forward(self, x):
        _, (h, _) = self.lstm(x)
        return self.fc(h.squeeze(0))


class BiLSTMClassifier(nn.Module):
    def __init__(self, input_size, hidden_size, num_classes):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True, bidirectional=True)
        self.fc = nn.Linear(hidden_size * 2, num_classes)

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :])


# ── Training ───────────────────────────────────────────────────

def prepare_data():
    df = pd.read_csv(DATA_PATH)
    features = ["view", "click", "cart", "purchase", "search", "wishlist", "review", "share"]
    X = df[features].values.astype(np.float32)
    le = LabelEncoder()
    y = le.fit_transform(df["segment"])

    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    # Reshape: (batch, seq_len=8, input_size=1) - treat each behavior as a timestep
    X = X.reshape(-1, SEQ_LEN, 1)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=SEED, stratify=y
    )
    return X_train, X_test, y_train, y_test, le, scaler


def train_model(model, train_loader, epochs=EPOCHS):
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    criterion = nn.CrossEntropyLoss()
    history = {"loss": [], "acc": []}

    for epoch in range(epochs):
        model.train()
        total_loss, correct, total = 0, 0, 0
        for X_batch, y_batch in train_loader:
            optimizer.zero_grad()
            out = model(X_batch)
            loss = criterion(out, y_batch)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            correct += (out.argmax(1) == y_batch).sum().item()
            total += len(y_batch)

        history["loss"].append(total_loss / len(train_loader))
        history["acc"].append(correct / total)

    return history


def evaluate_model(model, X_test, y_test):
    model.eval()
    with torch.no_grad():
        X_t = torch.tensor(X_test, dtype=torch.float32)
        preds = model(X_t).argmax(1).numpy()

    return {
        "accuracy": accuracy_score(y_test, preds),
        "precision": precision_score(y_test, preds, average="weighted", zero_division=0),
        "recall": recall_score(y_test, preds, average="weighted", zero_division=0),
        "f1": f1_score(y_test, preds, average="weighted", zero_division=0),
        "predictions": preds,
    }


# ── Visualization ──────────────────────────────────────────────

def plot_training_history(histories, names):
    os.makedirs(PLOT_DIR, exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

    for name, hist in zip(names, histories):
        ax1.plot(hist["loss"], label=name)
        ax2.plot(hist["acc"], label=name)

    ax1.set_title("Training Loss")
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Loss")
    ax1.legend()

    ax2.set_title("Training Accuracy")
    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("Accuracy")
    ax2.legend()

    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "training_curves.png"), dpi=150)
    plt.close()


def plot_comparison(results, names):
    os.makedirs(PLOT_DIR, exist_ok=True)
    metrics = ["accuracy", "precision", "recall", "f1"]
    data = {m: [results[n][m] for n in names] for m in metrics}

    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(metrics))
    width = 0.25

    for i, name in enumerate(names):
        vals = [results[name][m] for m in metrics]
        ax.bar(x + i * width, vals, width, label=name)

    ax.set_xticks(x + width)
    ax.set_xticklabels([m.capitalize() for m in metrics])
    ax.set_ylabel("Score")
    ax.set_title("Model Comparison")
    ax.legend()
    ax.set_ylim(0, 1)

    for i, name in enumerate(names):
        for j, m in enumerate(metrics):
            ax.text(j + i * width, results[name][m] + 0.02,
                    f"{results[name][m]:.3f}", ha="center", fontsize=7)

    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "model_comparison.png"), dpi=150)
    plt.close()


def plot_confusion_matrices(results, names, le):
    os.makedirs(PLOT_DIR, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    for ax, name in zip(axes, names):
        cm = confusion_matrix(results[name]["y_test"], results[name]["predictions"])
        sns.heatmap(cm, annot=True, fmt="d", ax=ax, cmap="Blues",
                    xticklabels=le.classes_, yticklabels=le.classes_)
        ax.set_title(f"{name}")
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Actual")

    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "confusion_matrices.png"), dpi=150)
    plt.close()


# ── Main ───────────────────────────────────────────────────────

def main():
    torch.manual_seed(SEED)
    np.random.seed(SEED)

    print("=" * 60)
    print("BEHAVIOR CLASSIFICATION: RNN vs LSTM vs BiLSTM")
    print("=" * 60)

    # Prepare data
    X_train, X_test, y_train, y_test, le, scaler = prepare_data()
    num_classes = len(le.classes_)
    print(f"\nData: {X_train.shape[0]} train, {X_test.shape[0]} test, {num_classes} classes")
    print(f"Classes: {list(le.classes_)}")

    train_ds = TensorDataset(
        torch.tensor(X_train, dtype=torch.float32),
        torch.tensor(y_train, dtype=torch.long)
    )
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)

    # Define models
    models = {
        "RNN": RNNClassifier(1, HIDDEN_DIM, num_classes),
        "LSTM": LSTMClassifier(1, HIDDEN_DIM, num_classes),
        "BiLSTM": BiLSTMClassifier(1, HIDDEN_DIM, num_classes),
    }

    # Train and evaluate
    histories = []
    results = {}
    names = list(models.keys())

    for name, model in models.items():
        print(f"\n{'─' * 40}")
        print(f"Training {name}...")
        hist = train_model(model, train_loader)
        histories.append(hist)

        res = evaluate_model(model, X_test, y_test)
        res["y_test"] = y_test
        results[name] = res

        print(f"  Accuracy:  {res['accuracy']:.4f}")
        print(f"  Precision: {res['precision']:.4f}")
        print(f"  Recall:    {res['recall']:.4f}")
        print(f"  F1-Score:  {res['f1']:.4f}")

    # Select best model
    best_name = max(names, key=lambda n: results[n]["f1"])
    print(f"\n{'=' * 60}")
    print(f"BEST MODEL: {best_name} (F1={results[best_name]['f1']:.4f})")
    print(f"{'=' * 60}")

    # Detailed report for best model
    print(f"\nClassification Report ({best_name}):")
    preds = results[best_name]["predictions"]
    print(classification_report(y_test, preds, target_names=le.classes_))

    # Save models
    os.makedirs(MODEL_DIR, exist_ok=True)
    for name, model in models.items():
        torch.save(model.state_dict(), os.path.join(MODEL_DIR, f"{name.lower()}_model.pt"))

    # Save best model info
    best_info = {
        "best_model": best_name,
        "metrics": {n: {k: v for k, v in r.items() if k != "predictions" and k != "y_test"} for n, r in results.items()},
        "classes": list(le.classes_),
        "num_users": 500,
        "num_behaviors": 8,
        "hidden_dim": HIDDEN_DIM,
        "epochs": EPOCHS,
    }
    with open(os.path.join(MODEL_DIR, "evaluation_results.json"), "w") as f:
        json.dump(best_info, f, indent=2)

    # Save scaler and label encoder
    import pickle
    with open(os.path.join(MODEL_DIR, "scaler.pkl"), "wb") as f:
        pickle.dump(scaler, f)
    with open(os.path.join(MODEL_DIR, "label_encoder.pkl"), "wb") as f:
        pickle.dump(le, f)

    # Generate plots
    print("\nGenerating plots...")
    plot_training_history(histories, names)
    plot_comparison(results, names)
    plot_confusion_matrices(results, names, le)
    print(f"Plots saved to {PLOT_DIR}/")

    # Evaluation commentary
    print(f"\n{'=' * 60}")
    print("ĐÁNH GIÁ MÔ HÌNH:")
    print(f"{'=' * 60}")
    for name in names:
        r = results[name]
        print(f"\n{name}:")
        print(f"  - Accuracy: {r['accuracy']:.4f}, F1: {r['f1']:.4f}")

    print(f"\n→ Kết luận: {best_name} cho kết quả tốt nhất với F1={results[best_name]['f1']:.4f}")
    if best_name == "BiLSTM":
        print("  BiLSTM tận dụng thông tin hai chiều (forward + backward) nên nắm bắt")
        print("  được mối quan hệ giữa các hành vi tốt hơn RNN và LSTM đơn hướng.")
    elif best_name == "LSTM":
        print("  LSTM xử lý tốt vấn đề vanishing gradient so với RNN cơ bản,")
        print("  giúp học được các pattern dài hạn trong chuỗi hành vi.")
    else:
        print("  RNN cơ bản đủ hiệu quả cho bài toán này do chuỗi hành vi ngắn (8 steps).")

    return best_name, results


if __name__ == "__main__":
    main()
