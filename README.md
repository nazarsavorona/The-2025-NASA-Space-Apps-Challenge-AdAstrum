# Hunting for Exoplanets with AI - Experimental Suite

A comprehensive machine learning project for detecting exoplanets using NASA's Kepler, K2, and TESS mission data.

## 📊 Project Overview

This project implements a complete experimental pipeline for exoplanet detection using various machine learning and deep learning approaches. The project includes:
- **Single-mission analysis**: Detailed experiments on Kepler dataset (11 experiments)
- **Multi-mission unified dataset**: Combined analysis of Kepler, K2, and TESS data (21,271 samples)
- Comprehensive model evaluation and cross-mission validation

## 🗂️ Datasets

### Available Datasets
1. **Kepler Mission**: 9,564 samples - Original Kepler mission data
2. **K2 Mission**: 4,004 samples - Kepler's extended mission
3. **TESS/TOI**: 7,703 samples - Transiting Exoplanet Survey Satellite
4. **Unified Dataset**: 21,271 samples - Intelligently combined data from all three missions

### Unified Dataset Features
The unified dataset (`unified_exoplanets.csv`) harmonizes features across missions:
- **48 total features** including source identifier (removed fp_flags due to data leakage)
- **Core features (>90% completeness)**: orbital period, stellar properties, transit characteristics
- **Mission-specific features**: signal-to-noise, number of transits, TESS magnitude
- **Standardized disposition**: Binary classification (CANDIDATE=1, FALSE POSITIVE=0)
- **⚠️ Data Leakage Prevention**: Removed false positive flags (koi_fpflag_*) as they are derived from disposition

See [UNIFIED_DATASET.md](UNIFIED_DATASET.md) for detailed documentation.

## 🔬 Experimental Pipeline

### **Experiment 1: Data Exploration & Understanding**
- Load and analyze Kepler dataset structure
- Examine target distribution (CANDIDATE vs FALSE POSITIVE)
- Identify missing values and data quality issues
- Statistical analysis of key features

### **Experiment 2: Data Preprocessing & Feature Selection**
- Create binary classification target
- Select relevant features (transit, orbital, and stellar properties)
- Handle missing values
- Train-test split with stratification
- **🔍 Data leakage checks** to ensure no target information in features

### **Experiment 3: Feature Engineering & Analysis**
- Correlation analysis and visualization (inter-feature correlations)
- **Feature-Target correlation analysis:**
  - Point-biserial correlation coefficients
  - Statistical significance tests (Mann-Whitney U)
  - Visualization of top correlated features
  - Scatter plots and distribution analysis by class
- Feature distribution analysis by class
- Create derived features:
  - Signal strength
  - Transit duty cycle
  - Radius ratio
- **Column tracking** for each experiment

### **Experiment 4: Baseline Models**
- Logistic Regression
- Decision Tree
- Establish performance benchmarks

### **Experiment 5: Advanced Machine Learning Models**
- Random Forest with feature importance
- XGBoost (Gradient Boosting)
- LightGBM
- Support Vector Machine (SVM)

### **Experiment 6: Deep Learning Approaches**
- Simple Feedforward Neural Network
- Deep Neural Network with Batch Normalization
- Training history visualization
- Early stopping and learning rate scheduling

### **Experiment 7: Ensemble Methods**
- Voting Ensemble (soft voting)
- Stacking Ensemble with meta-learner
- Custom Weighted Ensemble based on CV performance

### **Experiment 8: Hyperparameter Optimization**
- Random Search for XGBoost parameters
- Cross-validation strategies

### **Experiment 9: Handling Class Imbalance**
- SMOTE (Synthetic Minority Over-sampling)
- Class weight adjustments
- Comparative analysis

### **Experiment 10: Model Evaluation & Comparison**
- Comprehensive metrics comparison (Accuracy, Precision, Recall, F1, ROC-AUC)
- ROC curve visualization for all models
- Confusion matrices for top performers
- Performance visualization

### **Experiment 11: Advanced Feature Analysis**
- SHAP values for model interpretability
- Prediction confidence analysis
- Feature importance deep dive

### **🔒 Data Leakage Audit**
- Comprehensive tracking of features used in each experiment
- Validation checks before each training phase
- Complete audit summary ensuring no information leakage
- Verification of train-test split integrity

## � Multi-Mission Unified Analysis

The `unified_exoplanets.ipynb` notebook provides:

### **1. Dataset Unification**
- Intelligent column mapping across Kepler, K2, and TESS
- Standardized feature names and units
- Disposition normalization to binary classification

### **2. Cross-Mission Validation**
- Train on one mission, test on another
- Evaluate generalization across instruments
- Performance matrix showing cross-mission accuracy

### **3. Single vs Multi-Mission Comparison**
- Compare models trained on individual missions
- Evaluate benefits of combined training data
- Assess impact of 2.2x more training samples

### **4. Mission-Specific Performance**
- Analyze unified model performance per mission
- Identify mission-specific patterns
- Feature importance across different instruments

### **5. Best Practices**
- Missing value handling strategies
- Feature selection for multi-source data
- Source identifier utilization

## �📈 Key Features

### Data Analysis
- **21,271 total samples** across three missions:
  - Kepler: 9,564 samples
  - K2: 4,004 samples  
  - TESS/TOI: 7,703 samples
- **52 unified features** with intelligent mapping
- **Multiple feature groups**: Transit properties, orbital characteristics, stellar properties, error flags
- Class imbalance handling with multiple strategies

### Models Implemented
- **Traditional ML**: Logistic Regression, Decision Tree, SVM
- **Ensemble Methods**: Random Forest, XGBoost, LightGBM
- **Deep Learning (PyTorch)**: Feedforward NN, Deep NN with BatchNorm
- **Meta-Ensembles**: Voting, Stacking, Weighted averaging

### Evaluation Metrics
- Accuracy, Precision, Recall, F1-Score
- ROC-AUC (primary metric for imbalanced data)
- Confusion matrices
- Cross-validation scores

## 🚀 Getting Started

### Prerequisites
```bash
# Required packages
pandas
numpy
matplotlib
seaborn
scikit-learn
xgboost
lightgbm
torch
torchvision
imbalanced-learn
shap
scipy
```

### Installation
```bash
# Clone the repository
git clone https://github.com/nazarsavorona/The-2025-NASA-Space-Apps-Challenge-AdAstrum.git
cd The-2025-NASA-Space-Apps-Challenge-AdAstrum

# Install dependencies using UV (recommended)
uv sync

# Or install manually
pip install pandas numpy matplotlib seaborn scikit-learn xgboost lightgbm torch torchvision imbalanced-learn shap scipy
```

### Quick Start

#### Single Mission Analysis (Kepler)
```bash
# Open the main Kepler analysis notebook
jupyter notebook kepler.ipynb

# Or run experiments programmatically
python main.py
```

#### Multi-Mission Unified Analysis
```bash
# Step 1: Create unified dataset (if not already created)
python data_unification.py

# Step 2: Run unified analysis
jupyter notebook unified_exoplanets.ipynb

# The unified dataset will be saved to: data/input/unified_exoplanets.csv
```

#### Analyze Dataset Structure
```bash
# Compare all three datasets
python data_analysis.py
```
cd The-2025-NASA-Space-Apps-Challenge-AdAstrum

# Install dependencies (if using uv)
uv sync
```

### Running the Experiments
1. Open `kepler.ipynb` in Jupyter Notebook or VS Code
2. Run cells sequentially to execute all experiments
3. Results and visualizations will be generated inline

## 📊 Expected Results

### Model Performance
- **Baseline models**: 75-85% accuracy
- **Advanced ensemble methods**: 85-95% accuracy
- **Best ROC-AUC**: Typically 0.90-0.98

### Important Features
1. Transit depth (`koi_depth`)
2. Orbital period (`koi_period`)
3. Transit duration (`koi_duration`)
4. Stellar properties (temperature, radius, mass)
5. Signal-to-noise ratio

### ⚠️ Important Note on kepler.ipynb
The original `kepler.ipynb` notebook **includes false positive flags (koi_fpflag_*)** which cause data leakage.
- **For learning purposes**: The notebook demonstrates what NOT to do
- **For production use**: Use `unified_exoplanets.ipynb` which excludes these features
- See `FP_FLAGS_REMOVAL.md` for detailed explanation

## 🔍 Key Insights

### Best Practices
1. **Ensemble methods** consistently outperform single models
2. **Tree-based models** (XGBoost, LightGBM, Random Forest) work best for this tabular data
3. **Class imbalance** must be addressed through SMOTE or class weights
4. **Feature engineering** significantly improves model performance

### Recommendations
- Use **XGBoost or LightGBM** for production deployment (best speed/accuracy trade-off)
- Apply **Stacking Ensemble** for maximum accuracy
- Implement **confidence thresholds** for reliable predictions
- Monitor **prediction confidence levels** in production

## 📁 Project Structure
```
.
├── kepler.ipynb          # Main experimental notebook
├── data/
│   └── input/
│       └── kepler.csv    # Kepler dataset
├── README.md             # This file
├── LICENSE
├── pyproject.toml        # Project dependencies
└── uv.lock              # Lock file
```

## 🎯 Future Enhancements

### Advanced Techniques
1. **Time Series Analysis**: Analyze full light curve data with CNNs/RNNs
2. **Transfer Learning**: Use pre-trained models from similar astronomical tasks
3. **Active Learning**: Iteratively improve model with human expert feedback
4. **Multi-class Classification**: Distinguish between different types of false positives

### Production Deployment
1. Build REST API for real-time predictions
2. Create interactive visualization dashboard
3. Implement model monitoring and retraining pipeline
4. Add explainability layer for astronomers

## 📚 References

- NASA Exoplanet Archive: http://exoplanetarchive.ipac.caltech.edu
- Kepler Mission: https://www.nasa.gov/mission_pages/kepler/main/index.html
- Exoplanet Detection Methods: https://exoplanets.nasa.gov/alien-worlds/ways-to-find-a-planet/

## 🤝 Contributing

This is a NASA Space Apps Challenge 2025 project. Contributions, issues, and feature requests are welcome!

## 📝 License

See LICENSE file for details.

## 👥 Team

**AdAstrum** - NASA Space Apps Challenge 2025

---

**Note**: This experimental suite provides a comprehensive framework for exoplanet detection. Results may vary based on data quality and specific hyperparameter choices. Always validate models thoroughly before production use.
