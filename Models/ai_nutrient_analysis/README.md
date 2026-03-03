# AI Nutrient Analysis Model

## Overview
The AI Nutrient Analysis Model is a machine learning system that provides intelligent recommendations for hydroponic nutrient solution management. This model uses Random Forest classification to analyze sensor readings and recommend appropriate actions to maintain optimal growing conditions.

**Version**: 1.0.0 | **Developer**: Afsa Umutoniwase | **Organization**: African Union Young Leaders Academy

## Model Details
- **Model Type**: Random Forest Classifier (Ensemble Learning)
- **Framework**: scikit-learn
- **Algorithm**: Ensemble of 100 Decision Trees
- **Task**: Multi-class Classification
- **Input Features**: 4 (Crop Type, pH Level, EC Value, Ambient Temperature)
- **Output Classes**: 5 (Add_pH_Up, Add_pH_Down, Add_Nutrients, Dilute, Maintain)
- **Model Size**: ~15 MB
- **Date**: March 2026

## Intended Use

### Primary Use Cases
1. **Real-time Nutrient Management** - Instant recommendations for adjusting hydroponic nutrient solutions
2. **Sensor Monitoring** - Analyze pH, EC, and temperature readings to maintain optimal conditions
3. **Decision Support** - Help farmers make informed decisions about nutrient solution adjustments
4. **Educational Tool** - Teach beginners about hydroponic nutrient management

### Target Users
- Small-scale hydroponic farmers in Africa (especially Rwanda)
- Urban farmers using affordable hydroponic systems
- Agricultural extension workers and educators
- Home gardeners experimenting with hydroponics

### Out-of-Scope Uses
⚠️ **Not intended for**:
- Commercial greenhouse automation without human oversight
- Soil-based agriculture (model is specific to hydroponics)
- Crops not included in training data
- Medical or pharmaceutical applications

## Performance Metrics

### Overall Performance
- **Accuracy**: 98.64%
- **Precision**: 98.63%
- **Recall**: 98.64%
- **F1-Score**: 98.63%

### Per-Class Performance
| Action | Precision | Recall | F1-Score |
|--------|-----------|--------|----------|
| Add_Nutrients | 0.98 | 0.99 | 0.98 |
| Add_pH_Down | 0.99 | 0.98 | 0.98 |
| Add_pH_Up | 0.99 | 0.99 | 0.99 |
| Dilute | 0.98 | 0.98 | 0.98 |
| Maintain | 0.99 | 0.98 | 0.98 |

**Comparison with Baseline**: Random Forest (98.64%) vs Logistic Regression (93.22%) - **+5.42% improvement**

## Features

### Input Parameters
1. **Crop_ID**: Type of crop being grown
   - Lettuce
   - Peppers
   - Tomatoes

2. **pH_Level**: Acidity/alkalinity of nutrient solution (0-14 scale)
   - Optimal range: 5.5-6.5

3. **EC_Value**: Electrical Conductivity (mS/cm)
   - Measures nutrient concentration
   - Typical range: 0.5-4.0 mS/cm

4. **Ambient_Temp**: Temperature in Celsius
   - Typical range: 15-32°C

### Output Actions
1. **Add_pH_Up**: Increase pH level (solution too acidic)
2. **Add_pH_Down**: Decrease pH level (solution too alkaline)
3. **Add_Nutrients**: Increase nutrient concentration (EC too low)
4. **Dilute**: Decrease nutrient concentration (EC too high)
5. **Maintain**: Parameters are optimal, maintain current levels

## Model Architecture

### Random Forest Classifier
```
Input Layer: 4 features
  ├── Crop_ID (encoded)
  ├── pH_Level (5.5-6.5 optimal)
  ├── EC_Value (mS/cm)
  └── Ambient_Temp (°C)
      ↓
Feature Encoding & Scaling
  ├── LabelEncoder for Crop_ID
  └── StandardScaler for numerical features
      ↓
Ensemble Layer: 100 Decision Trees
  ├── Max Depth: Unlimited
  ├── Min Samples Split: 2
  └── Min Samples Leaf: 1
      ↓
Voting & Aggregation
      ↓
Output: Action Recommendation (5 classes)
```

## Training Data

### Data Sources
The model was trained on a comprehensive dataset combining:

1. **IoT Sensor Data** (Kaggle) - ~10,000 records
   - Real-world sensor logs from hydroponic systems
   - Columns: pH, TDS, water level, temperature, humidity, actuator states
   - Geographic origin: Various (international)

2. **Synthetic Data** (Rwanda Context) - ~4,000 records
   - Generated to represent African farming conditions
   - Includes variability in ambient temperature and power supply
   - Addresses local environmental challenges

### Dataset Characteristics
**Total Training Data**: ~14,000+ records
- Lettuce: ~4,700 records (33%)
- Peppers: ~4,700 records (33%)
- Tomatoes: ~4,700 records (33%)

**Class Distribution**:
- Add_Nutrients: ~28%
- Add_pH_Down: ~23%
- Add_pH_Up: ~22%
- Dilute: ~15%
- Maintain: ~12%

**Data Preprocessing**:
- Missing values: Forward fill method
- Feature encoding: LabelEncoder for Crop_ID
- Feature scaling: StandardScaler for numerical features
- Train/Test split: 80/20 stratified

## Feature Importance
1. **EC_Value**: 35.2% - Most important feature
2. **pH_Level**: 34.8% - Nearly equal importance
3. **Ambient_Temp**: 18.5%
4. **Crop_ID**: 11.5%

## Files Included

### Model Files
- `random_forest_model.pkl` - Trained Random Forest model
- `feature_scaler.pkl` - StandardScaler for feature normalization
- `crop_encoder.pkl` - LabelEncoder for crop type encoding
- `action_encoder.pkl` - LabelEncoder for action class encoding
- `model_metadata.json` - Model configuration and performance metrics

### Training Materials
- `ai_nutrient_model_training.ipynb` - Complete training notebook with data visualization and model training

### Documentation
- `README.md` - This file
- `.gitignore` - Git configuration

## Usage

### Loading the Model
```python
import joblib
import numpy as np

# Load model components
model = joblib.load('random_forest_model.pkl')
scaler = joblib.load('feature_scaler.pkl')
crop_encoder = joblib.load('crop_encoder.pkl')
action_encoder = joblib.load('action_encoder.pkl')
```

### Making Predictions
```python
# Prepare input
crop_id = "Lettuce"
ph_level = 5.8
ec_value = 1.8
ambient_temp = 23.5

# Encode crop
crop_encoded = crop_encoder.transform([crop_id])[0]

# Create feature array
features = np.array([[crop_encoded, ph_level, ec_value, ambient_temp]])

# Scale features
features_scaled = scaler.transform(features)

# Predict action
prediction = model.predict(features_scaled)
action = action_encoder.inverse_transform(prediction)[0]

# Get confidence
probabilities = model.predict_proba(features_scaled)[0]
confidence = max(probabilities) * 100

print(f"Recommended Action: {action}")
print(f"Confidence: {confidence:.2f}%")
```

### Example Integration (Flask API)
```python
@app.route('/api/predict-sensor', methods=['POST'])
def predict_sensor():
    data = request.get_json()
    
    # Extract inputs
    crop_id = data['crop_id']
    ph_level = float(data['ph_level'])
    ec_value = float(data['ec_value'])
    ambient_temp = float(data['ambient_temp'])
    
    # Encode and prepare features
    crop_encoded = crop_encoder.transform([crop_id])[0]
    features = np.array([[crop_encoded, ph_level, ec_value, ambient_temp]])
    features_scaled = scaler.transform(features)
    
    # Predict
    prediction = model.predict(features_scaled)
    action = action_encoder.inverse_transform(prediction)[0]
    confidence = max(model.predict_proba(features_scaled)[0]) * 100
    
    return jsonify({
        'success': True,
        'action': action,
        'confidence': confidence
    })
```

## Requirements
- Python 3.8+
- scikit-learn >= 1.0.0
- numpy >= 1.21.0
- pandas >= 1.3.0
- joblib >= 1.0.0

*Note: Dependencies are included in the main project's requirements.txt*

## Training Details

### Data Preprocessing
1. Data loading from multiple sources
2. Missing value handling (forward fill method)
3. Feature engineering for optimal ranges
4. Synthetic data generation for African context
5. Data merging and balancing

### Model Training
- **Algorithm**: Random Forest Classifier
- **n_estimators**: 100 trees
- **max_depth**: None (unlimited depth)
- **min_samples_split**: 2
- **random_state**: 42 (for reproducibility)
- **n_jobs**: -1 (parallel processing)

### Validation Strategy
- Train/Test Split: 80/20
- Stratified sampling to maintain class distribution
- Cross-validation for robust evaluation

## Usage Guidelines

### Best Practices ✅
1. **Use calibrated sensors** - Ensure pH and EC meters are properly calibrated
2. **Verify recommendations** - Always review AI suggestions before applying
3. **Make gradual adjustments** - Add nutrients/solutions slowly and retest
4. **Monitor plant response** - Observe how plants react to changes
5. **Keep manual logs** - Maintain backup records of adjustments

### Warnings ⚠️
1. **Don't rely solely on AI** - Use human judgment alongside recommendations
2. **Calibrate regularly** - Check sensor accuracy weekly
3. **Check for malfunctions** - Verify sensor readings if they seem unusual
4. **Consider plant-specific needs** - Some varieties may have unique requirements
5. **Consult experts** - Seek professional help for persistent issues

### When to Seek Human Expertise
- Rapid or extreme changes in sensor readings
- Persistent plant health issues despite corrections
- Equipment failures or malfunctions
- Unfamiliar crop types not in training data
- Unusual environmental conditions

## Model Limitations

### Technical Limitations
1. **Crop Coverage**: Only supports 3 crop types (Lettuce, Peppers, Tomatoes)
2. **Fixed Feature Set**: Requires exactly 4 input features
3. **No Time-Series Analysis**: Doesn't consider historical trends
4. **No Anomaly Detection**: Won't flag suspicious or unusual readings
5. **Static Model**: Requires manual retraining for updates

### Environmental Limitations
1. **Temperature Range**: Optimized for 15-32°C (may degrade outside this range)
2. **Water Quality**: Assumes standard water chemistry
3. **Seasonal Effects**: Not explicitly modeled
4. **Geographic Adaptation**: May not generalize to all climates

### Operational Limitations
1. **Sensor Dependency**: Assumes sensor readings are accurate
2. **No Uncertainty Quantification**: Doesn't provide confidence intervals
3. **Binary Recommendations**: Doesn't specify quantity to add/remove
4. **Independent Analysis**: Treats each reading separately

## Future Improvements

1. **Expand Crop Coverage**: Add more crop types (herbs, cucumbers, strawberries)
2. **Multi-language Support**: Add recommendations in Kinyarwanda
3. **Time-series Analysis**: Incorporate historical trends
4. **Anomaly Detection**: Detect unusual sensor patterns
5. **Mobile Optimization**: Create lightweight model for mobile devices
6. **Real-time Learning**: Implement online learning for continuous improvement

## Integration with FarmSmart Platform

This model is integrated into the FarmSmart hydroponic management platform:
- **Dashboard**: Real-time sensor monitoring and recommendations
- **API Endpoint**: `/api/predict-sensor` (POST request)
- **User Interface**: Easy-to-use form for manual sensor input
- **Affordable Equipment**: Works with basic handheld pH and EC meters
