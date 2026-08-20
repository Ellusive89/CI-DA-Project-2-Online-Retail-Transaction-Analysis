"""Home page for the Online Retail Transaction Analysis dashboard."""

import streamlit as st

from src.data_loader import (
    load_completed_sales,
    load_customer_segments,
)


st.set_page_config(
    page_title="Retail Revenue & Customer Intelligence",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.title("Retail Revenue & Customer Intelligence")

st.markdown(
    """
    An interactive analytics dashboard for understanding completed sales,
    product performance, geographic markets, customer behaviour, and targeted
    marketing opportunities.
    """
)

st.caption(
    "Designed for retail managers, marketing teams and commercial analysts."
)


try:
    completed_sales = load_completed_sales()
    customer_segments = load_customer_segments()
except (FileNotFoundError, ValueError) as error:
    st.error(
        "The dashboard could not load its processed data. "
        "Run the ETL and customer-segmentation notebooks before starting "
        f"the application. Technical detail: {error}"
    )
    st.stop()


total_revenue = completed_sales["LineRevenue"].sum()
completed_invoices = completed_sales["InvoiceNo"].nunique()
reliable_customers = customer_segments["CustomerID"].nunique()
countries_served = completed_sales["Country"].nunique()


st.subheader("Business performance at a glance")

revenue_column, invoice_column, customer_column, country_column = (
    st.columns(4)
)

with revenue_column:
    st.metric(
        label="Completed-sales revenue",
        value=f"£{total_revenue:,.0f}",
        help="Revenue from positive completed-sales product lines.",
    )

with invoice_column:
    st.metric(
        label="Completed invoices",
        value=f"{completed_invoices:,}",
        help="Unique invoices classified as completed sales.",
    )

with customer_column:
    st.metric(
        label="Reliable customers",
        value=f"{reliable_customers:,}",
        help=(
            "Customer identifiers used for RFM segmentation. "
            "Unreliable identifier 15287 is excluded."
        ),
    )

with country_column:
    st.metric(
        label="Countries served",
        value=f"{countries_served:,}",
        help="Distinct country labels in completed-sales transactions.",
    )


st.divider()

st.subheader("Questions this dashboard answers")

question_one, question_two = st.columns(2)

with question_one:
    st.markdown(
        """
        #### Sales and products

        - How does revenue change over time?
        - Which products generate the most revenue?
        - Which products have broad invoice reach?
        - Where are cancellations concentrated?
        """
    )

with question_two:
    st.markdown(
        """
        #### Customers and markets

        - Which geographic markets generate the most revenue?
        - How concentrated is revenue in the United Kingdom?
        - Which customer segments generate the most value?
        - Which marketing actions suit each customer segment?
        """
    )


st.divider()

st.subheader("How the analysis works")

workflow_column, outcome_column = st.columns(2)

with workflow_column:
    st.markdown(
        """
        #### Analytical workflow

        1. Extract the supplied online retail CSV.
        2. Clean and validate transaction records.
        3. Separate completed sales from adjustments.
        4. Analyse sales, products and geographic markets.
        5. create RFM customer features.
        6. Segment customers using K-Means clustering.
        """
    )

with outcome_column:
    st.markdown(
        """
        #### Intended outcome

        The dashboard converts transaction data into practical information for
        sales monitoring, customer retention, product promotion and targeted
        marketing.

        Interactive filters and charts will allow users to investigate the
        evidence behind each recommendation.
        """
    )


with st.expander("Data scope and important limitations"):
    st.markdown(
        """
        - The dataset covers transactions from December 2010 to December 2011.
        - December 2011 is incomplete because the data ends on 9 December.
        - Completed-sales revenue is analysed separately from cancellations and
          accounting adjustments.
        - Customer identifier `15287` appears to combine transactions belonging
          to unknown customers. Its valid transactions remain in general sales
          analysis, but it is excluded from customer segmentation.
        - The data contains revenue rather than profit, so high revenue does not
          necessarily mean high profitability.
        - Statistical associations do not by themselves demonstrate causation.
        """
    )


st.info(
    "Dashboard pages for sales, products, markets and customer segments "
    "will appear in the sidebar as they are added."
)