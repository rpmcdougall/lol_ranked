# Pattern Name: Ranking Analysis

**Tags:** #ranking #top-n #window-functions #performance-analysis

## Business Problem
Identifies top or bottom performers within groups, answers questions about relative positioning, and finds the best/worst examples in any category. Essential for performance analysis and identifying outliers.

## When to Use
- Stakeholders ask for "top 10" or "bottom 5" of anything
- Need to find best/worst performers by category
- Want to identify leaders and laggards
- Creating leaderboards or performance rankings
- Segmenting into performance tiers (top 25%, bottom quartile, etc.)

## Core SQL Implementation

```sql
-- Basic ranking with ROW_NUMBER (unique ranks)
SELECT 
    customer_id,
    customer_name,
    total_revenue,
    ROW_NUMBER() OVER (ORDER BY total_revenue DESC) as revenue_rank
FROM customer_summary
ORDER BY revenue_rank;

-- Ranking within groups using PARTITION BY
SELECT 
    region,
    salesperson_name,
    sales_amount,
    RANK() OVER (
        PARTITION BY region 
        ORDER BY sales_amount DESC
    ) as regional_rank
FROM sales_data
WHERE RANK() OVER (PARTITION BY region ORDER BY sales_amount DESC) <= 3;

-- Multiple ranking functions comparison
SELECT 
    product_name,
    revenue,
    ROW_NUMBER() OVER (ORDER BY revenue DESC) as row_num,     -- Always unique
    RANK() OVER (ORDER BY revenue DESC) as rank_val,         -- Ties get same rank
    DENSE_RANK() OVER (ORDER BY revenue DESC) as dense_rank  -- No gaps after ties
FROM product_performance;
```

## Python Alternative

```python
import pandas as pd

# Basic ranking
df['revenue_rank'] = df['total_revenue'].rank(method='min', ascending=False)

# Ranking within groups
df['regional_rank'] = df.groupby('region')['sales_amount'].rank(method='min', ascending=False)

# Top N within each group
top_3_by_region = df.groupby('region').apply(
    lambda x: x.nlargest(3, 'sales_amount')
).reset_index(drop=True)

# Percentile-based ranking
df['revenue_percentile'] = df['total_revenue'].rank(pct=True) * 100
```

## Business Questions Answered
- "Who are our top 10 customers by revenue?"
- "What are the best-performing products in each category?"
- "Which salespeople are in the bottom quartile for performance?"
- "Show me the 3 most recent orders for each customer"
- "What stores rank highest for customer satisfaction?"
- "Which regions have the lowest conversion rates?"

## Variations

### Variation 1: Top N with Ties Handling
```sql
-- Get exactly top 5, even if there are ties
SELECT *
FROM (
    SELECT 
        product_name,
        sales,
        ROW_NUMBER() OVER (ORDER BY sales DESC) as rn
    FROM products
) ranked
WHERE rn <= 5;

-- Get top 5 values, including all ties
SELECT *
FROM (
    SELECT 
        product_name,
        sales,
        DENSE_RANK() OVER (ORDER BY sales DESC) as dr
    FROM products
) ranked
WHERE dr <= 5;
```

### Variation 2: Percentile Rankings
```sql
-- Divide into quartiles
SELECT 
    customer_id,
    revenue,
    NTILE(4) OVER (ORDER BY revenue DESC) as revenue_quartile,
    PERCENT_RANK() OVER (ORDER BY revenue DESC) as revenue_percentile
FROM customer_revenue;
```

### Variation 3: Conditional Ranking
```sql
-- Only rank active customers
SELECT 
    customer_id,
    revenue,
    CASE 
        WHEN status = 'active' 
        THEN RANK() OVER (ORDER BY revenue DESC)
        ELSE NULL 
    END as active_customer_rank
FROM customers;
```

## Common Gotchas
- **ROW_NUMBER vs RANK vs DENSE_RANK**: Choose based on how you want ties handled
- **NULL values**: Decide if they should rank first, last, or be excluded entirely
- **Performance**: Ranking large datasets can be slow - consider adding WHERE clauses first
- **Memory usage**: Window functions can be memory-intensive on very large datasets
- **Partition size**: Very small partitions (like ranking within individual customers) may not be meaningful

## Related Patterns
- [Percentile Analysis](./percentile-analysis.md) - For statistical distribution analysis
- [Top N Analysis](./top-n-analysis.md) - Specialized ranking for finding top performers
- [Performance Targets](./performance-targets.md) - Comparing ranks against goals
- [ABC Analysis](./abc-analysis.md) - Pareto-based ranking and segmentation

## Real-World Example

### Context
Need to identify top-performing sales representatives in each region for bonus allocation, but also want to understand the performance distribution across all reps.

### Implementation
```sql
WITH rep_performance AS (
    SELECT 
        region,
        rep_name,
        SUM(deal_value) as total_sales,
        COUNT(deal_id) as deal_count,
        AVG(deal_value) as avg_deal_size
    FROM sales_deals 
    WHERE deal_date >= '2024-01-01'
    GROUP BY region, rep_name
),
ranked_reps AS (
    SELECT 
        *,
        RANK() OVER (PARTITION BY region ORDER BY total_sales DESC) as sales_rank,
        NTILE(4) OVER (PARTITION BY region ORDER BY total_sales DESC) as performance_quartile,
        PERCENT_RANK() OVER (PARTITION BY region ORDER BY total_sales DESC) as percentile_rank
    FROM rep_performance
)
SELECT 
    region,
    rep_name,
    total_sales,
    sales_rank,
    performance_quartile,
    ROUND(percentile_rank * 100, 1) as percentile
FROM ranked_reps
WHERE sales_rank <= 3  -- Top 3 in each region
ORDER BY region, sales_rank;
```

### Result
Identified top performers for bonuses and discovered that some regions had much more competitive performance distributions than others, leading to regional strategy adjustments.

## Sample Data Structure
```sql
-- Example input table
CREATE TABLE sales_data (
    rep_id INT,
    rep_name VARCHAR(100),
    region VARCHAR(50),
    deal_value DECIMAL(10,2),
    deal_date DATE,
    customer_type VARCHAR(50)
);

-- Sample data
INSERT INTO sales_data VALUES 
(1, 'John Smith', 'West', 15000.00, '2024-01-15', 'Enterprise'),
(2, 'Jane Doe', 'West', 12000.00, '2024-01-16', 'SMB'),
(3, 'Bob Johnson', 'East', 18000.00, '2024-01-17', 'Enterprise');
```

## Performance Tips
- Add WHERE clauses before window functions when possible
- Consider indexing on ranking columns
- For very large datasets, consider pre-aggregating data
- Use LIMIT with ORDER BY for simple top-N queries instead of window functions when you don't need ranks

## Further Reading
- [PostgreSQL Window Functions Documentation](https://www.postgresql.org/docs/current/functions-window.html)
- [SQL Server RANK Functions](https://docs.microsoft.com/en-us/sql/t-sql/functions/ranking-functions-transact-sql)
- [Oracle Analytic Functions Guide](https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/Analytic-Functions.html)