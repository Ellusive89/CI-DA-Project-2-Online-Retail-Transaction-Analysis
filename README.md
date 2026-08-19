# Retail: Online Retail Transaction Analysis (ORTA)

## Project overview

Retail: ORTA is an online retail data analytics project designed to help sales and marketing teams understand customer behaviour, product performance, geographic markets, cancellations, and sales trends.

The project uses historical transaction data from a UK-based online retailer. The analysis will be completed in Jupyter Notebooks and presented through an interactive Streamlit dashboard.

The finished application will help retail decision-makers identify valuable customer groups, popular products, important markets, and potential marketing opportunities.

## Table of contents

- [Business problem](#business-problem)
- [Project rationale](#project-rationale)
- [Target audience](#target-audience)
- [Business requirements](#business-requirements)
- [Dataset](#dataset)
- [Data analysis objectives](#data-analysis-objectives)
- [Planned hypotheses](#planned-hypotheses)
- [Machine learning objective](#machine-learning-objective)

## Business problem

Online retailers collect large volumes of transaction data, but raw transaction records do not directly explain:

- which customers are most valuable;
- which products generate the most sales;
- how revenue changes over time;
- which countries represent important markets;
- how cancellations affect business performance;
- which customer groups should receive different marketing treatments.

Retail: ORTA will transform the raw transaction data into understandable business insights and interactive decision-support tools.

## Project rationale

The project addresses a realistic retail analytics problem. Sales and marketing teams need reliable information to plan campaigns, prioritise customers, understand demand, and evaluate product performance.

The project will combine descriptive statistics, probability, hypothesis testing, exploratory analysis, machine learning, and interactive visualisation. This provides both analytical evidence and a practical tool for a real-world audience.

The project will not describe revenue as profit because the dataset does not contain product cost, fulfilment cost, marketing cost, or operating expenses.

## Target audience

The primary users are:

- e-commerce sales managers;
- marketing managers;
- customer relationship managers;
- product and pricing teams.

Users are expected to understand retail performance but should not need technical knowledge of Python or machine learning.

## Business requirements

The project will answer the following business questions:

1. What is the total completed sales revenue?
2. How does revenue change over time?
3. What is the average completed transaction value?
4. Which products generate the most revenue?
5. Which products sell the greatest number of units?
6. Which geographic markets generate the most revenue?
7. How many invoices are cancellations?
8. What customer groups can be identified from purchasing behaviour?
9. How do the identified customer groups differ?
10. Which products and marketing treatments may be appropriate for each group?
11. How could different campaign assumptions affect estimated revenue?

## Dataset

The project uses the Online Retail Transactions dataset.

Kaggle source:

https://www.kaggle.com/datasets/abhishekrp1517/online-retail-transactions-dataset


The dataset contains transactions from a UK-based non-store retailer between December 2010 and December 2011.

The principal fields are:

| Field | Description |
|---|---|
| `InvoiceNo` | Identifier assigned to an invoice |
| `StockCode` | Product identifier |
| `Description` | Product description |
| `Quantity` | Number of product units |
| `InvoiceDate` | Date and time of the transaction |
| `UnitPrice` | Price per unit in pounds sterling |
| `CustomerID` | Customer identifier |
| `Country` | Customer country |

Invoice numbers beginning with `C` represent cancellations.

The dataset does not contain product cost, product category, customer demographics, marketing-channel information, or profit.

## Data analysis objectives

The analysis will:

- inspect the structure and quality of the raw data;
- identify missing values, duplicates, cancellations, and unusual values;
- create a reproducible ETL pipeline;
- calculate line revenue using quantity multiplied by unit price;
- separate completed sales from cancellations and returns;
- calculate descriptive statistics;
- calculate relevant empirical probabilities;
- investigate sales trends over time;
- compare product and geographic performance;
- test business hypotheses;
- create customer-level RFM features;
- apply customer-segmentation machine learning;
- communicate findings through interactive Plotly charts;
- provide actionable but appropriately qualified recommendations.

## Planned hypotheses

### Hypothesis 1: Geographic order value

**Null hypothesis — H0**

The mean customer order value is the same for UK and non-UK customers.

**Alternative hypothesis — H1**

The mean customer order value differs between UK and non-UK customers.

The planned primary method is Welch's independent-samples t-test because the groups may have different sample sizes and variances.

The analysis will also consider distributions, confidence intervals, effect size, and a non-parametric sensitivity test.

### Hypothesis 2: Quantity and unit price

**Null hypothesis — H0**

There is no monotonic relationship between product quantity and unit price.

**Alternative hypothesis — H1**

There is a monotonic relationship between product quantity and unit price.

The planned method is Spearman rank correlation because retail quantity and price data may contain outliers and may not follow normal distributions.

Statistical significance will not automatically be treated as commercial importance. Effect sizes, data quality, assumptions, and business relevance will also be considered.

## Machine learning objective

The machine learning objective is to identify meaningful customer groups using RFM features:

- **Recency:** days since the customer's latest purchase;
- **Frequency:** number of completed invoices;
- **Monetary:** total completed revenue associated with the customer.

The project will use K-Means clustering from Scikit-learn.

K-Means is appropriate because the dataset does not provide a known customer segment target. This makes customer segmentation an unsupervised learning problem rather than a supervised classification problem.

The RFM features will be transformed and standardised so that features with large numerical values do not dominate the clustering calculation.

Several possible cluster counts will be evaluated using methods such as:

- inertia;
- silhouette score;
- cluster size;
- cluster interpretability;
- business usefulness.

Alternative methods such as hierarchical clustering and DBSCAN will be discussed as possible future approaches.