# Olist E-commerce Analytics with dbt and Snowflake

This project provides a complete setup for analyzing the Brazilian Olist e-commerce dataset using dbt (data build tool) and Snowflake. The pipeline transforms raw e-commerce data into analytics-ready models for customer cohort analysis, product performance, and business insights.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Data Setup](#data-setup)
- [dbt Project Setup](#dbt-project-setup)
- [Development Workflow](#development-workflow)
- [Project Structure](#project-structure)
- [Testing and Validation](#testing-and-validation)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software
- Python 3.8+ installed
- Access to a Snowflake account
- Git installed
- Text editor/IDE (VS Code recommended)

### Required Accounts
- Snowflake account with appropriate permissions
- Access to the Olist e-commerce dataset

### Knowledge Requirements
- Basic SQL knowledge
- Understanding of data warehousing concepts
- Familiarity with command line operations

## Getting Started

### Step 1: Download the Olist Dataset

1. Visit [Kaggle's Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
2. Download the dataset (requires Kaggle account)
3. Extract the CSV files to a local directory
4. You should have these files:
   - `olist_customers_dataset.csv`
   - `olist_orders_dataset.csv`
   - `olist_order_items_dataset.csv`
   - `olist_order_payments_dataset.csv`
   - `olist_order_reviews_dataset.csv`
   - `olist_products_dataset.csv`
   - `olist_sellers_dataset.csv`
   - `olist_geolocation_dataset.csv`
   - `product_category_name_translation.csv`

### Step 2: Set Up Python Environment

```bash
# Create a new Python virtual environment
python -m venv olist_env

# Activate the environment
# On Windows:
olist_env\Scripts\activate
# On macOS/Linux:
source olist_env/bin/activate

# Install required packages
pip install dbt-snowflake pandas snowflake-connector-python
```

### Step 3: Initialize Git Repository

```bash
# Create project directory
mkdir olist_analytics
cd olist_analytics

# Initialize git repository
git init

# Create .gitignore file
cat > .gitignore << EOF
target/
dbt_packages/
logs/
.env
profiles.yml
*.pyc
__pycache__/
.DS_Store
EOF
```

## Data Setup

### Step 1: Create Snowflake Database and Schema

Connect to Snowflake and run these commands:

```sql
-- Create database
CREATE DATABASE IF NOT EXISTS OLIST_DB;

-- Create schemas
CREATE SCHEMA IF NOT EXISTS OLIST_DB.RAW;
CREATE SCHEMA IF NOT EXISTS OLIST_DB.STAGING;
CREATE SCHEMA IF NOT EXISTS OLIST_DB.MARTS;
CREATE SCHEMA IF NOT EXISTS OLIST_DB.ANALYTICS;

-- Create warehouse (adjust size as needed)
CREATE WAREHOUSE IF NOT EXISTS ANALYTICS_WH
WITH WAREHOUSE_SIZE = 'X-SMALL'
AUTO_SUSPEND = 60
AUTO_RESUME = TRUE;
```

### Step 2: Create Raw Tables in Snowflake

```sql
USE DATABASE OLIST_DB;
USE SCHEMA RAW;

-- Orders table
CREATE OR REPLACE TABLE orders (
    order_id STRING,
    customer_id STRING,
    order_status STRING,
    order_purchase_timestamp STRING,
    order_approved_at STRING,
    order_delivered_carrier_date STRING,
    order_delivered_customer_date STRING,
    order_estimated_delivery_date STRING
);

-- Customers table
CREATE OR REPLACE TABLE customers (
    customer_id STRING,
    customer_unique_id STRING,
    customer_zip_code_prefix STRING,
    customer_city STRING,
    customer_state STRING
);

-- Order items table
CREATE OR REPLACE TABLE order_items (
    order_id STRING,
    order_item_id STRING,
    product_id STRING,
    seller_id STRING,
    shipping_limit_date STRING,
    price STRING,
    freight_value STRING
);

-- Products table
CREATE OR REPLACE TABLE products (
    product_id STRING,
    product_category_name STRING,
    product_name_lenght STRING,
    product_description_lenght STRING,
    product_photos_qty STRING,
    product_weight_g STRING,
    product_length_cm STRING,
    product_height_cm STRING,
    product_width_cm STRING
);

-- Sellers table
CREATE OR REPLACE TABLE sellers (
    seller_id STRING,
    seller_zip_code_prefix STRING,
    seller_city STRING,
    seller_state STRING
);

-- Order payments table
CREATE OR REPLACE TABLE order_payments (
    order_id STRING,
    payment_sequential STRING,
    payment_type STRING,
    payment_installments STRING,
    payment_value STRING
);

-- Order reviews table
CREATE OR REPLACE TABLE order_reviews (
    review_id STRING,
    order_id STRING,
    review_score STRING,
    review_comment_title STRING,
    review_comment_message STRING,
    review_creation_date STRING,
    review_answer_timestamp STRING
);
```

### Step 3: Load Data into Snowflake

#### Option A: Using Snowflake Web UI
1. Log into Snowflake web interface
2. Navigate to Databases > OLIST_DB > RAW
3. For each table, click on it and use "Load Data" option
4. Upload the corresponding CSV file
5. Configure file format (CSV, comma-delimited, skip first row)

#### Option B: Using SnowSQL (Command Line)
```bash
# Connect to Snowflake
snowsql -a your-account -u your-username

# Create file format
CREATE OR REPLACE FILE FORMAT csv_format
TYPE = 'CSV'
FIELD_DELIMITER = ','
SKIP_HEADER = 1
FIELD_OPTIONALLY_ENCLOSED_BY = '"'
ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE;

# Create internal stage
CREATE OR REPLACE STAGE olist_stage
FILE_FORMAT = csv_format;

# Upload files (run from directory containing CSV files)
PUT file://olist_orders_dataset.csv @olist_stage;
PUT file://olist_customers_dataset.csv @olist_stage;
PUT file://olist_order_items_dataset.csv @olist_stage;
PUT file://olist_products_dataset.csv @olist_stage;
PUT file://olist_sellers_dataset.csv @olist_stage;
PUT file://olist_order_payments_dataset.csv @olist_stage;
PUT file://olist_order_reviews_dataset.csv @olist_stage;

# Load data into tables
COPY INTO orders FROM @olist_stage/olist_orders_dataset.csv.gz;
COPY INTO customers FROM @olist_stage/olist_customers_dataset.csv.gz;
COPY INTO order_items FROM @olist_stage/olist_order_items_dataset.csv.gz;
COPY INTO products FROM @olist_stage/olist_products_dataset.csv.gz;
COPY INTO sellers FROM @olist_stage/olist_sellers_dataset.csv.gz;
COPY INTO order_payments FROM @olist_stage/olist_order_payments_dataset.csv.gz;
COPY INTO order_reviews FROM @olist_stage/olist_order_reviews_dataset.csv.gz;
```

### Step 4: Verify Data Load

```sql
-- Check row counts
SELECT 'orders' as table_name, COUNT(*) as row_count FROM orders
UNION ALL
SELECT 'customers', COUNT(*) FROM customers
UNION ALL
SELECT 'order_items', COUNT(*) FROM order_items
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'sellers', COUNT(*) FROM sellers
UNION ALL
SELECT 'order_payments', COUNT(*) FROM order_payments
UNION ALL
SELECT 'order_reviews', COUNT(*) FROM order_reviews;
```

## dbt Project Setup

### Step 1: Initialize dbt Project

```bash
# Navigate to your project directory
cd olist_analytics

# Initialize dbt project
dbt init olist_analytics

# Navigate into the created project
cd olist_analytics
```

### Step 2: Configure dbt Profile

Create or edit `~/.dbt/profiles.yml`:

```yaml
olist_analytics:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: your-account.snowflakecomputing.com  # Replace with your account
      user: your-username                           # Replace with your username
      password: your-password                       # Replace with your password
      role: your-role                              # Replace with your role
      database: OLIST_DB
      warehouse: ANALYTICS_WH
      schema: analytics
      threads: 4
      keepalives_idle: 240
    prod:
      type: snowflake
      account: your-account.snowflakecomputing.com
      user: your-prod-username
      password: your-prod-password
      role: your-prod-role
      database: OLIST_PROD_DB
      warehouse: ANALYTICS_WH
      schema: analytics
      threads: 8
      keepalives_idle: 240
```

### Step 3: Update dbt_project.yml

Replace the contents of `dbt_project.yml`:

```yaml
name: 'olist_analytics'
version: '1.0.0'
config-version: 2

profile: 'olist_analytics'

model-paths: ["models"]
analysis-paths: ["analyses"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]
snapshot-paths: ["snapshots"]

clean-targets:
  - "target"
  - "dbt_packages"

models:
  olist_analytics:
    staging:
      +materialized: view
      +schema: staging
    intermediate:
      +materialized: ephemeral
    marts:
      core:
        +materialized: table
        +schema: marts
      analytics:
        +materialized: table
        +schema: analytics

vars:
  # Define any project variables here
  start_date: '2016-01-01'
  end_date: '2018-12-31'
```

### Step 4: Create Project Directory Structure

```bash
# Create directory structure
mkdir -p models/staging
mkdir -p models/intermediate
mkdir -p models/marts/core
mkdir -p models/marts/analytics
mkdir -p macros
mkdir -p tests
mkdir -p analyses
mkdir -p snapshots
```

### Step 5: Install dbt Packages

Create `packages.yml` in the root directory:

```yaml
packages:
  - package: dbt-labs/dbt_utils
    version: 1.1.1
  - package: calogica/dbt_expectations
    version: 0.10.1
```

Install packages:
```bash
dbt deps
```

### Step 6: Test dbt Connection

```bash
# Test connection to Snowflake
dbt debug

# You should see "All checks passed!"
```

## Development Workflow

### Step 1: Create Sources Configuration

Create `models/staging/_sources.yml`:

```yaml
version: 2

sources:
  - name: raw_olist
    description: Raw Olist e-commerce data loaded from CSV files
    database: OLIST_DB
    schema: raw
    tables:
      - name: orders
        description: Order header information
        columns:
          - name: order_id
            description: Unique order identifier
            tests:
              - unique
              - not_null
          - name: customer_id
            description: Customer identifier
            tests:
              - not_null
      - name: order_items
        description: Order line items
        columns:
          - name: order_id
            tests:
              - not_null
          - name: order_item_id
            tests:
              - not_null
      - name: customers
        description: Customer information
        columns:
          - name: customer_id
            tests:
              - unique
              - not_null
      - name: products
        description: Product catalog
        columns:
          - name: product_id
            tests:
              - unique
              - not_null
      - name: sellers
        description: Seller information
        columns:
          - name: seller_id
            tests:
              - unique
              - not_null
      - name: order_payments
        description: Payment information for orders
      - name: order_reviews
        description: Customer reviews for orders
```

### Step 2: Create Staging Models

Create `models/staging/stg_orders.sql`:

```sql
{{ config(materialized='view') }}

with source as (
    select * from {{ source('raw_olist', 'orders') }}
),

cleaned as (
    select
        order_id,
        customer_id,
        order_status,
        
        -- Convert string timestamps to proper timestamp type
        try_to_timestamp(order_purchase_timestamp) as order_purchase_timestamp,
        try_to_timestamp(order_approved_at) as order_approved_at,
        try_to_timestamp(order_delivered_carrier_date) as order_delivered_carrier_date,
        try_to_timestamp(order_delivered_customer_date) as order_delivered_customer_date,
        try_to_timestamp(order_estimated_delivery_date) as order_estimated_delivery_date,
        
        -- Derived fields
        date_trunc('day', try_to_timestamp(order_purchase_timestamp)) as order_date,
        extract('year', try_to_timestamp(order_purchase_timestamp)) as order_year,
        extract('month', try_to_timestamp(order_purchase_timestamp)) as order_month,
        
        -- Delivery performance
        case 
            when try_to_timestamp(order_delivered_customer_date) <= try_to_timestamp(order_estimated_delivery_date) 
            then 'on_time'
            when try_to_timestamp(order_delivered_customer_date) > try_to_timestamp(order_estimated_delivery_date)
            then 'late'
            else 'unknown'
        end as delivery_performance
        
    from source
    where order_id is not null
)

select * from cleaned
```

Create other staging models similarly (`stg_customers.sql`, `stg_order_items.sql`, etc.)

### Step 3: Build and Test Staging Layer

```bash
# Build staging models
dbt run --models staging

# Test staging models
dbt test --models staging

# Check compiled SQL
dbt compile --models staging
```

### Step 4: Create Intermediate Models

Create `models/intermediate/int_order_metrics.sql` (see previous response for content)

### Step 5: Create Mart Models

Create fact and dimension tables in `models/marts/core/` and analytics models in `models/marts/analytics/`

### Step 6: Full Pipeline Build

```bash
# Run entire pipeline
dbt run

# Run tests
dbt test

# Generate documentation
dbt docs generate

# Serve documentation locally
dbt docs serve
```

## Testing and Validation

### Data Quality Tests

Add tests to your models:

```yaml
# In models/marts/core/schema.yml
version: 2

models:
  - name: fact_orders
    description: Fact table for orders
    columns:
      - name: order_id
        description: Unique order identifier
        tests:
          - unique
          - not_null
      - name: total_order_value
        description: Total value of the order
        tests:
          - not_null
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0
              max_value: 10000
```

### Custom Tests

Create custom tests in `tests/` directory:

```sql
-- tests/assert_positive_order_values.sql
select *
from {{ ref('fact_orders') }}
where total_order_value <= 0
```

### Run Tests

```bash
# Run all tests
dbt test

# Run tests for specific models
dbt test --models fact_orders

# Run only source tests
dbt test --models source:*
```

## Deployment

### Production Environment

1. Create production profile in `~/.dbt/profiles.yml`
2. Update production database/schema names
3. Set up CI/CD pipeline (GitHub Actions, GitLab CI, etc.)

### Sample GitHub Actions Workflow

Create `.github/workflows/dbt_ci.yml`:

```yaml
name: dbt CI

on:
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install dbt-snowflake
        dbt deps
    
    - name: Run dbt tests
      run: dbt test --profiles-dir ./
      env:
        SNOWFLAKE_ACCOUNT: ${{ secrets.SNOWFLAKE_ACCOUNT }}
        SNOWFLAKE_USER: ${{ secrets.SNOWFLAKE_USER }}
        SNOWFLAKE_PASSWORD: ${{ secrets.SNOWFLAKE_PASSWORD }}
```

## Troubleshooting

### Common Issues

1. **Connection Issues**
   ```bash
   # Check your profile configuration
   dbt debug
   
   # Verify Snowflake credentials
   # Check account URL format
   ```

2. **Data Type Issues**
   ```sql
   -- Use try_to_timestamp() for date conversions
   -- Use try_to_number() for numeric conversions
   ```

3. **Performance Issues**
   ```sql
   -- Add clustering keys to large tables
   {{ config(cluster_by=['order_date', 'customer_id']) }}
   ```

### Useful Commands

```bash
# Fresh start - clean and rebuild everything
dbt clean
dbt deps
dbt run

# Run specific model and its downstream dependencies
dbt run --models stg_orders+

# Run models that have been modified
dbt run --models state:modified

# Compile SQL without running
dbt compile

# Show lineage for a specific model
dbt list --models +fact_orders+
```

### Getting Help

- dbt Documentation: [docs.getdbt.com](https://docs.getdbt.com)
- dbt Community: [community.getdbt.com](https://community.getdbt.com)
- Snowflake Documentation: [docs.snowflake.com](https://docs.snowflake.com)

## Next Steps

After completing this setup:

1. Explore the generated documentation at `http://localhost:8080`
2. Create additional analytics models for your specific use cases
3. Set up alerting and monitoring
4. Implement data governance and lineage tracking
5. Consider adding incremental models for better performance
6. Explore advanced dbt features like macros and snapshots

This setup provides a solid foundation for analyzing e-commerce data and can be extended based on your specific analytical needs.