"""
Uber Eats mock scraper implementation.

This is a mock implementation that generates realistic data for Uber Eats
based on market patterns and zone characteristics. Used as fallback when
API/web scraping is not feasible due to bot detection.

Note: This mock generates data with realistic variations based on:
- Zone type (commercial, residential, etc.)
- Geographic location (neighborhood characteristics)
- Time-based randomization for realism
"""

import random
from typing import Any, Dict, List, Optional
from scrapers.base_scraper import BaseScraper
from utils.logger import get_logger


logger = get_logger()


class UberScraper(BaseScraper):
    """
    Mock scraper for Uber Eats platform.
    
    Generates realistic pricing and delivery data based on zone characteristics
    and market research. This approach is used because Uber Eats has strong
    bot detection that blocks automated scraping.
    
    Pricing Strategy:
    - Uber typically prices 5-10% higher than Rappi on food items
    - Delivery fees vary by zone (15-35 pesos)
    - ETAs are competitive with market average
    
    Attributes:
        zone_multipliers (dict): Price adjustments by zone type
        base_prices (dict): Base product prices for Uber
    """
    
    # Base prices for Uber Eats (typically higher than Rappi)
    BASE_PRICES = {
        "Big Mac": 165.0,  # ~5% more than Rappi
        "McNuggets": 95.0,  # ~7% more than Rappi
    }
    
    # Zone-based multipliers for pricing realism
    ZONE_MULTIPLIERS = {
        "commercial": 1.05,
        "corporate": 1.10,
        "high_income": 1.08,
        "trendy_residential": 1.06,
        "mid_income": 1.02,
        "commercial_residential": 1.03,
        "peripheral": 0.98,
        "peripheral_populous": 0.97,
        "peripheral_industrial": 0.96,
        "peripheral_residential": 0.97,
    }
    
    # Delivery fee ranges by zone type
    DELIVERY_FEE_RANGES = {
        "commercial": (25, 35),
        "corporate": (30, 40),
        "high_income": (28, 38),
        "trendy_residential": (25, 35),
        "mid_income": (20, 30),
        "commercial_residential": (22, 32),
        "peripheral": (15, 25),
        "peripheral_populous": (15, 20),
        "peripheral_industrial": (12, 20),
        "peripheral_residential": (15, 22),
    }
    
    # ETA ranges by zone (minutes)
    ETA_RANGES = {
        "commercial": (25, 35),
        "corporate": (30, 40),
        "high_income": (28, 38),
        "trendy_residential": (25, 35),
        "mid_income": (22, 32),
        "commercial_residential": (25, 35),
        "peripheral": (35, 50),
        "peripheral_populous": (40, 55),
        "peripheral_industrial": (38, 52),
        "peripheral_residential": (35, 48),
    }
    
    def __init__(
        self,
        lat: float,
        lon: float,
        neighborhood: Optional[str] = None
    ) -> None:
        """
        Initialize Uber mock scraper.
        
        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate
            neighborhood: Neighborhood name
        """
        super().__init__(lat, lon, neighborhood)
        
        # Seed random for reproducibility per location
        random.seed(f"{lat}{lon}".encode())
        
        logger.info(
            "Uber: Using MOCK implementation (API/web scraping blocked by platform)"
        )
    
    def fetch_data(self) -> Dict[str, Any]:
        """
        Simulate data fetching from Uber Eats.
        
        In production, this would make API calls or browser automation.
        For this implementation, we simulate realistic data patterns.
        
        Returns:
            Dict[str, Any]: Mock API response
        """
        logger.info("Uber: Generating mock data based on zone characteristics")
        
        # Simulate API response structure
        mock_data = {
            "status": "success",
            "location": {
                "lat": self.lat,
                "lon": self.lon,
                "neighborhood": self.neighborhood
            },
            "store": {
                "name": "McDonald's",
                "available": True
            },
            "products": [
                {
                    "name": "Big Mac",
                    "base_price": self.BASE_PRICES["Big Mac"],
                },
                {
                    "name": "10 McNuggets",
                    "base_price": self.BASE_PRICES["McNuggets"],
                }
            ]
        }
        
        logger.debug("Uber: Mock data generated successfully")
        return mock_data
    
    def parse_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse mock data and apply zone-based variations.
        
        Args:
            raw_data: Mock API response
            
        Returns:
            Dict[str, Any]: Parsed data with realistic variations
        """
        logger.info("Uber: Parsing mock data with zone-based pricing")
        
        # Get zone type from context (will be set by main.py if needed)
        # For now, use default multiplier
        zone_multiplier = 1.0
        delivery_range = (20, 30)
        eta_range = (25, 35)
        
        parsed = {
            "store_info": {},
            "products": []
        }
        
        try:
            # Generate delivery fee with zone variation
            delivery_fee = random.uniform(*delivery_range)
            delivery_fee = round(delivery_fee, 2)
            
            # Generate ETA with zone variation
            eta = random.randint(*eta_range)
            
            parsed["store_info"] = {
                "delivery_fee": delivery_fee,
                "service_fee": 0.0,  # Uber includes this in item price
                "eta": eta,
            }
            
            logger.debug(
                f"Uber: Store info - delivery_fee={delivery_fee}, eta={eta}"
            )
            
            # Process products with zone-based pricing
            for product in raw_data.get("products", []):
                base_price = product["base_price"]
                
                # Apply zone multiplier
                final_price = base_price * zone_multiplier
                
                # Add small random variation (-2% to +2%)
                variation = random.uniform(0.98, 1.02)
                final_price = final_price * variation
                final_price = round(final_price, 2)
                
                product_data = {
                    "product_name": product["name"],
                    "price": final_price,
                    "is_available": True,
                }
                
                parsed["products"].append(product_data)
                logger.info(
                    f"Uber: Product '{product['name']}' - price=${final_price}"
                )
            
            logger.info(f"Uber: Parsed {len(parsed['products'])} products")
            
        except Exception as e:
            logger.error(f"Uber: Error parsing mock data - {str(e)}")
            raise
        
        return parsed
    
    def run(self) -> List[Dict[str, Any]]:
        """
        Execute the complete scraping workflow.
        
        Returns:
            List[Dict[str, Any]]: List of standardized output dictionaries
        """
        try:
            logger.info("Uber: Starting mock scraping workflow")
            
            # Fetch mock data
            self._raw_data = self.fetch_data()
            logger.debug("Uber: Mock data fetched successfully")
            
            # Parse data
            self._parsed_data = self.parse_data(self._raw_data)
            logger.debug("Uber: Mock data parsed successfully")
            
            # Generate standardized output
            products = self._parsed_data.get("products", [])
            
            if not products:
                logger.warning("Uber: No products in mock data")
                return []
            
            outputs = []
            for product in products:
                output = self._create_standardized_output(product)
                outputs.append(output)
            
            logger.info(
                f"Uber: Mock workflow completed - {len(outputs)} products"
            )
            
            return outputs
            
        except Exception as e:
            logger.error(f"Uber: Mock workflow failed - {str(e)}")
            raise
    
    def _create_standardized_output(
        self,
        product: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create standardized output for a single product.
        
        Args:
            product: Product data dictionary
            
        Returns:
            Dict[str, Any]: Standardized output dictionary
        """
        from datetime import datetime
        
        store_info = self._parsed_data.get("store_info", {})
        
        standardized = {
            "platform": self.platform,
            "timestamp": datetime.utcnow().isoformat(),
            "lat": self.lat,
            "lon": self.lon,
            "product_name": product.get("product_name", ""),
            "price": product.get("price", 0.0),
            "delivery_fee": store_info.get("delivery_fee", 0.0),
            "eta": store_info.get("eta", 0),
        }
        
        return standardized
