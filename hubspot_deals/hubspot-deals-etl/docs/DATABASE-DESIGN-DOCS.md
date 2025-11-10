# 🗄️ HubSpot Deals - Database Schema Design

This document defines the PostgreSQL database schema for the HubSpot Deals ETL service with multi-tenant support and comprehensive deal data storage.

---

## 📋 Overview

The HubSpot Deals database schema consists of four main tables:

1. **scan_jobs** - Core scan job management and tracking
2. **hubspot_deals** - HubSpot deal records with all properties
3. **deal_associations** - Relationships between deals and other HubSpot objects
4. **deal_pipelines** - Pipeline and stage configuration metadata

**Design Principles:**
- **Multi-tenant isolation** using `_tenant_id` on all tables
- **Audit trail** with ETL metadata fields
- **Performance optimization** through strategic indexing
- **Type safety** with proper PostgreSQL type mapping
- **Scalability** for large deal volumes

---

## 🏗️ Table Schemas

### 1. ScanJob Table

**Purpose**: Core scan job management and status tracking for HubSpot Deals extraction

**Table Name**: `scan_jobs`

```sql
CREATE TABLE scan_jobs (
    -- Primary Key
    id VARCHAR(255) PRIMARY KEY,
    
    -- Scan Identification
    scan_id VARCHAR(255) UNIQUE NOT NULL,
    _tenant_id VARCHAR(255) NOT NULL,
    
    -- Status Tracking
    status VARCHAR(50) NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    scan_type VARCHAR(100) NOT NULL DEFAULT 'hubspot_deals',
    
    -- Configuration
    config JSONB NOT NULL,
    organization_id VARCHAR(255),
    
    -- Progress Tracking
    total_items INTEGER DEFAULT 0,
    processed_items INTEGER DEFAULT 0,
    failed_items INTEGER DEFAULT 0,
    success_rate VARCHAR(10),
    
    -- Error Handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    -- Execution Timing
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Performance Settings
    batch_size INTEGER DEFAULT 100,
    rate_limit_delay INTEGER DEFAULT 100,
    
    -- Audit Trail
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by VARCHAR(255),
    updated_by VARCHAR(255)
);

-- Performance Indexes
CREATE INDEX idx_scan_status_created ON scan_jobs(status, created_at DESC);
CREATE INDEX idx_scan_id_status ON scan_jobs(scan_id, status);
CREATE INDEX idx_scan_tenant ON scan_jobs(_tenant_id, created_at DESC);
CREATE INDEX idx_scan_org_status ON scan_jobs(organization_id, status);
CREATE INDEX idx_scan_type_status ON scan_jobs(scan_type, status, created_at DESC);

-- Comments
COMMENT ON TABLE scan_jobs IS 'Tracks HubSpot Deals extraction jobs with status and progress';
COMMENT ON COLUMN scan_jobs._tenant_id IS 'Multi-tenant isolation identifier';
COMMENT ON COLUMN scan_jobs.config IS 'JSONB configuration including auth, filters, date ranges';
```

---

### 2. HubSpot Deals Table

**Purpose**: Store complete HubSpot deal records with all standard and custom properties

**Table Name**: `hubspot_deals`

```sql
CREATE TABLE hubspot_deals (
    -- Primary Key
    id VARCHAR(255) PRIMARY KEY,
    
    -- ETL Metadata (Required for all tables)
    _scan_id VARCHAR(255) NOT NULL,
    _tenant_id VARCHAR(255) NOT NULL,
    _extracted_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    _hubspot_object_id VARCHAR(255) NOT NULL,
    
    -- Foreign Key
    scan_job_id VARCHAR(255) REFERENCES scan_jobs(id) ON DELETE CASCADE,
    
    -- Core Deal Identification
    deal_id VARCHAR(255) NOT NULL,
    dealname VARCHAR(500),
    
    -- Financial Information
    amount NUMERIC(18, 2),
    amount_in_home_currency NUMERIC(18, 2),
    hs_closed_amount NUMERIC(18, 2),
    hs_closed_amount_in_home_currency NUMERIC(18, 2),
    hs_tcv NUMERIC(18, 2),
    hs_mrr NUMERIC(18, 2),
    hs_arr NUMERIC(18, 2),
    hs_forecast_amount NUMERIC(18, 2),
    hs_projected_amount NUMERIC(18, 2),
    
    -- Pipeline & Stage Information
    pipeline VARCHAR(255),
    dealstage VARCHAR(255) NOT NULL,
    hs_deal_stage_probability NUMERIC(5, 4),
    hs_forecast_probability NUMERIC(5, 4),
    hs_manual_forecast_category VARCHAR(100),
    hs_priority VARCHAR(50),
    
    -- Deal Classification
    dealtype VARCHAR(100),
    hs_is_closed BOOLEAN DEFAULT FALSE,
    hs_is_closed_won BOOLEAN DEFAULT FALSE,
    
    -- Dates & Timing
    closedate TIMESTAMP WITH TIME ZONE,
    createdate TIMESTAMP WITH TIME ZONE,
    hs_lastmodifieddate TIMESTAMP WITH TIME ZONE,
    hs_date_entered_appointmentscheduled TIMESTAMP WITH TIME ZONE,
    hs_date_entered_qualifiedtobuy TIMESTAMP WITH TIME ZONE,
    hs_date_entered_presentationscheduled TIMESTAMP WITH TIME ZONE,
    hs_date_entered_decisionmakerboughtin TIMESTAMP WITH TIME ZONE,
    hs_date_entered_contractsent TIMESTAMP WITH TIME ZONE,
    hs_date_entered_closedwon TIMESTAMP WITH TIME ZONE,
    hs_date_entered_closedlost TIMESTAMP WITH TIME ZONE,
    hs_date_exited_appointmentscheduled TIMESTAMP WITH TIME ZONE,
    hs_date_exited_qualifiedtobuy TIMESTAMP WITH TIME ZONE,
    
    -- Ownership & Assignment
    hubspot_owner_id VARCHAR(255),
    hubspot_team_id VARCHAR(255),
    
    -- Source & Analytics
    hs_analytics_source VARCHAR(255),
    hs_analytics_source_data_1 VARCHAR(500),
    hs_analytics_source_data_2 VARCHAR(500),
    hs_campaign VARCHAR(255),
    
    -- Next Steps & Notes
    hs_next_step TEXT,
    
    -- Engagement Metrics
    notes_last_contacted TIMESTAMP WITH TIME ZONE,
    notes_last_updated TIMESTAMP WITH TIME ZONE,
    notes_next_activity_date TIMESTAMP WITH TIME ZONE,
    num_contacted_notes INTEGER DEFAULT 0,
    num_notes INTEGER DEFAULT 0,
    hs_num_of_associated_line_items INTEGER DEFAULT 0,
    hs_latest_meeting_activity TIMESTAMP WITH TIME ZONE,
    hs_sales_email_last_replied TIMESTAMP WITH TIME ZONE,
    
    -- Association Counts
    hs_num_associated_contacts INTEGER DEFAULT 0,
    hs_num_associated_companies INTEGER DEFAULT 0,
    hs_num_associated_deal_splits INTEGER DEFAULT 0,
    
    -- Custom Properties Storage
    custom_properties JSONB,
    
    -- HubSpot Metadata
    archived BOOLEAN DEFAULT FALSE,
    archived_at TIMESTAMP WITH TIME ZONE,
    
    -- Raw Data Backup
    raw_data JSONB NOT NULL,
    
    -- Audit Trail
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_deal_per_tenant UNIQUE (_tenant_id, deal_id, _scan_id)
);

-- Performance Indexes
CREATE INDEX idx_deals_scan_job ON hubspot_deals(scan_job_id);
CREATE INDEX idx_deals_tenant_scan ON hubspot_deals(_tenant_id, _scan_id);
CREATE INDEX idx_deals_extracted ON hubspot_deals(_extracted_at DESC);
CREATE INDEX idx_deals_deal_id ON hubspot_deals(deal_id);
CREATE INDEX idx_deals_hubspot_id ON hubspot_deals(_hubspot_object_id);

-- Business Logic Indexes
CREATE INDEX idx_deals_pipeline_stage ON hubspot_deals(pipeline, dealstage);
CREATE INDEX idx_deals_owner ON hubspot_deals(hubspot_owner_id, dealstage);
CREATE INDEX idx_deals_closedate ON hubspot_deals(closedate) WHERE closedate IS NOT NULL;
CREATE INDEX idx_deals_amount ON hubspot_deals(amount) WHERE amount IS NOT NULL;
CREATE INDEX idx_deals_closed_won ON hubspot_deals(hs_is_closed_won, closedate) WHERE hs_is_closed_won = TRUE;
CREATE INDEX idx_deals_active ON hubspot_deals(dealstage, amount) WHERE hs_is_closed = FALSE AND archived = FALSE;
CREATE INDEX idx_deals_modified ON hubspot_deals(hs_lastmodifieddate DESC);

-- Multi-tenant Composite Indexes
CREATE INDEX idx_deals_tenant_pipeline ON hubspot_deals(_tenant_id, pipeline, dealstage);
CREATE INDEX idx_deals_tenant_owner ON hubspot_deals(_tenant_id, hubspot_owner_id);
CREATE INDEX idx_deals_tenant_closedate ON hubspot_deals(_tenant_id, closedate) WHERE closedate IS NOT NULL;

-- JSON Indexes for Custom Properties
CREATE INDEX idx_deals_custom_props ON hubspot_deals USING GIN (custom_properties);
CREATE INDEX idx_deals_raw_data ON hubspot_deals USING GIN (raw_data);

-- Comments
COMMENT ON TABLE hubspot_deals IS 'HubSpot deal records with complete property set and ETL metadata';
COMMENT ON COLUMN hubspot_deals._scan_id IS 'Unique scan identifier for data lineage tracking';
COMMENT ON COLUMN hubspot_deals._tenant_id IS 'Multi-tenant isolation identifier';
COMMENT ON COLUMN hubspot_deals._extracted_at IS 'Timestamp when deal was extracted from HubSpot';
COMMENT ON COLUMN hubspot_deals._hubspot_object_id IS 'HubSpot internal object ID (hs_object_id)';
COMMENT ON COLUMN hubspot_deals.custom_properties IS 'JSONB storage for custom deal properties';
COMMENT ON COLUMN hubspot_deals.raw_data IS 'Complete API response for audit and recovery';
```

---

### 3. Deal Associations Table

**Purpose**: Store relationships between deals and other HubSpot objects (contacts, companies, line items)

**Table Name**: `deal_associations`

```sql
CREATE TABLE deal_associations (
    -- Primary Key
    id VARCHAR(255) PRIMARY KEY,
    
    -- ETL Metadata
    _scan_id VARCHAR(255) NOT NULL,
    _tenant_id VARCHAR(255) NOT NULL,
    _extracted_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Foreign Keys
    scan_job_id VARCHAR(255) REFERENCES scan_jobs(id) ON DELETE CASCADE,
    deal_id VARCHAR(255) NOT NULL,
    
    -- Association Details
    associated_object_id VARCHAR(255) NOT NULL,
    association_type VARCHAR(100) NOT NULL,
    association_category VARCHAR(50) NOT NULL,
    
    -- Association Metadata
    association_spec JSONB,
    
    -- Audit Trail
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_association UNIQUE (_tenant_id, deal_id, associated_object_id, association_type)
);

-- Performance Indexes
CREATE INDEX idx_assoc_scan_job ON deal_associations(scan_job_id);
CREATE INDEX idx_assoc_deal_id ON deal_associations(deal_id);
CREATE INDEX idx_assoc_object_id ON deal_associations(associated_object_id);
CREATE INDEX idx_assoc_type ON deal_associations(association_type, association_category);
CREATE INDEX idx_assoc_tenant ON deal_associations(_tenant_id, deal_id);

-- Comments
COMMENT ON TABLE deal_associations IS 'HubSpot deal associations with contacts, companies, and line items';
COMMENT ON COLUMN deal_associations.association_type IS 'Type: deal_to_contact, deal_to_company, deal_to_line_item';
COMMENT ON COLUMN deal_associations.association_category IS 'Category: contacts, companies, line_items, tickets';
```

---

### 4. Deal Pipelines Table

**Purpose**: Store pipeline and stage configuration metadata

**Table Name**: `deal_pipelines`

```sql
CREATE TABLE deal_pipelines (
    -- Primary Key
    id VARCHAR(255) PRIMARY KEY,
    
    -- ETL Metadata
    _scan_id VARCHAR(255) NOT NULL,
    _tenant_id VARCHAR(255) NOT NULL,
    _extracted_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Foreign Keys
    scan_job_id VARCHAR(255) REFERENCES scan_jobs(id) ON DELETE CASCADE,
    
    -- Pipeline Information
    pipeline_id VARCHAR(255) NOT NULL,
    pipeline_label VARCHAR(500),
    display_order INTEGER,
    
    -- Stage Information
    stages JSONB NOT NULL,
    
    -- Pipeline Metadata
    archived BOOLEAN DEFAULT FALSE,
    pipeline_created_at TIMESTAMP WITH TIME ZONE,
    pipeline_updated_at TIMESTAMP WITH TIME ZONE,
    
    -- Raw Data
    raw_data JSONB,
    
    -- Audit Trail
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_pipeline_per_tenant UNIQUE (_tenant_id, pipeline_id)
);

-- Performance Indexes
CREATE INDEX idx_pipelines_scan_job ON deal_pipelines(scan_job_id);
CREATE INDEX idx_pipelines_tenant ON deal_pipelines(_tenant_id);
CREATE INDEX idx_pipelines_id ON deal_pipelines(pipeline_id);
CREATE INDEX idx_pipelines_stages ON deal_pipelines USING GIN (stages);

-- Comments
COMMENT ON TABLE deal_pipelines IS 'HubSpot deal pipeline and stage configurations';
COMMENT ON COLUMN deal_pipelines.stages IS 'JSONB array of pipeline stages with metadata';
```

---

## 🗺️ HubSpot Property to PostgreSQL Type Mapping

### Standard Property Mappings

| **HubSpot Property Type** | **PostgreSQL Type** | **Notes** |
|---------------------------|---------------------|-----------|
| `string` | `VARCHAR(255)` or `TEXT` | Use TEXT for long descriptions |
| `number` | `NUMERIC(18, 2)` | For currency/amounts |
| `number` | `INTEGER` | For counts/IDs |
| `number` | `NUMERIC(5, 4)` | For probabilities (0-1) |
| `date` | `DATE` | Date only, no time |
| `datetime` | `TIMESTAMP WITH TIME ZONE` | Full timestamp with timezone |
| `enumeration` | `VARCHAR(100)` | Predefined values |
| `boolean` | `BOOLEAN` | True/False flags |
| `object_id` | `VARCHAR(255)` | HubSpot object references |
| `json` | `JSONB` | Complex nested data |

### Specific Property Mappings

```sql
-- Financial Fields
amount                              -> NUMERIC(18, 2)
hs_tcv                             -> NUMERIC(18, 2)
hs_mrr                             -> NUMERIC(18, 2)

-- Probability Fields
hs_deal_stage_probability          -> NUMERIC(5, 4)  -- 0.0000 to 1.0000
hs_forecast_probability            -> NUMERIC(5, 4)

-- Count Fields
num_contacted_notes                -> INTEGER
hs_num_associated_contacts         -> INTEGER
hs_num_of_associated_line_items    -> INTEGER

-- Date Fields
closedate                          -> TIMESTAMP WITH TIME ZONE
createdate                         -> TIMESTAMP WITH TIME ZONE
hs_lastmodifieddate                -> TIMESTAMP WITH TIME ZONE

-- Text Fields
dealname                           -> VARCHAR(500)
hs_next_step                       -> TEXT

-- Enumeration Fields
dealstage                          -> VARCHAR(255)
pipeline                           -> VARCHAR(255)
dealtype                           -> VARCHAR(100)
hs_priority                        -> VARCHAR(50)

-- Boolean Fields
hs_is_closed                       -> BOOLEAN
hs_is_closed_won                   -> BOOLEAN
archived                           -> BOOLEAN

-- Complex Data
custom_properties                  -> JSONB
raw_data                           -> JSONB
```

---

## 🔗 Relationships

### Entity Relationship Diagram

```
┌─────────────────┐
│   scan_jobs     │
│                 │
│ PK: id          │
│ UK: scan_id     │
│    _tenant_id   │
└────────┬────────┘
         │
         │ 1:N
         │
    ┌────┴──────────────┬────────────────────┬──────────────────┐
    │                   │                    │                  │
┌───▼───────────────┐ ┌─▼──────────────┐ ┌──▼──────────────┐ ┌─▼─────────────┐
│ hubspot_deals     │ │ deal_          │ │ deal_pipelines  │ │  [future      │
│                   │ │ associations   │ │                 │ │   tables]     │
│ PK: id            │ │                │ │ PK: id          │ │               │
│ FK: scan_job_id   │ │ FK: scan_job_id│ │ FK: scan_job_id │ │               │
│ UK: _tenant_id,   │ │ FK: deal_id    │ │ UK: _tenant_id, │ │               │
│     deal_id,      │ │                │ │     pipeline_id │ │               │
│     _scan_id      │ │                │ │                 │ │               │
└───────────────────┘ └────────────────┘ └─────────────────┘ └───────────────┘
```

### Referential Integrity

```sql
-- Foreign Key Constraints
ALTER TABLE hubspot_deals 
    ADD CONSTRAINT fk_deals_scan_job 
    FOREIGN KEY (scan_job_id) 
    REFERENCES scan_jobs(id) 
    ON DELETE CASCADE;

ALTER TABLE deal_associations 
    ADD CONSTRAINT fk_assoc_scan_job 
    FOREIGN KEY (scan_job_id) 
    REFERENCES scan_jobs(id) 
    ON DELETE CASCADE;

ALTER TABLE deal_pipelines 
    ADD CONSTRAINT fk_pipelines_scan_job 
    FOREIGN KEY (scan_job_id) 
    REFERENCES scan_jobs(id) 
    ON DELETE CASCADE;
```

---

## 🛡️ Multi-Tenant Data Isolation

### Tenant Isolation Strategy

**Every table includes `_tenant_id`** to ensure complete data isolation:

```sql
-- All queries MUST filter by tenant
SELECT * FROM hubspot_deals 
WHERE _tenant_id = 'tenant-abc-123';

-- Unique constraints include tenant ID
CONSTRAINT unique_deal_per_tenant UNIQUE (_tenant_id, deal_id, _scan_id);

-- Indexes optimize tenant-based queries
CREATE INDEX idx_deals_tenant_scan ON hubspot_deals(_tenant_id, _scan_id);
```

### Row-Level Security (Optional Enhancement)

```sql
-- Enable Row-Level Security
ALTER TABLE hubspot_deals ENABLE ROW LEVEL SECURITY;

-- Create policy for tenant isolation
CREATE POLICY tenant_isolation_policy ON hubspot_deals
    USING (_tenant_id = current_setting('app.current_tenant_id'));

-- Set tenant context in application
SET app.current_tenant_id = 'tenant-abc-123';
```

### Tenant Query Patterns

```sql
-- Get all deals for a tenant
SELECT * FROM hubspot_deals 
WHERE _tenant_id = 'tenant-abc-123'
ORDER BY _extracted_at DESC;

-- Get deal count by pipeline for a tenant
SELECT pipeline, dealstage, COUNT(*) as deal_count
FROM hubspot_deals 
WHERE _tenant_id = 'tenant-abc-123'
GROUP BY pipeline, dealstage;

-- Get deals for a specific scan
SELECT * FROM hubspot_deals 
WHERE _tenant_id = 'tenant-abc-123' 
  AND _scan_id = 'scan-2025-11-10'
ORDER BY closedate;
```

---

## 📊 Common Queries

### Scan Job Management

```sql
-- Get all scans for a tenant
SELECT scan_id, status, started_at, completed_at, 
       processed_items, total_items
FROM scan_jobs 
WHERE _tenant_id = 'tenant-abc-123'
ORDER BY created_at DESC;

-- Get active scans
SELECT * FROM scan_jobs 
WHERE status IN ('pending', 'running')
  AND _tenant_id = 'tenant-abc-123';

-- Get scan statistics
SELECT 
    status,
    COUNT(*) as scan_count,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_duration_seconds,
    SUM(processed_items) as total_deals_processed
FROM scan_jobs 
WHERE _tenant_id = 'tenant-abc-123'
GROUP BY status;
```

### Deal Analytics

```sql
-- Get open deals by pipeline stage
SELECT 
    pipeline,
    dealstage,
    COUNT(*) as deal_count,
    SUM(amount) as total_amount,
    AVG(amount) as avg_amount
FROM hubspot_deals 
WHERE _tenant_id = 'tenant-abc-123'
  AND hs_is_closed = FALSE
  AND archived = FALSE
GROUP BY pipeline, dealstage
ORDER BY pipeline, dealstage;

-- Get deals closing this month
SELECT 
    dealname,
    amount,
    closedate,
    dealstage,
    hubspot_owner_id
FROM hubspot_deals 
WHERE _tenant_id = 'tenant-abc-123'
  AND closedate >= DATE_TRUNC('month', CURRENT_DATE)
  AND closedate < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
ORDER BY closedate;

-- Get won deals in date range
SELECT 
    DATE_TRUNC('week', closedate) as week,
    COUNT(*) as deals_won,
    SUM(amount) as total_revenue
FROM hubspot_deals 
WHERE _tenant_id = 'tenant-abc-123'
  AND hs_is_closed_won = TRUE
  AND closedate >= '2025-01-01'
  AND closedate < '2025-12-31'
GROUP BY DATE_TRUNC('week', closedate)
ORDER BY week;

-- Get deals by owner
SELECT 
    hubspot_owner_id,
    COUNT(*) as total_deals,
    COUNT(*) FILTER (WHERE hs_is_closed_won = TRUE) as won_deals,
    SUM(amount) as total_value,
    SUM(amount) FILTER (WHERE hs_is_closed_won = TRUE) as won_value
FROM hubspot_deals 
WHERE _tenant_id = 'tenant-abc-123'
  AND closedate >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY hubspot_owner_id;
```

### Association Queries

```sql
-- Get all contacts associated with a deal
SELECT 
    da.deal_id,
    da.associated_object_id as contact_id,
    da.association_type
FROM deal_associations da
WHERE da._tenant_id = 'tenant-abc-123'
  AND da.deal_id = '12345678901'
  AND da.association_category = 'contacts';

-- Get deals with association counts
SELECT 
    d.deal_id,
    d.dealname,
    d.amount,
    COUNT(DISTINCT CASE WHEN da.association_category = 'contacts' THEN da.associated_object_id END) as contact_count,
    COUNT(DISTINCT CASE WHEN da.association_category = 'companies' THEN da.associated_object_id END) as company_count
FROM hubspot_deals d
LEFT JOIN deal_associations da ON d.deal_id = da.deal_id AND d._tenant_id = da._tenant_id
WHERE d._tenant_id = 'tenant-abc-123'
GROUP BY d.deal_id, d.dealname, d.amount;
```

### Pipeline Analysis

```sql
-- Get pipeline stages with metadata
SELECT 
    pipeline_id,
    pipeline_label,
    jsonb_array_length(stages) as stage_count,
    stages
FROM deal_pipelines 
WHERE _tenant_id = 'tenant-abc-123';

-- Get deal distribution across stages
SELECT 
    p.pipeline_label,
    stage->>'label' as stage_label,
    stage->>'metadata'->>'probability' as win_probability,
    COUNT(d.deal_id) as deal_count,
    SUM(d.amount) as total_amount
FROM deal_pipelines p
CROSS JOIN jsonb_array_elements(p.stages) as stage
LEFT JOIN hubspot_deals d ON d.pipeline = p.pipeline_id 
    AND d.dealstage = stage->>'id'
    AND d._tenant_id = p._tenant_id
WHERE p._tenant_id = 'tenant-abc-123'
  AND d.hs_is_closed = FALSE
GROUP BY p.pipeline_label, stage->>'label', stage->>'displayOrder', stage->>'metadata'->>'probability'
ORDER BY p.pipeline_label, (stage->>'displayOrder')::INTEGER;
```

---

## 🛠️ Implementation Examples

### Creating a Scan Job

```sql
INSERT INTO scan_jobs (
    id, scan_id, _tenant_id, status, scan_type, config, 
    organization_id, batch_size, created_by
) VALUES (
    'uuid-' || gen_random_uuid()::text,
    'hubspot-deals-2025-11-10',
    'tenant-abc-123',
    'pending',
    'hubspot_deals',
    '{"auth": {"access_token": "pat-xxx"}, "filters": {"pipeline": "default"}, "dateRange": {"startDate": "2025-01-01", "endDate": "2025-12-31"}}'::jsonb,
    'org-456',
    100,
    'etl-service'
);
```

### Inserting Deal Records

```sql
INSERT INTO hubspot_deals (
    id, _scan_id, _tenant_id, _extracted_at, _hubspot_object_id,
    scan_job_id, deal_id, dealname, amount, closedate, dealstage, 
    pipeline, hubspot_owner_id, hs_is_closed, raw_data
) VALUES (
    'uuid-' || gen_random_uuid()::text,
    'hubspot-deals-2025-11-10',
    'tenant-abc-123',
    NOW(),
    '12345678901',
    'uuid-scan-job-id',
    '12345678901',
    'Enterprise Software Deal - Acme Corp',
    50000.00,
    '2025-12-31T00:00:00Z',
    'appointmentscheduled',
    'default',
    '98765432',
    FALSE,
    '{"id": "12345678901", "properties": {...}}'::jsonb
);
```

### Updating Scan Status

```sql
-- Start scan
UPDATE scan_jobs 
SET status = 'running',
    started_at = NOW(),
    updated_at = NOW()
WHERE scan_id = 'hubspot-deals-2025-11-10'
  AND _tenant_id = 'tenant-abc-123';

-- Update progress
UPDATE scan_jobs 
SET processed_items = processed_items + 100,
    success_rate = ROUND((processed_items::numeric / NULLIF(total_items, 0)) * 100, 2)::text || '%',
    updated_at = NOW()
WHERE scan_id = 'hubspot-deals-2025-11-10'
  AND _tenant_id = 'tenant-abc-123';

-- Complete scan
UPDATE scan_jobs 
SET status = 'completed',
    completed_at = NOW(),
    updated_at = NOW()
WHERE scan_id = 'hubspot-deals-2025-11-10'
  AND _tenant_id = 'tenant-abc-123';
```

---

## 📈 Performance Considerations

### Index Strategy

**Primary Indexes** (Already Created):
- `_tenant_id` columns for multi-tenant isolation
- `scan_id` and `_scan_id` for data lineage
- `deal_id` and `_hubspot_object_id` for lookups
- `pipeline` and `dealstage` for analytics
- Date fields (`closedate`, `_extracted_at`)

**Composite Indexes** for Common Query Patterns:
```sql
-- Deal filtering and analytics
CREATE INDEX idx_deals_tenant_pipeline_stage_active 
ON hubspot_deals(_tenant_id, pipeline, dealstage, closedate)
WHERE hs_is_closed = FALSE AND archived = FALSE;

-- Owner-based queries
CREATE INDEX idx_deals_tenant_owner_stage 
ON hubspot_deals(_tenant_id, hubspot_owner_id, dealstage, closedate);

-- Time-series analytics
CREATE INDEX idx_deals_tenant_closedate_won 
ON hubspot_deals(_tenant_id, closedate, amount)
WHERE hs_is_closed_won = TRUE;
```

### Partitioning Strategy (For Large Datasets)

```sql
-- Partition by tenant (if tenant count is moderate)
CREATE TABLE hubspot_deals_partitioned (
    LIKE hubspot_deals INCLUDING ALL
) PARTITION BY LIST (_tenant_id);

-- Create partitions per tenant
CREATE TABLE hubspot_deals_tenant_1 PARTITION OF hubspot_deals_partitioned
    FOR VALUES IN ('tenant-abc-123');

-- Or partition by extraction date (for time-series queries)
CREATE TABLE hubspot_deals_partitioned (
    LIKE hubspot_deals INCLUDING ALL
) PARTITION BY RANGE (_extracted_at);

CREATE TABLE hubspot_deals_2025_q4 PARTITION OF hubspot_deals_partitioned
    FOR VALUES FROM ('2025-10-01') TO ('2026-01-01');
```

### Query Optimization Tips

```sql
-- Use EXPLAIN ANALYZE to check query performance
EXPLAIN ANALYZE
SELECT * FROM hubspot_deals 
WHERE _tenant_id = 'tenant-abc-123' 
  AND dealstage = 'appointmentscheduled';

-- Create partial indexes for frequent filters
CREATE INDEX idx_deals_open_high_value 
ON hubspot_deals(_tenant_id, amount, closedate)
WHERE hs_is_closed = FALSE 
  AND archived = FALSE 
  AND amount > 10000;

-- Use materialized views for heavy analytics
CREATE MATERIALIZED VIEW mv_deal_pipeline_summary AS
SELECT 
    _tenant_id,
    pipeline,
    dealstage,
    COUNT(*) as deal_count,
    SUM(amount) as total_amount,
    AVG(amount) as avg_amount
FROM hubspot_deals
WHERE hs_is_closed = FALSE AND archived = FALSE
GROUP BY _tenant_id, pipeline, dealstage;

-- Refresh materialized view after ETL runs
REFRESH MATERIALIZED VIEW mv_deal_pipeline_summary;
```

---

## 🛡️ Data Integrity

### Constraints and Validations

```sql
-- Status check constraints
ALTER TABLE scan_jobs 
ADD CONSTRAINT check_valid_status 
CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled'));

-- Amount validations
ALTER TABLE hubspot_deals 
ADD CONSTRAINT check_positive_amount 
CHECK (amount IS NULL OR amount >= 0);

-- Date validations
ALTER TABLE hubspot_deals 
ADD CONSTRAINT check_valid_closedate 
CHECK (closedate IS NULL OR closedate >= createdate);

-- Probability validations
ALTER TABLE hubspot_deals 
ADD CONSTRAINT check_probability_range 
CHECK (hs_deal_stage_probability IS NULL OR (hs_deal_stage_probability >= 0 AND hs_deal_stage_probability <= 1));
```

### Triggers for Audit Trail

```sql
-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_scan_jobs_updated_at 
    BEFORE UPDATE ON scan_jobs 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_deals_updated_at 
    BEFORE UPDATE ON hubspot_deals 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

---

## 🔧 Maintenance Operations

### Data Cleanup

```sql
-- Remove old completed scans (older than 90 days)
DELETE FROM scan_jobs 
WHERE _tenant_id = 'tenant-abc-123'
  AND status = 'completed'
  AND completed_at < NOW() - INTERVAL '90 days';

-- Archive old deals (moves to archive table)
INSERT INTO hubspot_deals_archive 
SELECT * FROM hubspot_deals 
WHERE _tenant_id = 'tenant-abc-123'
  AND _extracted_at < NOW() - INTERVAL '180 days';

DELETE FROM hubspot_deals 
WHERE _tenant_id = 'tenant-abc-123'
  AND _extracted_at < NOW() - INTERVAL '180 days';

-- Vacuum and analyze
VACUUM ANALYZE hubspot_deals;
VACUUM ANALYZE scan_jobs;
```

### Index Maintenance

```sql
-- Rebuild indexes
REINDEX TABLE hubspot_deals;
REINDEX TABLE scan_jobs;

-- Update statistics
ANALYZE hubspot_deals;
ANALYZE scan_jobs;
```

---

## 📊 Sample Data Structure

### Example: Complete Deal Record

```json
{
  "id": "uuid-abc-123",
  "_scan_id": "hubspot-deals-2025-11-10",
  "_tenant_id": "tenant-abc-123",
  "_extracted_at": "2025-11-10T16:00:00Z",
  "_hubspot_object_id": "12345678901",
  "scan_job_id": "uuid-scan-job",
  "deal_id": "12345678901",
  "dealname": "Enterprise Software Deal - Acme Corp",
  "amount": 50000.00,
  "closedate": "2025-12-31T00:00:00Z",
  "dealstage": "appointmentscheduled",
  "pipeline": "default",
  "hubspot_owner_id": "98765432",
  "hs_is_closed": false,
  "hs_is_closed_won": false,
  "hs_deal_stage_probability": 0.20,
  "custom_properties": {
    "custom_field_1": "value1",
    "industry_vertical": "SaaS"
  },
  "raw_data": {
    "id": "12345678901",
    "properties": {...},
    "associations": {...}
  }
}
```

---

## 🔄 Migration Scripts

### Initial Schema Setup

```sql
-- Run these scripts in order:

-- 1. Create scan_jobs table
\i create_scan_jobs_table.sql

-- 2. Create hubspot_deals table
\i create_hubspot_deals_table.sql

-- 3. Create deal_associations table
\i create_deal_associations_table.sql

-- 4. Create deal_pipelines table
\i create_deal_pipelines_table.sql

-- 5. Create indexes
\i create_indexes.sql

-- 6. Create triggers
\i create_triggers.sql

-- 7. Grant permissions
\i grant_permissions.sql
```

### Permissions

```sql
-- Grant permissions to ETL service user
GRANT SELECT, INSERT, UPDATE, DELETE ON scan_jobs TO etl_service_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON hubspot_deals TO etl_service_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON deal_associations TO etl_service_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON deal_pipelines TO etl_service_user;

-- Grant read-only access to analytics users
GRANT SELECT ON hubspot_deals TO analytics_user;
GRANT SELECT ON deal_associations TO analytics_user;
GRANT SELECT ON deal_pipelines TO analytics_user;
```

---

## 📚 Documentation References

- **HubSpot CRM API v3**: https://developers.hubspot.com/docs/api/crm/deals
- **PostgreSQL Data Types**: https://www.postgresql.org/docs/current/datatype.html
- **PostgreSQL Indexing**: https://www.postgresql.org/docs/current/indexes.html
- **Multi-Tenant Design Patterns**: https://docs.microsoft.com/en-us/azure/architecture/guide/multitenant/considerations/tenancy-models

---

**Document Status**: ✅ Complete  
**Last Updated**: November 10, 2025  
**Database**: PostgreSQL 14+  
**Schema Version**: 1.0  
**Maintainer**: Data Engineering Team
