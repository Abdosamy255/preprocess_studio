# Preprocess Studio

A modern web-based machine learning data preprocessing and analysis tool, built with FastAPI and vanilla JavaScript.

## Overview

Preprocess Studio is a complete data science workflow application that allows users to:
- Upload and explore CSV datasets
- Generate interactive visualizations (heatmaps, scatter plots, bar charts, box plots, histograms)
- Train machine learning models (Random Forest, Gradient Boosting, Linear/Logistic Regression)
- Make predictions using trained models
- Download trained models for later use

## Tech Stack

**Backend:**
- FastAPI 0.95+
- Uvicorn 0.22+
- pandas 2.2+
- scikit-learn 1.4+
- matplotlib 3.8+
- seaborn 0.13+
- joblib 1.4+

**Frontend:**
- HTML5 with semantic structure
- CSS3 with responsive grid layout
- Vanilla JavaScript (no frameworks)
- Fetch API for async communication

## Features

### 📤 Data Upload
- Support for CSV files with multiple encodings (UTF-8, Latin-1, ISO-8859-1, CP1252)
- Automatic file validation and error handling
- Quick data preview on upload

### 📊 Data Exploration
- **Schema Tab**: Column names, data types, and missing value counts
- **Statistics Tab**: Descriptive statistics for all columns
- **Sample Data Tab**: First 5 rows of the dataset
- **Missing Values Tab**: Detailed missing value analysis

### 📈 Visualization
- Correlation heatmaps
- Scatter plots with optional hue dimension
- Bar charts with aggregation options
- Box plots for distribution analysis
- Histograms with KDE overlay
- Dark mode styling for better visibility

### 🤖 Model Training
- Random Forest Classifier/Regressor
- Gradient Boosting Classifier/Regressor
- Linear/Logistic Regression
- Automatic feature type detection (numeric vs categorical)
- Configurable train/test split
- Multiple scaler options (StandardScaler, MinMaxScaler)
- Multiple imputation strategies (Median, Mean, Most Frequent)

### 🎯 Predictions
- Load trained models
- Make predictions with new data
- Support for both classification and regression tasks

### 💾 Model Management
- In-memory model storage
- Download trained models as pickle files
- Retrieve model metadata and metrics

## Project Structure

```
preprocess_studio/
├── app.py                 # FastAPI backend
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html        # Main web UI
├── static/
│   ├── app.js           # Frontend logic
│   └── style.css        # Styling
├── test_data.csv        # Sample dataset
└── README.md
```

## Installation

### Prerequisites
- Python 3.8+
- pip or conda

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/preprocess_studio.git
cd preprocess_studio
```

2. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

5. Open your browser and navigate to:
```
http://127.0.0.1:8000
```

## Usage

1. **Upload Data**: Drag and drop a CSV file or click to browse
2. **Explore**: Switch to the Explore tab to view dataset statistics
3. **Visualize**: Generate charts from the Visualize tab
4. **Train**: Configure and train a model from the Train tab
5. **Predict**: Use the trained model to make predictions from the Predict tab
6. **Download**: Download your trained model for later use

## API Endpoints

- `GET /` - Serve the main HTML interface
- `POST /upload` - Upload and process CSV file
- `GET /plot` - Generate visualization
- `POST /train` - Train a machine learning model
- `POST /predict` - Make predictions
- `GET /model_info/{model_id}` - Get model metadata
- `GET /download_model/{model_id}` - Download trained model
- `GET /health` - Health check endpoint

## Key Implementation Details

### CSV Encoding Support
The application automatically tries multiple encodings (UTF-8, Latin-1, ISO-8859-1, CP1252) to handle real-world CSV files with different character encodings.

### matplotlib Configuration
The backend uses the "Agg" backend to avoid GUI-related errors in headless environments:
```python
import matplotlib
matplotlib.use("Agg")
```

### NaN/Inf Handling
Statistics and metrics are properly serialized to JSON by converting NaN and Inf values to None.

### Model Persistence
Models are stored in memory during the session and can be downloaded as pickle files for external use.

## Development

### Code Style
- Python: PEP 8 compliant
- JavaScript: ES6+ with defensive null checks
- CSS: Mobile-first responsive design

### Adding New Features
1. Backend endpoints are defined in `app.py`
2. Frontend handlers are in `static/app.js`
3. Styling is in `static/style.css`
4. HTML structure is in `templates/index.html`

## Known Limitations

- Models are stored in memory and lost when the server restarts
- Large datasets (>100K rows) may have performance issues
- Maximum file upload size depends on server configuration

## Future Improvements

- Persistent database for model storage
- Support for more file formats (Excel, Parquet, etc.)
- Advanced feature engineering tools
- Model comparison and ensemble methods
- Authentication and user sessions
- Docker containerization
- Deployment to cloud platforms

## Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests

## License

This project is open source and available under the MIT License.

## Author

Created as a modern alternative to Streamlit-based data apps, focusing on clean architecture and user experience.

---

**Built with ❤️ using FastAPI and vanilla JavaScript**
