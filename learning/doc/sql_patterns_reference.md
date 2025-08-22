# SQL Analytical Patterns Reference Guide

## **Ranking & Top-N Analysis**
**SQL Tools:** ROW_NUMBER(), RANK(), DENSE_RANK(), NTILE()

**Business Questions:**
- "Who are our top 10 customers by revenue?"
- "What's the best-performing product in each category?"
- "Which stores are in the bottom quartile for sales?"
- "Show me the 3 most recent orders for each customer"
- "What are the top 5 cities by user engagement?"

---

## **Time-Based Comparisons**
**SQL Tools:** LAG(), LEAD(), DATEADD(), DATEDIFF(), window functions with date ranges

**Business Questions:**
- "How did this month compare to last month?"
- "What's our month-over-month growth rate?"
- "Show me year-over-year revenue comparison"
- "What was the previous order date for each customer?"
- "Which customers haven't ordered in the last 90 days?"

---

## **Running Totals & Cumulative Analysis**
**SQL Tools:** SUM() OVER(), COUNT() OVER() with ROWS/RANGE

**Business Questions:**
- "What's our cumulative revenue this year?"
- "Show me running count of new customers by month"
- "What's the running total of inventory received?"
- "How many customers have we acquired cumulatively?"
- "What's the progressive sum of daily sales?"

---

## **Moving Averages & Trends**
**SQL Tools:** AVG() OVER(), window functions with ROWS BETWEEN

**Business Questions:**
- "What's the 30-day moving average of daily active users?"
- "Show me the 7-day rolling average of sales"
- "What's the 3-month moving average revenue?"
- "Smooth out daily fluctuations to see the trend"
- "What's the rolling average response time?"

---

## **Cohort Analysis**
**SQL Tools:** CASE WHEN, GROUP BY, window functions, date functions

**Business Questions:**
- "How do customer retention rates vary by signup month?"
- "What's the lifetime value by customer acquisition cohort?"
- "How does product adoption differ by user cohort?"
- "Which marketing campaign cohorts have the best retention?"
- "What's the month-by-month retention curve?"

---

## **Funnel Analysis**
**SQL Tools:** SUM(CASE WHEN), conditional aggregation, CTEs

**Business Questions:**
- "What's our conversion rate through the sales funnel?"
- "Where do most users drop off in our signup process?"
- "How many users complete each step of onboarding?"
- "What's the conversion from trial to paid?"
- "Which funnel step has the biggest drop-off?"

---

## **Pivot & Cross-Tab Analysis**
**SQL Tools:** CASE WHEN with GROUP BY, PIVOT (if available), conditional aggregation

**Business Questions:**
- "Show me sales by product category for each month"
- "What's revenue by region and quarter in a matrix?"
- "Display customer counts by age group and gender"
- "Show me conversion rates by traffic source and device type"
- "Create a cross-tab of satisfaction scores by department"

---

## **Bucketing & Segmentation**
**SQL Tools:** CASE WHEN, NTILE(), mathematical functions

**Business Questions:**
- "Segment customers into high/medium/low value groups"
- "Create age brackets for demographic analysis"
- "Bucket transaction amounts into ranges"
- "Classify customers by purchase frequency"
- "Group response times into performance tiers"

---

## **Gap & Island Analysis**
**SQL Tools:** ROW_NUMBER(), LAG(), LEAD(), GROUP BY with arithmetic

**Business Questions:**
- "Find periods of consecutive activity for each user"
- "Identify gaps in our data collection"
- "What are the longest streaks of daily logins?"
- "Find missing sequence numbers in orders"
- "Identify continuous periods of high sales"

---

## **Percentage of Total**
**SQL Tools:** SUM() OVER(), window functions without PARTITION BY

**Business Questions:**
- "What percentage of total revenue does each product represent?"
- "Show me each region's share of total sales"
- "What's each customer's contribution to total revenue?"
- "Calculate department headcount as % of company"
- "Show market share by competitor"

---

## **Outlier Detection**
**SQL Tools:** STDDEV(), percentile functions, CASE WHEN with statistical functions

**Business Questions:**
- "Which transactions are unusually large?"
- "Find customers with abnormal purchase patterns"
- "Identify products with unusual price fluctuations"
- "Which days had exceptionally high/low traffic?"
- "Find outlier response times in our system"

---

## **First/Last Analysis**
**SQL Tools:** FIRST_VALUE(), LAST_VALUE(), MIN()/MAX() with window functions

**Business Questions:**
- "What was each customer's first purchase?"
- "Show me the most recent order status for each customer"
- "What's the first product each user viewed?"
- "Find the latest price for each product"
- "What was the initial vs final value for each record?"

---

## **Period-over-Period Comparison**
**SQL Tools:** LAG(), LEAD(), CASE WHEN, date functions

**Business Questions:**
- "Compare Q4 performance to Q3 for each salesperson"
- "Show week-over-week change in key metrics"
- "How does this year's monthly performance compare to last year?"
- "What's the day-over-day change in user activity?"
- "Compare current quarter to same quarter last year"

---

## **Conditional Aggregation**
**SQL Tools:** SUM(CASE WHEN), COUNT(CASE WHEN), AVG(CASE WHEN)

**Business Questions:**
- "How many orders were completed vs cancelled?"
- "What's the average revenue for premium vs basic customers?"
- "Count active vs inactive users by region"
- "Sum revenue only for profitable products"
- "Calculate conversion rates for different user segments"

---

## **Duplicate Detection & Deduplication**
**SQL Tools:** ROW_NUMBER() OVER(), COUNT(*) with HAVING, GROUP BY

**Business Questions:**
- "Find customers with duplicate records"
- "Identify repeat transactions that might be errors"
- "Which products have multiple entries in our catalog?"
- "Find users with multiple accounts"
- "Detect potential data quality issues"

---

## **Survival Analysis**
**SQL Tools:** DATEDIFF(), CASE WHEN, aggregation functions

**Business Questions:**
- "How long do customers typically stay active?"
- "What's the average time between first and last purchase?"
- "How long does it take to convert leads to customers?"
- "What's the typical lifespan of our products?"
- "How long do employees usually stay with the company?"

---

## **Market Basket Analysis**
**SQL Tools:** INNER JOIN, COUNT(), window functions, correlation functions

**Business Questions:**
- "Which products are frequently bought together?"
- "What's the typical bundle size for our customers?"
- "Find complementary products based on purchase patterns"
- "Which service combinations are most popular?"
- "Identify cross-selling opportunities"

---

## **Performance Against Targets**
**SQL Tools:** CASE WHEN, percentage calculations, comparison operators

**Business Questions:**
- "Which salespeople are meeting their quotas?"
- "How are we tracking against budget by department?"
- "Which metrics are above/below target?"
- "Show performance vs goal for each KPI"
- "Identify teams that are exceeding expectations"

---

## **ABC/Pareto Analysis (80/20 Rule)**
**SQL Tools:** SUM() OVER(), NTILE(), PERCENT_RANK(), running totals

**Business Questions:**
- "Which 20% of customers generate 80% of revenue?"
- "What products make up the majority of our sales volume?"
- "Which issues account for most of our customer complaints?"
- "Find the vital few vs useful many in any distribution"
- "What's our Pareto distribution for inventory turns?"

---

## **Seasonality & Cyclical Analysis**
**SQL Tools:** EXTRACT(), date functions, LAG() with yearly offsets, moving averages

**Business Questions:**
- "How do sales vary by season across years?"
- "What's our typical monthly pattern for user signups?"
- "Which days of the week perform best for each product?"
- "How does performance vary by quarter historically?"
- "What's the cyclical pattern in our support tickets?"

---

## **Recency, Frequency, Monetary (RFM) Analysis**
**SQL Tools:** NTILE(), DATEDIFF(), COUNT(), SUM(), CASE WHEN

**Business Questions:**
- "Segment customers by recency, frequency, and monetary value"
- "Which customers are at risk of churning?"
- "Identify our most valuable customer segments"
- "Who are our champions vs at-risk customers?"
- "Create targeted marketing segments based on behavior"

---

## **Text & Category Analysis**
**SQL Tools:** LIKE, REGEXP, STRING functions, CASE WHEN, GROUP BY

**Business Questions:**
- "What are the most common keywords in customer feedback?"
- "Group products by category patterns in descriptions"
- "Find all records containing specific terms"
- "Standardize inconsistent category naming"
- "Extract meaningful patterns from text fields"

---

## **Attribution & Multi-Touch Analysis**
**SQL Tools:** window functions, LAG(), LEAD(), weighted calculations, CTEs

**Business Questions:**
- "Which marketing touchpoints deserve credit for conversions?"
- "What's the customer journey from first touch to purchase?"
- "How do different channels contribute to final sales?"
- "What's the assisted conversion value for each channel?"
- "Which touchpoint sequence leads to highest conversion?"

---

## **Nested/Hierarchical Analysis**
**SQL Tools:** recursive CTEs, LEVEL, CONNECT BY (Oracle), self-joins

**Business Questions:**
- "Show me the organizational reporting structure"
- "What's the full product category hierarchy?"
- "Find all subordinates for each manager"
- "Calculate rollup totals by department tree"
- "Show parent-child relationships in our data"

---

## **Variance & Statistical Analysis**
**SQL Tools:** STDDEV(), VAR(), statistical functions, percentile functions

**Business Questions:**
- "Which metrics have the highest variability?"
- "Find products with inconsistent performance"
- "What's the standard deviation of our key KPIs?"
- "Identify high-variance vs stable metrics"
- "Which regions have the most volatile sales?"

---

## **Data Quality & Completeness**
**SQL Tools:** COUNT(), NULL checks, CASE WHEN, data profiling functions

**Business Questions:**
- "What percentage of records have missing data?"
- "Which fields have the most null values?"
- "Find records that don't meet business rules"
- "What's our data completeness rate by source?"
- "Identify data anomalies and inconsistencies"

---

## **Churn Prediction & Analysis**
**SQL Tools:** DATEDIFF(), LAG(), CASE WHEN, date comparisons

**Business Questions:**
- "Which customers haven't been active recently?"
- "What's our monthly churn rate?"
- "Find customers showing early churn signals"
- "How long before inactive customers typically churn?"
- "What's the churn rate by customer segment?"

---

## **Aggregation at Different Granularities**
**SQL Tools:** GROUP BY with ROLLUP/CUBE, GROUPING SETS, multiple CTEs

**Business Questions:**
- "Show me totals by day, month, quarter, and year simultaneously"
- "I need subtotals at multiple hierarchy levels"
- "Create summary tables at different grain levels"
- "Roll up metrics from transaction to customer to region level"
- "Show both detail and summary views in one query"