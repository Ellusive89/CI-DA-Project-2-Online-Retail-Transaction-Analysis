# Retail: Online Retail Transaction Analysis (ORTA)

## Project overview

Retail: ORTA is an online retail data analytics project designed to help sales and marketing teams understand customer behaviour, product performance, geographic markets, cancellations, and sales trends.

The project uses historical transaction data from a UK-based online retailer. The analysis is documented in Jupyter Notebooks and presented through an interactive Streamlit dashboard.

The application helps retail decision-makers identify valuable customer groups, popular products, important markets, cancellation patterns, and potential marketing opportunities.

## Table of contents

- [Project overview](#project-overview)
- [Business problem](#business-problem)
- [Project rationale](#project-rationale)
- [Target audience](#target-audience)
- [Business requirements](#business-requirements)
- [Dataset](#dataset)
- [Data analysis objectives](#data-analysis-objectives)
- [Analytical methodology](#analytical-methodology)
- [ETL pipeline](#etl-pipeline)
- [Key analysis findings](#key-analysis-findings)
- [Hypothesis testing](#hypothesis-testing)
- [Machine learning](#machine-learning)
- [Streamlit dashboard](#streamlit-dashboard)
- [Project structure](#project-structure)

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

The project combines descriptive statistics, probability, hypothesis testing, exploratory analysis, machine learning, and interactive visualisation. This provides both analytical evidence and a practical tool for a real-world audience.

The project will not describe revenue as profit because the dataset does not contain product cost, fulfilment cost, marketing cost, or operating expenses.

## Target audience

The primary users are:

- e-commerce sales managers;
- marketing managers;
- customer relationship managers;
- product and pricing teams.

Users are expected to understand retail performance but should not need technical knowledge of Python or machine learning.

## Business requirements

The project answers the following business questions:

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

The analysis:

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

## Analytical methodology

The project follows a structured data analytics workflow:

1. **Business understanding:** define the retail questions, users, objectives,
   limitations, and required outputs.
2. **Data extraction:** load the supplied raw CSV without altering its original
   contents.
3. **Data transformation:** inspect quality, remove exact duplicates, label
   missing descriptions, classify transaction types, and create analytical
   features.
4. **Data loading:** export validated purpose-specific Parquet datasets.
5. **Exploratory data analysis:** analyse sales, products, time periods,
   geographic markets, cancellations, and invoice values.
6. **Statistical analysis:** apply descriptive statistics, empirical
   probability, hypothesis testing, correlation, and effect-size measurement.
7. **Machine learning:** create RFM customer features and apply K-Means
   clustering.
8. **Application development:** communicate results through a multipage
   Streamlit dashboard with interactive Plotly visualisations.
9. **Decision support:** provide an assumption-based marketing campaign planner.
10. **Evaluation:** explain model performance, analytical limitations, and
    appropriate use of the results.

Completed sales are analysed separately from cancellations and operational
adjustments. Customer-level analysis uses only identifiers considered reliable.

The project uses both descriptive and inferential methods. Descriptive methods
summarise the historical dataset, while hypothesis tests assess whether observed
relationships are unlikely under specified null hypotheses. Neither method
automatically demonstrates causation.

## ETL pipeline

The ETL pipeline is documented in
`jupyter_notebooks/01_ETL_Data_Cleaning.ipynb`.

### Extract

The original CSV is loaded into `df_raw`. It contains:

- 541,909 rows;
- 8 original columns;
- transactions between December 2010 and December 2011.

The raw DataFrame remains available for comparison throughout the notebook. All
cleaning and feature engineering are performed on a separate copy.

### Transform

The transformation process:

- removes 5,268 exact duplicate rows;
- converts invoice dates to a datetime format;
- strips unnecessary whitespace from text columns;
- labels 1,454 missing descriptions as `UNKNOWN DESCRIPTION`;
- identifies invoice numbers beginning with `C` as cancellations;
- identifies negative quantities, zero prices, and negative prices;
- creates a `TransactionType` classification;
- calculates `LineRevenue` as `Quantity * UnitPrice`;
- creates day, month, year, weekday, hour, and weekend features;
- identifies customer records suitable for customer-level analysis.

The transformed data contains 536,641 deduplicated and classified rows.

### Transaction classification

The transformed transactions are separated into:

| Transaction type | Rows |
|---|---:|
| Completed sale | 524,878 |
| Cancellation | 9,251 |
| Return or negative quantity | 1,336 |
| Zero-price transaction | 1,174 |
| Accounting adjustment | 2 |

Negative-quantity rows with zero prices are retained as operational adjustments
rather than automatically described as monetary customer returns.

### Customer identifier limitation

Customer identifier `15287` occurs 135,101 times, representing approximately
24.93% of the raw dataset. It appears across thousands of invoices, several
countries, and thousands of products. It is also equal to the dataset's median
customer identifier.

This pattern suggests that the supplied CSV may use `15287` as a replacement
for transactions where the original customer identifier was unknown.

The associated valid transactions remain included in sales, product, time, and
geographic analysis. Identifier `15287` is excluded from RFM segmentation
because treating it as one real customer would severely distort customer-level
results.

### Load

The ETL notebook exports four validated Parquet datasets:

| Dataset | Purpose | Rows |
|---|---|---:|
| `transactions_clean.parquet` | All deduplicated and classified rows | 536,641 |
| `completed_sales.parquet` | Positive completed sales | 524,878 |
| `returns_adjustments.parquet` | Cancellations and operational adjustments | 11,763 |
| `customer_sales.parquet` | Reliable customer-level completed sales | 392,672 |

Parquet preserves data types and reduces application loading time. The original
raw CSV remains unchanged and committed separately.

## Key analysis findings

The exploratory analysis is documented in
`jupyter_notebooks/02_Exploratory_Data_Analysis.ipynb`.

### Sales performance

The completed-sales dataset generated:

| Metric | Result |
|---|---:|
| Completed-sales revenue | £10,642,110.80 |
| Completed invoices | 19,960 |
| Mean invoice value | £533.17 |
| Median invoice value | £303.30 |
| Units sold | 5,572,420 |
| Unique products | 3,922 |
| Countries represented | 38 |

The mean invoice value is considerably higher than the median, demonstrating a
strongly right-skewed distribution. A relatively small number of large invoices
increase the mean.

November 2011 was the highest-revenue complete month, generating approximately
£1.50 million. February 2011 was the lowest complete month.

December 2011 is incomplete because the dataset ends on 9 December. It is not
compared directly with complete months.

### Product performance

`REGENCY CAKESTAND 3 TIER` generated the highest merchandise revenue.

`PAPER CRAFT, LITTLE BIRDIE` recorded exceptionally high unit sales and revenue,
but those sales occurred in only one completed invoice. It is therefore treated
as an exceptional bulk transaction rather than evidence of broad popularity.

`WHITE HANGING HEART T-LIGHT HOLDER` and `JUMBO BAG RED RETROSPOT` performed
strongly across revenue, units, and invoice reach. Invoice reach is used
alongside unit sales to distinguish widespread demand from isolated bulk
purchases.

Administrative codes such as postage, fees, manual entries, discounts, and
accounting adjustments remain included in overall financial totals but are
excluded from merchandise-product rankings.

### Geographic performance

The United Kingdom generated approximately 84.59% of completed-sales revenue,
making it the retailer's dominant market and indicating substantial geographic
concentration.

The Netherlands and EIRE were the largest international markets by revenue.
The Netherlands and Australia had high average invoice values but relatively
few reliable customers, suggesting possible wholesale concentration.

Germany and France had broader invoice and customer activity and may provide
more diversified international marketing opportunities.

These results do not show that location causes customer behaviour. Country may
be associated with wholesale activity, product mix, shipping arrangements, or
other unobserved factors.

### Cancellations and adjustments

The data contains:

- 9,251 cancellation product lines;
- 3,836 cancellation invoices;
- 275,560 cancelled units;
- £893,979.73 in recorded cancellation value.

The recorded cancellation value is approximately 8.40% of completed-sales
revenue. This is a comparison of transaction values, not a formal refund rate or
confirmed financial loss.

`PAPER CRAFT, LITTLE BIRDIE` has the highest cancellation value, but it is
associated with one cancellation invoice. This corresponds with the exceptional
bulk order found in the completed-sales analysis.

The dataset does not contain cancellation-reason or return-reason fields, so the
underlying causes cannot be confirmed.

## Hypothesis testing

Statistical principles and hypothesis tests are documented in
`jupyter_notebooks/03_Statistical_Analysis.ipynb`.

The notebook explains and applies:

- mean;
- median;
- variance;
- standard deviation;
- empirical probability;
- probability distributions;
- null and alternative hypotheses;
- significance levels;
- p-values;
- effect size;
- statistical and practical significance.

A significance level of 0.05 is used.

### Hypothesis 1: UK and international invoice values

**H0:** The mean log-transformed invoice value is equal for United Kingdom and
international invoices.

**H1:** The mean log-transformed invoice value differs between United Kingdom
and international invoices.

A Welch independent-samples t-test is used because the groups have unequal
sample sizes and equal variances cannot be assumed. Invoice values are
log-transformed to reduce right skew.

Results:

| Measure | Result |
|---|---:|
| UK mean invoice value | £499.57 |
| International mean invoice value | £845.11 |
| UK median invoice value | £299.95 |
| International median invoice value | £424.06 |
| Welch t-statistic | 18.85 |
| p-value | approximately 4.29 × 10⁻⁷⁴ |
| Cohen's d | approximately 0.435 |

The null hypothesis is rejected. There is strong evidence that transformed
invoice values differ between the two markets. Cohen's d indicates a
small-to-moderate standardised difference.

The result does not demonstrate that international location causes higher order
values. Wholesale customers, product combinations, or bulk purchasing may
explain part of the difference.

### Hypothesis 2: Product price and units sold

**H0:** There is no negative monotonic association between realised average unit
price and units sold.

**H1:** There is a negative monotonic association between realised average unit
price and units sold.

Spearman rank correlation is used because price and unit-sales data are strongly
skewed and the relationship does not need to be linear.

Results:

| Measure | Result |
|---|---:|
| Spearman correlation | approximately -0.379 |
| p-value | approximately 5.01 × 10⁻¹³⁴ |

The null hypothesis is rejected. The analysis finds a statistically significant,
moderate negative association between realised average unit price and units
sold.

This association does not estimate causal price elasticity. Product type,
seasonality, availability, wholesale purchasing, and promotions may influence
both observed price and sales volume.

## Machine learning

Customer segmentation is documented in
`jupyter_notebooks/04_Customer_Segmentation.ipynb`.

### Problem definition

The dataset does not contain existing customer-segment labels. Customer
segmentation is therefore treated as an unsupervised machine-learning problem.

RFM features are created for 4,337 reliable customer identifiers:

- **Recency:** days since the customer's most recent completed purchase;
- **Frequency:** number of unique completed invoices;
- **Monetary:** total completed-sales revenue generated by the customer.

The analysis date is set to one day after the final recorded transaction.

### Model selection

K-Means was selected because it:

- supports numeric behavioural features;
- produces distinct customer assignments;
- can be explained to non-technical users;
- integrates with Scikit-learn and Streamlit.

RFM features are transformed using `log1p` to reduce skew and standardised using
`StandardScaler`.

Models containing between two and eight clusters are compared using inertia,
silhouette score, interpretability, and business usefulness.

The two-cluster model produced the highest silhouette score of approximately
0.433. A four-cluster model was selected despite its lower score of approximately
0.333 because it provides more actionable marketing detail.

This trade-off is documented rather than presenting the four-cluster solution as
the statistically strongest option.

### Customer segments

| Segment | Customers | Customer share | Revenue share |
|---|---:|---:|---:|
| High-Value Loyal | 711 | 16.39% | 64.53% |
| Established Regulars | 1,175 | 27.09% | 24.23% |
| Recent Low-Frequency | 893 | 20.59% | 4.89% |
| Inactive Low-Value | 1,558 | 35.92% | 6.35% |

The High-Value Loyal segment represents a relatively small proportion of
customers but generates most customer-attributed revenue. This makes retention
and monitoring especially important.

The segmentation is exported to
`data/processed/customer_segments.parquet` for use in Streamlit.

### Model limitations

K-Means favours compact and approximately spherical clusters. Results depend on
the selected features, transformation, scaling, model initialisation, and
analysis date.

The moderate silhouette score indicates useful but overlapping customer groups.
Segment membership should be recalculated when substantial new transaction data
becomes available.

The model does not contain demographics, campaign response, profitability, or
customer-preference data.

## Streamlit dashboard

The project provides a multipage Streamlit application with explicit labelled
navigation.

### 🏠 Project Overview

Introduces the purpose, audience, business questions, workflow, headline KPIs,
and principal data limitations.

### 📈 Sales Overview

Provides:

- inclusive date filtering;
- country filtering;
- daily, weekly, and monthly aggregation;
- dynamic completed-sales KPIs;
- interactive revenue trends;
- interactive invoice-value distributions;
- downloadable filtered data.

### 📦 Product Analysis

Provides:

- date and country filters;
- product-description and stock-code search;
- rankings by revenue, units sold, or invoice reach;
- selectable top-product counts;
- interactive product bars;
- an interactive price-and-volume bubble chart;
- downloadable rankings.

### 🌍 Market Analysis

Provides:

- geographic market filters;
- market concentration metrics;
- revenue rankings;
- an interactive country map;
- adjustable invoice thresholds;
- average-invoice-value comparisons;
- downloadable country results.

A temporary `MapCountry` field converts dataset labels such as `EIRE`, `RSA`,
and `USA` into names recognised reliably by Plotly. The original country values
remain unchanged.

### ↩️ Cancellation Analysis

Provides:

- date, country, and adjustment-type filters;
- cancellation KPIs;
- adjustment-type comparison;
- monthly cancellation analysis;
- cancelled-product rankings;
- downloadable summaries.

### 👥 Customer Segmentation

Provides:

- customer-segment filters;
- Recency, Frequency, and Monetary filters;
- customer-identifier search;
- dynamic customer and revenue metrics;
- segment contribution comparisons;
- an interactive three-dimensional RFM explorer;
- segment-specific marketing recommendations;
- downloadable customer audiences.

### 🎯 Marketing Campaign Planner

The prototype converts user-supplied assumptions into estimated:

- contacts;
- conversions;
- incremental revenue;
- gross profit;
- campaign cost;
- contribution;
- return on investment;
- break-even conversion rate.

The planner is explicitly described as an assumption-based scenario tool, not a
prediction. The dataset does not contain historical campaign response, marketing
cost, or profit-margin data.

## Project structure

```text
.
├── app.py
├── pages/
│   ├── 0_Project_Overview.py
│   ├── 1_Sales_Overview.py
│   ├── 2_Product_Analysis.py
│   ├── 3_Market_Analysis.py
│   ├── 4_Cancellation_Analysis.py
│   ├── 5_Customer_Segmentation.py
│   └── 6_Marketing_Campaign_Planner.py
├── src/
│   ├── __init__.py
│   └── data_loader.py
├── data/
│   ├── raw/
│   │   └── online_retail.csv
│   └── processed/
│       ├── transactions_clean.parquet
│       ├── completed_sales.parquet
│       ├── returns_adjustments.parquet
│       ├── customer_sales.parquet
│       └── customer_segments.parquet
├── jupyter_notebooks/
│   ├── 01_ETL_Data_Cleaning.ipynb
│   ├── 02_Exploratory_Data_Analysis.ipynb
│   ├── 03_Statistical_Analysis.ipynb
│   └── 04_Customer_Segmentation.ipynb
├── .streamlit/
│   └── config.toml
├── requirements.txt
├── Procfile
├── setup.sh
└── README.md
