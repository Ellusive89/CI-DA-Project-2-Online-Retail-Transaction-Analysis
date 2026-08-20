"""Interactive marketing-campaign scenario planner."""

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from src.data_loader import load_customer_segments


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

SEGMENT_CAMPAIGNS = {
    "High-Value Loyal": {
        "campaign": "VIP retention and early-access campaign",
        "objective": (
            "Protect high-value relationships and maintain "
            "repeat-purchase behaviour."
        ),
        "example": (
            "Offer early access to new products or a loyalty benefit "
            "without relying on a broad price discount."
        ),
        "caution": (
            "Avoid unnecessary incentives that reduce margin from "
            "customers who may already intend to purchase."
        ),
    },
    "Established Regulars": {
        "campaign": "Cross-sell and loyalty progression campaign",
        "objective": (
            "Increase purchase frequency and encourage movement "
            "toward the High-Value Loyal segment."
        ),
        "example": (
            "Recommend complementary products and promote the next "
            "loyalty milestone."
        ),
        "caution": (
            "Recommendations should be relevant to previous purchases "
            "rather than applied uniformly."
        ),
    },
    "Recent Low-Frequency": {
        "campaign": "Second-purchase campaign",
        "objective": (
            "Encourage recent customers to complete another purchase."
        ),
        "example": (
            "Send a timely product recommendation related to the "
            "customer's recent order."
        ),
        "caution": (
            "Do not assume that every recent customer requires a discount."
        ),
    },
    "Inactive Low-Value": {
        "campaign": "Controlled win-back campaign",
        "objective": (
            "Test whether inactive customers can be re-engaged "
            "cost-effectively."
        ),
        "example": (
            "Send a low-cost reactivation message to a treatment group "
            "and compare it with an untreated control group."
        ),
        "caution": (
            "Avoid expensive incentives because this segment has low "
            "historical value and uncertain reactivation potential."
        ),
    },
}


def calculate_campaign_results(
    audience_size: int,
    conversion_rate_percentage: float,
    average_order_value: float,
    gross_margin_percentage: float,
    cost_per_contact: float,
    fixed_campaign_cost: float,
) -> dict[str, float]:
    """Calculate an assumption-based campaign scenario."""
    conversion_rate = conversion_rate_percentage / 100
    gross_margin_rate = gross_margin_percentage / 100

    expected_conversions = (
        audience_size
        * conversion_rate
    )

    estimated_revenue = (
        expected_conversions
        * average_order_value
    )

    estimated_gross_profit = (
        estimated_revenue
        * gross_margin_rate
    )

    variable_campaign_cost = (
        audience_size
        * cost_per_contact
    )

    total_campaign_cost = (
        fixed_campaign_cost
        + variable_campaign_cost
    )

    estimated_contribution = (
        estimated_gross_profit
        - total_campaign_cost
    )

    if total_campaign_cost > 0:
        estimated_roi_percentage = (
            estimated_contribution
            / total_campaign_cost
            * 100
        )
    else:
        estimated_roi_percentage = np.nan

    contribution_per_conversion = (
        average_order_value
        * gross_margin_rate
    )

    if total_campaign_cost == 0:
        break_even_conversions = 0
        break_even_conversion_rate = 0
    elif contribution_per_conversion > 0:
        break_even_conversions = int(
            np.ceil(
                total_campaign_cost
                / contribution_per_conversion
            )
        )

        break_even_conversion_rate = (
            break_even_conversions
            / audience_size
            * 100
        )
    else:
        break_even_conversions = np.nan
        break_even_conversion_rate = np.nan

    if expected_conversions > 0:
        cost_per_conversion = (
            total_campaign_cost
            / expected_conversions
        )
    else:
        cost_per_conversion = np.nan

    return {
        "ExpectedConversions": expected_conversions,
        "EstimatedRevenue": estimated_revenue,
        "EstimatedGrossProfit": estimated_gross_profit,
        "VariableCampaignCost": variable_campaign_cost,
        "TotalCampaignCost": total_campaign_cost,
        "EstimatedContribution": estimated_contribution,
        "EstimatedROIPercentage": estimated_roi_percentage,
        "BreakEvenConversions": break_even_conversions,
        "BreakEvenConversionRate": break_even_conversion_rate,
        "CostPerConversion": cost_per_conversion,
    }


def create_scenario_curve(
    audience_size: int,
    maximum_conversion_rate: float,
    average_order_value: float,
    gross_margin_percentage: float,
    cost_per_contact: float,
    fixed_campaign_cost: float,
) -> pd.DataFrame:
    """Calculate contribution across a range of conversion assumptions."""
    conversion_rates = np.linspace(
        0,
        maximum_conversion_rate,
        51,
    )

    scenario_records = []

    for conversion_rate in conversion_rates:
        result = calculate_campaign_results(
            audience_size=audience_size,
            conversion_rate_percentage=conversion_rate,
            average_order_value=average_order_value,
            gross_margin_percentage=gross_margin_percentage,
            cost_per_contact=cost_per_contact,
            fixed_campaign_cost=fixed_campaign_cost,
        )

        scenario_records.append(
            {
                "ConversionRatePercentage": conversion_rate,
                **result,
            }
        )

    return pd.DataFrame(
        scenario_records
    )


st.title("Marketing Campaign Planner")

st.markdown(
    """
    Test the possible financial outcome of a targeted marketing campaign.
    Select a customer segment and adjust the assumptions to estimate
    conversions, revenue, contribution and break-even performance.
    """
)

st.warning(
    "This is an assumption-based scenario tool, not a predictive model or "
    "guaranteed forecast. The dataset does not contain historical campaign "
    "response, profit-margin or marketing-cost data."
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


# Segment selection
st.sidebar.header("Campaign audience")

selected_segment = st.sidebar.selectbox(
    "Target customer segment",
    options=available_segments,
    index=0,
)

segment_customers = customer_segments.loc[
    customer_segments["Segment"].eq(
        selected_segment
    )
].copy()

segment_customer_count = len(
    segment_customers
)

segment_invoice_values = (
    segment_customers["Monetary"]
    / segment_customers["Frequency"]
)

benchmark_order_value = float(
    segment_invoice_values.median()
)

benchmark_recency = float(
    segment_customers["Recency"].median()
)

benchmark_frequency = float(
    segment_customers["Frequency"].median()
)


selected_audience_percentage = st.sidebar.slider(
    "Percentage of segment contacted",
    min_value=10,
    max_value=100,
    value=100,
    step=5,
)

audience_size = max(
    1,
    int(
        round(
            segment_customer_count
            * selected_audience_percentage
            / 100
        )
    ),
)


st.sidebar.divider()
st.sidebar.header("Campaign assumptions")

conversion_rate_percentage = st.sidebar.slider(
    "Expected conversion rate (%)",
    min_value=0.0,
    max_value=50.0,
    value=5.0,
    step=0.5,
    help=(
        "The assumed percentage of contacted customers "
        "who make an incremental purchase."
    ),
)

average_order_value = st.sidebar.number_input(
    "Expected order value (£)",
    min_value=1.0,
    value=round(
        benchmark_order_value,
        2,
    ),
    step=10.0,
    key=f"order_value_{selected_segment}",
    help=(
        "Defaults to the selected segment's median historical "
        "revenue per completed invoice. Change it to test another assumption."
    ),
)

gross_margin_percentage = st.sidebar.slider(
    "Assumed gross margin (%)",
    min_value=1.0,
    max_value=100.0,
    value=30.0,
    step=1.0,
    help=(
        "The dataset does not contain costs. Enter a business-approved "
        "gross-margin assumption after discounts."
    ),
)

cost_per_contact = st.sidebar.number_input(
    "Cost per contacted customer (£)",
    min_value=0.0,
    value=0.25,
    step=0.05,
)

fixed_campaign_cost = st.sidebar.number_input(
    "Fixed campaign cost (£)",
    min_value=0.0,
    value=250.0,
    step=50.0,
)


campaign_guidance = SEGMENT_CAMPAIGNS[
    selected_segment
]


# Historical segment context
st.subheader("Target-segment context")

customer_column, value_column, frequency_column, recency_column = (
    st.columns(4)
)

with customer_column:
    st.metric(
        label="Available customers",
        value=f"{segment_customer_count:,}",
    )

with value_column:
    st.metric(
        label="Median historical invoice value",
        value=f"£{benchmark_order_value:,.2f}",
        help=(
            "Median of customer revenue divided by completed "
            "invoice frequency within this segment."
        ),
    )

with frequency_column:
    st.metric(
        label="Median completed invoices",
        value=f"{benchmark_frequency:,.0f}",
    )

with recency_column:
    st.metric(
        label="Median recency",
        value=f"{benchmark_recency:,.0f} days",
    )


st.info(
    f"Suggested campaign: **{campaign_guidance['campaign']}**. "
    f"{campaign_guidance['objective']}"
)

with st.expander("Campaign example and caution"):
    st.markdown(
        f"**Example:** {campaign_guidance['example']}"
    )

    st.markdown(
        f"**Caution:** {campaign_guidance['caution']}"
    )


st.divider()


# Selected scenario
st.subheader("Selected campaign scenario")

campaign_results = calculate_campaign_results(
    audience_size=audience_size,
    conversion_rate_percentage=conversion_rate_percentage,
    average_order_value=average_order_value,
    gross_margin_percentage=gross_margin_percentage,
    cost_per_contact=cost_per_contact,
    fixed_campaign_cost=fixed_campaign_cost,
)

roi_value = campaign_results[
    "EstimatedROIPercentage"
]

roi_display = (
    f"{roi_value:,.1f}%"
    if np.isfinite(roi_value)
    else "N/A"
)

break_even_rate = campaign_results[
    "BreakEvenConversionRate"
]

break_even_rate_display = (
    f"{break_even_rate:,.2f}%"
    if np.isfinite(break_even_rate)
    else "N/A"
)


contact_column, conversion_column, revenue_column, cost_column = (
    st.columns(4)
)

with contact_column:
    st.metric(
        label="Customers contacted",
        value=f"{audience_size:,}",
    )

with conversion_column:
    st.metric(
        label="Expected conversions",
        value=(
            f"{campaign_results['ExpectedConversions']:,.1f}"
        ),
    )

with revenue_column:
    st.metric(
        label="Estimated incremental revenue",
        value=(
            f"£{campaign_results['EstimatedRevenue']:,.2f}"
        ),
    )

with cost_column:
    st.metric(
        label="Total campaign cost",
        value=(
            f"£{campaign_results['TotalCampaignCost']:,.2f}"
        ),
    )


contribution_column, roi_column, break_even_column = (
    st.columns(3)
)

with contribution_column:
    st.metric(
        label="Estimated contribution",
        value=(
            f"£{campaign_results['EstimatedContribution']:,.2f}"
        ),
        help=(
            "Estimated gross profit minus variable and fixed "
            "campaign costs."
        ),
    )

with roi_column:
    st.metric(
        label="Estimated campaign ROI",
        value=roi_display,
        help=(
            "Estimated contribution divided by total campaign cost."
        ),
    )

with break_even_column:
    st.metric(
        label="Break-even conversion rate",
        value=break_even_rate_display,
    )


if not np.isfinite(break_even_rate):
    st.error(
        "A break-even rate cannot be calculated with the current assumptions."
    )
elif break_even_rate > 100:
    st.error(
        "The estimated break-even conversion rate is above 100%. "
        "This scenario cannot break even under the current assumptions."
    )
elif conversion_rate_percentage >= break_even_rate:
    st.success(
        "The selected conversion assumption is at or above "
        "the estimated break-even rate."
    )
else:
    st.warning(
        "The selected conversion assumption is below the estimated "
        "break-even rate. Review the audience, costs, order value or "
        "margin assumptions."
    )


st.caption(
    "Contribution uses an assumed gross margin because the dataset "
    "contains revenue but does not contain product cost or profit."
)


st.divider()


# Conversion-rate scenario chart
st.subheader("Conversion-rate sensitivity")

if np.isfinite(break_even_rate):
    scenario_maximum_rate = min(
        100.0,
        max(
            20.0,
            conversion_rate_percentage * 2,
            break_even_rate * 1.25,
        ),
    )
else:
    scenario_maximum_rate = max(
        20.0,
        conversion_rate_percentage * 2,
    )

scenario_curve = create_scenario_curve(
    audience_size=audience_size,
    maximum_conversion_rate=scenario_maximum_rate,
    average_order_value=average_order_value,
    gross_margin_percentage=gross_margin_percentage,
    cost_per_contact=cost_per_contact,
    fixed_campaign_cost=fixed_campaign_cost,
)

scenario_figure = px.line(
    scenario_curve,
    x="ConversionRatePercentage",
    y="EstimatedContribution",
    labels={
        "ConversionRatePercentage": "Conversion rate (%)",
        "EstimatedContribution": "Estimated contribution (£)",
    },
    hover_data={
        "ExpectedConversions": ":.1f",
        "EstimatedRevenue": ":£,.2f",
        "EstimatedGrossProfit": ":£,.2f",
        "TotalCampaignCost": ":£,.2f",
        "EstimatedROIPercentage": ":.1f",
    },
)

scenario_figure.update_traces(
    line={
        "color": "#0B6E4F",
        "width": 3,
    },
)

scenario_figure.add_scatter(
    x=[
        conversion_rate_percentage,
    ],
    y=[
        campaign_results["EstimatedContribution"],
    ],
    mode="markers",
    name="Selected assumption",
    marker={
        "color": "#C62828",
        "size": 12,
    },
)

scenario_figure.add_hline(
    y=0,
    line_dash="dash",
    line_color="#555555",
)

scenario_figure.update_xaxes(
    ticksuffix="%",
)

scenario_figure.update_yaxes(
    tickprefix="£",
    tickformat=",.0f",
)

scenario_figure.update_layout(
    height=500,
    legend_title_text="",
    margin={
        "l": 70,
        "r": 30,
        "t": 30,
        "b": 70,
    },
)

st.plotly_chart(
    scenario_figure,
    use_container_width=True,
    config=PLOTLY_CONFIG,
)

st.caption(
    "The sensitivity curve changes only the conversion-rate assumption. "
    "Audience size, order value, margin and campaign costs remain fixed."
)


st.divider()


# Scenario details and download
st.subheader("Scenario assumptions and results")

scenario_summary = pd.DataFrame(
    {
        "Item": [
            "Target segment",
            "Available segment customers",
            "Audience percentage",
            "Customers contacted",
            "Expected conversion rate",
            "Expected order value",
            "Assumed gross margin",
            "Cost per contact",
            "Fixed campaign cost",
            "Expected conversions",
            "Estimated incremental revenue",
            "Estimated gross profit",
            "Total campaign cost",
            "Estimated contribution",
            "Estimated ROI",
            "Break-even conversions",
            "Break-even conversion rate",
        ],
        "Value": [
            selected_segment,
            f"{segment_customer_count:,}",
            f"{selected_audience_percentage:.0f}%",
            f"{audience_size:,}",
            f"{conversion_rate_percentage:.2f}%",
            f"£{average_order_value:,.2f}",
            f"{gross_margin_percentage:.2f}%",
            f"£{cost_per_contact:,.2f}",
            f"£{fixed_campaign_cost:,.2f}",
            f"{campaign_results['ExpectedConversions']:,.2f}",
            f"£{campaign_results['EstimatedRevenue']:,.2f}",
            f"£{campaign_results['EstimatedGrossProfit']:,.2f}",
            f"£{campaign_results['TotalCampaignCost']:,.2f}",
            f"£{campaign_results['EstimatedContribution']:,.2f}",
            roi_display,
            (
                f"{campaign_results['BreakEvenConversions']:,.0f}"
                if np.isfinite(
                    campaign_results["BreakEvenConversions"]
                )
                else "N/A"
            ),
            break_even_rate_display,
        ],
    }
)

st.dataframe(
    scenario_summary,
    use_container_width=True,
    hide_index=True,
)

scenario_csv = scenario_curve.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    label="Download sensitivity scenario as CSV",
    data=scenario_csv,
    file_name=(
        f"campaign_scenario_"
        f"{selected_segment.lower().replace(' ', '_')}.csv"
    ),
    mime="text/csv",
)


with st.expander("How this tool could improve sales"):
    st.markdown(
        """
        The campaign planner helps a marketing or retail manager:

        - focus a campaign on a behaviourally relevant customer segment;
        - test campaign economics before committing budget;
        - identify the conversion rate required to break even;
        - compare potential revenue with marketing and margin assumptions;
        - document assumptions for review by commercial stakeholders;
        - design a treatment-and-control experiment for real campaign
          validation.

        The tool should support a decision, not make the decision automatically.
        A campaign should initially be tested on a limited audience with a
        control group. Actual incremental conversion, revenue and contribution
        should then replace the assumptions used by this prototype.
        """
    )
