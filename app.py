import io
import os
import uuid
import warnings
from typing import List, Tuple, Dict, Any

import joblib
import matplotlib
matplotlib.use("Agg")  # FIX: Must set backend before importing pyplot
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    RandomForestClassifier,
    RandomForestRegressor,
    GradientBoostingClassifier,
    GradientBoostingRegressor,
)
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler, MinMaxScaler

warnings.filterwarnings("ignore")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Ensure directories exist
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

app = FastAPI(title="Preprocess Studio API")

# FIX: Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

DATASETS: Dict[str, pd.DataFrame] = {}
MODELS: Dict[str, Dict[str, Any]] = {}


def _convert_nan_inf(obj):
    """Recursively convert NaN/Inf to None for JSON serialization"""
    if isinstance(obj, dict):
        return {k: _convert_nan_inf(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_nan_inf(item) for item in obj]
    elif isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return obj
    elif isinstance(obj, (np.floating, np.integer)):
        if isinstance(obj, np.floating) and (np.isnan(obj) or np.isinf(obj)):
            return None
        return obj.item() if hasattr(obj, 'item') else obj
    return obj


def _numeric_columns(df: pd.DataFrame) -> List[str]:
    return df.select_dtypes(include=np.number).columns.tolist()


def _safe_stratify_target(y: pd.Series):
    if y.nunique(dropna=True) <= 1:
        return None
    class_counts = y.value_counts(dropna=False)
    if class_counts.min() < 2:
        return None
    return y


def _is_regression_target(series: pd.Series) -> bool:
    if pd.api.types.is_numeric_dtype(series):
        return series.nunique(dropna=True) > 15
    return False


def _build_model_pipeline(
    x: pd.DataFrame,
    y: pd.Series,
    model_choice: str,
    scaler_choice: str,
    imputer_strategy: str,
    random_state: int = 42,
) -> Tuple[Pipeline, str]:
    categorical_features = x.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
    numeric_features = x.select_dtypes(include=np.number).columns.tolist()

    scaler = StandardScaler() if scaler_choice == "StandardScaler" else MinMaxScaler()

    numeric_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy=imputer_strategy)),
        ("scaler", scaler)
    ])
    categorical_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore")),
    ])

    transformers = []
    if numeric_features:
        transformers.append(("num", numeric_transformer, numeric_features))
    if categorical_features:
        transformers.append(("cat", categorical_transformer, categorical_features))

    # FIX: Handle case where no transformers exist
    if not transformers:
        raise ValueError("No valid features found for preprocessing.")

    preprocessor = ColumnTransformer(transformers=transformers)

    is_reg = _is_regression_target(y)
    task_type = "Regression" if is_reg else "Classification"

    if is_reg:
        if model_choice == "Random Forest":
            model = RandomForestRegressor(n_estimators=100, random_state=random_state, n_jobs=-1)
        elif model_choice == "Gradient Boosting":
            model = GradientBoostingRegressor(n_estimators=100, random_state=random_state)
        else:
            model = LinearRegression()
    else:
        if model_choice == "Random Forest":
            model = RandomForestClassifier(n_estimators=100, random_state=random_state, n_jobs=-1)
        elif model_choice == "Gradient Boosting":
            model = GradientBoostingClassifier(n_estimators=100, random_state=random_state)
        else:
            model = LogisticRegression(max_iter=1000, random_state=random_state)

    pipeline = Pipeline(steps=[("preprocessor", preprocessor), ("model", model)])
    return pipeline, task_type


def _train_model(
    df: pd.DataFrame,
    feature_cols: List[str],
    target_col: str,
    model_choice: str,
    scaler_choice: str,
    imputer_strategy: str,
    test_size: float,
    random_state: int,
) -> Tuple[Pipeline, str, dict, np.ndarray, np.ndarray]:
    # FIX: Validate columns exist
    missing = [c for c in feature_cols + [target_col] if c not in df.columns]
    if missing:
        raise ValueError(f"Columns not found in dataset: {missing}")

    clean_df = df[feature_cols + [target_col]].dropna(subset=[target_col]).copy()

    if clean_df.shape[0] < 10:
        raise ValueError("Not enough rows to train a model (need at least 10).")

    x = clean_df[feature_cols]
    y = clean_df[target_col]

    model_pipeline, task_type = _build_model_pipeline(
        x, y, model_choice, scaler_choice, imputer_strategy, random_state
    )

    stratify = _safe_stratify_target(y) if task_type == "Classification" else None
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=test_size, random_state=random_state, stratify=stratify
    )

    model_pipeline.fit(x_train, y_train)
    preds = model_pipeline.predict(x_test)

    if task_type == "Regression":
        metrics = {
            "r2": float(round(r2_score(y_test, preds), 4)),
            "mae": float(round(mean_absolute_error(y_test, preds), 4))
        }
    else:
        metrics = {"accuracy": float(round(accuracy_score(y_test, preds), 4))}

    return model_pipeline, task_type, metrics, y_test.to_numpy(), preds


@app.get("/")
async def index():
    html_file = os.path.join(TEMPLATES_DIR, "index.html")
    if not os.path.exists(html_file):
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(html_file, media_type="text/html")


@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    # FIX: Better validation and error handling
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV (.csv)")

    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="File is empty")

        df = None
        last_error = None
        for encoding in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
            try:
                df = pd.read_csv(io.BytesIO(content), encoding=encoding)
                break
            except Exception as e:
                last_error = e
                continue

        if df is None:
            raise HTTPException(status_code=400, detail=f"Could not parse CSV: {last_error}")

        if df.empty:
            raise HTTPException(status_code=400, detail="CSV file has no data")

        df.columns = [str(col).strip() for col in df.columns]

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Server error reading file: {str(exc)}")

    dataset_id = uuid.uuid4().hex
    DATASETS[dataset_id] = df

    # FIX: Safe stats serialization (handle NaN/Inf)
    def safe_stats(df):
        stats = df.describe(include="all").transpose()
        return {
            col: {
                k: (None if (isinstance(v, float) and (np.isnan(v) or np.isinf(v))) else v)
                for k, v in row.items()
            }
            for col, row in stats.to_dict(orient="index").items()
        }

    # Missing values info
    missing_info = {col: int(df[col].isna().sum()) for col in df.columns}
    
    response = {
        "dataset_id": dataset_id,
        "shape": list(df.shape),
        "columns": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "sample": df.head(5).fillna("").to_dict(orient="records"),
        "stats": safe_stats(df),
        "missing": missing_info,
    }
    
    # Clean NaN/Inf values before returning
    return _convert_nan_inf(response)


@app.get("/plot")
async def plot(
    dataset_id: str,
    plot_type: str = "heatmap",
    x: str = None,
    y: str = None,
    hue: str = None,
    agg: str = "mean"
):
    if dataset_id not in DATASETS:
        raise HTTPException(status_code=404, detail="Dataset not found")
    df = DATASETS[dataset_id]

    # FIX: Use dark style for better visuals
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(9, 6))
    fig.patch.set_facecolor("#0f1117")
    ax.set_facecolor("#0f1117")

    try:
        if plot_type == "heatmap":
            numeric_cols = _numeric_columns(df)
            if len(numeric_cols) < 2:
                raise HTTPException(status_code=400, detail="Need at least 2 numeric columns for heatmap")
            corr = df[numeric_cols].corr()
            sns.heatmap(
                corr, annot=True, fmt=".2f", cmap="coolwarm",
                linewidths=0.5, ax=ax,
                annot_kws={"size": 9},
                cbar_kws={"shrink": 0.8}
            )
            ax.set_title("Correlation Heatmap", color="#e2e8f0", fontsize=14, pad=15)

        elif plot_type == "scatter":
            if not x or not y:
                raise HTTPException(status_code=400, detail="x and y are required for scatter")
            sns.scatterplot(
                data=df, x=x, y=y,
                hue=(None if hue in (None, "None", "") else hue),
                ax=ax, alpha=0.7, edgecolor="none"
            )
            ax.set_title(f"{x} vs {y}", color="#e2e8f0", fontsize=14)

        elif plot_type == "bar":
            if not x or not y:
                raise HTTPException(status_code=400, detail="x and y are required for bar")
            plot_df = (
                df[[x, y]].dropna()
                .groupby(x, as_index=False)
                .agg({y: agg})
                .sort_values(by=y, ascending=False)
                .head(20)
            )
            sns.barplot(data=plot_df, x=x, y=y, ax=ax, palette="viridis")
            ax.tick_params(axis="x", rotation=45, colors="#e2e8f0")
            ax.tick_params(axis="y", colors="#e2e8f0")
            ax.set_title(f"{agg.capitalize()} of {y} by {x}", color="#e2e8f0", fontsize=14)

        elif plot_type == "box":
            if not x:
                raise HTTPException(status_code=400, detail="x is required for box plot")
            sns.boxplot(x=df[x], ax=ax, color="#6366f1")
            ax.set_title(f"Distribution of {x}", color="#e2e8f0", fontsize=14)

        elif plot_type == "histogram":
            if not x:
                raise HTTPException(status_code=400, detail="x is required for histogram")
            sns.histplot(df[x].dropna(), ax=ax, color="#6366f1", kde=True)
            ax.set_title(f"Histogram of {x}", color="#e2e8f0", fontsize=14)

        else:
            raise HTTPException(status_code=400, detail=f"Unknown plot_type: {plot_type}")

        # Style axes
        for spine in ax.spines.values():
            spine.set_edgecolor("#334155")
        ax.xaxis.label.set_color("#94a3b8")
        ax.yaxis.label.set_color("#94a3b8")
        ax.tick_params(colors="#94a3b8")

        buf = io.BytesIO()
        fig.tight_layout()
        fig.savefig(buf, format="png", dpi=120, bbox_inches="tight", facecolor="#0f1117")
        plt.close(fig)
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/png")

    except HTTPException:
        plt.close(fig)
        raise
    except Exception as exc:
        plt.close(fig)
        raise HTTPException(status_code=500, detail=str(exc))


class TrainRequest(BaseModel):
    dataset_id: str
    target_col: str
    feature_cols: List[str]
    model_choice: str = "Random Forest"
    scaler_choice: str = "StandardScaler"
    imputer_strategy: str = "median"
    test_size: float = 0.2
    random_state: int = 42


@app.post("/train")
async def train(req: TrainRequest):
    if req.dataset_id not in DATASETS:
        raise HTTPException(status_code=404, detail="Dataset not found")
    df = DATASETS[req.dataset_id]

    if not req.feature_cols:
        raise HTTPException(status_code=400, detail="At least one feature column is required")
    if req.target_col in req.feature_cols:
        raise HTTPException(status_code=400, detail="Target column cannot also be a feature column")

    try:
        model_pipeline, task_type, metrics, y_test, preds = _train_model(
            df, req.feature_cols, req.target_col,
            req.model_choice, req.scaler_choice,
            req.imputer_strategy, req.test_size, req.random_state
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Training error: {str(exc)}")

    model_id = uuid.uuid4().hex
    buffer = io.BytesIO()
    joblib.dump(model_pipeline, buffer)
    buffer.seek(0)
    MODELS[model_id] = {
        "pipeline": model_pipeline,
        "bytes": buffer.getvalue(),
        "task_type": task_type,
        "metrics": metrics,
        "feature_cols": req.feature_cols,
        "target_col": req.target_col,
    }

    return {
        "model_id": model_id,
        "task_type": task_type,
        "metrics": metrics,
        "feature_cols": req.feature_cols,
        "target_col": req.target_col,
    }


class PredictRequest(BaseModel):
    model_id: str
    input: Dict[str, Any]


@app.post("/predict")
async def predict(req: PredictRequest):
    if req.model_id not in MODELS:
        raise HTTPException(status_code=404, detail="Model not found")
    model_info = MODELS[req.model_id]
    model = model_info["pipeline"]
    input_df = pd.DataFrame([req.input])
    try:
        pred = model.predict(input_df)[0]
        # Convert numpy types to Python native
        if hasattr(pred, 'item'):
            pred = pred.item()
        return {"prediction": pred, "task_type": model_info["task_type"]}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/model_info/{model_id}")
async def model_info(model_id: str):
    if model_id not in MODELS:
        raise HTTPException(status_code=404, detail="Model not found")
    info = MODELS[model_id]
    return {
        "model_id": model_id,
        "task_type": info["task_type"],
        "metrics": info["metrics"],
        "feature_cols": info.get("feature_cols", []),
        "target_col": info.get("target_col", ""),
    }


@app.get("/download_model/{model_id}")
async def download_model(model_id: str):
    if model_id not in MODELS:
        raise HTTPException(status_code=404, detail="Model not found")
    data = MODELS[model_id]["bytes"]
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename=model_{model_id[:8]}.pkl"}
    )


# Health check
@app.get("/health")
async def health():
    return {"status": "ok", "datasets": len(DATASETS), "models": len(MODELS)}