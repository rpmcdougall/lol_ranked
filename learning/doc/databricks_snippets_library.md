# Databricks SQL Analytical Patterns Snippet Library

## **Ranking & Top-N Analysis**

### Top N by Group
```sql
-- Top 3 products by revenue in each category
SELECT category, product_name, revenue, product_rank
FROM (
  SELECT 
    category,
    product_name,
    revenue,
    ROW_NUMBER() OVER (PARTITION BY category ORDER BY revenue DESC) as product_rank
  FROM products
) ranked
WHERE product_rank <= 3
ORDER BY category, product_rank;
```

### Quartile Segmentation
```sql
-- Segment customers into quartiles by revenue
SELECT 
  customer_id,
  revenue,
  NTILE(4) OVER (ORDER BY revenue DESC) as revenue_quartile,
  CASE 
    WHEN NTILE(4) OVER (ORDER BY revenue DESC) = 1 THEN 'Top 25%'
    WHEN NTILE(4) OVER (ORDER BY revenue DESC) = 2 THEN 'Second 25%'
    WHEN NTILE(4) OVER (ORDER BY revenue DESC) = 3 THEN 'Third 25%'
    ELSE 'Bottom 25%'
  END as quartile_label
FROM customer_revenue;
```

### Recent Records per Group
```sql
-- 3 most recent orders per customer
SELECT customer_id, order_date, order_amount
FROM (
  SELECT 
    customer_id,
    order_date,
    order_amount,
    ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC) as rn
  FROM orders
) recent
WHERE rn <= 3;
```

---

## **Time-Based Comparisons**

### Month-over-Month Growth
```sql
-- Monthly revenue with MoM growth rate
SELECT 
  month,
  revenue,
  LAG(revenue, 1) OVER (ORDER BY month) as prev_month_revenue,
  ROUND(
    (revenue - LAG(revenue, 1) OVER (ORDER BY month)) / 
    LAG(revenue, 1) OVER (ORDER BY month) * 100, 2
  ) as mom_growth_rate
FROM monthly_revenue
ORDER BY month;
```

### Year-over-Year Comparison
```sql
-- YoY comparison using date functions
SELECT 
  date_trunc('month', order_date) as month,
  SUM(order_amount) as current_revenue,
  LAG(SUM(order_amount), 12) OVER (ORDER BY date_trunc('month', order_date)) as prev_year_revenue,
  ROUND(
    (SUM(order_amount) - LAG(SUM(order_amount), 12) OVER (ORDER BY date_trunc('month', order_date))) /
    LAG(SUM(order_amount), 12) OVER (ORDER BY date_trunc('month', order_date)) * 100, 2
  ) as yoy_growth
FROM orders
GROUP BY date_trunc('month', order_date)
ORDER BY month;
```

### Customer Recency Analysis
```sql
-- Find customers who haven't ordered in 90 days
SELECT 
  customer_id,
  MAX(order_date) as last_order_date,
  datediff(current_date(), MAX(order_date)) as days_since_last_order
FROM orders
GROUP BY customer_id
HAVING datediff(current_date(), MAX(order_date)) > 90
ORDER BY days_since_last_order DESC;
```

---

## **Running Totals & Cumulative Analysis**

### Cumulative Revenue
```sql
-- Running total of daily revenue
SELECT 
  order_date,
  daily_revenue,
  SUM(daily_revenue) OVER (ORDER BY order_date ROWS UNBOUNDED PRECEDING) as cumulative_revenue
FROM (
  SELECT 
    date(order_date) as order_date,
    SUM(order_amount) as daily_revenue
  FROM orders
  GROUP BY date(order_date)
) daily_totals
ORDER BY order_date;
```

### Running Customer Count
```sql
-- Cumulative customer acquisition
SELECT 
  signup_month,
  new_customers,
  SUM(new_customers) OVER (ORDER BY signup_month ROWS UNBOUNDED PRECEDING) as total_customers
FROM (
  SELECT 
    date_trunc('month', signup_date) as signup_month,
    COUNT(DISTINCT customer_id) as new_customers
  FROM customers
  GROUP BY date_trunc('month', signup_date)
) monthly_signups
ORDER BY signup_month;
```

---

## **Moving Averages & Trends**

### 7-Day Moving Average
```sql
-- 7-day rolling average of daily sales
SELECT 
  order_date,
  daily_sales,
  AVG(daily_sales) OVER (
    ORDER BY order_date 
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
  ) as ma_7_day
FROM (
  SELECT 
    date(order_date) as order_date,
    SUM(order_amount) as daily_sales
  FROM orders
  GROUP BY date(order_date)
) daily_sales
ORDER BY order_date;
```

### 30-Day Moving Average with Trend
```sql
-- 30-day MA with trend indicator
WITH daily_metrics AS (
  SELECT 
    date(created_at) as metric_date,
    COUNT(DISTINCT user_id) as daily_active_users
  FROM user_activity
  GROUP BY date(created_at)
),
moving_avg AS (
  SELECT 
    metric_date,
    daily_active_users,
    AVG(daily_active_users) OVER (
      ORDER BY metric_date 
      ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as ma_30_day
  FROM daily_metrics
)
SELECT 
  *,
  CASE 
    WHEN daily_active_users > ma_30_day THEN 'Above Trend'
    WHEN daily_active_users < ma_30_day THEN 'Below Trend'
    ELSE 'On Trend'
  END as trend_status
FROM moving_avg
ORDER BY metric_date;
```

---

## **Cohort Analysis**

### Monthly Retention Cohort
```sql
-- Customer cohort retention analysis
WITH cohorts AS (
  SELECT 
    customer_id,
    date_trunc('month', MIN(order_date)) as cohort_month
  FROM orders
  GROUP BY customer_id
),
cohort_data AS (
  SELECT 
    c.cohort_month,
    date_trunc('month', o.order_date) as order_month,
    COUNT(DISTINCT o.customer_id) as customers
  FROM cohorts c
  JOIN orders o ON c.customer_id = o.customer_id
  GROUP BY c.cohort_month, date_trunc('month', o.order_date)
),
cohort_sizes AS (
  SELECT cohort_month, COUNT(*) as total_customers
  FROM cohorts
  GROUP BY cohort_month
)
SELECT 
  cd.cohort_month,
  cd.order_month,
  datediff(cd.order_month, cd.cohort_month) as months_since_first_order,
  cd.customers,
  cs.total_customers,
  ROUND(cd.customers * 100.0 / cs.total_customers, 2) as retention_rate
FROM cohort_data cd
JOIN cohort_sizes cs ON cd.cohort_month = cs.cohort_month
ORDER BY cd.cohort_month, cd.order_month;
```

---

## **Funnel Analysis**

### Conversion Funnel
```sql
-- Multi-step conversion funnel
WITH funnel_steps AS (
  SELECT 
    user_id,
    MAX(CASE WHEN event_type = 'page_view' THEN 1 ELSE 0 END) as viewed,
    MAX(CASE WHEN event_type = 'add_to_cart' THEN 1 ELSE 0 END) as added_to_cart,
    MAX(CASE WHEN event_type = 'checkout_start' THEN 1 ELSE 0 END) as started_checkout,
    MAX(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) as purchased
  FROM user_events
  GROUP BY user_id
)
SELECT 
  'Page View' as step,
  SUM(viewed) as users,
  ROUND(SUM(viewed) * 100.0 / SUM(viewed), 2) as conversion_rate
FROM funnel_steps
UNION ALL
SELECT 
  'Add to Cart' as step,
  SUM(added_to_cart) as users,
  ROUND(SUM(added_to_cart) * 100.0 / SUM(viewed), 2) as conversion_rate
FROM funnel_steps
UNION ALL
SELECT 
  'Checkout Started' as step,
  SUM(started_checkout) as users,
  ROUND(SUM(started_checkout) * 100.0 / SUM(viewed), 2) as conversion_rate
FROM funnel_steps
UNION ALL
SELECT 
  'Purchase' as step,
  SUM(purchased) as users,
  ROUND(SUM(purchased) * 100.0 / SUM(viewed), 2) as conversion_rate
FROM funnel_steps;
```

---

## **Pivot & Cross-Tab Analysis**

### Revenue by Region and Quarter
```sql
-- Pivot table: revenue by region and quarter
SELECT 
  region,
  SUM(CASE WHEN quarter(order_date) = 1 THEN order_amount ELSE 0 END) as Q1_revenue,
  SUM(CASE WHEN quarter(order_date) = 2 THEN order_amount ELSE 0 END) as Q2_revenue,
  SUM(CASE WHEN quarter(order_date) = 3 THEN order_amount ELSE 0 END) as Q3_revenue,
  SUM(CASE WHEN quarter(order_date) = 4 THEN order_amount ELSE 0 END) as Q4_revenue,
  SUM(order_amount) as total_revenue
FROM orders
WHERE year(order_date) = 2024
GROUP BY region
ORDER BY total_revenue DESC;
```

### Customer Segmentation Cross-Tab
```sql
-- Customer counts by age group and gender
SELECT 
  age_group,
  SUM(CASE WHEN gender = 'M' THEN 1 ELSE 0 END) as male_customers,
  SUM(CASE WHEN gender = 'F' THEN 1 ELSE 0 END) as female_customers,
  SUM(CASE WHEN gender = 'Other' THEN 1 ELSE 0 END) as other_customers,
  COUNT(*) as total_customers
FROM (
  SELECT 
    *,
    CASE 
      WHEN age < 25 THEN '18-24'
      WHEN age < 35 THEN '25-34'
      WHEN age < 45 THEN '35-44'
      WHEN age < 55 THEN '45-54'
      ELSE '55+'
    END as age_group
  FROM customers
) customer_segments
GROUP BY age_group
ORDER BY age_group;
```

---

## **Bucketing & Segmentation**

### Customer Value Segmentation
```sql
-- Segment customers by total spend
WITH customer_spend AS (
  SELECT 
    customer_id,
    SUM(order_amount) as total_spend
  FROM orders
  GROUP BY customer_id
),
spend_percentiles AS (
  SELECT 
    percentile_approx(total_spend, 0.8) as p80,
    percentile_approx(total_spend, 0.5) as p50,
    percentile_approx(total_spend, 0.2) as p20
  FROM customer_spend
)
SELECT 
  cs.customer_id,
  cs.total_spend,
  CASE 
    WHEN cs.total_spend >= sp.p80 THEN 'High Value'
    WHEN cs.total_spend >= sp.p50 THEN 'Medium Value'
    WHEN cs.total_spend >= sp.p20 THEN 'Low Value'
    ELSE 'Very Low Value'
  END as customer_segment
FROM customer_spend cs
CROSS JOIN spend_percentiles sp;
```

### Transaction Amount Buckets
```sql
-- Bucket transactions by amount ranges
SELECT 
  CASE 
    WHEN order_amount < 50 THEN '$0-49'
    WHEN order_amount < 100 THEN '$50-99'
    WHEN order_amount < 250 THEN '$100-249'
    WHEN order_amount < 500 THEN '$250-499'
    ELSE '$500+'
  END as amount_bucket,
  COUNT(*) as transaction_count,
  SUM(order_amount) as total_revenue,
  AVG(order_amount) as avg_order_value
FROM orders
GROUP BY 
  CASE 
    WHEN order_amount < 50 THEN '$0-49'
    WHEN order_amount < 100 THEN '$50-99'
    WHEN order_amount < 250 THEN '$100-249'
    WHEN order_amount < 500 THEN '$250-499'
    ELSE '$500+'
  END
ORDER BY MIN(order_amount);
```

---

## **Gap & Island Analysis**

### Consecutive Login Streaks
```sql
-- Find consecutive daily login streaks
WITH daily_logins AS (
  SELECT 
    user_id,
    date(login_timestamp) as login_date
  FROM user_logins
  GROUP BY user_id, date(login_timestamp)
),
login_groups AS (
  SELECT 
    user_id,
    login_date,
    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY login_date) as rn,
    DATE_SUB(login_date, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY login_date)) as group_date
  FROM daily_logins
)
SELECT 
  user_id,
  MIN(login_date) as streak_start,
  MAX(login_date) as streak_end,
  COUNT(*) as streak_length
FROM login_groups
GROUP BY user_id, group_date
HAVING COUNT(*) >= 3  -- Only streaks of 3+ days
ORDER BY user_id, streak_start;
```

### Missing Sequence Detection
```sql
-- Find gaps in order sequence numbers
WITH order_sequence AS (
  SELECT 
    order_id,
    LAG(order_id) OVER (ORDER BY order_id) as prev_order_id
  FROM orders
  WHERE order_id IS NOT NULL
)
SELECT 
  prev_order_id + 1 as missing_start,
  order_id - 1 as missing_end,
  order_id - prev_order_id - 1 as gap_size
FROM order_sequence
WHERE order_id - prev_order_id > 1
ORDER BY missing_start;
```

---

## **Percentage of Total**

### Revenue Share Analysis
```sql
-- Each product's share of total revenue
SELECT 
  product_name,
  product_revenue,
  total_revenue,
  ROUND(product_revenue * 100.0 / total_revenue, 2) as revenue_share_pct
FROM (
  SELECT 
    product_name,
    SUM(order_amount) as product_revenue,
    SUM(SUM(order_amount)) OVER () as total_revenue
  FROM orders o
  JOIN products p ON o.product_id = p.product_id
  GROUP BY product_name
) revenue_calc
ORDER BY revenue_share_pct DESC;
```

### Regional Performance Share
```sql
-- Regional contribution to total sales
SELECT 
  region,
  region_sales,
  SUM(region_sales) OVER () as total_sales,
  ROUND(region_sales * 100.0 / SUM(region_sales) OVER (), 2) as sales_share_pct,
  ROUND(SUM(region_sales * 100.0 / SUM(region_sales) OVER ()) OVER (ORDER BY region_sales DESC), 2) as cumulative_share_pct
FROM (
  SELECT 
    region,
    SUM(order_amount) as region_sales
  FROM orders
  GROUP BY region
) regional_totals
ORDER BY region_sales DESC;
```

---

## **Outlier Detection**

### Statistical Outliers using IQR
```sql
-- Detect outlier transactions using IQR method
WITH transaction_stats AS (
  SELECT 
    percentile_approx(order_amount, 0.25) as q1,
    percentile_approx(order_amount, 0.75) as q3,
    percentile_approx(order_amount, 0.75) - percentile_approx(order_amount, 0.25) as iqr
  FROM orders
),
outlier_bounds AS (
  SELECT 
    q1 - (1.5 * iqr) as lower_bound,
    q3 + (1.5 * iqr) as upper_bound
  FROM transaction_stats
)
SELECT 
  order_id,
  customer_id,
  order_amount,
  CASE 
    WHEN order_amount < ob.lower_bound THEN 'Low Outlier'
    WHEN order_amount > ob.upper_bound THEN 'High Outlier'
    ELSE 'Normal'
  END as outlier_status
FROM orders o
CROSS JOIN outlier_bounds ob
WHERE order_amount < ob.lower_bound OR order_amount > ob.upper_bound
ORDER BY order_amount DESC;
```

### Z-Score Based Outliers
```sql
-- Outlier detection using z-score
WITH order_stats AS (
  SELECT 
    AVG(order_amount) as mean_amount,
    STDDEV(order_amount) as std_amount
  FROM orders
)
SELECT 
  order_id,
  customer_id,
  order_amount,
  ROUND((order_amount - os.mean_amount) / os.std_amount, 2) as z_score,
  CASE 
    WHEN ABS((order_amount - os.mean_amount) / os.std_amount) > 3 THEN 'Extreme Outlier'
    WHEN ABS((order_amount - os.mean_amount) / os.std_amount) > 2 THEN 'Moderate Outlier'
    ELSE 'Normal'
  END as outlier_category
FROM orders o
CROSS JOIN order_stats os
WHERE ABS((order_amount - os.mean_amount) / os.std_amount) > 2
ORDER BY ABS((order_amount - os.mean_amount) / os.std_amount) DESC;
```

---

## **First/Last Analysis**

### Customer First and Last Purchase
```sql
-- First and last purchase analysis
SELECT 
  customer_id,
  FIRST_VALUE(order_date) OVER (PARTITION BY customer_id ORDER BY order_date) as first_purchase_date,
  FIRST_VALUE(order_amount) OVER (PARTITION BY customer_id ORDER BY order_date) as first_purchase_amount,
  LAST_VALUE(order_date) OVER (
    PARTITION BY customer_id 
    ORDER BY order_date 
    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
  ) as last_purchase_date,
  LAST_VALUE(order_amount) OVER (
    PARTITION BY customer_id 
    ORDER BY order_date 
    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
  ) as last_purchase_amount,
  COUNT(*) OVER (PARTITION BY customer_id) as total_orders
FROM orders
QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date) = 1;
```

### Product Price History
```sql
-- Latest price for each product
SELECT 
  product_id,
  product_name,
  LAST_VALUE(price) OVER (
    PARTITION BY product_id 
    ORDER BY price_date 
    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
  ) as current_price,
  FIRST_VALUE(price) OVER (PARTITION BY product_id ORDER BY price_date) as initial_price,
  LAST_VALUE(price_date) OVER (
    PARTITION BY product_id 
    ORDER BY price_date 
    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
  ) as last_updated
FROM product_prices
QUALIFY ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY price_date DESC) = 1;
```

---

## **Conditional Aggregation**

### Order Status Analysis
```sql
-- Aggregate metrics by order status
SELECT 
  COUNT(*) as total_orders,
  SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_orders,
  SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled_orders,
  SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_orders,
  
  -- Revenue metrics
  SUM(CASE WHEN status = 'completed' THEN order_amount ELSE 0 END) as completed_revenue,
  SUM(CASE WHEN status = 'cancelled' THEN order_amount ELSE 0 END) as lost_revenue,
  
  -- Conversion rates
  ROUND(SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as completion_rate,
  ROUND(SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as cancellation_rate
FROM orders;
```

### Segmented Performance Metrics
```sql
-- Performance by customer type
SELECT 
  customer_type,
  COUNT(DISTINCT customer_id) as unique_customers,
  COUNT(*) as total_orders,
  SUM(order_amount) as total_revenue,
  AVG(order_amount) as avg_order_value,
  
  -- Premium vs Basic comparison
  AVG(CASE WHEN customer_type = 'Premium' THEN order_amount END) as premium_aov,
  AVG(CASE WHEN customer_type = 'Basic' THEN order_amount END) as basic_aov,
  
  -- Order frequency
  COUNT(*) / COUNT(DISTINCT customer_id) as avg_orders_per_customer
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY customer_type;
```

---

## **Duplicate Detection & Deduplication**

### Find Duplicate Records
```sql
-- Identify potential duplicate customers
SELECT 
  email,
  phone,
  COUNT(*) as duplicate_count,
  COLLECT_LIST(customer_id) as customer_ids
FROM customers
GROUP BY email, phone
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;
```

### Deduplication with Row Numbers
```sql
-- Remove duplicates keeping most recent record
SELECT 
  customer_id,
  email,
  phone,
  registration_date
FROM (
  SELECT 
    *,
    ROW_NUMBER() OVER (
      PARTITION BY email, phone 
      ORDER BY registration_date DESC, customer_id DESC
    ) as rn
  FROM customers
) ranked
WHERE rn = 1;
```

---

## **Survival Analysis**

### Customer Lifespan Analysis
```sql
-- Customer activity duration analysis
WITH customer_lifespan AS (
  SELECT 
    customer_id,
    MIN(order_date) as first_order,
    MAX(order_date) as last_order,
    datediff(MAX(order_date), MIN(order_date)) as lifespan_days,
    COUNT(*) as total_orders
  FROM orders
  GROUP BY customer_id
)
SELECT 
  CASE 
    WHEN lifespan_days = 0 THEN 'Single Purchase'
    WHEN lifespan_days <= 30 THEN '0-30 days'
    WHEN lifespan_days <= 90 THEN '31-90 days'
    WHEN lifespan_days <= 365 THEN '91-365 days'
    ELSE '1+ years'
  END as lifespan_bucket,
  COUNT(*) as customer_count,
  AVG(total_orders) as avg_orders,
  AVG(lifespan_days) as avg_lifespan_days
FROM customer_lifespan
GROUP BY 
  CASE 
    WHEN lifespan_days = 0 THEN 'Single Purchase'
    WHEN lifespan_days <= 30 THEN '0-30 days'
    WHEN lifespan_days <= 90 THEN '31-90 days'
    WHEN lifespan_days <= 365 THEN '91-365 days'
    ELSE '1+ years'
  END
ORDER BY MIN(lifespan_days);
```

---

## **Performance Against Targets**

### Sales Target Performance
```sql
-- Sales performance vs targets
WITH actual_performance AS (
  SELECT 
    salesperson_id,
    SUM(deal_value) as actual_sales
  FROM sales_deals
  WHERE deal_date >= '2024-01-01'
  GROUP BY salesperson_id
)
SELECT 
  sp.salesperson_name,
  st.annual_target,
  ap.actual_sales,
  ROUND((ap.actual_sales / st.annual_target) * 100, 1) as target_achievement_pct,
  ap.actual_sales - st.annual_target as variance_from_target,
  CASE 
    WHEN ap.actual_sales >= st.annual_target * 1.1 THEN 'Exceeding (110%+)'
    WHEN ap.actual_sales >= st.annual_target THEN 'Meeting Target'
    WHEN ap.actual_sales >= st.annual_target * 0.8 THEN 'Close to Target'
    ELSE 'Below Target'
  END as performance_category
FROM actual_performance ap
JOIN salesperson_targets st ON ap.salesperson_id = st.salesperson_id
JOIN salespeople sp ON ap.salesperson_id = sp.salesperson_id
ORDER BY target_achievement_pct DESC;
```