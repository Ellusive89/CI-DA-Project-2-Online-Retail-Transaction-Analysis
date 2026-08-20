"""Interactive product-performance analysis for the retail dashboard."""

import pandas as pd
import plotly.express as px
import streamlit as st

from src.data_loader import load_completed_sales


st.set_page_config(
    page_title="Product Analysis",
    page_icon="📦",
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

METRIC_OPTIONS = {
    "Revenue": {
        "column": "Revenue",
        "axis_label": "Completed-sales revenue (£)",
        "colour_scale": "Blues",
    },
    "Units sold": {
        "column": "UnitsSold",
        "axis_label": "Units sold",
        "colour_scale": "Greens",
    },
    "Invoice reach": {
        "column": "InvoiceReach",
        "axis_label": "Completed invoices",
        "colour_scale": "Oranges",
    },
}


def filter_sales_data(
    data: pd.DataFrame,
    start_date,
    end_date,
    selected_countries: list[str],
) -> pd.DataFrame:
    """Filter completed sales by date and optional countries."""
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


def select_merchandise_rows(
    data: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separate merchandise from administrative product codes."""
    non_merchandise_mask = (
        data["StockCode"]
        .astype("string")
        .str.upper()
        .isin(NON_MERCHANDISE_CODES)
    )

    merchandise = data.loc[
        ~non_merchandise_mask
    ].copy()

    non_merchandise = data.loc[
        non_merchandise_mask
    ].copy()

    return merchandise, non_merchandise


def apply_product_search(
    data: pd.DataFrame,
    search_text: str,
) -> pd.DataFrame:
    """Filter merchandise using stock code or product description."""
    cleaned_search = search_text.strip()

    if not cleaned_search:
        return data.copy()

    stock_code_match = (
        data["StockCode"]
        .astype("string")
        .str.contains(
            cleaned_search,
            case=False,
            na=False,
            regex=False,
        )
    )

    description_match = (
        data["Description"]
        .astype("string")
        .str.contains(
            cleaned_search,
            case=False,
            na=False,
            regex=False,
        )
    )

    return data.loc[
        stock_code_match | description_match
    ].copy()


def create_product_summary(
    merchandise: pd.DataFrame,
) -> pd.DataFrame:
    """Create one analytical record per merchandise stock code."""
    primary_descriptions = (
        merchandise.groupby(
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
        merchandise.groupby(
            "StockCode",
            as_index=False,
        )
        .agg(
            Revenue=("LineRevenue", "sum"),
            UnitsSold=("Quantity", "sum"),
            InvoiceReach=("InvoiceNo", "nunique"),
        )
        .merge(
            primary_descriptions,
            on="StockCode",
            how="left",
            validate="one_to_one",
        )
    )

    product_summary["RealisedAverageUnitPrice"] = (
        product_summary["Revenue"]
        / product_summary["UnitsSold"]
    )

    total_product_revenue = product_summary[
        "Revenue"
    ].sum()

    product_summary["RevenueSharePercentage"] = (
        product_summary["Revenue"]
        / total_product_revenue
        * 100
    )

    return product_summary


def format_leading_value(
    metric_column: str,
    metric_value: float,
) -> str:
    """Format the leading product value for a dynamic insight."""
    if metric_column == "Revenue":
        return f"£{metric_value:,.2f}"

    return f"{metric_value:,.0f}"


st.title("Product Analysis")

st.markdown(
    """
    Identify high-performing merchandise products using revenue, units sold,
    and invoice reach. Use the controls to distinguish broadly popular products
    from isolated bulk orders.
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
st.sidebar.header("Product filters")

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

product_search = st.sidebar.text_input(
    "Product search",
    value="",
    placeholder="Stock code or description",
    help=(
        "Search for a complete or partial stock code "
        "or product description."
    ),
)

selected_metric_name = st.sidebar.selectbox(
    "Rank products by",
    options=list(METRIC_OPTIONS),
    index=0,
)

top_product_count = st.sidebar.slider(
    "Number of products",
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


start_date, end_date = selected_date_range

filtered_sales = filter_sales_data(
    completed_sales,
    start_date,
    end_date,
    selected_countries,
)


if filtered_sales.empty:
    st.warning(
        "No completed sales match the selected date and country filters."
    )
    st.stop()


merchandise_sales, non_merchandise_sales = (
    select_merchandise_rows(
        filtered_sales
    )
)

merchandise_sales = apply_product_search(
    merchandise_sales,
    product_search,
)


if merchandise_sales.empty:
    st.warning(
        "No merchandise products match the selected filters or search."
    )
    st.stop()


product_summary = create_product_summary(
    merchandise_sales
)


# Selected-scope KPIs
merchandise_revenue = merchandise_sales[
    "LineRevenue"
].sum()

merchandise_units = merchandise_sales[
    "Quantity"
].sum()

product_count = product_summary[
    "StockCode"
].nunique()

invoice_count = merchandise_sales[
    "InvoiceNo"
].nunique()

selected_country_count = merchandise_sales[
    "Country"
].nunique()

country_word = (
    "country"
    if selected_country_count == 1
    else "countries"
)


st.caption(
    f"Showing {product_count:,} merchandise products from "
    f"{start_date:%d %B %Y} to {end_date:%d %B %Y}, across "
    f"{selected_country_count:,} {country_word}."
)


st.subheader("Selected product scope")

revenue_column, unit_column, product_column, invoice_column = (
    st.columns(4)
)

with revenue_column:
    st.metric(
        label="Merchandise revenue",
        value=f"£{merchandise_revenue:,.2f}",
    )

with unit_column:
    st.metric(
        label="Merchandise units",
        value=f"{merchandise_units:,.0f}",
    )

with product_column:
    st.metric(
        label="Products",
        value=f"{product_count:,}",
    )

with invoice_column:
    st.metric(
        label="Invoice reach",
        value=f"{invoice_count:,}",
        help=(
            "Unique completed invoices containing at least "
            "one product in the selected scope."
        ),
    )


st.divider()


# Product ranking chart
selected_metric = METRIC_OPTIONS[
    selected_metric_name
]

metric_column = selected_metric["column"]
metric_axis_label = selected_metric["axis_label"]

top_products = (
    product_summary.nlargest(
        top_product_count,
        metric_column,
    )
    .sort_values(
        metric_column,
        ascending=True,
    )
)

st.subheader(
    f"Top products by {selected_metric_name.lower()}"
)

ranking_figure = px.bar(
    top_products,
    x=metric_column,
    y="Description",
    orientation="h",
    color=metric_column,
    color_continuous_scale=selected_metric[
        "colour_scale"
    ],
    labels={
        metric_column: metric_axis_label,
        "Description": "Product",
    },
    hover_data={
        "StockCode": True,
        "Revenue": ":£,.2f",
        "UnitsSold": ":,",
        "InvoiceReach": ":,",
        "RealisedAverageUnitPrice": ":£,.2f",
        "RevenueSharePercentage": ":.2f",
    },
)

if metric_column == "Revenue":
    ranking_figure.update_xaxes(
        tickprefix="£",
        tickformat=",.0f",
    )
else:
    ranking_figure.update_xaxes(
        tickformat=",",
    )

ranking_figure.update_layout(
    height=max(
        450,
        top_product_count * 31,
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
    ranking_figure,
    use_container_width=True,
    config=PLOTLY_CONFIG,
)


leading_product = top_products.loc[
    top_products[metric_column].idxmax()
]

formatted_leading_value = format_leading_value(
    metric_column,
    leading_product[metric_column],
)

st.success(
    f"{leading_product['Description']} leads the selected ranking "
    f"with {formatted_leading_value}. It appears across "
    f"{leading_product['InvoiceReach']:,.0f} completed invoices."
)

if leading_product["InvoiceReach"] <= 2:
    st.warning(
        "The leading product appears in very few invoices. "
        "Its ranking may be driven by an isolated bulk purchase "
        "rather than broad customer demand."
    )


st.divider()


# Price and volume relationship
st.subheader("Price and product sales volume")

st.markdown(
    """
    The bubble chart compares realised average unit price with units sold.
    Bubble size represents invoice reach and colour represents revenue.
    Logarithmic axes make highly skewed products easier to compare.
    """
)

price_volume_figure = px.scatter(
    product_summary,
    x="RealisedAverageUnitPrice",
    y="UnitsSold",
    size="InvoiceReach",
    color="Revenue",
    hover_name="Description",
    hover_data={
        "StockCode": True,
        "Revenue": ":£,.2f",
        "InvoiceReach": ":,",
        "RevenueSharePercentage": ":.2f",
    },
    log_x=True,
    log_y=True,
    size_max=36,
    color_continuous_scale="Viridis",
    labels={
        "RealisedAverageUnitPrice": (
            "Realised average unit price (£, logarithmic)"
        ),
        "UnitsSold": "Units sold (logarithmic)",
        "InvoiceReach": "Invoice reach",
        "Revenue": "Revenue (£)",
    },
)

price_volume_figure.update_layout(
    height=520,
    margin={
        "l": 70,
        "r": 40,
        "t": 30,
        "b": 80,
    },
)

st.plotly_chart(
    price_volume_figure,
    use_container_width=True,
    config=PLOTLY_CONFIG,
)

st.caption(
    "The chart shows an association, not a causal price effect. "
    "Product type, promotions, seasonality, wholesale orders and "
    "availability may affect both price and sales volume."
)


st.divider()


# Product table and download
st.subheader("Product ranking data")

ranking_table = top_products.sort_values(
    metric_column,
    ascending=False,
).reset_index(drop=True)

st.dataframe(
    ranking_table[
        [
            "StockCode",
            "Description",
            "Revenue",
            "UnitsSold",
            "InvoiceReach",
            "RealisedAverageUnitPrice",
            "RevenueSharePercentage",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)

product_csv = ranking_table.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    label="Download selected product ranking as CSV",
    data=product_csv,
    file_name=(
        f"product_ranking_{start_date}_{end_date}.csv"
    ),
    mime="text/csv",
)


with st.expander("Product-analysis scope and limitations"):
    st.markdown(
        f"""
        - Administrative and non-merchandise stock codes are excluded from
          product rankings.
        - The current filtered data contains
          **{len(non_merchandise_sales):,} excluded non-merchandise rows**.
        - These rows remain included in the Sales Overview revenue KPIs.
        - The dataset does not contain an original product-category field, so
          the application does not invent product categories.
        - Where one stock code has several descriptions, the most frequently
          occurring description in the selected data is displayed.
        - Revenue is not equivalent to profit because product costs are not
          supplied.
        """
    )
