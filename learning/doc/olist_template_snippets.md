# Olist Dataset SQL Template Snippets

## **Ranking & Top-N Analysis**

### Top N by Group Template
```sql
-- Top N [entities] by [metric] in each [group]
-- Example: Top 3 sellers by revenue in each state
SELECT 
    [grouping_column],     -- seller_state
    [entity_column],       -- seller_id
    [metric_column],       -- total_revenue
    [ranking_column]       -- seller_rank
FROM (
  SELECT 
    [grouping_column],     -- seller_state
    [entity_column],       -- seller_id
    [metric_column],       -- SUM(price) as total_revenue
    ROW_NUMBER() OVER (
        PARTITION BY [grouping_column]     -- seller_state
        ORDER BY [metric_column] DESC      -- total_revenue DESC
    ) as [ranking_column]                  -- seller_rank
  FROM [main_table]                        -- order_items oi
  JOIN [dimension_table] ON [join_condition] -- JOIN sellers s ON oi.seller_id = s.seller_id
  GROUP BY [grouping_column], [entity_column] -- seller_state, seller_id
) ranked
WHERE [ranking_column] <= [N]              -- seller_rank <= 3
ORDER BY [grouping_column], [ranking_column]; -- seller_state, seller_rank
```

### Customer Value Quartiles Template
```sql
-- Segment [entities] into quartiles by [metric]
-- Example: Segment customers into quartiles by total spending
SELECT 
    [entity_id],           -- customer_unique_id
    [metric_value],        -- total_spent
    NTILE(4) OVER (ORDER BY [metric_value] DESC) as [quartile_column], -- spending_quartile
    CASE 
        WHEN NTILE(4) OVER (ORDER BY [metric_value] DESC) = 1 THEN '[top_label]'    -- 'High Value'
        WHEN NTILE(4) OVER (ORDER BY [metric_value] DESC) = 2 THEN '[second_label]' -- 'Medium-High Value'
        WHEN NTILE(4) OVER (ORDER BY [metric_value] DESC) = 3 THEN '[third_label]'  -- 'Medium-Low Value'
        ELSE '[bottom_label]'                                                        -- 'Low Value'
    END as [segment_label] -- customer_segment
FROM (
    SELECT 
        [entity_id],       -- customer_unique_id
        SUM([metric_column]) as [metric_value] -- SUM(payment_value) as total_spent
    FROM [transaction_table] -- orders o
    JOIN [payment_table] ON [join_condition] -- JOIN order_payments op ON o.order_id = op.order_id
    GROUP BY [entity_id]   -- customer_unique_id
) [subquery_alias];        -- customer_totals
```

---

## **Time-Based Comparisons**

### Month-over-Month Growth Template
```sql
-- [Metric] with MoM growth rate
-- Example: Monthly order volume with MoM growth
SELECT 
    [time_period],         -- order_month
    [current_metric],      -- order_count
    LAG([current_metric], 1) OVER (ORDER BY [time_period]) as [previous_metric], -- prev_month_orders
    ROUND(
        ([current_metric] - LAG([current_metric], 1) OVER (ORDER BY [time_period])) * 100.0 / 
        LAG([current_metric], 1) OVER (ORDER BY [time_period]), 2
    ) as [growth_rate_column] -- mom_growth_rate
FROM (
    SELECT 
        date_trunc('month', [date_column]) as [time_period], -- date_trunc('month', order_purchase_timestamp) as order_month
        COUNT([entity_column]) as [current_metric]           -- COUNT(order_id) as order_count
    FROM [main_table]      -- orders
    WHERE [date_filter]    -- order_purchase_timestamp >= '2017-01-01'
    GROUP BY date_trunc('month', [date_column]) -- order_purchase_timestamp
) [monthly_summary]        -- monthly_orders
ORDER BY [time_period];    -- order_month
```

### Customer Recency Analysis Template
```sql
-- Find [entities] who haven't [action] in [time_period]
-- Example: Find customers who haven't ordered in 90 days
SELECT 
    [entity_id],           -- customer_unique_id
    MAX([date_column]) as [last_action_date], -- last_order_date
    datediff(current_date(), MAX([date_column])) as [days_since_column] -- days_since_last_order
FROM [main_table]          -- orders
WHERE [status_filter]      -- order_status = 'delivered'
GROUP BY [entity_id]       -- customer_unique_id
HAVING datediff(current_date(), MAX([date_column])) > [threshold] -- > 90
ORDER BY [days_since_column] DESC; -- days_since_last_order DESC
```

---

## **Running Totals & Cumulative Analysis**

### Cumulative Revenue Template
```sql
-- Running total of [time_period] [metric]
-- Example: Running total of daily revenue
SELECT 
    [time_period],         -- order_date
    [period_metric],       -- daily_revenue
    SUM([period_metric]) OVER (
        ORDER BY [time_period] 
        ROWS UNBOUNDED PRECEDING
    ) as [cumulative_metric] -- cumulative_revenue
FROM (
    SELECT 
        date([date_column]) as [time_period], -- date(order_purchase_timestamp) as order_date
        SUM([value_column]) as [period_metric] -- SUM(payment_value) as daily_revenue
    FROM [main_table]      -- orders o
    JOIN [value_table] ON [join_condition] -- JOIN order_payments op ON o.order_id = op.order_id
    WHERE [date_filter]    -- order_purchase_timestamp >= '2018-01-01'
    GROUP BY date([date_column]) -- order_purchase_timestamp
) [daily_summary]          -- daily_totals
ORDER BY [time_period];    -- order_date
```

---

## **Moving Averages & Trends**

### Moving Average Template
```sql
-- [N]-day rolling average of [metric]
-- Example: 7-day rolling average of daily order count
SELECT 
    [time_period],         -- order_date
    [daily_metric],        -- daily_orders
    AVG([daily_metric]) OVER (
        ORDER BY [time_period] 
        ROWS BETWEEN [N-1] PRECEDING AND CURRENT ROW -- 6 PRECEDING AND CURRENT ROW
    ) as [moving_avg_column] -- ma_7_day
FROM (
    SELECT 
        date([date_column]) as [time_period], -- date(order_purchase_timestamp) as order_date
        COUNT([entity_column]) as [daily_metric] -- COUNT(order_id) as daily_orders
    FROM [main_table]      -- orders
    WHERE [date_filter]    -- order_status IN ('delivered', 'shipped')
    GROUP BY date([date_column]) -- order_purchase_timestamp
) [daily_aggregation]      -- daily_orders
ORDER BY [time_period];    -- order_date
```

---

## **Cohort Analysis**

### Monthly Retention Cohort Template
```sql
-- [Entity] cohort retention analysis
-- Example: Customer cohort retention analysis
WITH cohorts AS (
    SELECT 
        [entity_id],       -- customer_unique_id
        date_trunc('month', MIN([first_action_date])) as [cohort_period] -- cohort_month
    FROM [transaction_table] -- orders
    WHERE [status_filter]  -- order_status = 'delivered'
    GROUP BY [entity_id]   -- customer_unique_id
),
cohort_data AS (
    SELECT 
        c.[cohort_period], -- cohort_month
        date_trunc('month', t.[action_date]) as [activity_period], -- activity_month
        COUNT(DISTINCT t.[entity_id]) as [active_entities] -- active_customers
    FROM cohorts c
    JOIN [transaction_table] t ON c.[entity_id] = t.[entity_id] -- orders t ON c.customer_unique_id = t.customer_unique_id
    WHERE t.[status_filter] -- order_status = 'delivered'
    GROUP BY c.[cohort_period], date_trunc('month', t.[action_date]) -- cohort_month, activity_month
),
cohort_sizes AS (
    SELECT [cohort_period], COUNT(*) as [total_entities] -- cohort_month, total_customers
    FROM cohorts
    GROUP BY [cohort_period] -- cohort_month
)
SELECT 
    cd.[cohort_period],    -- cohort_month
    cd.[activity_period],  -- activity_month
    datediff(cd.[activity_period], cd.[cohort_period]) as [periods_since], -- months_since_first_order
    cd.[active_entities],  -- active_customers
    cs.[total_entities],   -- total_customers
    ROUND(cd.[active_entities] * 100.0 / cs.[total_entities], 2) as [retention_rate] -- retention_rate
FROM cohort_data cd
JOIN cohort_sizes cs ON cd.[cohort_period] = cs.[cohort_period] -- cohort_month
ORDER BY cd.[cohort_period], cd.[activity_period]; -- cohort_month, activity_month
```

---

## **Funnel Analysis**

### Multi-Step Funnel Template
```sql
-- [Process] conversion funnel
-- Example: Order fulfillment funnel
WITH funnel_steps AS (
    SELECT 
        [entity_id],       -- order_id
        MAX(CASE WHEN [condition_1] THEN 1 ELSE 0 END) as [step_1], -- order_status = 'processing'
        MAX(CASE WHEN [condition_2] THEN 1 ELSE 0 END) as [step_2], -- order_status = 'shipped'
        MAX(CASE WHEN [condition_3] THEN 1 ELSE 0 END) as [step_3], -- order_status = 'delivered'
        MAX(CASE WHEN [condition_4] THEN 1 ELSE 0 END) as [step_4]  -- review_id IS NOT NULL
    FROM [main_table]      -- orders o
    LEFT JOIN [additional_table] ON [join_condition] -- LEFT JOIN order_reviews r ON o.order_id = r.order_id
    WHERE [filter_condition] -- order_purchase_timestamp >= '2018-01-01'
    GROUP BY [entity_id]   -- order_id
)
SELECT 
    '[Step 1 Name]' as step,        -- 'Order Placed'
    SUM([step_1]) as entities,       -- step_1, orders
    ROUND(SUM([step_1]) * 100.0 / SUM([step_1]), 2) as conversion_rate -- always 100% for first step
FROM funnel_steps
UNION ALL
SELECT 
    '[Step 2 Name]' as step,        -- 'Order Shipped'
    SUM([step_2]) as entities,       -- step_2, orders
    ROUND(SUM([step_2]) * 100.0 / SUM([step_1]), 2) as conversion_rate
FROM funnel_steps
UNION ALL
SELECT 
    '[Step 3 Name]' as step,        -- 'Order Delivered'
    SUM([step_3]) as entities,       -- step_3, orders
    ROUND(SUM([step_3]) * 100.0 / SUM([step_1]), 2) as conversion_rate
FROM funnel_steps
UNION ALL
SELECT 
    '[Step 4 Name]' as step,        -- 'Customer Reviewed'
    SUM([step_4]) as entities,       -- step_4, orders
    ROUND(SUM([step_4]) * 100.0 / SUM([step_1]), 2) as conversion_rate
FROM funnel_steps;
```

---

## **Pivot & Cross-Tab Analysis**

### Revenue by Dimensions Template
```sql
-- [Metric] by [dimension_1] and [time_period] matrix
-- Example: Revenue by product category and quarter
SELECT 
    [dimension_column],    -- product_category_name_english
    SUM(CASE WHEN [time_condition_1] THEN [value_column] ELSE 0 END) as [period_1], -- quarter = 1, revenue
    SUM(CASE WHEN [time_condition_2] THEN [value_column] ELSE 0 END) as [period_2], -- quarter = 2, revenue
    SUM(CASE WHEN [time_condition_3] THEN [value_column] ELSE 0 END) as [period_3], -- quarter = 3, revenue
    SUM(CASE WHEN [time_condition_4] THEN [value_column] ELSE 0 END) as [period_4], -- quarter = 4, revenue
    SUM([value_column]) as [total_column] -- total_revenue
FROM [main_table]          -- order_items oi
JOIN [dimension_table] ON [join_condition] -- JOIN products p ON oi.product_id = p.product_id
JOIN [time_table] ON [join_condition]      -- JOIN orders o ON oi.order_id = o.order_id
WHERE [time_filter]        -- year(order_purchase_timestamp) = 2018
GROUP BY [dimension_column] -- product_category_name_english
ORDER BY [total_column] DESC; -- total_revenue DESC
```

---

## **Bucketing & Segmentation**

### Value-Based Segmentation Template
```sql
-- Segment [entities] by [metric] into [segments]
-- Example: Segment sellers by revenue performance
WITH entity_metrics AS (
    SELECT 
        [entity_id],       -- seller_id
        SUM([value_column]) as [total_metric] -- SUM(price) as total_revenue
    FROM [transaction_table] -- order_items
    WHERE [filter_condition] -- price > 0
    GROUP BY [entity_id]   -- seller_id
),
metric_percentiles AS (
    SELECT 
        percentile_approx([total_metric], [high_threshold]) as [high_cutoff], -- 0.8, high_revenue_cutoff
        percentile_approx([total_metric], [medium_threshold]) as [medium_cutoff], -- 0.5, medium_revenue_cutoff
        percentile_approx([total_metric], [low_threshold]) as [low_cutoff] -- 0.2, low_revenue_cutoff
    FROM entity_metrics
)
SELECT 
    em.[entity_id],        -- seller_id
    em.[total_metric],     -- total_revenue
    CASE 
        WHEN em.[total_metric] >= mp.[high_cutoff] THEN '[high_segment]'     -- 'High Performer'
        WHEN em.[total_metric] >= mp.[medium_cutoff] THEN '[medium_segment]' -- 'Medium Performer'
        WHEN em.[total_metric] >= mp.[low_cutoff] THEN '[low_segment]'       -- 'Low Performer'
        ELSE '[bottom_segment]'                                              -- 'Underperformer'
    END as [segment_column] -- performance_segment
FROM entity_metrics em
CROSS JOIN metric_percentiles mp
ORDER BY em.[total_metric] DESC; -- total_revenue DESC
```

---

## **Gap & Island Analysis**

### Consecutive Activity Periods Template
```sql
-- Find consecutive [time_periods] of [activity] for each [entity]
-- Example: Find consecutive months of seller activity
WITH activity_periods AS (
    SELECT 
        [entity_id],       -- seller_id
        date_trunc('month', [date_column]) as [activity_period] -- activity_month
    FROM [transaction_table] -- order_items oi
    JOIN [date_table] ON [join_condition] -- JOIN orders o ON oi.order_id = o.order_id
    WHERE [activity_filter] -- price > 0
    GROUP BY [entity_id], date_trunc('month', [date_column]) -- seller_id, activity_month
),
activity_groups AS (
    SELECT 
        [entity_id],       -- seller_id
        [activity_period], -- activity_month
        ROW_NUMBER() OVER (PARTITION BY [entity_id] ORDER BY [activity_period]) as rn,
        DATE_SUB([activity_period], ROW_NUMBER() OVER (PARTITION BY [entity_id] ORDER BY [activity_period])) as group_identifier
    FROM activity_periods
)
SELECT 
    [entity_id],           -- seller_id
    MIN([activity_period]) as [streak_start], -- streak_start_month
    MAX([activity_period]) as [streak_end],   -- streak_end_month
    COUNT(*) as [streak_length] -- streak_length_months
FROM activity_groups
GROUP BY [entity_id], group_identifier -- seller_id, group_identifier
HAVING COUNT(*) >= [minimum_streak]     -- >= 3
ORDER BY [entity_id], [streak_start];   -- seller_id, streak_start_month
```

---

## **Percentage of Total**

### Share Analysis Template
```sql
-- Each [entity]'s share of total [metric]
-- Example: Each seller's share of total revenue
SELECT 
    [entity_column],       -- seller_id
    [entity_metric],       -- seller_revenue
    [total_metric],        -- total_revenue
    ROUND([entity_metric] * 100.0 / [total_metric], 2) as [share_percentage] -- revenue_share_pct
FROM (
    SELECT 
        [entity_column],   -- seller_id
        SUM([value_column]) as [entity_metric], -- SUM(price) as seller_revenue
        SUM(SUM([value_column])) OVER () as [total_metric] -- total_revenue
    FROM [transaction_table] -- order_items
    WHERE [filter_condition] -- price > 0
    GROUP BY [entity_column] -- seller_id
) [calculation_subquery]   -- revenue_calc
ORDER BY [share_percentage] DESC; -- revenue_share_pct DESC
```

---

## **Outlier Detection**

### Statistical Outliers Template
```sql
-- Detect outlier [entities] using [method]
-- Example: Detect outlier orders using IQR method
WITH metric_stats AS (
    SELECT 
        percentile_approx([metric_column], 0.25) as q1, -- payment_value
        percentile_approx([metric_column], 0.75) as q3, -- payment_value
        percentile_approx([metric_column], 0.75) - percentile_approx([metric_column], 0.25) as iqr
    FROM [main_table]      -- order_payments
    WHERE [filter_condition] -- payment_value > 0
),
outlier_bounds AS (
    SELECT 
        q1 - ([multiplier] * iqr) as lower_bound, -- 1.5
        q3 + ([multiplier] * iqr) as upper_bound  -- 1.5
    FROM metric_stats
)
SELECT 
    [entity_id],           -- order_id
    [related_entity],      -- customer_unique_id (from join)
    [metric_column],       -- payment_value
    CASE 
        WHEN [metric_column] < ob.lower_bound THEN '[low_outlier_label]'  -- 'Unusually Low'
        WHEN [metric_column] > ob.upper_bound THEN '[high_outlier_label]' -- 'Unusually High'
        ELSE '[normal_label]'                                             -- 'Normal'
    END as [outlier_status] -- outlier_category
FROM [main_table] mt       -- order_payments mt
LEFT JOIN [dimension_table] ON [join_condition] -- LEFT JOIN orders o ON mt.order_id = o.order_id
CROSS JOIN outlier_bounds ob
WHERE [metric_column] < ob.lower_bound OR [metric_column] > ob.upper_bound -- payment_value
ORDER BY [metric_column] DESC; -- payment_value DESC
```

---

## **First/Last Analysis**

### First and Last Activity Template
```sql
-- First and last [activity] analysis for each [entity]
-- Example: First and last purchase analysis for customers
SELECT 
    [entity_id],           -- customer_unique_id
    FIRST_VALUE([activity_date]) OVER (
        PARTITION BY [entity_id] ORDER BY [activity_date]
    ) as [first_activity], -- first_order_date
    FIRST_VALUE([metric_column]) OVER (
        PARTITION BY [entity_id] ORDER BY [activity_date]
    ) as [first_metric],   -- first_order_value
    LAST_VALUE([activity_date]) OVER (
        PARTITION BY [entity_id] 
        ORDER BY [activity_date] 
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) as [last_activity],  -- last_order_date
    LAST_VALUE([metric_column]) OVER (
        PARTITION BY [entity_id] 
        ORDER BY [activity_date] 
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) as [last_metric],    -- last_order_value
    COUNT(*) OVER (PARTITION BY [entity_id]) as [total_activities] -- total_orders
FROM [transaction_table]   -- orders o
JOIN [value_table] ON [join_condition] -- JOIN order_payments op ON o.order_id = op.order_id
WHERE [filter_condition]   -- order_status = 'delivered'
QUALIFY ROW_NUMBER() OVER (PARTITION BY [entity_id] ORDER BY [activity_date]) = 1; -- Keep one row per customer
```

---

## **Conditional Aggregation**

### Status-Based Metrics Template
```sql
-- Aggregate metrics by [status/category]
-- Example: Order metrics by delivery status
SELECT 
    COUNT(*) as [total_count],                    -- total_orders
    SUM(CASE WHEN [condition_1] THEN 1 ELSE 0 END) as [count_1], -- delivered_orders
    SUM(CASE WHEN [condition_2] THEN 1 ELSE 0 END) as [count_2], -- cancelled_orders
    SUM(CASE WHEN [condition_3] THEN 1 ELSE 0 END) as [count_3], -- processing_orders
    
    -- Value metrics
    SUM(CASE WHEN [condition_1] THEN [value_column] ELSE 0 END) as [value_1], -- delivered_revenue
    SUM(CASE WHEN [condition_2] THEN [value_column] ELSE 0 END) as [value_2], -- lost_revenue
    
    -- Percentage calculations
    ROUND(SUM(CASE WHEN [condition_1] THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as [rate_1], -- delivery_rate
    ROUND(SUM(CASE WHEN [condition_2] THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as [rate_2]  -- cancellation_rate
FROM [main_table]          -- orders o
JOIN [value_table] ON [join_condition] -- JOIN order_payments op ON o.order_id = op.order_id
WHERE [time_filter];       -- order_purchase_timestamp >= '2018-01-01'
```

---

## **Duplicate Detection**

### Find Potential Duplicates Template
```sql
-- Identify potential duplicate [entities] based on [criteria]
-- Example: Find potential duplicate customers based on location
SELECT 
    [grouping_field_1],    -- customer_city
    [grouping_field_2],    -- customer_zip_code_prefix
    [grouping_field_3],    -- customer_state (optional)
    COUNT(*) as [duplicate_count], -- customer_count
    COLLECT_LIST([entity_id]) as [entity_list] -- customer_ids
FROM [main_table]          -- customers
WHERE [filter_condition]   -- customer_city IS NOT NULL
GROUP BY [grouping_field_1], [grouping_field_2], [grouping_field_3] -- customer_city, customer_zip_code_prefix
HAVING COUNT(*) > [threshold] -- > 1
ORDER BY [duplicate_count] DESC; -- customer_count DESC
```

---

## **Performance Against Targets**

### Target Performance Template
```sql
-- [Entity] performance vs [targets]
-- Example: Seller performance vs average seller metrics
WITH actual_performance AS (
    SELECT 
        [entity_id],       -- seller_id
        COUNT([transaction_id]) as [actual_count], -- actual_orders
        SUM([value_column]) as [actual_value]     -- actual_revenue
    FROM [transaction_table] -- order_items
    WHERE [time_filter]    -- order_purchase_timestamp >= '2018-01-01' (via join)
    GROUP BY [entity_id]   -- seller_id
),
benchmark_metrics AS (
    SELECT 
        AVG([actual_count]) as [avg_count],   -- avg_orders_per_seller
        AVG([actual_value]) as [avg_value],   -- avg_revenue_per_seller
        percentile_approx([actual_value], 0.5) as [median_value] -- median_revenue
    FROM actual_performance
)
SELECT 
    ap.[entity_id],        -- seller_id
    ap.[actual_count],     -- actual_orders
    ap.[actual_value],     -- actual_revenue
    bm.[avg_value],        -- avg_revenue_per_seller
    ROUND((ap.[actual_value] / bm.[avg_value]) * 100, 1) as [performance_vs_avg], -- performance_vs_average_pct
    ap.[actual_value] - bm.[avg_value] as [variance_from_avg], -- revenue_variance
    CASE 
        WHEN ap.[actual_value] >= bm.[avg_value] * [high_threshold] THEN '[high_performer]'    -- 1.5, 'Top Performer'
        WHEN ap.[actual_value] >= bm.[avg_value] THEN '[good_performer]'                       -- 'Above Average'
        WHEN ap.[actual_value] >= bm.[avg_value] * [low_threshold] THEN '[average_performer]'  -- 0.5, 'Below Average'
        ELSE '[poor_performer]'                                                                -- 'Underperformer'
    END as [performance_category] -- performance_tier
FROM actual_performance ap
CROSS JOIN benchmark_metrics bm
ORDER BY [performance_vs_avg] DESC; -- performance_vs_average_pct DESC
```