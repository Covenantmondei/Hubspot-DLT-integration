
# 📋 HubSpot Deals - Integration with HubSpot CRM API v3

## 📋 Overview

This document details the integration with **HubSpot CRM API v3** for extracting **Deal** data. HubSpot Deals represent potential revenue opportunities tracked in your CRM.

### ✅ **Required Endpoint (Essential)**
| **API Endpoint**                    | **Purpose**                          | **Version** | **Required Permissions** | **Usage**    |
|-------------------------------------|--------------------------------------|-------------|--------------------------|--------------|
| `/crm/v3/objects/deals`             | Search and list deals                | v3          | `crm.objects.deals.read` | **Required** |

### 🔧 **Optional Endpoints (Advanced Features)**
| **API Endpoint**                    | **Purpose**                          | **Version** | **Required Permissions** | **Usage**    |
|-------------------------------------|--------------------------------------|-------------|--------------------------|--------------|
| `/crm/v3/objects/deals/{dealId}`    | Get detailed deal information        | v3          | `crm.objects.deals.read` | Optional     |
| `/crm/v3/objects/deals/{dealId}/associations` | Get deal associations      | v3          | `crm.objects.deals.read` | Optional     |
| `/crm/v3/objects/deals/batch/read`  | Batch read multiple deals            | v3          | `crm.objects.deals.read` | Optional     |
| `/crm/v3/pipelines/deals`           | Get deal pipelines configuration     | v3          | `crm.objects.deals.read` | Optional     |

---

## 🔐 Authentication

### **Method**: Private App Access Token (Recommended)

HubSpot uses **Bearer Token authentication** with Private App Access Tokens.

**Steps to get your Access Token:**
1. Go to **Settings** → **Integrations** → **Private Apps** in your HubSpot account
2. Click **Create a private app**
3. Configure the app with required scopes: `crm.objects.deals.read`
4. Generate and copy the **Access Token**

**Authentication Header:**
```http
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Security Best Practices:**
- Store access tokens securely (environment variables, secrets manager)
- Use separate tokens for dev/staging/production
- Rotate tokens periodically
- Never commit tokens to version control
- Monitor token usage through HubSpot's API logs

---

## 🌐 HubSpot CRM API v3 Endpoints

### 1. **Search Deals** - `/crm/v3/objects/deals` ✅ **REQUIRED**

**Purpose**: Retrieve a paginated list of deals with configurable properties

**Method**: `GET`

**Base URL**: `https://api.hubapi.com/crm/v3/objects/deals`

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | No | 10 | Number of deals per page (max: 100) |
| `after` | string | No | - | Pagination cursor from previous response |
| `properties` | string | No | - | Comma-separated list of properties to return |
| `associations` | string | No | - | Comma-separated list of object types to retrieve associations for |
| `archived` | boolean | No | false | Include archived deals |

**Request Example:**
```http
GET https://api.hubapi.com/crm/v3/objects/deals?limit=50&properties=dealname,amount,closedate,dealstage,pipeline&associations=contacts,companies
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Response Structure:**
```json
{
  "results": [
    {
      "id": "12345678901",
      "properties": {
        "amount": "50000",
        "closedate": "2025-12-31T00:00:00.000Z",
        "createdate": "2025-01-15T10:30:00.000Z",
        "dealname": "Enterprise Software Deal - Acme Corp",
        "dealstage": "appointmentscheduled",
        "hs_lastmodifieddate": "2025-11-10T15:45:00.000Z",
        "hs_object_id": "12345678901",
        "pipeline": "default",
        "hubspot_owner_id": "98765432"
      },
      "createdAt": "2025-01-15T10:30:00.000Z",
      "updatedAt": "2025-11-10T15:45:00.000Z",
      "archived": false,
      "associations": {
        "contacts": {
          "results": [
            {
              "id": "1001",
              "type": "deal_to_contact"
            }
          ]
        },
        "companies": {
          "results": [
            {
              "id": "2001",
              "type": "deal_to_company"
            }
          ]
        }
      }
    },
    {
      "id": "12345678902",
      "properties": {
        "amount": "25000",
        "closedate": "2025-11-30T00:00:00.000Z",
        "createdate": "2025-02-20T14:15:00.000Z",
        "dealname": "Q4 Consulting Services - TechStart Inc",
        "dealstage": "qualifiedtobuy",
        "hs_lastmodifieddate": "2025-11-09T09:20:00.000Z",
        "hs_object_id": "12345678902",
        "pipeline": "default",
        "hubspot_owner_id": "98765433"
      },
      "createdAt": "2025-02-20T14:15:00.000Z",
      "updatedAt": "2025-11-09T09:20:00.000Z",
      "archived": false
    }
  ],
  "paging": {
    "next": {
      "after": "NTI1Cg%3D%3D",
      "link": "https://api.hubapi.com/crm/v3/objects/deals?after=NTI1Cg%3D%3D&limit=50"
    }
  }
}
```

**✅ This endpoint provides ALL the default deal fields:**
- Deal ID, Deal Name, Amount, Close Date
- Deal Stage, Pipeline, Hubspot Owner ID
- Create Date, Last Modified Date
- Custom properties if specified
- Associations with Contacts, Companies, Line Items
- Archived status

**Rate Limit**: 100 requests per 10 seconds per access token

---

## 🔧 **OPTIONAL ENDPOINTS (Advanced Features Only)**

### 2. **Get Deal Details** - `/crm/v3/objects/deals/{dealId}` 🔧 **OPTIONAL**

**Purpose**: Get detailed information for a specific deal

**When to use**: Only if you need additional deal metadata not available in search

**Method**: `GET`

**URL**: `https://api.hubapi.com/crm/v3/objects/deals/{dealId}`

**Request Example**:
```http
GET https://api.hubapi.com/crm/v3/objects/deals/12345678901?properties=dealname,amount,dealstage,num_contacted_notes,notes_last_contacted
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Response Structure**:
```json
{
  "id": "12345678901",
  "properties": {
    "amount": "50000",
    "closedate": "2025-12-31T00:00:00.000Z",
    "createdate": "2025-01-15T10:30:00.000Z",
    "dealname": "Enterprise Software Deal - Acme Corp",
    "dealstage": "appointmentscheduled",
    "hs_lastmodifieddate": "2025-11-10T15:45:00.000Z",
    "hs_object_id": "12345678901",
    "pipeline": "default",
    "hubspot_owner_id": "98765432",
    "num_contacted_notes": "5",
    "notes_last_contacted": "2025-11-08T14:30:00.000Z"
  },
  "createdAt": "2025-01-15T10:30:00.000Z",
  "updatedAt": "2025-11-10T15:45:00.000Z",
  "archived": false
}
```

**Rate Limit**: 100 requests per 10 seconds

---

### 3. **Get Deal Associations** - `/crm/v3/objects/deals/{dealId}/associations/{toObjectType}` 🔧 **OPTIONAL**

**Purpose**: Get all associations for a specific deal

**When to use**: For detailed relationship analysis between deals and other objects

**Method**: `GET`

**URL**: `https://api.hubapi.com/crm/v3/objects/deals/{dealId}/associations/{toObjectType}`

**Object Types**: `contacts`, `companies`, `line_items`, `tickets`, `engagements`

**Request Example**:
```http
GET https://api.hubapi.com/crm/v3/objects/deals/12345678901/associations/contacts
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Response Structure**:
```json
{
  "results": [
    {
      "id": "1001",
      "type": "deal_to_contact"
    },
    {
      "id": "1002",
      "type": "deal_to_contact"
    }
  ],
  "paging": {
    "next": {
      "after": "string"
    }
  }
}
```

**Rate Limit**: 100 requests per 10 seconds

---

### 4. **Batch Read Deals** - `/crm/v3/objects/deals/batch/read` 🔧 **OPTIONAL**

**Purpose**: Retrieve multiple deals by ID in a single request

**When to use**: Efficient bulk retrieval of specific deals

**Method**: `POST`

**URL**: `https://api.hubapi.com/crm/v3/objects/deals/batch/read`

**Request Body**:
```json
{
  "properties": ["dealname", "amount", "closedate", "dealstage"],
  "inputs": [
    {"id": "12345678901"},
    {"id": "12345678902"},
    {"id": "12345678903"}
  ]
}
```

**Response Structure**:
```json
{
  "status": "COMPLETE",
  "results": [
    {
      "id": "12345678901",
      "properties": {
        "dealname": "Enterprise Software Deal",
        "amount": "50000",
        "closedate": "2025-12-31T00:00:00.000Z",
        "dealstage": "appointmentscheduled"
      },
      "createdAt": "2025-01-15T10:30:00.000Z",
      "updatedAt": "2025-11-10T15:45:00.000Z",
      "archived": false
    }
  ],
  "startedAt": "2025-11-10T16:00:00.000Z",
  "completedAt": "2025-11-10T16:00:01.000Z"
}
```

**Limits**: Maximum 100 deals per batch request

**Rate Limit**: 100 requests per 10 seconds

---

### 5. **Get Deal Pipelines** - `/crm/v3/pipelines/deals` 🔧 **OPTIONAL**

**Purpose**: Get all deal pipelines and their stages configuration

**When to use**: For pipeline analysis and deal stage mapping

**Method**: `GET`

**URL**: `https://api.hubapi.com/crm/v3/pipelines/deals`

**Request Example**:
```http
GET https://api.hubapi.com/crm/v3/pipelines/deals
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Response Structure**:
```json
{
  "results": [
    {
      "id": "default",
      "label": "Sales Pipeline",
      "displayOrder": 0,
      "stages": [
        {
          "id": "appointmentscheduled",
          "label": "Appointment Scheduled",
          "displayOrder": 0,
          "metadata": {
            "probability": "0.2"
          }
        },
        {
          "id": "qualifiedtobuy",
          "label": "Qualified to Buy",
          "displayOrder": 1,
          "metadata": {
            "probability": "0.4"
          }
        },
        {
          "id": "presentationscheduled",
          "label": "Presentation Scheduled",
          "displayOrder": 2,
          "metadata": {
            "probability": "0.6"
          }
        },
        {
          "id": "closedwon",
          "label": "Closed Won",
          "displayOrder": 3,
          "metadata": {
            "probability": "1.0",
            "isClosed": "true"
          }
        }
      ],
      "createdAt": "2020-01-01T00:00:00.000Z",
      "updatedAt": "2025-01-01T00:00:00.000Z",
      "archived": false
    }
  ]
}
```

**Rate Limit**: 100 requests per 10 seconds

---

## 📊 Available Deal Properties

### **Standard Deal Properties** (Always Available)

| Property Name | Field Type | Description |
|---------------|------------|-------------|
| `dealname` | string | Name of the deal |
| `amount` | string | Monetary value of the deal |
| `closedate` | datetime | Expected close date |
| `pipeline` | string | Pipeline ID the deal belongs to |
| `dealstage` | string | Current stage in the pipeline |
| `hubspot_owner_id` | string | ID of the deal owner |
| `createdate` | datetime | Date deal was created |
| `hs_lastmodifieddate` | datetime | Last modification timestamp |
| `hs_object_id` | string | Unique HubSpot deal ID |
| `dealtype` | enumeration | Type of deal (newbusiness, existingbusiness, etc.) |

### **Additional Standard Properties**

| Property Name | Field Type | Description |
|---------------|------------|-------------|
| `amount_in_home_currency` | string | Deal amount in portal currency |
| `hs_analytics_source` | enumeration | Original source of the deal |
| `hs_analytics_source_data_1` | string | Drill-down 1 on original source |
| `hs_analytics_source_data_2` | string | Drill-down 2 on original source |
| `hs_campaign` | string | HubSpot campaign GUID |
| `hs_closed_amount` | number | Deal amount if closed won |
| `hs_closed_amount_in_home_currency` | number | Closed amount in home currency |
| `hs_deal_stage_probability` | number | Probability of deal closing (0-1) |
| `hs_forecast_amount` | number | Weighted forecast amount |
| `hs_forecast_probability` | number | Forecast probability |
| `hs_is_closed` | boolean | Whether deal is closed |
| `hs_is_closed_won` | boolean | Whether deal is closed won |
| `hs_manual_forecast_category` | enumeration | Manual forecast category |
| `hs_mrr` | number | Monthly recurring revenue |
| `hs_next_step` | string | Next step in the sales process |
| `hs_num_associated_contacts` | number | Number of associated contacts |
| `hs_num_associated_companies` | number | Number of associated companies |
| `hs_priority` | enumeration | Deal priority (low, medium, high) |
| `hs_projected_amount` | number | Projected deal amount |
| `hs_projected_amount_in_home_currency` | number | Projected amount in home currency |
| `hs_tcv` | number | Total contract value |

### **Engagement & Activity Properties**

| Property Name | Field Type | Description |
|---------------|------------|-------------|
| `notes_last_contacted` | datetime | Last contact note timestamp |
| `notes_last_updated` | datetime | Last note update timestamp |
| `notes_next_activity_date` | datetime | Next planned activity date |
| `num_contacted_notes` | number | Number of contact notes |
| `num_notes` | number | Total number of notes |
| `hs_num_of_associated_line_items` | number | Number of line items |
| `hs_latest_meeting_activity` | datetime | Latest meeting activity |
| `hs_sales_email_last_replied` | datetime | Last sales email reply |

### **Custom Properties**

Custom properties created in your HubSpot portal can be retrieved by using their internal property name (e.g., `custom_property_name`).

**To get all properties including custom ones:**
```http
GET https://api.hubapi.com/crm/v3/properties/deals
Authorization: Bearer YOUR_ACCESS_TOKEN
```

---

## ⚡ Performance Considerations

### **Rate Limiting**
- **Default Limit**: 100 requests per 10 seconds per access token
- **Burst Limit**: Up to 150 requests in short bursts (monitored over 10-second windows)
- **Best Practice**: Implement exponential backoff on 429 responses

**Rate Limit Headers:**
```http
X-HubSpot-RateLimit-Daily: 500000
X-HubSpot-RateLimit-Daily-Remaining: 499950
X-HubSpot-RateLimit-Interval-Milliseconds: 10000
X-HubSpot-RateLimit-Max: 100
X-HubSpot-RateLimit-Remaining: 99
X-HubSpot-RateLimit-Secondly: 10
X-HubSpot-RateLimit-Secondly-Remaining: 9
```

### **Batch Processing**
- **Recommended Batch Size**: 100 deals per request (API maximum)
- **Concurrent Requests**: Max 3-5 parallel requests to stay under rate limits
- **Request Interval**: 100ms between requests for optimal throughput

### **Pagination Best Practices**
- Always use the `after` cursor from the previous response
- Don't rely on offset-based pagination
- Store the pagination state for resumable extractions
- Handle the last page (no `paging.next` object)

### **Error Handling**
```http
# Rate limit exceeded
HTTP/429 Too Many Requests
X-HubSpot-RateLimit-Remaining: 0
Retry-After: 1

# Authentication failed  
HTTP/401 Unauthorized
{
  "status": "error",
  "message": "This request requires authentication",
  "correlationId": "abc-123-def"
}

# Insufficient permissions
HTTP/403 Forbidden
{
  "status": "error",
  "message": "This access token does not have proper permissions",
  "correlationId": "abc-123-def"
}

# Deal not found
HTTP/404 Not Found
{
  "status": "error",
  "message": "resource not found",
  "correlationId": "abc-123-def"
}

# Invalid request
HTTP/400 Bad Request
{
  "status": "error",
  "message": "Property values were not valid",
  "correlationId": "abc-123-def",
  "validationResults": [
    {
      "isValid": false,
      "message": "Property \"amount\" is invalid",
      "error": "INVALID_PROPERTY"
    }
  ]
}
```

---

## 📈 Monitoring & Debugging

### **Logging Best Practices**
- Log all API requests with timestamps
- Track rate limit headers in every response
- Monitor authentication failures
- Log pagination cursors for resumability
- Track extraction duration and record counts

### **API Usage Metrics**
- Track requests per 10-second window
- Monitor daily request consumption
- Log response times and identify slow endpoints
- Track authentication failures
- Monitor 429 rate limit responses

### **Debugging Tools**
- Use HubSpot's API logs in Settings → Integrations → API Key/Private Apps
- Check correlation IDs in error responses
- Monitor webhook notifications for data changes
- Use HubSpot's API Status page: https://status.hubspot.com

---

## 💡 **Implementation Recommendations**

### 🎯 **Phase 1: Start Simple (Recommended)**
1. Implement only `/crm/v3/objects/deals` endpoint
2. Extract basic deal data (dealname, amount, closedate, dealstage, pipeline)
3. Include standard associations (contacts, companies)
4. This covers 90% of deal analytics needs

### 🔧 **Phase 2: Add Advanced Features (If Needed)**
1. Add `/crm/v3/objects/deals/{dealId}` for detailed deal metadata
2. Add `/crm/v3/objects/deals/batch/read` for efficient bulk retrieval
3. Add `/crm/v3/pipelines/deals` for pipeline configuration analysis
4. Add specific association endpoints for deep relationship analysis

### ⚡ **Performance Tip**
- **Simple approach**: 1 API call per 100 deals (using search endpoint)
- **Advanced approach**: 1 + N API calls (N = number of deals needing detailed metadata)
- Start simple to minimize API usage and complexity!

---

## 📞 Support Resources

- **HubSpot API Documentation**: https://developers.hubspot.com/docs/api/crm/deals
- **Rate Limiting Guide**: https://developers.hubspot.com/docs/api/usage-details
- **Authentication Guide**: https://developers.hubspot.com/docs/api/private-apps
- **Deal Permissions Reference**: https://knowledge.hubspot.com/settings/hubspot-user-permissions-guide
- **API Status**: https://status.hubspot.com
- **Developer Forum**: https://community.hubspot.com/t5/APIs-Integrations/ct-p/APIs

---

## 🔄 Changelog

### Version 1.0 (2025-11-10)
- Initial documentation for HubSpot Deals API v3 integration
- Documented primary `/crm/v3/objects/deals` endpoint
- Added optional endpoints for advanced features
- Documented all standard deal properties
- Added rate limiting and error handling guidelines
- Included implementation recommendations

---

**Document Status**: ✅ Complete  
**Last Updated**: November 10, 2025  
**API Version**: HubSpot CRM API v3  
**Maintainer**: Data Engineering Team