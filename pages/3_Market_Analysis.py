"""Interactive geographic market analysis for the retail dashboard."""

import pandas as pd
import plotly.express as px
import streamlit as st

from src.data_loader import load_completed_sales


st.set_page_config(
    page_title="Market Analysis",
    page_icon="🌍",
    layout="wide",
)

PLOTLY_CONFIG = {
    "displaylogo": False,
    "scrollZoom": False,
}

MAP_COUNTRY_REPLACEMENTS = {
    "EIRE": "Ireland",
    "RSA": "South Africa",
    "USA": "United States",
}

MAP_EXCLUSIONS = {
    "Unspecified",
    "European Community",
    "Channel Islands",
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


def create_country_summary(
    data: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate completed-sales performance by country."""
    country_summary = (
        data.groupby(
            "Country",
            as_index=False,
        )
        .agg(
            Revenue=("LineRevenue", "sum"),
            CompletedInvoices=("InvoiceNo", "nunique"),
            UnitsSold=("Quantity", "sum"),
            Products=("StockCode", "nunique"),
        )
    )

    country_summary["AverageInvoiceValue"] = (
        country_summary["Revenue"]
        / country_summary["CompletedInvoices"]
    )

    total_revenue = country_summary["Revenue"].sum()

    country_summary["RevenueSharePercentage"] = (
        country_summary["Revenue"]
        / total_revenue
        * 100
    )

    return country_summary.sort_values(
        "Revenue",
        ascending=False,
    ).reset_index(drop=True)


st.title("Market Analysis")

st.markdown(
    """
    Compare completed-sales performance across customer locations. Use the
    controls to investigate market size, revenue concentration and average
    invoice value.
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
st.sidebar.header("Market filters")

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
        "or select one or more countries for comparison."
    ),
)

top_market_count = st.sidebar.slider(
    "Markets in revenue ranking",
    min_value=5,
    max_value=20,
    value=12,
    step=1,
)

minimum_invoice_count = st.sidebar.slider(
    "Minimum invoices for average-value ranking",
    min_value=1,
    max_value=100,
    value=20,
    step=1,
    help=(
        "Markets below this threshold are excluded from the "
        "average-invoice-value chart to reduce small-sample distortion."
    ),
)


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
        "No completed sales match the selected market filters."
    )
    st.stop()


country_summary = create_country_summary(
    filtered_sales
)

selected_revenue = filtered_sales["LineRevenue"].sum()
selected_invoice_count = filtered_sales["InvoiceNo"].nunique()

selected_average_invoice_value = (
    selected_revenue
    / selected_invoice_count
)

market_count = country_summary["Country"].nunique()

top_market = country_summary.iloc[0]


st.caption(
    f"Showing completed sales from {start_date:%d %B %Y} to "
    f"{end_date:%d %B %Y}, across {market_count:,} "
    f"{'market' if market_count == 1 else 'markets'}."
)


# KPI section
st.subheader("Selected-market performance")

revenue_column, market_column, average_column, leader_column = (
    st.columns(4)
)

with revenue_column:
    st.metric(
        label="Completed-sales revenue",
        value=f"£{selected_revenue:,.2f}",
    )

with market_column:
    st.metric(
        label="Markets represented",
        value=f"{market_count:,}",
    )

with average_column:
    st.metric(
        label="Average invoice value",
        value=f"£{selected_average_invoice_value:,.2f}",
    )

with leader_column:
    st.metric(
        label="Leading market",
        value=top_market["Country"],
        help=(
            f"£{top_market['Revenue']:,.2f}, representing "
            f"{top_market['RevenueSharePercentage']:.2f}% "
            "of the selected revenue."
        ),
    )


if "United Kingdom" in country_summary["Country"].values:
    uk_revenue_share = country_summary.loc[
        country_summary["Country"].eq("United Kingdom"),
        "RevenueSharePercentage",
    ].iloc[0]

    st.info(
        f"The United Kingdom contributes {uk_revenue_share:.2f}% "
        "of revenue in the current selection."
    )
else:
    st.info(
        f"{top_market['Country']} contributes "
        f"{top_market['RevenueSharePercentage']:.2f}% "
        "of revenue in the current selection."
    )


st.divider()


# Revenue-ranking chart
st.subheader("Market revenue ranking")

top_revenue_markets = (
    country_summary.head(
        top_market_count
    )
    .sort_values(
        "Revenue",
        ascending=True,
    )
)

revenue_ranking_figure = px.bar(
    top_revenue_markets,
    x="Revenue",
    y="Country",
    orientation="h",
    color="Revenue",
    color_continuous_scale="Blues",
    labels={
        "Revenue": "Completed-sales revenue (£)",
        "Country": "Market",
    },
    hover_data={
        "CompletedInvoices": ":,",
        "UnitsSold": ":,",
        "Products": ":,",
        "AverageInvoiceValue": ":£,.2f",
        "RevenueSharePercentage": ":.2f",
    },
)

revenue_ranking_figure.update_xaxes(
    tickprefix="£",
    tickformat=",.0f",
)

revenue_ranking_figure.update_layout(
    height=max(
        440,
        len(top_revenue_markets) * 34,
    ),
    coloraxis_showscale=False,
    yaxis={
        "title": None,
        "automargin": True,
    },
    margin={
        "l": 150,
        "r": 30,
        "t": 30,
        "b": 70,
    },
)

st.plotly_chart(
    revenue_ranking_figure,
    use_container_width=True,
    config=PLOTLY_CONFIG,
)


st.divider()


# Geographic map
st.subheader("Geographic revenue distribution")

map_data = country_summary.copy()

map_data["MapCountry"] = map_data["Country"].replace(
    MAP_COUNTRY_REPLACEMENTS
)

map_data = map_data.loc[
    ~map_data["Country"].isin(MAP_EXCLUSIONS)
].copy()


if map_data.empty:
    st.info(
        "The selected locations cannot be displayed using standard "
        "country map boundaries. They remain included in the KPI "
        "and ranking calculations."
    )

else:
    map_figure = px.choropleth(
        map_data,
        locations="MapCountry",
        locationmode="country names",
        color="Revenue",
        hover_name="Country",
        hover_data={
            "MapCountry": False,
            "Revenue": ":£,.2f",
            "CompletedInvoices": ":,",
            "AverageInvoiceValue": ":£,.2f",
            "RevenueSharePercentage": ":.2f",
        },
        color_continuous_scale="Blues",
        labels={
            "Revenue": "Revenue (£)",
        },
    )

    map_figure.update_geos(
        showframe=False,
        showcoastlines=True,
        coastlinecolor="#7A8B85",
        projection_type="natural earth",
        fitbounds="locations",
    )

    map_figure.update_layout(
        height=560,
        margin={
            "l": 20,
            "r": 20,
            "t": 20,
            "b": 20,
        },
        coloraxis_colorbar={
            "title": "Revenue (£)",
        },
    )

    st.plotly_chart(
        map_figure,
        use_container_width=True,
        config=PLOTLY_CONFIG,
    )


st.caption(
    "Channel Islands, European Community and Unspecified records "
    "are excluded only from the map because they do not correspond "
    "cleanly to one standard country boundary. They remain included "
    "in totals and ranking tables."
)


st.divider()


# Average invoice value
st.subheader("Average invoice value by established market")

st.markdown(
    f"""
    Only markets with at least **{minimum_invoice_count:,} completed
    invoices** are included in this comparison. This reduces the risk that
    one unusually large invoice makes a very small market appear consistently
    high value.
    """
)

established_markets = country_summary.loc[
    country_summary["CompletedInvoices"]
    >= minimum_invoice_count
].copy()


if established_markets.empty:
    st.warning(
        "No markets meet the current minimum-invoice threshold. "
        "Reduce the threshold or broaden the date and country filters."
    )

else:
    top_average_value_markets = (
        established_markets.nlargest(
            10,
            "AverageInvoiceValue",
        )
        .sort_values(
            "AverageInvoiceValue",
            ascending=True,
        )
    )

    average_value_figure = px.bar(
        top_average_value_markets,
        x="AverageInvoiceValue",
        y="Country",
        orientation="h",
        color="AverageInvoiceValue",
        color_continuous_scale="Teal",
        labels={
            "AverageInvoiceValue": "Average invoice value (£)",
            "Country": "Market",
        },
        hover_data={
            "Revenue": ":£,.2f",
            "CompletedInvoices": ":,",
            "UnitsSold": ":,",
            "RevenueSharePercentage": ":.2f",
        },
    )

    average_value_figure.update_xaxes(
        tickprefix="£",
        tickformat=",.0f",
    )

    average_value_figure.update_layout(
        height=max(
            440,
            len(top_average_value_markets) * 38,
        ),
        coloraxis_showscale=False,
        yaxis={
            "title": None,
            "automargin": True,
        },
        margin={
            "l": 150,
            "r": 30,
            "t": 30,
            "b": 70,
        },
    )

    st.plotly_chart(
        average_value_figure,
        use_container_width=True,
        config=PLOTLY_CONFIG,
    )


st.caption(
    "A high average invoice value may indicate wholesale or bulk "
    "purchasing. It does not necessarily represent broad customer demand "
    "or high profitability."
)


st.divider()


# Market table and download
st.subheader("Market performance data")

market_table = country_summary[
    [
        "Country",
        "Revenue",
        "RevenueSharePercentage",
        "CompletedInvoices",
        "AverageInvoiceValue",
        "UnitsSold",
        "Products",
    ]
].copy()

st.dataframe(
    market_table,
    use_container_width=True,
    hide_index=True,
)

market_csv = market_table.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    label="Download selected market data as CSV",
    data=market_csv,
    file_name=(
        f"market_analysis_{start_date}_{end_date}.csv"
    ),
    mime="text/csv",
)


with st.expander("Market-analysis scope and limitations"):
    st.markdown(
        """
        - Country is taken directly from the supplied transaction dataset.
        - The dataset does not contain a separate geographic-region field.
        - Location does not demonstrate why customers behave differently.
        - Revenue is not equivalent to profit because costs are unavailable.
        - A high average invoice value may be caused by a small number of
          wholesale or bulk transactions.
        - December 2011 is incomplete because the dataset ends on 9 December.
        """
    )
