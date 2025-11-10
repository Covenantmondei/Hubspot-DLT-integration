# HubSpot Deals ETL - API Documentation

## 📋 Table of Contents
1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Base URLs](#base-urls)
4. [Common Response Formats](#common-response-formats)
5. [Scan Endpoints](#scan-endpoints)
6. [Health & Stats Endpoints](#health--stats-endpoints)
7. [Error Handling](#error-handling)
8. [Examples](#examples)
9. [Rate Limiting](#rate-limiting)
10. [Changelog](#changelog)

---

## 🔍 Overview

The **HubSpot Deals ETL Service** provides a RESTful API for extracting deal data from HubSpot CRM and loading it into PostgreSQL. The service handles authentication, rate limiting, pagination, and multi-tenant data isolation.

### API Version
- **Version**: 1.0.0
- **Base Path**: `/api/v1`
- **Content Type**: `application/json`
- **Documentation**: Available at `/docs` (Swagger UI)

### Key Features
- **HubSpot Deal Extraction**: Extract deals with all properties and associations
- **Multi-Tenant Support**: Isolated data per tenant with `_tenant_id`
- **Progress Tracking**: Real-time scan status and progress monitoring
- **Batch Processing**: Efficient batch extraction (100 deals per request)
- **Error Recovery**: Automatic retry with exponential backoff
- **Multiple Export Formats**: JSON, CSV, Excel downloads
- **RESTful Design**: Standard HTTP methods and status codes

---

## 🔐 Authentication

The API uses **Bearer Token authentication** with tenant-specific API keys.

### Required Credentials
- **API Key**: Service-level authentication token
- **Tenant ID**: Multi-tenant isolation identifier
- **HubSpot Access Token**: Private App Access Token from HubSpot (provided in scan config)

### Required Permissions
- `hubspot_deals:read` - Read deal data from HubSpot
- `hubspot_deals:extract` - Execute deal extraction scans
- `hubspot_deals:download` - Download extraction results

### Authentication Headers
```http
Authorization: Bearer YOUR_API_KEY
X-Tenant-ID: tenant-abc-123
Content-Type: application/json
```

### Example Authentication
```bash
curl -X GET "https://api.your-domain.com/health" \
  -H "Authorization: Bearer sk_live_abc123xyz..." \
  -H "X-Tenant-ID: tenant-abc-123"
```

---

## 🌐 Base URLs

### Development
```
http://localhost:5200
```

### Staging
```
https://staging-hubspot-deals-api.your-domain.com
```

### Production
```
https://hubspot-deals-api.your-domain.com
```

### Swagger Documentation
```
http://localhost:5200/docs
http://localhost:5200/redoc
```

---

## 📊 Common Response Formats

### Success Response
```json
{
  "status": "success",
  "message": "Operation completed successfully",
  "data": { },
  "timestamp": "2025-11-10T16:00:00Z"
}
```

### Error Response
```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid scan configuration",
    "details": [
      {
        "field": "config.auth.access_token",
        "message": "HubSpot access token is required"
      }
    ]
  },
  "timestamp": "2025-11-10T16:00:00Z"
}
```

### Pagination Response
```json
{
  "pagination": {
    "current_page": 1,
    "page_size": 100,
    "total_items": 523,
    "total_pages": 6,
    "has_next": true,
    "has_previous": false,
    "next_page": 2,
    "previous_page": null
  }
}
```

---

## 🔍 Scan Endpoints

### 1. Start Deal Extraction

**POST** `/api/v1/scan/start`

Initiates a new HubSpot deal extraction process.

#### Request Body
```json
{
  "config": {
    "scanId": "hubspot-deals-2025-11-10",
    "tenantId": "tenant-abc-123",
    "organizationId": "org-456",
    "auth": {
      "accessToken": "pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    },
    "filters": {
      "pipeline": "default",
      "dealStage": null,
      "archived": false
    },
    "dateRange": {
      "startDate": "2025-01-01",
      "endDate": "2025-12-31"
    },
    "properties": [
      "dealname",
      "amount",
      "closedate",
      "dealstage",
      "pipeline",
      "hubspot_owner_id",
      "hs_is_closed",
      "hs_is_closed_won"
    ],
    "associations": ["contacts", "companies"],
    "batchSize": 100,
    "rateLimitDelay": 100
  }
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `config.scanId` | string | Yes | Unique identifier for this scan |
| `config.tenantId` | string | Yes | Tenant isolation identifier |
| `config.organizationId` | string | No | Organization identifier |
| `config.auth.accessToken` | string | Yes | HubSpot Private App Access Token |
| `config.filters.pipeline` | string | No | Filter by specific pipeline ID |
| `config.filters.dealStage` | string | No | Filter by specific deal stage |
| `config.filters.archived` | boolean | No | Include archived deals (default: false) |
| `config.dateRange.startDate` | string | No | Filter deals created after this date (ISO 8601) |
| `config.dateRange.endDate` | string | No | Filter deals created before this date (ISO 8601) |
| `config.properties` | array | No | Specific properties to extract (default: all) |
| `config.associations` | array | No | Object types to include associations for |
| `config.batchSize` | integer | No | Deals per batch (default: 100, max: 100) |
| `config.rateLimitDelay` | integer | No | Delay between requests in ms (default: 100) |

#### Response (202 Accepted)
```json
{
  "status": "success",
  "message": "Deal extraction started successfully",
  "data": {
    "scanId": "hubspot-deals-2025-11-10",
    "scanJobId": "uuid-abc-123-def-456",
    "tenantId": "tenant-abc-123",
    "status": "pending",
    "createdAt": "2025-11-10T16:00:00Z",
    "estimatedDuration": "5-10 minutes",
    "statusUrl": "/api/v1/scan/status/hubspot-deals-2025-11-10"
  },
  "timestamp": "2025-11-10T16:00:00Z"
}
```

#### Status Codes
- **202**: Scan started successfully
- **400**: Invalid request body or configuration
- **401**: Missing or invalid authentication
- **403**: Insufficient permissions
- **409**: Scan with this ID already exists
- **500**: Internal server error

---

### 2. Get Scan Status

**GET** `/api/v1/scan/status/{scan_id}`

Retrieves the current status and progress of a deal extraction scan.

#### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `scan_id` | string | Yes | Unique scan identifier |

#### Response (200 OK)
```json
{
  "status": "success",
  "data": {
    "scanId": "hubspot-deals-2025-11-10",
    "scanJobId": "uuid-abc-123-def-456",
    "tenantId": "tenant-abc-123",
    "organizationId": "org-456",
    "status": "running",
    "progress": {
      "totalItems": 523,
      "processedItems": 300,
      "failedItems": 2,
      "successRate": "99.3%",
      "percentComplete": 57.4,
      "currentBatch": 3,
      "totalBatches": 6
    },
    "timing": {
      "startedAt": "2025-11-10T16:00:00Z",
      "estimatedCompletionAt": "2025-11-10T16:08:00Z",
      "elapsedSeconds": 240,
      "estimatedRemainingSeconds": 180
    },
    "config": {
      "batchSize": 100,
      "rateLimitDelay": 100,
      "filters": {
        "pipeline": "default"
      }
    },
    "errors": [
      {
        "dealId": "12345678901",
        "error": "Rate limit exceeded",
        "timestamp": "2025-11-10T16:03:00Z",
        "retryCount": 1
      }
    ]
  },
  "timestamp": "2025-11-10T16:04:00Z"
}
```

#### Status Values
- `pending`: Scan queued, not yet started
- `running`: Actively extracting deals from HubSpot
- `completed`: Scan finished successfully
- `failed`: Scan encountered critical error
- `cancelled`: Scan was cancelled by user

#### Status Codes
- **200**: Status retrieved successfully
- **404**: Scan not found
- **401**: Missing or invalid authentication
- **403**: Insufficient permissions (wrong tenant)

---

### 3. List All Scans

**GET** `/api/v1/scan/list`

Retrieves a paginated list of all scans for the authenticated tenant.

#### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `status` | string | No | all | Filter by status (pending, running, completed, failed) |
| `page` | integer | No | 1 | Page number (minimum: 1) |
| `page_size` | integer | No | 50 | Scans per page (1-100) |
| `sort` | string | No | created_at | Sort field (created_at, started_at, status) |
| `order` | string | No | desc | Sort order (asc, desc) |

#### Response (200 OK)
```json
{
  "status": "success",
  "data": {
    "scans": [
      {
        "scanId": "hubspot-deals-2025-11-10",
        "scanJobId": "uuid-abc-123",
        "status": "completed",
        "totalItems": 523,
        "processedItems": 523,
        "startedAt": "2025-11-10T16:00:00Z",
        "completedAt": "2025-11-10T16:08:00Z",
        "duration": "8m 15s"
      },
      {
        "scanId": "hubspot-deals-2025-11-09",
        "scanJobId": "uuid-def-456",
        "status": "completed",
        "totalItems": 487,
        "processedItems": 487,
        "startedAt": "2025-11-09T10:00:00Z",
        "completedAt": "2025-11-09T10:07:00Z",
        "duration": "7m 32s"
      }
    ],
    "pagination": {
      "current_page": 1,
      "page_size": 50,
      "total_items": 15,
      "total_pages": 1,
      "has_next": false,
      "has_previous": false
    }
  },
  "timestamp": "2025-11-10T16:10:00Z"
}
```

#### Status Codes
- **200**: List retrieved successfully
- **400**: Invalid query parameters
- **401**: Missing or invalid authentication
- **403**: Insufficient permissions

---

### 4. Cancel Scan

**POST** `/api/v1/scan/cancel/{scan_id}`

Cancels a running or pending deal extraction scan.

#### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `scan_id` | string | Yes | Unique scan identifier |

#### Response (200 OK)
```json
{
  "status": "success",
  "message": "Scan cancelled successfully",
  "data": {
    "scanId": "hubspot-deals-2025-11-10",
    "previousStatus": "running",
    "currentStatus": "cancelled",
    "processedItems": 300,
    "totalItems": 523,
    "cancelledAt": "2025-11-10T16:05:00Z"
  },
  "timestamp": "2025-11-10T16:05:00Z"
}
```

#### Status Codes
- **200**: Scan cancelled successfully
- **404**: Scan not found
- **409**: Scan already completed or cancelled
- **401**: Missing or invalid authentication
- **403**: Insufficient permissions

---

### 5. Get Extraction Results

**GET** `/api/v1/scan/result/{scan_id}`

Retrieves paginated deal extraction results with full deal details.

#### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `scan_id` | string | Yes | Unique scan identifier |

#### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number (minimum: 1) |
| `page_size` | integer | No | 100 | Deals per page (1-1000) |
| `include_raw` | boolean | No | false | Include raw HubSpot API response |
| `include_associations` | boolean | No | false | Include deal associations |

#### Response (200 OK)
```json
{
  "status": "success",
  "data": {
    "scanId": "hubspot-deals-2025-11-10",
    "scanStatus": "completed",
    "deals": [
      {
        "id": "uuid-deal-1",
        "dealId": "12345678901",
        "hubspotObjectId": "12345678901",
        "dealname": "Enterprise Software Deal - Acme Corp",
        "amount": 50000.00,
        "closedate": "2025-12-31T00:00:00Z",
        "dealstage": "appointmentscheduled",
        "pipeline": "default",
        "hubspotOwnerId": "98765432",
        "isClosedWon": false,
        "isClosed": false,
        "dealStageProbability": 0.20,
        "createdate": "2025-01-15T10:30:00Z",
        "lastmodifieddate": "2025-11-10T15:45:00Z",
        "customProperties": {
          "industry_vertical": "SaaS",
          "deal_priority": "high"
        },
        "associations": {
          "contacts": [
            {
              "id": "1001",
              "type": "deal_to_contact"
            }
          ],
          "companies": [
            {
              "id": "2001",
              "type": "deal_to_company"
            }
          ]
        },
        "extractedAt": "2025-11-10T16:02:00Z"
      }
    ],
    "pagination": {
      "current_page": 1,
      "page_size": 100,
      "total_items": 523,
      "total_pages": 6,
      "has_next": true,
      "has_previous": false,
      "next_page": 2
    },
    "summary": {
      "totalDeals": 523,
      "totalAmount": 5425000.00,
      "closedWonDeals": 87,
      "closedWonAmount": 1250000.00,
      "openDeals": 436,
      "openAmount": 4175000.00
    }
  },
  "timestamp": "2025-11-10T16:10:00Z"
}
```

#### Status Codes
- **200**: Results retrieved successfully
- **404**: Scan not found or no results available
- **400**: Invalid pagination parameters
- **401**: Missing or invalid authentication
- **403**: Insufficient permissions

---

### 6. Download Results

**GET** `/api/v1/scan/download/{scan_id}/{format}`

Downloads extraction results in the specified format (JSON, CSV, Excel).

#### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `scan_id` | string | Yes | Unique scan identifier |
| `format` | string | Yes | Download format: `json`, `csv`, `excel` |

#### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `include_associations` | boolean | No | false | Include associations in export |
| `include_custom_props` | boolean | No | true | Include custom properties |

#### Response Headers
```http
Content-Type: application/json | text/csv | application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="hubspot_deals_2025-11-10.{format}"
```

#### CSV Format Example
```csv
deal_id,dealname,amount,closedate,dealstage,pipeline,hubspot_owner_id,is_closed_won,extracted_at
12345678901,"Enterprise Software Deal - Acme Corp",50000.00,2025-12-31T00:00:00Z,appointmentscheduled,default,98765432,false,2025-11-10T16:02:00Z
12345678902,"Q4 Consulting Services - TechStart Inc",25000.00,2025-11-30T00:00:00Z,qualifiedtobuy,default,98765433,false,2025-11-10T16:02:15Z
```

#### Status Codes
- **200**: File downloaded successfully
- **404**: Scan not found or no results
- **400**: Invalid format specified
- **401**: Missing or invalid authentication
- **403**: Insufficient permissions

---

### 7. Delete Scan Results

**DELETE** `/api/v1/scan/remove/{scan_id}`

Removes scan job and associated deal records from the database.

#### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `scan_id` | string | Yes | Unique scan identifier |

#### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `confirm` | boolean | Yes | - | Must be `true` to confirm deletion |

#### Response (200 OK)
```json
{
  "status": "success",
  "message": "Scan and all associated data removed successfully",
  "data": {
    "scanId": "hubspot-deals-2025-11-10",
    "deletedRecords": {
      "scanJob": 1,
      "deals": 523,
      "associations": 1246
    },
    "deletedAt": "2025-11-10T17:00:00Z"
  },
  "timestamp": "2025-11-10T17:00:00Z"
}
```

#### Status Codes
- **200**: Scan removed successfully
- **404**: Scan not found
- **400**: Missing confirmation parameter
- **401**: Missing or invalid authentication
- **403**: Insufficient permissions

---

## 🏥 Health & Stats Endpoints

### 1. Health Check

**GET** `/health`

Returns the overall health status of the service.

#### Response (Healthy)
```json
{
  "status": "healthy",
  "service": "hubspot-deals-etl",
  "version": "1.0.0",
  "uptime": "5d 12h 34m",
  "timestamp": "2025-11-10T16:00:00Z",
  "dependencies": {
    "database": {
      "status": "healthy",
      "responseTime": "12ms"
    },
    "hubspot_api": {
      "status": "healthy",
      "responseTime": "245ms"
    }
  }
}
```

#### Response (Unhealthy)
```json
{
  "status": "unhealthy",
  "service": "hubspot-deals-etl",
  "version": "1.0.0",
  "timestamp": "2025-11-10T16:00:00Z",
  "dependencies": {
    "database": {
      "status": "unhealthy",
      "error": "Connection timeout",
      "responseTime": "5000ms"
    },
    "hubspot_api": {
      "status": "healthy",
      "responseTime": "245ms"
    }
  }
}
```

#### Status Codes
- **200**: Service is healthy
- **503**: Service is unhealthy

---

### 2. Service Statistics

**GET** `/api/v1/stats`

Returns aggregated statistics for the authenticated tenant.

#### Response (200 OK)
```json
{
  "status": "success",
  "data": {
    "tenantId": "tenant-abc-123",
    "scans": {
      "total": 47,
      "completed": 42,
      "running": 1,
      "failed": 4,
      "successRate": "89.4%"
    },
    "deals": {
      "totalExtracted": 24567,
      "averagePerScan": 523,
      "lastExtraction": "2025-11-10T16:00:00Z"
    },
    "performance": {
      "averageScanDuration": "7m 45s",
      "averageDealsPerMinute": 67,
      "fastestScan": "4m 12s",
      "slowestScan": "15m 32s"
    },
    "storage": {
      "totalRecords": 24567,
      "diskUsage": "2.4 GB",
      "avgRecordSize": "102 KB"
    }
  },
  "timestamp": "2025-11-10T16:00:00Z"
}
```

#### Status Codes
- **200**: Statistics retrieved successfully
- **401**: Missing or invalid authentication
- **403**: Insufficient permissions

---

## ⚠️ Error Handling

### Error Response Format
```json
{
  "status": "error",
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": [
      {
        "field": "config.auth.accessToken",
        "message": "Access token is required"
      }
    ],
    "correlationId": "uuid-error-123-abc"
  },
  "timestamp": "2025-11-10T16:00:00Z"
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request body validation failed |
| `UNAUTHORIZED` | 401 | Missing or invalid authentication token |
| `FORBIDDEN` | 403 | Insufficient permissions or wrong tenant |
| `NOT_FOUND` | 404 | Scan or resource not found |
| `CONFLICT` | 409 | Scan with this ID already exists |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests to API |
| `HUBSPOT_API_ERROR` | 502 | HubSpot API returned an error |
| `HUBSPOT_AUTH_ERROR` | 502 | HubSpot authentication failed |
| `HUBSPOT_RATE_LIMIT` | 502 | HubSpot rate limit exceeded |
| `DATABASE_ERROR` | 500 | Database operation failed |
| `INTERNAL_ERROR` | 500 | Unexpected server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

### HubSpot-Specific Errors

```json
{
  "status": "error",
  "error": {
    "code": "HUBSPOT_API_ERROR",
    "message": "HubSpot API request failed",
    "details": {
      "hubspotStatus": 401,
      "hubspotMessage": "This access token does not have proper permissions",
      "hubspotCorrelationId": "abc-123-def",
      "requiredScopes": ["crm.objects.deals.read"]
    },
    "correlationId": "uuid-error-456-xyz"
  },
  "timestamp": "2025-11-10T16:00:00Z"
}
```

---

## 📚 Examples

### Complete Extraction Workflow

#### 1. Start Extraction
```bash
curl -X POST "https://hubspot-deals-api.your-domain.com/api/v1/scan/start" \
  -H "Authorization: Bearer sk_live_abc123..." \
  -H "X-Tenant-ID: tenant-abc-123" \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "scanId": "weekly-deals-sync-001",
      "tenantId": "tenant-abc-123",
      "organizationId": "org-456",
      "auth": {
        "accessToken": "pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
      },
      "filters": {
        "pipeline": "default",
        "archived": false
      },
      "dateRange": {
        "startDate": "2025-01-01",
        "endDate": "2025-12-31"
      },
      "properties": [
        "dealname",
        "amount",
        "closedate",
        "dealstage",
        "pipeline",
        "hubspot_owner_id"
      ],
      "associations": ["contacts", "companies"],
      "batchSize": 100
    }
  }'
```

#### 2. Monitor Progress
```bash
curl "https://hubspot-deals-api.your-domain.com/api/v1/scan/status/weekly-deals-sync-001" \
  -H "Authorization: Bearer sk_live_abc123..." \
  -H "X-Tenant-ID: tenant-abc-123"
```

#### 3. Get Results
```bash
curl "https://hubspot-deals-api.your-domain.com/api/v1/scan/result/weekly-deals-sync-001?page=1&page_size=100" \
  -H "Authorization: Bearer sk_live_abc123..." \
  -H "X-Tenant-ID: tenant-abc-123"
```

#### 4. Download Results
```bash
# Download as CSV
curl "https://hubspot-deals-api.your-domain.com/api/v1/scan/download/weekly-deals-sync-001/csv" \
  -H "Authorization: Bearer sk_live_abc123..." \
  -H "X-Tenant-ID: tenant-abc-123" \
  -o "hubspot_deals_2025-11-10.csv"

# Download as Excel
curl "https://hubspot-deals-api.your-domain.com/api/v1/scan/download/weekly-deals-sync-001/excel" \
  -H "Authorization: Bearer sk_live_abc123..." \
  -H "X-Tenant-ID: tenant-abc-123" \
  -o "hubspot_deals_2025-11-10.xlsx"

# Download as JSON
curl "https://hubspot-deals-api.your-domain.com/api/v1/scan/download/weekly-deals-sync-001/json" \
  -H "Authorization: Bearer sk_live_abc123..." \
  -H "X-Tenant-ID: tenant-abc-123" \
  -o "hubspot_deals_2025-11-10.json"
```

#### 5. Cancel Extraction (if needed)
```bash
curl -X POST "https://hubspot-deals-api.your-domain.com/api/v1/scan/cancel/weekly-deals-sync-001" \
  -H "Authorization: Bearer sk_live_abc123..." \
  -H "X-Tenant-ID: tenant-abc-123"
```

#### 6. Remove Extraction (cleanup)
```bash
curl -X DELETE "https://hubspot-deals-api.your-domain.com/api/v1/scan/remove/weekly-deals-sync-001?confirm=true" \
  -H "Authorization: Bearer sk_live_abc123..." \
  -H "X-Tenant-ID: tenant-abc-123"
```

---

### PowerShell Examples

#### Start Extraction
```powershell
$headers = @{
    "Authorization" = "Bearer sk_live_abc123..."
    "X-Tenant-ID" = "tenant-abc-123"
    "Content-Type" = "application/json"
}

$body = @{
    config = @{
        scanId = "powershell-test-001"
        tenantId = "tenant-abc-123"
        auth = @{
            accessToken = "pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        }
        filters = @{
            pipeline = "default"
        }
        associations = @("contacts", "companies")
    }
} | ConvertTo-Json -Depth 5

$response = Invoke-RestMethod -Uri "https://hubspot-deals-api.your-domain.com/api/v1/scan/start" `
    -Method Post `
    -Headers $headers `
    -Body $body

Write-Host "Scan started: $($response.data.scanId)"
Write-Host "Status: $($response.data.status)"
```

#### Get Status
```powershell
$scanId = "powershell-test-001"
$response = Invoke-RestMethod -Uri "https://hubspot-deals-api.your-domain.com/api/v1/scan/status/$scanId" `
    -Headers $headers

Write-Host "Progress: $($response.data.progress.percentComplete)%"
Write-Host "Processed: $($response.data.progress.processedItems) / $($response.data.progress.totalItems)"
```

#### Download Results
```powershell
$scanId = "powershell-test-001"
$formats = @("json", "csv", "excel")

foreach ($format in $formats) {
    $extension = if ($format -eq "excel") { "xlsx" } else { $format }
    $filename = "hubspot_deals_results.$extension"
    
    Invoke-WebRequest -Uri "https://hubspot-deals-api.your-domain.com/api/v1/scan/download/$scanId/$format" `
        -Headers $headers `
        -OutFile $filename
    
    Write-Host "Downloaded: $filename"
}
```

---

### Python Examples

#### Start Extraction
```python
import requests

url = "https://hubspot-deals-api.your-domain.com/api/v1/scan/start"
headers = {
    "Authorization": "Bearer sk_live_abc123...",
    "X-Tenant-ID": "tenant-abc-123",
    "Content-Type": "application/json"
}
payload = {
    "config": {
        "scanId": "python-test-001",
        "tenantId": "tenant-abc-123",
        "auth": {
            "accessToken": "pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        },
        "filters": {
            "pipeline": "default",
            "archived": False
        },
        "associations": ["contacts", "companies"],
        "batchSize": 100
    }
}

response = requests.post(url, json=payload, headers=headers)
data = response.json()

print(f"Scan started: {data['data']['scanId']}")
print(f"Status: {data['data']['status']}")
print(f"Status URL: {data['data']['statusUrl']}")
```

#### Monitor Progress
```python
import requests
import time

scan_id = "python-test-001"
url = f"https://hubspot-deals-api.your-domain.com/api/v1/scan/status/{scan_id}"

while True:
    response = requests.get(url, headers=headers)
    data = response.json()['data']
    
    status = data['status']
    progress = data['progress']
    
    print(f"Status: {status} | Progress: {progress['percentComplete']}% | "
          f"Deals: {progress['processedItems']}/{progress['totalItems']}")
    
    if status in ['completed', 'failed', 'cancelled']:
        break
    
    time.sleep(5)  # Poll every 5 seconds
```

#### Get Paginated Results
```python
import requests

scan_id = "python-test-001"
page = 1
all_deals = []

while True:
    url = f"https://hubspot-deals-api.your-domain.com/api/v1/scan/result/{scan_id}"
    params = {"page": page, "page_size": 100}
    
    response = requests.get(url, params=params, headers=headers)
    data = response.json()['data']
    
    all_deals.extend(data['deals'])
    
    if not data['pagination']['has_next']:
        break
    
    page += 1

print(f"Total deals retrieved: {len(all_deals)}")
```

#### Download Results
```python
import requests

scan_id = "python-test-001"
formats = ['json', 'csv', 'excel']

for fmt in formats:
    url = f"https://hubspot-deals-api.your-domain.com/api/v1/scan/download/{scan_id}/{fmt}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        extension = 'xlsx' if fmt == 'excel' else fmt
        filename = f"hubspot_deals_results.{extension}"
        
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        print(f"Downloaded: {filename}")
    else:
        print(f"Failed to download {fmt}: {response.status_code}")
```

#### Error Handling
```python
import requests
from requests.exceptions import RequestException

try:
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    if data['status'] == 'success':
        print(f"Success: {data['message']}")
    else:
        print(f"Error: {data['error']['message']}")
        
except RequestException as e:
    print(f"Request failed: {str(e)}")
except ValueError as e:
    print(f"Invalid JSON response: {str(e)}")
```

---

## ⏱️ Rate Limiting

### Service Rate Limits
- **Default**: 100 requests per minute per tenant
- **Burst**: Up to 150 requests in short bursts
- **Scan Concurrency**: Max 5 concurrent scans per tenant

### Rate Limit Headers
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1699632000
Retry-After: 60
```

### Rate Limit Response (429)
```json
{
  "status": "error",
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Please retry after 60 seconds.",
    "retryAfter": 60
  },
  "timestamp": "2025-11-10T16:00:00Z"
}
```

### Best Practices
- Implement exponential backoff on 429 responses
- Cache scan status results (poll every 5-10 seconds)
- Use pagination for large result sets
- Download results in batches during off-peak hours
- Monitor rate limit headers and adjust request frequency

---

## 🔄 Changelog

### Version 1.0.0 (2025-11-10)
- Initial API release
- HubSpot Deals extraction endpoints
- Multi-tenant support
- Progress tracking and monitoring
- Multiple export formats (JSON, CSV, Excel)
- Comprehensive error handling
- Rate limiting implementation

---

**Document Status**: ✅ Complete  
**Last Updated**: November 10, 2025  
**API Version**: 1.0.0  
**Service**: HubSpot Deals ETL  
**Maintainer**: Data Engineering Team