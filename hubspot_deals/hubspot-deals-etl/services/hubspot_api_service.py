import requests
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import time
import json
from loki_logger import get_logger, log_api_call


class HubSpotAPIService:
    """
    Service for interacting with HubSpot CRM API v3 for deals extraction
    """
    
    def __init__(self, base_url: str = "https://api.hubapi.com", test_delay_seconds: float = 0):
        self.base_url = base_url.rstrip('/')
        self.test_delay_seconds = test_delay_seconds
        self.logger = get_logger(__name__)
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'HubSpot-Deals-Extraction-Service/1.0'
        })
        
        self.logger.debug(
            "HubSpot API service initialized",
            extra={
                'operation': 'hubspot_api_service_init',
                'base_url': base_url,
                'test_delay_seconds': test_delay_seconds
            }
        )
    
    def set_access_token(self, token: str):
        """Set the HubSpot API access token"""
        self.session.headers.update({
            'Authorization': f'Bearer {token}'
        })
        self.logger.debug("Access token set", extra={'operation': 'token_set'})
    
    def get_deal_properties(self, access_token: str) -> Dict[str, Any]:
        """
        Get all available deal properties from HubSpot
        """
        self.set_access_token(access_token)
        start_time = datetime.utcnow()
        
        try:
            url = f"{self.base_url}/crm/v3/properties/deals"
            
            self.logger.info(
                "Fetching deal properties",
                extra={'operation': 'get_deal_properties'}
            )
            
            response = self.session.get(url)
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('X-HubSpot-RateLimit-Interval-Milliseconds', 10000)) / 1000
                self.logger.warning(
                    f"Rate limited getting deal properties, retrying after {retry_after} seconds",
                    extra={'operation': 'get_deal_properties', 'retry_after': retry_after}
                )
                time.sleep(retry_after)
                response = self.session.get(url)
            
            response.raise_for_status()
            data = response.json()
            
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            self.logger.info(
                f"Retrieved {len(data.get('results', []))} deal properties",
                extra={
                    'operation': 'get_deal_properties',
                    'property_count': len(data.get('results', [])),
                    'duration_ms': round(duration_ms, 2)
                }
            )
            
            log_api_call(
                self.logger,
                "hubspot_get_deal_properties",
                method='GET',
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2)
            )
            
            return data
            
        except requests.exceptions.RequestException as e:
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.logger.error(
                f"Failed to get deal properties: {e}",
                extra={'operation': 'get_deal_properties', 'error': str(e), 'duration_ms': round(duration_ms, 2)},
                exc_info=True
            )
            raise
    
    def get_deals(self, 
                  access_token: str, 
                  limit: int = 100,
                  after: Optional[str] = None,
                  properties: Optional[List[str]] = None,
                  associations: Optional[List[str]] = None,
                  **kwargs) -> Dict[str, Any]:
        """
        Get deals from HubSpot CRM with pagination support
        
        Args:
            access_token: HubSpot access token
            limit: Number of deals to retrieve (max 100)
            after: Pagination cursor for next page
            properties: List of deal properties to retrieve
            associations: List of associations to include (e.g., ['contacts', 'companies'])
            **kwargs: Additional parameters for filtering
        
        Returns:
            Dict containing deals data and pagination info
        """
        self.set_access_token(access_token)
        start_time = datetime.utcnow()
        
        try:
            # Add test delay if configured
            if self.test_delay_seconds > 0:
                self.logger.info(
                    f"Test delay: sleeping for {self.test_delay_seconds} seconds",
                    extra={'operation': 'get_deals', 'delay_type': 'test_delay'}
                )
                time.sleep(self.test_delay_seconds)
            
            # Build URL - HubSpot CRM v3 deals endpoint
            url = f"{self.base_url}/crm/v3/objects/deals"
            
            # Build parameters
            params = {
                'limit': min(limit, 100)  # HubSpot max limit is 100
            }
            
            if after:
                params['after'] = after
            
            # Add properties to retrieve
            if properties:
                params['properties'] = ','.join(properties)
            else:
                # Default properties
                params['properties'] = 'dealname,amount,dealstage,pipeline,closedate,createdate,hs_lastmodifieddate'
            
            # Add associations
            if associations:
                params['associations'] = ','.join(associations)
            
            self.logger.info(
                "Fetching deals from HubSpot",
                extra={
                    'operation': 'get_deals',
                    'limit': params['limit'],
                    'has_cursor': after is not None,
                    'properties_count': len(properties) if properties else 'default'
                }
            )
            
            response = self.session.get(url, params=params)
            
            # Handle rate limiting - HubSpot specific
            if response.status_code == 429:
                retry_after = int(response.headers.get('X-HubSpot-RateLimit-Interval-Milliseconds', 10000)) / 1000
                self.logger.warning(
                    f"Rate limited getting deals, retrying after {retry_after} seconds",
                    extra={
                        'operation': 'get_deals',
                        'retry_after': retry_after,
                        'status_code': 429
                    }
                )
                time.sleep(retry_after)
                response = self.session.get(url, params=params)
            
            response.raise_for_status()
            result = response.json()
            
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            deal_count = len(result.get('results', []))
            
            self.logger.info(
                "Deals retrieved successfully",
                extra={
                    'operation': 'get_deals',
                    'status_code': response.status_code,
                    'duration_ms': round(duration_ms, 2),
                    'deal_count': deal_count,
                    'has_more': result.get('paging', {}).get('next') is not None
                }
            )
            
            log_api_call(
                self.logger,
                "hubspot_get_deals",
                method='GET',
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2)
            )
            
            return result
            
        except requests.exceptions.RequestException as e:
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            self.logger.error(
                "Error fetching deals",
                extra={
                    'operation': 'get_deals',
                    'error': str(e),
                    'duration_ms': round(duration_ms, 2),
                    'status_code': getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
                },
                exc_info=True
            )
            
            log_api_call(
                self.logger,
                "hubspot_get_deals",
                method='GET',
                status_code=getattr(e.response, 'status_code', None) if hasattr(e, 'response') else 500,
                duration_ms=round(duration_ms, 2)
            )
            
            raise
    
    def get_deal_by_id(self, access_token: str, deal_id: str, 
                       properties: Optional[List[str]] = None,
                       associations: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """
        Get a specific deal by ID
        """
        self.set_access_token(access_token)
        
        url = f"{self.base_url}/crm/v3/objects/deals/{deal_id}"
        params = {}
        
        if properties:
            params['properties'] = ','.join(properties)
        
        if associations:
            params['associations'] = ','.join(associations)
        
        try:
            response = self.session.get(url, params=params)
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('X-HubSpot-RateLimit-Interval-Milliseconds', 10000)) / 1000
                time.sleep(retry_after)
                response = self.session.get(url, params=params)
            
            # Handle 404 - deal not found
            if response.status_code == 404:
                self.logger.warning(
                    f"Deal not found: {deal_id}",
                    extra={'operation': 'get_deal_by_id', 'deal_id': deal_id}
                )
                return None
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(
                f"Failed to get deal {deal_id}: {e}",
                extra={'operation': 'get_deal_by_id', 'deal_id': deal_id, 'error': str(e)}
            )
            raise
    
    def validate_credentials(self, access_token: str) -> bool:
        """
        Validate HubSpot access token by making a test API call
        """
        try:
            self.logger.info(
                "Validating HubSpot credentials",
                extra={'operation': 'validate_credentials'}
            )
            
            self.set_access_token(access_token)
            
            # Test by getting deal properties (lightweight call)
            url = f"{self.base_url}/crm/v3/properties/deals"
            params = {'limit': 1}
            
            response = self.session.get(url, params=params)
            is_valid = response.status_code == 200
            
            if is_valid:
                self.logger.info(
                    "Credentials validated successfully",
                    extra={'operation': 'validate_credentials'}
                )
            else:
                self.logger.warning(
                    "Credential validation failed",
                    extra={
                        'operation': 'validate_credentials',
                        'status_code': response.status_code
                    }
                )
            
            return is_valid
            
        except requests.exceptions.RequestException as e:
            self.logger.error(
                "Credential validation error",
                extra={'operation': 'validate_credentials', 'error': str(e)},
                exc_info=True
            )
            return False
    
    def get_account_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get HubSpot account information
        """
        try:
            self.set_access_token(access_token)
            
            # Get account details using the account-info endpoint
            url = f"{self.base_url}/integrations/v1/me"
            response = self.session.get(url)
            
            if response.status_code == 200:
                account_info = response.json()
                self.logger.debug(
                    "Account info retrieved",
                    extra={
                        'operation': 'get_account_info',
                        'portal_id': account_info.get('portalId'),
                        'hub_domain': account_info.get('hubDomain')
                    }
                )
                return account_info
            
            return None
            
        except requests.exceptions.RequestException as e:
            self.logger.debug(
                "Account info not available",
                extra={'operation': 'get_account_info', 'error': str(e)}
            )
            return None
    
    def get_api_usage(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get API usage information from HubSpot response headers
        """
        try:
            self.set_access_token(access_token)
            
            # Make a lightweight API call to get rate limit headers
            url = f"{self.base_url}/crm/v3/properties/deals"
            params = {'limit': 1}
            
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                usage_info = {}
                
                # Extract HubSpot rate limit headers
                rate_limit_headers = [
                    'X-HubSpot-RateLimit-Daily',
                    'X-HubSpot-RateLimit-Daily-Remaining',
                    'X-HubSpot-RateLimit-Interval-Milliseconds',
                    'X-HubSpot-RateLimit-Max',
                    'X-HubSpot-RateLimit-Remaining',
                    'X-HubSpot-RateLimit-Secondly',
                    'X-HubSpot-RateLimit-Secondly-Remaining'
                ]
                
                for header in rate_limit_headers:
                    if header in response.headers:
                        usage_info[header] = response.headers[header]
                
                if usage_info:
                    usage_info['timestamp'] = datetime.now(timezone.utc).isoformat()
                    
                    self.logger.debug(
                        "API usage info retrieved",
                        extra={
                            'operation': 'get_api_usage',
                            'daily_remaining': usage_info.get('X-HubSpot-RateLimit-Daily-Remaining'),
                            'interval_remaining': usage_info.get('X-HubSpot-RateLimit-Remaining')
                        }
                    )
                    
                    return usage_info
                    
            return None
            
        except requests.exceptions.RequestException as e:
            self.logger.warning(
                "Could not retrieve API usage",
                extra={'operation': 'get_api_usage', 'error': str(e)}
            )
            return None
    
    def test_connection(self, access_token: str) -> Dict[str, Any]:
        """
        Test connection to HubSpot API
        """
        self.logger.info(
            "Testing HubSpot API connection",
            extra={'operation': 'test_connection'}
        )
        
        results = {
            'token_valid': False,
            'api_reachable': False,
            'data_accessible': False,
            'account_info': None,
            'usage_info': None,
            'error': None
        }
        
        try:
            # Test token validation
            results['token_valid'] = self.validate_credentials(access_token)
            results['api_reachable'] = results['token_valid']
            
            if results['token_valid']:
                # Get additional info
                results['account_info'] = self.get_account_info(access_token)
                results['usage_info'] = self.get_api_usage(access_token)
                
                # Test basic data access
                try:
                    test_data = self.get_deals(access_token, limit=1)
                    results['data_accessible'] = True
                    
                    self.logger.info(
                        "Connection test successful",
                        extra={
                            'operation': 'test_connection',
                            'token_valid': results['token_valid'],
                            'data_accessible': results['data_accessible']
                        }
                    )
                    
                except Exception as e:
                    self.logger.warning(
                        "Data access test failed",
                        extra={'operation': 'test_connection', 'error': str(e)}
                    )
            else:
                self.logger.warning(
                    "Connection test failed - invalid token",
                    extra={'operation': 'test_connection'}
                )
                
        except Exception as e:
            results['error'] = str(e)
            self.logger.error(
                "Connection test error",
                extra={'operation': 'test_connection', 'error': str(e)},
                exc_info=True
            )
        
        return results