"""
Rappi scraper implementation (Enhanced with discount tracking).

This module uses Rappi's brand API endpoint and captures comprehensive data including
discount tags, real prices, promotional offers, and product availability.
"""

import requests
from typing import Any, Dict, List, Optional
from datetime import datetime
from scrapers.base_scraper import BaseScraper
from utils.logger import get_logger


class RappiScraper(BaseScraper):
    """
    Enhanced Rappi scraper for McDonald's data collection.
    
    Captures comprehensive metrics:
    - Product prices (price, real_price, discounted_price)
    - Discount information (percentage, type, global offers)
    - Store-level discount tags (free shipping, promos)
    - Delivery fees and ETAs
    - Product availability status
    - Schedules and operating hours
    """
    
    def __init__(
        self, 
        lat: float, 
        lon: float, 
        neighborhood: Optional[str] = None
    ) -> None:
        """Initialize Rappi scraper with coordinates."""
        super().__init__(lat, lon, neighborhood)
        self.platform = "Rappi"
        self.logger = get_logger()
    
    def _build_headers(self) -> Dict[str, str]:
        """Build HTTP headers for API request."""
        return {
            "accept": "application/json",
            "accept-language": "es-MX",
            "access-control-allow-headers": "*",
            "access-control-allow-origin": "*",
            "app-version": "1.161.2",
            "app-version-name": "1.161.2",
            "authorization": "Bearer ft.gAAAAABpzbFEKiM5V5VTXffVdHNiqnSkh8I6IDSBAqVz2u7h3QyrE6c6wCTn1szemrENBbGEnLYgWmBTsNtvyrBP-3fCcgWUerzXAGi-GYRXOTQCQTlIjk9AiHhtHJx9o069xAQaCY5PgHMIA7v4Qv035wlaZSh8b74BqKAP5qj797OKBODhQE3WYUiD0Dbir_Q3rMbEpQ1AIt4NwUEDAn2cwYy4QAEoKBIRaiwS95Nbem8z0_3KI5_TVHqTz3M4wp7aEf_KhvuOvyqTx0ngQcR9KvIL8yoWf3n3BVAubQ3knENGcHdYlmrM-6y0HjaJ3NW2XlM8yRWmxzgrpzkYsvUpqQh1d01MhaRAUGpley5_hAKxqhiVYvtXvPEo8AOhvbetyadBAO73eRO6SigI9A3x0ttl3lOz7w==",
            "content-type": "application/json; charset=UTF-8",
            "deviceid": "1bb7b5e1-840d-4f83-b2ca-df193b55646bR",
            "needappsflyerid": "false",
            "origin": "https://www.rappi.com.mx",
            "priority": "u=1, i",
            "referer": "https://www.rappi.com.mx/",
            "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        }
    
    def _build_payload(self) -> Dict[str, Any]:
        """Build JSON payload with dynamic coordinates."""
        return {
            "lat": self.lat,
            "lng": self.lon,
            "store_type": "restaurant",
            "is_prime": False,
            "prime_config": {
                "unlimited_shipping": False
            }
        }
    
    def fetch_data(self) -> Optional[Dict[str, Any]]:
        """
        Fetch data from Rappi brand API.
        
        Returns:
            JSON response if successful, None otherwise
        """
        # Using brand endpoint (stable, captures full data including discounts)
        brand_id = "706"  # McDonald's brand ID
        url = f"https://services.mxgrability.rappi.com/api/restaurant-bus/store/brand/id/{brand_id}"
        
        self.logger.info(f"{self.platform}: Fetching data for brand {brand_id}")
        self.logger.debug(f"{self.platform}: Request URL: {url}")
        self.logger.debug(f"{self.platform}: Coordinates: lat={self.lat}, lon={self.lon}")
        
        try:
            response = requests.post(
                url,
                headers=self._build_headers(),
                json=self._build_payload(),
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info(f"{self.platform}: Successfully fetched data")
                return response.json()
            else:
                self.logger.error(
                    f"{self.platform}: API returned status {response.status_code}"
                )
                return None
                
        except requests.Timeout:
            self.logger.error(f"{self.platform}: Request timeout")
            return None
        except requests.RequestException as e:
            self.logger.error(f"{self.platform}: Request failed - {e}")
            return None
        except Exception as e:
            self.logger.error(f"{self.platform}: Unexpected error - {e}")
            return None
    
    def parse_data(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse API response to extract enhanced product data.
        
        Args:
            raw_data: Raw JSON from API
            
        Returns:
            List of product dictionaries with enhanced fields
        """
        self.logger.info(f"{self.platform}: Parsing API response")
        
        products_found = []
        
        try:
            # Extract store-level info
            delivery_fee = raw_data.get('delivery_price', 0)
            eta_min = raw_data.get('eta', 'Unknown')
            
            # Convert eta to string
            if isinstance(eta_min, (int, float)):
                eta_str = f"{int(eta_min)} min"
            else:
                eta_str = str(eta_min)
            
            # Extract store-level discount tags
            discount_tags = raw_data.get('discount_tags', [])
            store_discounts_summary = []
            for tag in discount_tags[:3]:  # Top 3 discounts
                store_discounts_summary.append({
                    'type': tag.get('type', ''),
                    'value': tag.get('value', 0),
                    'tag': tag.get('tag', '')
                })
            
            self.logger.debug(
                f"{self.platform}: Store info - "
                f"delivery_fee={delivery_fee}, eta={eta_str}, "
                f"discount_tags={len(discount_tags)}"
            )
            
            # Search for products in corridors
            corridors = raw_data.get('corridors', [])
            target_keywords = ['Big Mac', '10 McNuggets', 'McNuggets']
            
            for corridor in corridors:
                products = corridor.get('products', [])
                
                for product in products:
                    product_name = product.get('name', '')
                    
                    # Check if product matches target keywords
                    if any(keyword.lower() in product_name.lower() 
                           for keyword in target_keywords):
                        
                        # Extract pricing info
                        price = product.get('price')
                        real_price = product.get('real_price')
                        discount_percentage = product.get('discount_percentage', 0)
                        is_available = product.get('is_available', False)
                        
                        # Extract product-level discounts
                        product_discounts = product.get('discounts', [])
                        has_discount = len(product_discounts) > 0
                        discount_type = None
                        discounted_price = None
                        
                        if product_discounts:
                            discount_type = product_discounts[0].get('type', '')
                            discounted_price = product_discounts[0].get('price')
                        
                        # If unavailable, price will be None but we keep real_price & discount info
                        if not is_available:
                            self.logger.warning(
                                f"{self.platform}: Product '{product_name}' found but unavailable"
                            )
                            price = None
                            # Calculate theoretical discounted price for competitive analysis
                            if real_price and discount_percentage > 0:
                                discounted_price = round(real_price * (1 - discount_percentage/100), 2)
                        
                        self.logger.info(
                            f"{self.platform}: Found '{product_name}' - "
                            f"price={price}, real_price={real_price}, "
                            f"discount={discount_percentage}%, available={is_available}"
                        )
                        
                        # Build enhanced product record
                        product_data = {
                            'platform': self.platform,
                            'timestamp': datetime.now().isoformat(),
                            'lat': self.lat,
                            'lon': self.lon,
                            'product_name': product_name,
                            'price': price,
                            'real_price': real_price,
                            'discount_percentage': discount_percentage,
                            'discounted_price': discounted_price,
                            'has_discount': has_discount,
                            'discount_type': discount_type,
                            'delivery_fee': delivery_fee,
                            'eta': eta_str,
                            'is_available': is_available
                        }
                        
                        products_found.append(product_data)
                        
                        # Limit to 2 products per address
                        if len(products_found) >= 2:
                            break
                
                if len(products_found) >= 2:
                    break
            
            self.logger.info(f"{self.platform}: Parsed {len(products_found)} products")
            
        except Exception as e:
            self.logger.error(f"{self.platform}: Error parsing data - {e}")
            return []
        
        return products_found
    
    def run(self) -> List[Dict[str, Any]]:
        """
        Execute scraping workflow.
        
        Returns:
            List of product dictionaries (can be empty if scraping fails)
        """
        self.logger.info(f"{self.platform}: Starting scraping workflow")
        
        # Fetch data
        raw_data = self.fetch_data()
        if raw_data is None:
            self.logger.error(f"{self.platform}: Failed to fetch data")
            return []
        
        # Parse data
        products = self.parse_data(raw_data)
        
        self.logger.info(
            f"{self.platform}: Scraping workflow completed - {len(products)} products"
        )
        
        return products
