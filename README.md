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
- [UX design and accessibility](#ux-design-and-accessibility)
- [Technologies used](#technologies-used)
- [Local installation](#local-installation)
- [Testing](#testing)

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

1. **Business understanding:** define the retail questions, users, objectives, limitations, and required outputs.
2. **Data extraction:** load the supplied raw CSV without altering its original contents.
3. **Data transformation:** inspect quality, remove exact duplicates, label missing descriptions, classify transaction types, and create analytical features.
4. **Data loading:** export validated purpose-specific Parquet datasets.
5. **Exploratory data analysis:** analyse sales, products, time periods, geographic markets, cancellations, and invoice values.
6. **Statistical analysis:** apply descriptive statistics, empirical probability, hypothesis testing, correlation, and effect-size measurement.
7. **Machine learning:** create RFM customer features and apply K-Means clustering.
8. **Application development:** communicate results through a multipage Streamlit dashboard with interactive Plotly visualisations.
9. **Decision support:** provide an assumption-based marketing campaign planner.
10. **Evaluation:** explain model performance, analytical limitations, and appropriate use of the results.

Completed sales are analysed separately from cancellations and operational adjustments. Customer-level analysis uses only identifiers considered reliable.

The project uses both descriptive and inferential methods. Descriptive methods summarise the historical dataset, while hypothesis tests assess whether observed relationships are unlikely under specified null hypotheses. Neither method automatically demonstrates causation.

## ETL pipeline

The ETL pipeline is documented in `jupyter_notebooks/01_ETL_Data_Cleaning.ipynb`.

### Extract

The original CSV is loaded into `df_raw`. It contains:

- 541,909 rows;
- 8 original columns;
- transactions between December 2010 and December 2011.

The raw DataFrame remains available for comparison throughout the notebook. All cleaning and feature engineering are performed on a separate copy.

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

Negative-quantity rows with zero prices are retained as operational adjustments rather than automatically described as monetary customer returns.

### Customer identifier limitation

Customer identifier `15287` occurs 135,101 times, representing approximately 24.93% of the raw dataset. It appears across thousands of invoices, several
countries, and thousands of products. It is also equal to the dataset's median customer identifier.

This pattern suggests that the supplied CSV may use `15287` as a replacement for transactions where the original customer identifier was unknown.

The associated valid transactions remain included in sales, product, time, and geographic analysis. Identifier `15287` is excluded from RFM segmentation
because treating it as one real customer would severely distort customer-level results.

### Load

The ETL notebook exports four validated Parquet datasets:

| Dataset | Purpose | Rows |
|---|---|---:|
| `transactions_clean.parquet` | All deduplicated and classified rows | 536,641 |
| `completed_sales.parquet` | Positive completed sales | 524,878 |
| `returns_adjustments.parquet` | Cancellations and operational adjustments | 11,763 |
| `customer_sales.parquet` | Reliable customer-level completed sales | 392,672 |

Parquet preserves data types and reduces application loading time. The original raw CSV remains unchanged and committed separately.

## Key analysis findings

The exploratory analysis is documented in `jupyter_notebooks/02_Exploratory_Data_Analysis.ipynb`.

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

#### Invoice-value distribution

<img
  src="assets/images/invoice-value-distribution.png"
  alt="Histogram showing the right-skewed distribution of completed invoice values"
  width="900">

*Figure 1: Distribution of completed invoice values up to the 99th percentile.*

The distribution is strongly right-skewed. Most invoices are concentrated at lower values, while a relatively small number of large transactions extend the
upper tail. This explains why the mean invoice value of £533.17 is considerably higher than the median of £303.30. The 99th-percentile limit improves
readability without removing invoices from the KPI calculations.

#### Monthly completed-sales revenue

<img
  src="assets/images/monthly-sales-revenue.png"
  alt="Interactive line chart showing monthly completed-sales revenue from December 2010 to December 2011"
  width="900">

*Figure 2: Monthly completed-sales revenue.*

Revenue strengthened during September, October, and November 2011. November was the strongest complete month, generating approximately £1.50 million. December
2011 must not be interpreted as a full-month decline because the dataset ends on 9 December.

### Product performance

#### Top merchandise products by revenue

<img
  src="assets/images/top-products-revenue.png"
  alt="Horizontal bar chart ranking the ten highest-revenue merchandise products"
  width="900">

*Figure 3: Highest-revenue merchandise products.*

`REGENCY CAKESTAND 3 TIER` leads merchandise revenue.
`PAPER CRAFT, LITTLE BIRDIE` also records very high revenue, but its completed sales occur in only one invoice. Invoice reach is therefore considered alongside revenue and units sold so that isolated bulk transactions are not automatically described as widespread product popularity.

### Geographic performance

#### Geographic distribution of completed-sales revenue

<img
  src="assets/images/geographic-revenue-map.png"
  alt="World choropleth map showing completed-sales revenue by customer country"
  width="900">

*Figure 4: Geographic distribution of completed-sales revenue.*

The map makes the retailer's dependence on the United Kingdom immediately visible. The UK generated approximately 84.59% of completed-sales revenue.
International revenue exists across several markets, but its distribution is much smaller and sometimes concentrated among a limited number of customers or
bulk invoices.

### Cancellations and adjustments

#### Products with the highest cancellation value

<img
  src="assets/images/cancellation-product-values.png"
  alt="Horizontal bar chart showing merchandise products with the highest recorded cancellation values"
  width="900">

*Figure 5: Merchandise products with the highest cancellation values.*

`PAPER CRAFT, LITTLE BIRDIE` has the highest cancellation value, but the result comes from one cancellation invoice corresponding with the exceptional bulk
order identified in completed sales. It should not be interpreted as evidence of widespread customer dissatisfaction. The dataset does not provide
cancellation-reason fields.

The data contains:

- 9,251 cancellation product lines;
- 3,836 cancellation invoices;
- 275,560 cancelled units;
- £893,979.73 in recorded cancellation value.

The recorded cancellation value is approximately 8.40% of completed-sales revenue. This is a comparison of transaction values, not a formal refund rate or
confirmed financial loss.

## Hypothesis testing

Statistical principles and hypothesis tests are documented in `jupyter_notebooks/03_Statistical_Analysis.ipynb`.

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

**H0:** The mean log-transformed invoice value is equal for United Kingdom and international invoices.

**H1:** The mean log-transformed invoice value differs between United Kingdom and international invoices.

A Welch independent-samples t-test is used because the groups have unequal sample sizes and equal variances cannot be assumed. Invoice values are
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

The null hypothesis is rejected. There is strong evidence that transformed invoice values differ between the two markets. Cohen's d indicates a
small-to-moderate standardised difference.

The result does not demonstrate that international location causes higher order values. Wholesale customers, product combinations, or bulk purchasing may
explain part of the difference.

### Hypothesis 2: Product price and units sold

**H0:** There is no negative monotonic association between realised average unit price and units sold.

**H1:** There is a negative monotonic association between realised average unit price and units sold.

Spearman rank correlation is used because price and unit-sales data are strongly skewed and the relationship does not need to be linear.

Results:

| Measure | Result |
|---|---:|
| Spearman correlation | approximately -0.379 |
| p-value | approximately 5.01 × 10⁻¹³⁴ |

#### Price and sales-volume relationship

<img
  src="assets/images/price-units-relationship.png"
  alt="Logarithmic scatter plot comparing realised average product price with units sold"
  width="900">

*Figure 6: Realised average unit price compared with product sales volume.*

The chart supports the Spearman result of approximately -0.379: higher-priced products tend to have lower unit volumes. The relationship is moderate rather
than deterministic, and substantial variation remains. Product type, seasonality, promotions, availability, and wholesale purchasing may affect both
variables, so the chart does not demonstrate causal price elasticity.

## Machine learning

Customer segmentation is documented in
`jupyter_notebooks/04_Customer_Segmentation.ipynb`.

### Problem definition

The dataset does not contain existing customer-segment labels. Customer segmentation is therefore treated as an unsupervised machine-learning problem.

RFM features are created for 4,337 reliable customer identifiers:

- **Recency:** days since the customer's most recent completed purchase;
- **Frequency:** number of unique completed invoices;
- **Monetary:** total completed-sales revenue generated by the customer.

The analysis date is set to one day after the final recorded transaction.

### Model selection

#### Silhouette-score comparison

<img
  src="assets/images/cluster-silhouette-scores.png"
  alt="Line chart comparing silhouette scores for K-Means models containing two to eight clusters"
  width="900">

*Figure 7: Silhouette scores for candidate K-Means models.*

The two-cluster model has the highest silhouette score of approximately 0.433. The selected four-cluster model has a lower score of approximately 0.333.
Four clusters were retained because they provide more detailed and actionable marketing groups, while the reduced statistical separation is documented as a
model limitation.

K-Means was selected because it:

- supports numeric behavioural features;
- produces distinct customer assignments;
- can be explained to non-technical users;
- integrates with Scikit-learn and Streamlit.

RFM features are transformed using `log1p` to reduce skew and standardised using `StandardScaler`.

Models containing between two and eight clusters are compared using inertia, silhouette score, interpretability, and business usefulness.

### Customer segments

| Segment | Customers | Customer share | Revenue share |
|---|---:|---:|---:|
| High-Value Loyal | 711 | 16.39% | 64.53% |
| Established Regulars | 1,175 | 27.09% | 24.23% |
| Recent Low-Frequency | 893 | 20.59% | 4.89% |
| Inactive Low-Value | 1,558 | 35.92% | 6.35% |

#### Customer share and revenue contribution

<img
  src="assets/images/customer-segment-shares.png"
  alt="Grouped bar chart comparing customer share and revenue share across four RFM segments"
  width="900">

*Figure 8: Customer and revenue share by RFM segment.*

The High-Value Loyal segment contains approximately 16.39% of reliable customers but generates about 64.53% of customer-attributed revenue. In
contrast, the Inactive Low-Value segment is the largest by customer count but contributes only about 6.35% of revenue. This supports different marketing
objectives for retention, development, second-purchase activity, and controlled reactivation.

The segmentation is exported to `data/processed/customer_segments.parquet` for use in Streamlit.

### Model limitations

K-Means favours compact and approximately spherical clusters. Results depend on the selected features, transformation, scaling, model initialisation, and
analysis date.

The moderate silhouette score indicates useful but overlapping customer groups. Segment membership should be recalculated when substantial new transaction data becomes available.

The model does not contain demographics, campaign response, profitability, or customer-preference data.

## Streamlit dashboard

The project provides a multipage Streamlit application with explicit labelled navigation.

### 🏠 Project Overview

Introduces the purpose, audience, business questions, workflow, headline KPIs, and principal data limitations.

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

A temporary `MapCountry` field converts dataset labels such as `EIRE`, `RSA`, and `USA` into names recognised reliably by Plotly. The original country values
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

The planner is explicitly described as an assumption-based scenario tool, not a prediction. The dataset does not contain historical campaign response, marketing cost, or profit-margin data.

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
├── assets/
│   └── images/
│       ├── cancellation-product-values.png
│       ├── cluster-silhouette-scores.png
│       ├── customer-segment-shares.png
│       ├── geographic-revenue-map.png
│       ├── invoice-value-distribution.png
│       ├── monthly-sales-revenue.png
│       ├── price-units-relationship.png
│       └── top-products-revenue.png
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

## UX design and accessibility

The Streamlit dashboard is intended for retail managers, marketing teams, sales analysts, and other business users who need to explore sales performance
without working directly with Python code.

### Information hierarchy

The application presents information from general to specific:

1. The Project Overview introduces the business problem and analytical goals.
2. Sales Overview presents the principal performance indicators and sales trends.
3. Product and Market Analysis identify important products and geographic markets.
4. Cancellation Analysis investigates potentially lost revenue.
5. Customer Segmentation explains the machine-learning results.
6. Marketing Campaign Planner converts the analytical findings into an interactive business scenario.

Each dashboard page begins with a clear title and short explanation. Summary metrics are displayed before detailed charts so that users can understand the
most important results first.

### User control

Users control the analysis through Streamlit widgets, including:

- date-range filters;
- country and market filters;
- product selection;
- customer-segment selection;
- chart aggregation controls;
- marketing campaign assumptions;
- CSV download buttons.

Charts and metrics update when the selected filters change. The application does not use automatic pop-ups, audio, video, or other interactions that could
interrupt the user.

### Consistency

The dashboard uses consistent:

- page titles and introductory descriptions;
- sidebar navigation;
- filter placement;
- KPI formatting;
- Plotly chart styling;
- currency and percentage formatting;
- explanatory messages and chart captions.

The same terminology is used throughout the notebooks, processed datasets, README, and Streamlit application.

### Confirmation and feedback

The application provides feedback by:

- describing the currently selected reporting period;
- displaying the number of filtered records or customers;
- updating KPIs immediately after a filter changes;
- showing informative messages when a selection contains insufficient data;
- clearly labelling downloadable data;
- distinguishing calculated campaign scenarios from predictions.

### Accessibility

Accessibility was considered through:

- descriptive page, chart, axis, filter, and button labels;
- readable font sizes and chart heights;
- colour choices with visible contrast;
- information presented through text and values as well as colour;
- explanatory text accompanying visualisations;
- native Streamlit controls that support keyboard interaction;
- avoidance of flashing, autoplay, and time-limited content;
- responsive dashboard layouts that adapt to different screen widths.

Some Plotly charts use colour to help distinguish categories. Labels, hover information, and supporting text are also provided so that colour is not the
only way information is communicated.

## Technologies used

### Programming and analysis

- **Python** — principal programming language.
- **Pandas** — data loading, cleaning, transformation, aggregation, and analysis.
- **NumPy** — numerical calculations and feature creation.
- **SciPy** — statistical hypothesis testing.
- **Scikit-learn** — preprocessing, K-Means clustering, and model evaluation.
- **PyArrow** — storage and retrieval of processed Parquet datasets.
- **Jupyter Notebook** — documented ETL, exploratory analysis, statistics, and machine-learning workflows.

### Visualisation and application

- **Plotly** — interactive charts with zoom, hover, selection, and export controls.
- **Matplotlib and Seaborn** — supporting notebook visualisations.
- **Streamlit** — interactive multipage business dashboard.
- **HTML and Markdown** — application and project documentation.

### Development and deployment

- **Visual Studio Code** — project development environment.
- **Git** — version control.
- **GitHub** — remote repository and project hosting.
- **Heroku** — planned deployment platform.

## Local installation

Follow these instructions to run the project locally.

### Requirements

- Python 3.12
- Git
- A terminal or command-line application

### Installation

Clone the GitHub repository:

```bash
git clone https://github.com/Ellusive89/CI-DA-Project-2-Online-Retail-Transaction-Analysis.git