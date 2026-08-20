"""Interactive sales-performance overview for the retail dashboard."""

import pandas as pd
import plotly.express as px
import streamlit as st

from src.data_loader import load_completed_sales


PLOTLY_CONFIG = {
    "displaylogo": False,
    "scrollZoom": False,
}


def filter_sales_data(
    data: pd.DataFrame,
    start_date,
    end_date,
    selected_countries: list[str],
) -> pd.DataFrame:
    """Filter completed sales by an inclusive date range and countries."""
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


def create_invoice_summary(
    data: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate product lines to one row per completed invoice."""
    return (
        data.groupby(
            "InvoiceNo",
            as_index=False,
        )
        .agg(
            InvoiceValue=("LineRevenue", "sum"),
            InvoiceDate=("InvoiceDate", "min"),
            Country=("Country", "first"),
            Units=("Quantity", "sum"),
            ProductLines=("StockCode", "count"),
        )
    )


def aggregate_sales_trend(
    data: pd.DataFrame,
    aggregation_level: str,
) -> pd.DataFrame:
    """Aggregate completed sales for the selected chart interval."""
    frequency_mapping = {
        "Daily": "D",
        "Weekly": "W",
        "Monthly": "M",
    }

    frequency = frequency_mapping[aggregation_level]

    trend_data = data.copy()

    trend_data["Period"] = (
        trend_data["InvoiceDate"]
        .dt.to_period(frequency)
        .dt.start_time
    )

    return (
        trend_data.groupby(
            "Period",
            as_index=False,
        )
        .agg(
            Revenue=("LineRevenue", "sum"),
            CompletedInvoices=("InvoiceNo", "nunique"),
            UnitsSold=("Quantity", "sum"),
        )
        .sort_values("Period")
    )


st.title("Sales Overview")

st.markdown(
    """
    Explore completed-sales performance over time. Use the filters to focus on
    a specific reporting period or geographic market. Every KPI and chart
    updates automatically.
    """
)


try:
    completed_sales = load_completed_sales()
except (FileNotFoundError, ValueError) as error:
    st.error(
        "The completed-sales data could not be loaded. "
        f"Technical detail: {error}"
    )
    st.stop()


minimum_date = completed_sales["InvoiceDate"].min().date()
maximum_date = completed_sales["InvoiceDate"].max().date()

country_options = sorted(
    completed_sales["Country"].dropna().unique()
)


# Sidebar filters
st.sidebar.header("Sales filters")

selected_date_range = st.sidebar.date_input(
    "Transaction date range",
    value=(
        minimum_date,
        maximum_date,
    ),
    min_value=minimum_date,
    max_value=maximum_date,
    help="Both the start date and end date are included.",
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

aggregation_level = st.sidebar.selectbox(
    "Trend aggregation",
    options=[
        "Daily",
        "Weekly",
        "Monthly",
    ],
    index=2,
    help="Choose how transaction dates are grouped in the trend chart.",
)


# The date widget may temporarily contain only one date while being edited.
if (
    not isinstance(selected_date_range, (tuple, list))
    or len(selected_date_range) != 2
):
    st.warning(
        "Select both a start date and an end date to continue."
    )
    st.stop()


start_date, end_date = selected_date_range

filtered_sales = filter_sales_data(
    completed_sales,
    start_date,
    end_date,
    selected_countries,
)


if filtered_sales.empty:
    st.warning(
        "No completed sales match the selected filters. "
        "Change the date range or country selection."
    )
    st.stop()


# Invoice-level aggregation prevents product lines from being counted as
# separate completed transactions.
invoice_summary = create_invoice_summary(
    filtered_sales
)

total_revenue = filtered_sales["LineRevenue"].sum()
completed_invoice_count = len(invoice_summary)

average_invoice_value = invoice_summary[
    "InvoiceValue"
].mean()

median_invoice_value = invoice_summary[
    "InvoiceValue"
].median()

units_sold = filtered_sales["Quantity"].sum()

selected_country_count = filtered_sales[
    "Country"
].nunique()

country_word = (
    "country"
    if selected_country_count == 1
    else "countries"
)


st.caption(
    f"Showing {len(filtered_sales):,} product lines from "
    f"{start_date:%d %B %Y} to {end_date:%d %B %Y}, across "
    f"{selected_country_count:,} {country_word}."
)


# KPI section
st.subheader("Selected-period performance")

revenue_column, invoice_column, average_column, units_column = (
    st.columns(4)
)

with revenue_column:
    st.metric(
        label="Completed-sales revenue",
        value=f"£{total_revenue:,.2f}",
        help="Revenue from completed positive-sales product lines.",
    )

with invoice_column:
    st.metric(
        label="Completed invoices",
        value=f"{completed_invoice_count:,}",
        help="Number of unique completed invoice identifiers.",
    )

with average_column:
    st.metric(
        label="Average invoice value",
        value=f"£{average_invoice_value:,.2f}",
        help="Mean revenue after aggregation to invoice level.",
    )

with units_column:
    st.metric(
        label="Units sold",
        value=f"{units_sold:,.0f}",
        help="Total product quantity in the selected completed sales.",
    )


st.divider()


# Revenue-trend section
st.subheader("Revenue trend")

sales_trend = aggregate_sales_trend(
    filtered_sales,
    aggregation_level,
)


# A bar is clearer than a line when filters produce only one reporting period.
if len(sales_trend) == 1:
    trend_figure = px.bar(
        sales_trend,
        x="Period",
        y="Revenue",
        labels={
            "Period": "Reporting period",
            "Revenue": "Revenue (£)",
        },
        hover_data={
            "CompletedInvoices": ":,",
            "UnitsSold": ":,",
            "Revenue": ":£,.2f",
        },
    )

    trend_figure.update_traces(
        marker_color="#0B6E4F",
    )

else:
    trend_figure = px.line(
        sales_trend,
        x="Period",
        y="Revenue",
        markers=True,
        labels={
            "Period": "Reporting period",
            "Revenue": "Revenue (£)",
        },
        hover_data={
            "CompletedInvoices": ":,",
            "UnitsSold": ":,",
            "Revenue": ":£,.2f",
        },
    )

    trend_figure.update_traces(
        line={
            "color": "#0B6E4F",
            "width": 3,
        },
        marker={
            "size": 7,
        },
    )


trend_figure.update_yaxes(
    tickprefix="£",
    tickformat=",.0f",
)

trend_figure.update_layout(
    height=440,
    hovermode="x unified",
    margin={
        "l": 60,
        "r": 30,
        "t": 30,
        "b": 60,
    },
)

st.plotly_chart(
    trend_figure,
    use_container_width=True,
    config=PLOTLY_CONFIG,
)


peak_period = sales_trend.loc[
    sales_trend["Revenue"].idxmax()
]

if aggregation_level == "Monthly":
    peak_period_label = peak_period["Period"].strftime(
        "%B %Y"
    )
else:
    peak_period_label = peak_period["Period"].strftime(
        "%d %B %Y"
    )

st.info(
    f"The highest {aggregation_level.lower()} revenue in the "
    f"selected data was £{peak_period['Revenue']:,.2f}, beginning "
    f"{peak_period_label}."
)


st.divider()


# Invoice-value distribution section
st.subheader("Invoice-value distribution")

invoice_chart_limit = invoice_summary[
    "InvoiceValue"
].quantile(0.99)

invoice_values_for_chart = invoice_summary.loc[
    invoice_summary["InvoiceValue"] <= invoice_chart_limit
].copy()

histogram_bin_count = max(
    1,
    min(
        50,
        round(len(invoice_values_for_chart) ** 0.5),
    ),
)

distribution_figure = px.histogram(
    invoice_values_for_chart,
    x="InvoiceValue",
    nbins=histogram_bin_count,
    labels={
        "InvoiceValue": "Invoice value (£)",
        "count": "Number of invoices",
    },
    hover_data={
        "InvoiceValue": ":£,.2f",
    },
)

distribution_figure.update_traces(
    marker_color="#2C7FB8",
)

distribution_figure.update_xaxes(
    tickprefix="£",
    tickformat=",.0f",
)

distribution_figure.update_layout(
    height=460,
    bargap=0.05,
    showlegend=False,
    margin={
        "l": 60,
        "r": 30,
        "t": 30,
        "b": 70,
    },
)

st.plotly_chart(
    distribution_figure,
    use_container_width=True,
    config=PLOTLY_CONFIG,
)

st.caption(
    f"Mean invoice value: £{average_invoice_value:,.2f}. "
    f"Median invoice value: £{median_invoice_value:,.2f}. "
    f"The chart is limited to £{invoice_chart_limit:,.2f}, the "
    "99th percentile of the selected data, for readability. "
    "All invoices remain included in the KPIs."
)


st.divider()


# Data table and download section
st.subheader("Download the selected trend data")

st.dataframe(
    sales_trend,
    use_container_width=True,
    hide_index=True,
)

trend_csv = sales_trend.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    label="Download filtered trend data as CSV",
    data=trend_csv,
    file_name=(
        f"sales_trend_{start_date}_{end_date}.csv"
    ),
    mime="text/csv",
    help=(
        "Download the aggregated data currently displayed "
        "in the revenue chart."
    ),
)
