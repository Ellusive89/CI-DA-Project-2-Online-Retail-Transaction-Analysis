"""Interactive RFM customer-segmentation dashboard."""

import pandas as pd
import plotly.express as px
import streamlit as st

from src.data_loader import load_customer_segments


st.set_page_config(
    page_title="Customer Segmentation",
    page_icon="👥",
    layout="wide",
)

PLOTLY_CONFIG = {
    "displaylogo": False,
    "scrollZoom": False,
}

SEGMENT_ORDER = [
    "High-Value Loyal",
    "Established Regulars",
    "Recent Low-Frequency",
    "Inactive Low-Value",
]

SEGMENT_COLOURS = {
    "High-Value Loyal": "#2E7D32",
    "Established Regulars": "#1976D2",
    "Recent Low-Frequency": "#F9A825",
    "Inactive Low-Value": "#C62828",
}

SEGMENT_GUIDANCE = {
    "High-Value Loyal": {
        "objective": "Retain and protect the retailer's highest-value audience.",
        "actions": [
            "Provide early access to new or limited products.",
            "Use personalised product recommendations.",
            "Offer loyalty benefits that encourage retention.",
            "Monitor declining purchase frequency as an early churn signal.",
            "Avoid unnecessary blanket discounts that reduce margin.",
        ],
        "measure": (
            "Retention rate, repeat-purchase frequency, customer revenue "
            "and campaign-generated incremental revenue."
        ),
    },
    "Established Regulars": {
        "objective": (
            "Increase customer value and encourage movement toward "
            "the High-Value Loyal segment."
        ),
        "actions": [
            "Recommend complementary products.",
            "Use cross-selling campaigns based on purchase history.",
            "Introduce loyalty milestones.",
            "Promote relevant seasonal collections.",
            "Test incentives for reaching the next loyalty level.",
        ],
        "measure": (
            "Purchase frequency, average invoice value, cross-sell "
            "conversion and movement into the High-Value Loyal segment."
        ),
    },
    "Recent Low-Frequency": {
        "objective": "Encourage a timely second or next purchase.",
        "actions": [
            "Use second-purchase campaigns.",
            "Recommend products related to the recent purchase.",
            "Introduce the retailer's loyalty programme.",
            "Test time-limited incentives where commercially appropriate.",
            "Provide useful post-purchase communication.",
        ],
        "measure": (
            "Second-purchase conversion, time to next purchase, "
            "repeat-order rate and incremental campaign revenue."
        ),
    },
    "Inactive Low-Value": {
        "objective": (
            "Test whether inactive customers can be re-engaged "
            "cost-effectively."
        ),
        "actions": [
            "Use low-cost automated re-engagement messages.",
            "Test win-back messages on a limited treatment group.",
            "Avoid expensive incentives without evidence of likely return.",
            "Reduce marketing frequency after repeated non-response.",
            "Compare campaign revenue with the cost of reactivation.",
        ],
        "measure": (
            "Reactivation rate, campaign cost, incremental revenue "
            "and unsubscribe rate."
        ),
    },
}


def create_segment_profile(
    data: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate the selected customer audience by segment."""
    segment_profile = (
        data.groupby(
            "Segment",
            as_index=False,
            observed=True,
        )
        .agg(
            Customers=("CustomerID", "size"),
            MeanRecency=("Recency", "mean"),
            MedianRecency=("Recency", "median"),
            MeanFrequency=("Frequency", "mean"),
            MedianFrequency=("Frequency", "median"),
            MeanMonetary=("Monetary", "mean"),
            MedianMonetary=("Monetary", "median"),
            TotalRevenue=("Monetary", "sum"),
        )
    )

    segment_profile["CustomerSharePercentage"] = (
        segment_profile["Customers"]
        / len(data)
        * 100
    )

    segment_profile["RevenueSharePercentage"] = (
        segment_profile["TotalRevenue"]
        / data["Monetary"].sum()
        * 100
    )

    segment_profile["Segment"] = pd.Categorical(
        segment_profile["Segment"],
        categories=SEGMENT_ORDER,
        ordered=True,
    )

    return segment_profile.sort_values(
        "Segment"
    ).reset_index(drop=True)


st.title("Customer Segmentation")

st.markdown(
    """
    Explore customer groups created using RFM features and K-Means clustering.
    Use the filters to define an audience and review suitable marketing
    strategies for each selected segment.
    """
)


try:
    customer_segments = load_customer_segments()
except (FileNotFoundError, ValueError) as error:
    st.error(
        "The customer-segmentation data could not be loaded. "
        f"Technical detail: {error}"
    )
    st.stop()


available_segments = [
    segment
    for segment in SEGMENT_ORDER
    if segment in customer_segments["Segment"].unique()
]

maximum_recency = int(
    customer_segments["Recency"].max()
)

maximum_frequency = int(
    customer_segments["Frequency"].max()
)

maximum_monetary = float(
    customer_segments["Monetary"].max()
)


# Sidebar filters
st.sidebar.header("Customer filters")

selected_segments = st.sidebar.multiselect(
    "Customer segments",
    options=available_segments,
    default=available_segments,
    help=(
        "Select one or more behavioural customer segments."
    ),
)

maximum_selected_recency = st.sidebar.slider(
    "Maximum recency in days",
    min_value=1,
    max_value=maximum_recency,
    value=maximum_recency,
    help=(
        "Keep customers whose most recent purchase occurred "
        "within this number of days of the analysis date."
    ),
)

minimum_selected_frequency = st.sidebar.slider(
    "Minimum completed invoices",
    min_value=1,
    max_value=maximum_frequency,
    value=1,
)

minimum_selected_monetary = st.sidebar.number_input(
    "Minimum customer revenue (£)",
    min_value=0.0,
    max_value=maximum_monetary,
    value=0.0,
    step=100.0,
    help=(
        "Minimum completed-sales revenue generated by a customer "
        "during the dataset period."
    ),
)

customer_id_search = st.sidebar.text_input(
    "Customer identifier",
    value="",
    placeholder="Optional identifier search",
    help=(
        "Enter a complete or partial customer identifier."
    ),
)


if not selected_segments:
    st.warning(
        "Select at least one customer segment to continue."
    )
    st.stop()


audience_mask = (
    customer_segments["Segment"].isin(selected_segments)
    & customer_segments["Recency"].le(
        maximum_selected_recency
    )
    & customer_segments["Frequency"].ge(
        minimum_selected_frequency
    )
    & customer_segments["Monetary"].ge(
        minimum_selected_monetary
    )
)

filtered_customers = customer_segments.loc[
    audience_mask
].copy()


if customer_id_search.strip():
    filtered_customers = filtered_customers.loc[
        filtered_customers["CustomerID"]
        .astype("string")
        .str.contains(
            customer_id_search.strip(),
            case=False,
            na=False,
            regex=False,
        )
    ].copy()


if filtered_customers.empty:
    st.warning(
        "No customers match the selected segment and RFM filters."
    )
    st.stop()


selected_customer_count = len(filtered_customers)

selected_revenue = filtered_customers[
    "Monetary"
].sum()

average_customer_revenue = filtered_customers[
    "Monetary"
].mean()

median_recency = filtered_customers[
    "Recency"
].median()

selected_customer_share = (
    selected_customer_count
    / len(customer_segments)
    * 100
)

selected_revenue_share = (
    selected_revenue
    / customer_segments["Monetary"].sum()
    * 100
)


st.success(
    f"The selected audience contains {selected_customer_count:,} customers, "
    f"representing {selected_customer_share:.2f}% of reliable customers "
    f"and {selected_revenue_share:.2f}% of customer-attributed revenue."
)


# KPI section
st.subheader("Selected audience")

customer_column, revenue_column, average_column, recency_column = (
    st.columns(4)
)

with customer_column:
    st.metric(
        label="Customers",
        value=f"{selected_customer_count:,}",
    )

with revenue_column:
    st.metric(
        label="Customer-attributed revenue",
        value=f"£{selected_revenue:,.2f}",
    )

with average_column:
    st.metric(
        label="Average customer revenue",
        value=f"£{average_customer_revenue:,.2f}",
    )

with recency_column:
    st.metric(
        label="Median recency",
        value=f"{median_recency:,.0f} days",
        help=(
            "Median number of days between the analysis date "
            "and each customer's most recent completed purchase."
        ),
    )


st.caption(
    "Customer-attributed revenue is lower than total completed-sales "
    "revenue because unreliable customer identifier 15287 is excluded "
    "from customer-level analysis."
)


st.divider()


# Segment profile and share comparison
st.subheader("Segment contribution")

segment_profile = create_segment_profile(
    filtered_customers
)

segment_share_data = segment_profile.melt(
    id_vars="Segment",
    value_vars=[
        "CustomerSharePercentage",
        "RevenueSharePercentage",
    ],
    var_name="Measure",
    value_name="Percentage",
)

segment_share_data["Measure"] = (
    segment_share_data["Measure"].replace(
        {
            "CustomerSharePercentage": "Customer share",
            "RevenueSharePercentage": "Revenue share",
        }
    )
)

share_figure = px.bar(
    segment_share_data,
    x="Segment",
    y="Percentage",
    color="Measure",
    barmode="group",
    category_orders={
        "Segment": SEGMENT_ORDER,
    },
    labels={
        "Segment": "Customer segment",
        "Percentage": "Share of current selection (%)",
        "Measure": "Measure",
    },
    hover_data={
        "Percentage": ":.2f",
    },
)

share_figure.update_yaxes(
    ticksuffix="%",
)

share_figure.update_layout(
    height=470,
    xaxis={
        "title": None,
        "automargin": True,
    },
    legend_title_text="",
    margin={
        "l": 70,
        "r": 30,
        "t": 30,
        "b": 110,
    },
)

st.plotly_chart(
    share_figure,
    use_container_width=True,
    config=PLOTLY_CONFIG,
)


st.dataframe(
    segment_profile[
        [
            "Segment",
            "Customers",
            "MeanRecency",
            "MedianRecency",
            "MeanFrequency",
            "MedianFrequency",
            "MeanMonetary",
            "MedianMonetary",
            "TotalRevenue",
            "CustomerSharePercentage",
            "RevenueSharePercentage",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)


st.divider()


# Interactive three-dimensional RFM chart
st.subheader("RFM customer explorer")

st.markdown(
    """
    Rotate, zoom and hover over the chart to explore customer behaviour.
    Logarithmic axes make the highly skewed RFM values easier to compare.
    Lower Recency values indicate more recent purchasing.
    """
)

rfm_figure = px.scatter_3d(
    filtered_customers,
    x="Recency",
    y="Frequency",
    z="Monetary",
    color="Segment",
    color_discrete_map=SEGMENT_COLOURS,
    category_orders={
        "Segment": SEGMENT_ORDER,
    },
    log_x=True,
    log_y=True,
    log_z=True,
    opacity=0.68,
    labels={
        "Recency": "Recency in days (logarithmic)",
        "Frequency": "Completed invoices (logarithmic)",
        "Monetary": "Customer revenue (£, logarithmic)",
        "Segment": "Customer segment",
    },
    hover_data={
        "CustomerID": True,
        "LastPurchase": True,
        "Cluster": False,
    },
)

rfm_figure.update_layout(
    height=650,
    legend_title_text="Customer segment",
    margin={
        "l": 20,
        "r": 20,
        "t": 30,
        "b": 30,
    },
)

st.plotly_chart(
    rfm_figure,
    use_container_width=True,
    config=PLOTLY_CONFIG,
)


st.divider()


# Marketing actions
st.subheader("Recommended marketing actions")

st.markdown(
    """
    Recommendations are displayed for the currently selected segments.
    They are starting hypotheses for controlled campaigns rather than
    guaranteed outcomes.
    """
)

for segment in SEGMENT_ORDER:
    if segment not in selected_segments:
        continue

    guidance = SEGMENT_GUIDANCE[segment]

    with st.expander(
        f"{segment}: {guidance['objective']}",
        expanded=len(selected_segments) == 1,
    ):
        st.markdown("**Recommended actions**")

        for action in guidance["actions"]:
            st.markdown(f"- {action}")

        st.markdown(
            f"**Suggested evaluation measures:** "
            f"{guidance['measure']}"
        )


st.divider()


# Downloadable customer audience
st.subheader("Selected customer audience")

audience_table = filtered_customers[
    [
        "CustomerID",
        "Segment",
        "Recency",
        "Frequency",
        "Monetary",
        "LastPurchase",
    ]
].sort_values(
    "Monetary",
    ascending=False,
)

st.dataframe(
    audience_table,
    use_container_width=True,
    hide_index=True,
)

audience_csv = audience_table.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    label="Download selected customer audience as CSV",
    data=audience_csv,
    file_name="selected_customer_audience.csv",
    mime="text/csv",
    help=(
        "Download the customers currently included by the "
        "segment and RFM filters."
    ),
)


with st.expander("Model methodology and limitations"):
    st.markdown(
        """
        - The model uses Recency, Frequency and Monetary features.
        - RFM values were log-transformed and standardised before clustering.
        - K-Means was trained with four clusters, `random_state=42` and
          `n_init=20`.
        - The four-cluster silhouette score is approximately 0.333.
        - A two-cluster model had a higher silhouette score of approximately
          0.433, but four clusters were retained to provide more actionable
          marketing detail.
        - A silhouette score of 0.333 indicates useful but overlapping
          customer groups.
        - Segment labels describe observed purchase behaviour, not customer
          demographics or motivations.
        - Filters do not retrain the model. They select customers from the
          previously validated clustering result.
        - Customer identifier 15287 is excluded because it appears to combine
          transactions belonging to unknown customers.
        - Campaign effectiveness must be tested using treatment and control
          groups before causal conclusions are made.
        """
    )
