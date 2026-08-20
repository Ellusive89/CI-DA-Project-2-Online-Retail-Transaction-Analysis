"""Load and validate processed datasets used by the Streamlit application."""

from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"


def _read_processed_data(
    filename: str,
    required_columns: set[str],
) -> pd.DataFrame:
    """Read a processed Parquet file and validate its required columns."""
    data_path = PROCESSED_DATA_DIR / filename

    if not data_path.exists():
        raise FileNotFoundError(
            f"Required processed dataset was not found: {data_path}"
        )

    data = pd.read_parquet(data_path)

    missing_columns = required_columns.difference(data.columns)

    if missing_columns:
        missing_column_names = ", ".join(sorted(missing_columns))
        raise ValueError(
            f"{filename} is missing required columns: "
            f"{missing_column_names}"
        )

    return data


@st.cache_data(show_spinner=False)
def load_completed_sales() -> pd.DataFrame:
    """Load validated completed-sales transactions."""
    return _read_processed_data(
        "completed_sales.parquet",
        {
            "InvoiceNo",
            "StockCode",
            "Description",
            "Quantity",
            "InvoiceDate",
            "UnitPrice",
            "Country",
            "LineRevenue",
        },
    )


@st.cache_data(show_spinner=False)
def load_returns_adjustments() -> pd.DataFrame:
    """Load validated returns and adjustment transactions."""
    return _read_processed_data(
        "returns_adjustments.parquet",
        {
            "InvoiceNo",
            "StockCode",
            "Description",
            "Quantity",
            "InvoiceDate",
            "Country",
            "TransactionType",
            "LineRevenue",
        },
    )


@st.cache_data(show_spinner=False)
def load_customer_segments() -> pd.DataFrame:
    """Load validated RFM customer segments."""
    return _read_processed_data(
        "customer_segments.parquet",
        {
            "CustomerID",
            "Recency",
            "Frequency",
            "Monetary",
            "LastPurchase",
            "Cluster",
            "Segment",
        },
    )