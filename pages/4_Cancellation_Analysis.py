"""Interactive cancellation and adjustment analysis."""

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from src.data_loader import (
    load_completed_sales,
    load_returns_adjustments,
)


st.set_page_config(
    page_title="Cancellation Analysis",
    page_icon="↩️",
    layout="wide",
)

PLOTLY_CONFIG = {
    "displaylogo": False,
    "scrollZoom": False,
}

NON_MERCHANDISE_CODES = {
    "DOT",
    "POST",
    "M",
    "AMAZONFEE",
    "BANK CHARGES",
    "CRUK",
    "D",
    "S",
    "B",
    "PADS",
    "C2",
}


def filter_transaction_data(
    data: pd.DataFrame,
    start_date,
    end_date,
    selected_countries: list[str],
) -> pd.DataFrame:
    """Filter transaction rows by date and optional countries."""
    transaction_dates = data["InvoiceDate"].dt.date

    date_mask = transaction_dates.between(
        start_date,
        end_date,
    )

    if selected_countries:
        country_mask = data["Country"].isin(
            selected_countries
        )
    else:
        country_mask = pd.Series(
            True,
            index=data.index,
            dtype=bool,
        )

    return data.loc[
        date_mask & country_mask
    ].copy()


def create_adjustment_summary(
    data: pd.DataFrame,
) -> pd.DataFrame:
    """Summarise adjustment categories."""
    return (
        data.groupby(
            "TransactionType",
            as_index=False,
        )
        .agg(
            AdjustmentRows=("InvoiceNo", "size"),
            AffectedInvoices=("InvoiceNo", "nunique"),
            NetQuantity=("Quantity", "sum"),
            NetLineRevenue=("LineRevenue", "sum"),
        )
        .sort_values(
            "AdjustmentRows",
            ascending=False,
        )
    )


def create_monthly_cancellation_summary(
    cancellations: pd.DataFrame,
    completed_sales: pd.DataFrame,
) -> pd.DataFrame:
    """Compare monthly cancellation value with completed-sales revenue."""
    monthly_cancellations = cancellations.copy()

    monthly_cancellations["Period"] = (
        monthly_cancellations["InvoiceDate"]
        .dt.to_period("M")
        .dt.start_time
    )

    monthly_cancellations = (
        monthly_cancellations.groupby(
            "Period",
            as_index=False,
        )
        .agg(
            CancellationValue=(
                "LineRevenue",
                lambda values: -values.sum(),
            ),
            CancellationInvoices=(
                "InvoiceNo",
                "nunique",
            ),
            CancelledUnits=(
                "Quantity",
                lambda values: -values.sum(),
            ),
        )
    )

    monthly_sales = completed_sales.copy()

    monthly_sales["Period"] = (
        monthly_sales["InvoiceDate"]
        .dt.to_period("M")
        .dt.start_time
    )

    monthly_sales = (
        monthly_sales.groupby(
            "Period",
            as_index=False,
        )
        .agg(
            SalesRevenue=("LineRevenue", "sum"),
            CompletedInvoices=("InvoiceNo", "nunique"),
        )
    )

    monthly_summary = monthly_sales.merge(
        monthly_cancellations,
        on="Period",
        how="outer",
        validate="one_to_one",
    ).sort_values("Period")

    value_columns = [
        "SalesRevenue",
        "CompletedInvoices",
        "CancellationValue",
        "CancellationInvoices",
        "CancelledUnits",
    ]

    monthly_summary[value_columns] = monthly_summary[
        value_columns
    ].fillna(0)

    monthly_summary["CancellationValuePercentage"] = np.where(
        monthly_summary["SalesRevenue"] > 0,
        (
            monthly_summary["CancellationValue"]
            / monthly_summary["SalesRevenue"]
            * 100
        ),
        np.nan,
    )

    return monthly_summary


def create_cancelled_product_summary(
    cancellations: pd.DataFrame,
) -> tuple[pd.DataFrame, int]:
    """Aggregate monetary merchandise cancellations by stock code."""
    non_merchandise_mask = (
        cancellations["StockCode"]
        .astype("string")
        .str.upper()
        .isin(NON_MERCHANDISE_CODES)
    )

    merchandise_cancellations = cancellations.loc[
        ~non_merchandise_mask
    ].copy()

    excluded_row_count = int(
        non_merchandise_mask.sum()
    )

    if merchandise_cancellations.empty:
        return pd.DataFrame(), excluded_row_count

    merchandise_cancellations["CancelledUnits"] = (
        -merchandise_cancellations["Quantity"]
    )

    merchandise_cancellations["CancellationValue"] = (
        -merchandise_cancellations["LineRevenue"]
    )

    primary_descriptions = (
        merchandise_cancellations.groupby(
            [
                "StockCode",
                "Description",
            ],
            as_index=False,
        )
        .size()
        .rename(
            columns={
                "size": "DescriptionFrequency",
            }
        )
        .sort_values(
            [
                "StockCode",
                "DescriptionFrequency",
            ],
            ascending=[
                True,
                False,
            ],
        )
        .drop_duplicates(
            subset="StockCode"
        )
        [
            [
                "StockCode",
                "Description",
            ]
        ]
    )

    product_summary = (
        merchandise_cancellations.groupby(
            "StockCode",
            as_index=False,
        )
        .agg(
            CancellationValue=("CancellationValue", "sum"),
            CancelledUnits=("CancelledUnits", "sum"),
            CancellationInvoices=("InvoiceNo", "nunique"),
        )
        .merge(
            primary_descriptions,
            on="StockCode",
            how="left",
            validate="one_to_one",
        )
        .sort_values(
            "CancellationValue",
            ascending=False,
        )
    )

    return product_summary, excluded_row_count


st.title("Cancellation Analysis")

st.markdown(
    """
    Examine cancellations and operational adjustments separately from completed
    sales. The dashboard distinguishes monetary cancellations from zero-price
    inventory movements and accounting adjustments.
    """
)


try:
    completed_sales = load_completed_sales()
    returns_adjustments = load_returns_adjustments()
except (FileNotFoundError, ValueError) as error:
    st.error(
        "The processed transaction data could not be loaded. "
        f"Technical detail: {error}"
    )
    st.stop()


minimum_date = min(
    completed_sales["InvoiceDate"].min(),
    returns_adjustments["InvoiceDate"].min(),
).date()

maximum_date = max(
    completed_sales["InvoiceDate"].max(),
    returns_adjustments["InvoiceDate"].max(),
).date()

country_options = sorted(
    set(completed_sales["Country"].dropna())
    | set(returns_adjustments["Country"].dropna())
)

transaction_type_options = [
    transaction_type
    for transaction_type in [
        "Cancellation",
        "Return or negative quantity",
        "Zero-price transaction",
        "Accounting adjustment",
    ]
    if transaction_type
    in returns_adjustments["TransactionType"].unique()
]


# Sidebar filters
st.sidebar.header("Cancellation filters")

selected_date_range = st.sidebar.date_input(
    "Transaction date range",
    value=(
        minimum_date,
        maximum_date,
    ),
    min_value=minimum_date,
    max_value=maximum_date,
    help="Both the start and end dates are included.",
)

selected_countries = st.sidebar.multiselect(
    "Countries",
    options=country_options,
    default=[],
    placeholder="All countries",
    help=(
        "Leave this empty to include every country, "
        "or select one or more countries."
    ),
)

selected_transaction_types = st.sidebar.multiselect(
    "Adjustment types",
    options=transaction_type_options,
    default=transaction_type_options,
    help=(
        "Select the adjustment categories displayed in the "
        "overview chart and table."
    ),
)

top_product_count = st.sidebar.slider(
    "Cancelled products to display",
    min_value=5,
    max_value=30,
    value=10,
    step=5,
)


if (
    not isinstance(selected_date_range, (tuple, list))
    or len(selected_date_range) != 2
):
    st.warning(
        "Select both a start date and an end date to continue."
    )
    st.stop()


if not selected_transaction_types:
    st.warning(
        "Select at least one adjustment type to continue."
    )
    st.stop()


start_date, end_date = selected_date_range

filtered_sales = filter_transaction_data(
    completed_sales,
    start_date,
    end_date,
    selected_countries,
)

filtered_adjustments = filter_transaction_data(
    returns_adjustments,
    start_date,
    end_date,
    selected_countries,
)

filtered_adjustments = filtered_adjustments.loc[
    filtered_adjustments["TransactionType"].isin(
        selected_transaction_types
    )
].copy()


if filtered_adjustments.empty:
    st.warning(
        "No adjustment rows match the selected filters."
    )
    st.stop()


cancellations = filtered_adjustments.loc[
    filtered_adjustments["TransactionType"].eq(
        "Cancellation"
    )
].copy()

zero_value_negative_rows = filtered_adjustments.loc[
    filtered_adjustments["TransactionType"].eq(
        "Return or negative quantity"
    )
].copy()


completed_sales_revenue = filtered_sales[
    "LineRevenue"
].sum()

cancellation_value = (
    -cancellations["LineRevenue"].sum()
    if not cancellations.empty
    else 0
)

cancelled_units = (
    -cancellations["Quantity"].sum()
    if not cancellations.empty
    else 0
)

cancellation_invoice_count = cancellations[
    "InvoiceNo"
].nunique()

if completed_sales_revenue > 0:
    cancellation_value_percentage = (
        cancellation_value
        / completed_sales_revenue
        * 100
    )

    cancellation_percentage_display = (
        f"{cancellation_value_percentage:.2f}%"
    )
else:
    cancellation_value_percentage = np.nan
    cancellation_percentage_display = "N/A"


selected_country_count = filtered_adjustments[
    "Country"
].nunique()

country_word = (
    "country"
    if selected_country_count == 1
    else "countries"
)

st.caption(
    f"Showing {len(filtered_adjustments):,} adjustment rows from "
    f"{start_date:%d %B %Y} to {end_date:%d %B %Y}, across "
    f"{selected_country_count:,} {country_word}."
)


# KPI section
st.subheader("Cancellation indicators")

value_column, invoice_column, unit_column, ratio_column = (
    st.columns(4)
)

with value_column:
    st.metric(
        label="Cancellation value",
        value=f"£{cancellation_value:,.2f}",
        help=(
            "Absolute recorded value of rows classified "
            "as cancellations."
        ),
    )

with invoice_column:
    st.metric(
        label="Cancellation invoices",
        value=f"{cancellation_invoice_count:,}",
    )

with unit_column:
    st.metric(
        label="Cancelled units",
        value=f"{cancelled_units:,.0f}",
    )

with ratio_column:
    st.metric(
        label="Cancellation value vs sales",
        value=cancellation_percentage_display,
        help=(
            "Cancellation value divided by completed-sales revenue "
            "for the same selected date and country scope."
        ),
    )


st.warning(
    "Cancellation value compared with sales is not a formal refund rate "
    "or confirmed financial loss. Cancellation entries may reverse orders "
    "created in another reporting period."
)


st.divider()


# Adjustment-type chart
st.subheader("Adjustment types")

adjustment_summary = create_adjustment_summary(
    filtered_adjustments
)

adjustment_figure = px.bar(
    adjustment_summary,
    x="TransactionType",
    y="AdjustmentRows",
    color="TransactionType",
    labels={
        "TransactionType": "Adjustment type",
        "AdjustmentRows": "Number of product-line rows",
    },
    hover_data={
        "AffectedInvoices": ":,",
        "NetQuantity": ":,",
        "NetLineRevenue": ":£,.2f",
    },
)

adjustment_figure.update_layout(
    height=440,
    showlegend=False,
    xaxis={
        "title": None,
        "automargin": True,
    },
    margin={
        "l": 60,
        "r": 30,
        "t": 30,
        "b": 100,
    },
)

st.plotly_chart(
    adjustment_figure,
    use_container_width=True,
    config=PLOTLY_CONFIG,
)

st.caption(
    f"The current selection includes "
    f"{len(zero_value_negative_rows):,} negative-quantity rows "
    "with zero recorded revenue. These may represent inventory "
    "corrections rather than monetary customer returns."
)


st.divider()


# Monthly cancellation pattern
st.subheader("Monthly cancellation value")

if cancellations.empty:
    st.info(
        "The current adjustment-type selection does not include "
        "any monetary cancellation rows."
    )

else:
    monthly_cancellation_summary = (
        create_monthly_cancellation_summary(
            cancellations,
            filtered_sales,
        )
    )

    monthly_figure = px.bar(
        monthly_cancellation_summary,
        x="Period",
        y="CancellationValue",
        labels={
            "Period": "Month",
            "CancellationValue": "Cancellation value (£)",
        },
        hover_data={
            "CancellationInvoices": ":,",
            "CancelledUnits": ":,",
            "SalesRevenue": ":£,.2f",
            "CompletedInvoices": ":,",
            "CancellationValuePercentage": ":.2f",
        },
    )

    monthly_figure.update_traces(
        marker_color="#C44E52",
    )

    monthly_figure.update_yaxes(
        tickprefix="£",
        tickformat=",.0f",
    )

    monthly_figure.update_layout(
        height=460,
        margin={
            "l": 70,
            "r": 30,
            "t": 30,
            "b": 70,
        },
    )

    st.plotly_chart(
        monthly_figure,
        use_container_width=True,
        config=PLOTLY_CONFIG,
    )


st.divider()


# Cancelled-product analysis
st.subheader("Products with the highest cancellation value")

if cancellations.empty:
    st.info(
        "Select the Cancellation adjustment type to view "
        "cancelled-product analysis."
    )

else:
    (
        cancelled_product_summary,
        excluded_non_merchandise_rows,
    ) = create_cancelled_product_summary(
        cancellations
    )

    if cancelled_product_summary.empty:
        st.info(
            "No merchandise cancellation products match "
            "the selected filters."
        )

    else:
        top_cancelled_products = (
            cancelled_product_summary.head(
                top_product_count
            )
            .sort_values(
                "CancellationValue",
                ascending=True,
            )
        )

        cancelled_product_figure = px.bar(
            top_cancelled_products,
            x="CancellationValue",
            y="Description",
            orientation="h",
            color="CancellationValue",
            color_continuous_scale="Reds",
            labels={
                "CancellationValue": "Cancellation value (£)",
                "Description": "Product",
            },
            hover_data={
                "StockCode": True,
                "CancelledUnits": ":,",
                "CancellationInvoices": ":,",
            },
        )

        cancelled_product_figure.update_xaxes(
            tickprefix="£",
            tickformat=",.0f",
        )

        cancelled_product_figure.update_layout(
            height=max(
                450,
                len(top_cancelled_products) * 34,
            ),
            coloraxis_showscale=False,
            yaxis={
                "title": None,
                "automargin": True,
            },
            margin={
                "l": 220,
                "r": 30,
                "t": 30,
                "b": 70,
            },
        )

        st.plotly_chart(
            cancelled_product_figure,
            use_container_width=True,
            config=PLOTLY_CONFIG,
        )

        leading_cancelled_product = (
            cancelled_product_summary.iloc[0]
        )

        st.info(
            f"{leading_cancelled_product['Description']} has the "
            f"highest selected cancellation value at "
            f"£{leading_cancelled_product['CancellationValue']:,.2f}, "
            f"across "
            f"{leading_cancelled_product['CancellationInvoices']:,.0f} "
            "cancellation invoices."
        )

        if (
            leading_cancelled_product[
                "CancellationInvoices"
            ]
            <= 2
        ):
            st.warning(
                "The leading product appears in very few cancellation "
                "invoices. Its value may be driven by an isolated bulk-order "
                "reversal rather than widespread product dissatisfaction."
            )

        st.caption(
            f"{excluded_non_merchandise_rows:,} non-merchandise "
            "cancellation rows were excluded from the product ranking."
        )


st.divider()


# Data tables and downloads
st.subheader("Adjustment data")

st.dataframe(
    adjustment_summary,
    use_container_width=True,
    hide_index=True,
)

adjustment_csv = adjustment_summary.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    label="Download adjustment summary as CSV",
    data=adjustment_csv,
    file_name=(
        f"adjustment_summary_{start_date}_{end_date}.csv"
    ),
    mime="text/csv",
)


if (
    not cancellations.empty
    and not cancelled_product_summary.empty
):
    product_csv = cancelled_product_summary.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="Download cancelled-product data as CSV",
        data=product_csv,
        file_name=(
            f"cancelled_products_{start_date}_{end_date}.csv"
        ),
        mime="text/csv",
    )


with st.expander("Cancellation-analysis scope and limitations"):
    st.markdown(
        """
        - Cancellations are identified using the transaction classification
          created in the ETL notebook.
        - A cancellation does not necessarily mean that products were shipped
          and later returned.
        - Negative-quantity rows with zero prices may represent inventory
          corrections, damaged stock, or administrative changes.
        - The dataset does not contain cancellation or return reason fields.
        - Cancellation entries may relate to orders from another month.
        - Recorded cancellation value is not equivalent to confirmed profit
          loss.
        - Product-level results should be investigated at invoice level before
          operational decisions are made.
        """
    )
