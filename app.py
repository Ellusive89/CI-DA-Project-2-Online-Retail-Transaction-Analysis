"""Application entry point and dashboard navigation."""

import streamlit as st


st.set_page_config(
    page_title="Retail Revenue & Customer Intelligence",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)


navigation = st.navigation(
    {
        "Overview": [
            st.Page(
                "pages/0_Project_Overview.py",
                title="Project Overview",
                icon="🏠",
                default=True,
            ),
            st.Page(
                "pages/1_Sales_Overview.py",
                title="Sales Overview",
                icon="📈",
            ),
        ],
        "Business Analysis": [
            st.Page(
                "pages/2_Product_Analysis.py",
                title="Product Analysis",
                icon="📦",
            ),
            st.Page(
                "pages/3_Market_Analysis.py",
                title="Market Analysis",
                icon="🌍",
            ),
            st.Page(
                "pages/4_Cancellation_Analysis.py",
                title="Cancellation Analysis",
                icon="↩️",
            ),
            st.Page(
                "pages/5_Customer_Segmentation.py",
                title="Customer Segmentation",
                icon="👥",
            ),
        ],
        "Decision Support": [
            st.Page(
                "pages/6_Marketing_Campaign_Planner.py",
                title="Marketing Campaign Planner",
                icon="🎯",
            ),
        ],
    },
    position="sidebar",
    expanded=True,
)


navigation.run()
