"""
Base scraper module for competitive intelligence data collection.

This module defines the abstract base class for all platform-specific scrapers,
ensuring a consistent interface and standardized output format.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional
from utils.logger import get_logger


logger = get_logger()


class BaseScraper(ABC):
    """
    Abstract base class for platform scrapers.
    
    This class defines the interface that all platform-specific scrapers
    must implement. It ensures consistent data collection and standardization
    across different delivery platforms.
    
    Attributes:
        lat (float): Latitude coordinate for the search location
        lon (float): Longitude coordinate for the search location
        platform (str): Name of the platform being scraped
        _raw_data (Optional[Any]): Raw data fetched from the platform
        _parsed_data (Optional[Dict[str, Any]]): Parsed and structured data
    """
    
    def __init__(
        self, 
        lat: float, 
        lon: float, 
        neighborhood: Optional[str] = None
    ) -> None:
        """
        Initialize the scraper with location coordinates.
        
        Args:
            lat: Latitude coordinate for the search location
            lon: Longitude coordinate for the search location
            neighborhood: Optional neighborhood name for address-based scrapers
        """
        self.lat: float = lat
        self.lon: float = lon
        self.neighborhood: Optional[str] = neighborhood
        self.platform: str = self.__class__.__name__.replace("Scraper", "")
        self._raw_data: Optional[Any] = None
        self._parsed_data: Optional[Dict[str, Any]] = None
        
        location_info = f"({lat}, {lon})"
        if neighborhood:
            location_info = f"{neighborhood} {location_info}"
        
        logger.info(
            f"Initialized {self.platform} scraper for location: {location_info}"
        )
    
    @abstractmethod
    def fetch_data(self) -> Any:
        """
        Fetch raw data from the platform.
        
        This method must be implemented by each platform-specific scraper
        to handle the actual data retrieval from the platform's API or website.
        
        Returns:
            Any: Raw data from the platform (format varies by implementation)
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        pass
    
    @abstractmethod
    def parse_data(self, raw_data: Any) -> Dict[str, Any]:
        """
        Parse raw data into a structured format.
        
        This method must be implemented by each platform-specific scraper
        to transform the raw data into a standardized dictionary format.
        
        Args:
            raw_data: Raw data fetched from the platform
            
        Returns:
            Dict[str, Any]: Parsed and structured data
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        pass
    
    def get_standardized_output(self) -> Dict[str, Any]:
        """
        Get standardized output dictionary.
        
        This method returns a dictionary with a consistent structure across
        all platforms, making it easy to compare and analyze data.
        
        Returns:
            Dict[str, Any]: Standardized output with the following keys:
                - platform (str): Name of the platform
                - timestamp (str): ISO format timestamp of data collection
                - lat (float): Latitude coordinate
                - lon (float): Longitude coordinate
                - product_name (str): Name of the product/service
                - price (float): Product price
                - delivery_fee (float): Delivery fee amount
                - eta (int): Estimated time of arrival in minutes
                
        Raises:
            ValueError: If required data has not been fetched and parsed
        """
        if self._parsed_data is None:
            logger.error(
                f"{self.platform}: Cannot generate output without parsed data"
            )
            raise ValueError(
                "Data must be fetched and parsed before generating output. "
                "Call fetch_data() and parse_data() first."
            )
        
        standardized = {
            "platform": self.platform,
            "timestamp": datetime.utcnow().isoformat(),
            "lat": self.lat,
            "lon": self.lon,
            "product_name": self._parsed_data.get("product_name", ""),
            "price": self._parsed_data.get("price", 0.0),
            "delivery_fee": self._parsed_data.get("delivery_fee", 0.0),
            "eta": self._parsed_data.get("eta", 0),
        }
        
        logger.debug(
            f"{self.platform}: Generated standardized output for "
            f"{standardized['product_name']}"
        )
        
        return standardized
    
    def run(self) -> Dict[str, Any]:
        """
        Execute the complete scraping workflow.
        
        This convenience method runs the full scraping pipeline:
        1. Fetch raw data from the platform
        2. Parse the raw data into structured format
        3. Generate standardized output
        
        Returns:
            Dict[str, Any]: Standardized output dictionary
            
        Raises:
            Exception: If any step in the pipeline fails
        """
        try:
            logger.info(f"{self.platform}: Starting scraping workflow")
            
            # Fetch data
            self._raw_data = self.fetch_data()
            logger.debug(f"{self.platform}: Data fetched successfully")
            
            # Parse data
            self._parsed_data = self.parse_data(self._raw_data)
            logger.debug(f"{self.platform}: Data parsed successfully")
            
            # Generate output
            output = self.get_standardized_output()
            logger.info(f"{self.platform}: Scraping workflow completed")
            
            return output
            
        except Exception as e:
            logger.error(
                f"{self.platform}: Scraping workflow failed - {str(e)}"
            )
            raise
