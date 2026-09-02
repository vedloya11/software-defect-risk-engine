# Predictive Code Quality & Software Defect Risk Engine

A machine learning system for predicting whether software modules/files are likely to be defect-prone using static code metrics and AST features.

---

## 📌 Project Overview
The goal of this engine is to assess defect risk in software modules prior to release or during code review. Rather than simply claiming to find specific bugs, the engine scores modules by their **defect risk probability** and highlights key contributing risk factors (e.g., high cyclomatic complexity, excessive coupling, or high operand density).

---

## 🚀 Development Phases

- [x] **Phase 0**: Project architecture and environment setup
- [x] **Phase 1**: Dataset inspection and schema understanding
- [x] **Phase 2**: Data validation and cleaning pipeline (`src/data/clean_data.py`)
- [x] **Phase 3**: Exploratory Data Analysis & Class Imbalance Analysis (`notebooks/Data_Exploration.ipynb`)
- [x] **Phase 4**: Feature Engineering (`src/features/build_features.py`)
- [ ] **Phase 5**: Proper Train/Validation/Test Split Strategy
- [ ] **Phase 6**: Baseline Logistic Regression
- [ ] **Phase 7**: Random Forest Classifier
- [ ] **Phase 8**: XGBoost Defect Classifier
- [ ] **Phase 9**: Hyperparameter Tuning
- [ ] **Phase 10**: Model Evaluation & Error Analysis
- [ ] **Phase 11**: SHAP Explainability Engine
- [ ] **Phase 12**: Export Production Pipeline
- [ ] **Phase 13**: Source Code AST Analysis Engine
- [ ] **Phase 14**: AST Feature Extraction & Metric Bridge
- [ ] **Phase 15**: FastAPI Backend
- [ ] **Phase 16**: Code Upload Prediction Endpoint
- [ ] **Phase 17**: PostgreSQL Integration
- [ ] **Phase 18**: Frontend Dashboard
- [ ] **Phase 19**: Dockerization & Container Setup
- [ ] **Phase 20**: Automated Unit & Integration Tests
- [ ] **Phase 21**: GitHub Actions CI/CD Pipeline
- [ ] **Phase 22**: MLflow Experiment Tracking
- [ ] **Phase 23**: Model & Data Drift Monitoring (Evidently)
- [ ] **Phase 24**: Cloud Deployment
- [ ] **Phase 25**: Final Documentation & Presentation

---

## 🛠️ Technology Stack
- **Languages & Frameworks**: Python, Pandas, NumPy, Scikit-learn, XGBoost
- **Explainability**: SHAP
- **Code Analysis**: Tree-sitter, AST, Radon
- **API & Backend**: FastAPI, Pydantic, PostgreSQL
- **MLOps**: MLflow, Evidently, Docker, GitHub Actions
- **Testing**: Pytest

---

## 📂 Project Structure
```text
software-defect-risk-engine/
│
├── data/
│   ├── raw/
│   │   └── SoftwareDefectDataset.csv
│   └── processed/
│       ├── cleaned_dataset.csv
│       └── engineered_dataset.csv
│
├── notebooks/
│   └── Data_Exploration.ipynb
│
├── src/
│   ├── data/
│   │   └── clean_data.py
│   └── features/
│       └── build_features.py
│
├── requirements.txt
├── .gitignore
└── README.md
```
