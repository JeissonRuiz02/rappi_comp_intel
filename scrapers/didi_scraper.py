"""
DiDi Food mock scraper implementation.

This is a mock implementation that generates realistic data for DiDi Food
based on market patterns and zone characteristics. DiDi typically positions
itself as a value option with competitive pricing.

Note: DiDi Food is known for:
- Aggressive pricing (typically lowest in market)
- Higher delivery fees in some zones
- Slightly longer ETAs due to driver availability
"""

import random
from typing import Any, Dict, List, Optional
from scrapers.base_scraper import BaseScraper
from utils.logger import get_logger


logger = get_logger()


class DiDiScraper(BaseScraper):
    """
    Mock scraper for DiDi Food platform.
    
    Generates realistic pricing data. DiDi typically positions as a value
    brand with lower product prices but variable delivery fees.
    
    Pricing Strategy:
    - DiDi typically prices 3-8% lower than Rappi on food items
    - Delivery fees can be higher or lower depending on driver availability
    - ETAs tend to be slightly longer (2-5 min more)
    
    Attributes:
        base_prices (dict): Base product prices for DiDi
    """
    
    # Base prices for DiDi Food (typically competitive/lower)
    BASE_PRICES = {
        "Big Mac": 152.0,  # ~3% less than Rappi
        "McNuggets": 86.0,  # ~4% less than Rappi
    }
    
    # Delivery fee ranges by zone type
    DELIVERY_FEE_RANGES = {
        "commercial": (18, 28),
        "corporate": (22, 32),
        "high_income": (25, 35),
        "trendy_residential": (20, 30),
        "mid_income": (15, 25),
        "commercial_residential": (18, 28),
        "peripheral": (20, 30),
        "peripheral_populous": (18, 28),
        "peripheral_industrial": (15, 25),
        "peripheral_residential": (18, 28),
    }
    
    # ETA ranges by zone (minutes) - typically 2-5 min longer
    ETA_RANGES = {
        "commercial": (28, 38),
        "corporate": (32, 42),
        "high_income": (30, 40),
        "trendy_residential": (28, 38),
        "mid_income": (25, 35),
        "commercial_residential": (27, 37),
        "peripheral": (38, 52),
        "peripheral_populous": (42, 57),
        "peripheral_industrial": (40, 54),
        "peripheral_residential": (38, 50),
    }
    
    def __init__(
        self,
        lat: float,
        lon: float,
        neighborhood: Optional[str] = None
    ) -> None:
        """
        Initialize DiDi mock scraper.
        
        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate
            neighborhood: Neighborhood name
        """
        super().__init__(lat, lon, neighborhood)
        
        # Seed random for reproducibility per location
        random.seed(f"{lat}{lon}didi".encode())
        
        logger.info(
            "DiDi: Using MOCK implementation (API endpoint not available)"
        )
    
    def fetch_data(self) -> Dict[str, Any]:
        """
        Simulate data fetching from DiDi Food.
        
        Returns:
            Dict[str, Any]: Mock API response
        """
        logger.info("DiDi: Generating mock data based on competitive positioning")
        
        # Simulate API response
        mock_data = {
            "status": "success",
            "location": {
                "lat": self.lat,
                "lon": self.lon,
                "neighborhood": self.neighborhood
            },
            "restaurant": {
                "name": "McDonald's",
                "is_open": True
            },
            "menu_items": [
                {
                    "name": "Big Mac",
                    "base_price": self.BASE_PRICES["Big Mac"],
                },
                {
                    "name": "McNuggets 10 piezas",
                    "base_price": self.BASE_PRICES["McNuggets"],
                }
            ]
        }
        
        logger.debug("DiDi: Mock data generated successfully")
        return mock_data
    
    def parse_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse mock data with zone-based variations.
        
        Args:
            raw_data: Mock API response
            
        Returns:
            Dict[str, Any]: Parsed data with realistic variations
        """
        logger.info("DiDi: Parsing mock data with competitive pricing model")
        
        # Default values
        delivery_range = (20, 30)
        eta_range = (30, 40)
        
        parsed = {
            "store_info": {},
            "products": []
        }
        
        try:
            # Generate delivery fee
            delivery_fee = random.uniform(*delivery_range)
            delivery_fee = round(delivery_fee, 2)
            
            # Generate ETA (slightly longer than competition)
            eta = random.randint(*eta_range)
            
            parsed["store_info"] = {
                "delivery_fee": delivery_fee,
                "service_fee": 0.0,
                "eta": eta,
            }
            
            logger.debug(
                f"DiDi: Store info - delivery_fee={delivery_fee}, eta={eta}"
            )
            
            # Process products with competitive pricing
            for item in raw_data.get("menu_items", []):
                base_price = item["base_price"]
                
                # Add small random variation (-3% to +2%)
                variation = random.uniform(0.97, 1.02)
                final_price = base_price * variation
                final_price = round(final_price, 2)
                
                product_data = {
                    "product_name": item["name"],
                    "price": final_price,
                    "is_available": True,
                }
                
                parsed["products"].append(product_data)
                logger.info(
                    f"DiDi: Product '{item['name']}' - price=${final_price}"
                )
            
            logger.info(f"DiDi: Parsed {len(parsed['products'])} products")
            
        except Exception as e:
            logger.error(f"DiDi: Error parsing mock data - {str(e)}")
            raise
        
        return parsed
    
    def run(self) -> List[Dict[str, Any]]:
        """
        Execute the complete mock scraping workflow.
        
        Returns:
            List[Dict[str, Any]]: List of standardized output dictionaries
        """
        try:
            logger.info("DiDi: Starting mock scraping workflow")
            
            # Fetch mock data
            self._raw_data = self.fetch_data()
            logger.debug("DiDi: Mock data fetched successfully")
            
            # Parse data
            self._parsed_data = self.parse_data(self._raw_data)
            logger.debug("DiDi: Mock data parsed successfully")
            
            # Generate standardized output
            products = self._parsed_data.get("products", [])
            
            if not products:
                logger.warning("DiDi: No products in mock data")
                return []
            
            outputs = []
            for product in products:
                output = self._create_standardized_output(product)
                outputs.append(output)
            
            logger.info(
                f"DiDi: Mock workflow completed - {len(outputs)} products"
            )
            
            return outputs
            
        except Exception as e:
            logger.error(f"DiDi: Mock workflow failed - {str(e)}")
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
