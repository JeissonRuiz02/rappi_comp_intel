"""
Main script for competitive intelligence data collection.

This script orchestrates the scraping process across multiple delivery platforms
(Rappi, Uber Eats, DiDi) for a list of addresses, handling errors gracefully
and storing results in a structured format.
"""

import time
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
import polars as pl

from scrapers.rappi_scraper import RappiScraper
from scrapers.uber_scraper import UberScraper
from scrapers.didi_scraper import DiDiScraper
from scrapers.base_scraper import BaseScraper
from utils.logger import get_logger


logger = get_logger()


class CompetitiveIntelligenceCollector:
    """
    Main collector class for orchestrating multi-platform data collection.
    
    This class manages the workflow of reading addresses, instantiating scrapers,
    collecting data from multiple platforms, and storing results.
    
    Attributes:
        addresses_file (Path): Path to the CSV file containing addresses
        output_file (Path): Path to the output CSV file for results
        min_sleep (int): Minimum sleep time between requests in seconds
        max_sleep (int): Maximum sleep time between requests in seconds
        scrapers (List[type]): List of scraper classes to use
    """
    
    def __init__(
        self,
        addresses_file: str = "data/addresses.csv",
        output_file: str = "data/raw_data.csv",
        min_sleep: int = 2,
        max_sleep: int = 5,
    ) -> None:
        """
        Initialize the collector with configuration parameters.
        
        Args:
            addresses_file: Path to input CSV with addresses
            output_file: Path to output CSV for results
            min_sleep: Minimum seconds to wait between addresses
            max_sleep: Maximum seconds to wait between addresses
        """
        self.addresses_file = Path(addresses_file)
        self.output_file = Path(output_file)
        self.min_sleep = min_sleep
        self.max_sleep = max_sleep
        
        # Define scraper classes to use
        self.scrapers = [RappiScraper, UberScraper, DiDiScraper]
        
        logger.info("Initialized CompetitiveIntelligenceCollector")
        logger.info(f"Input file: {self.addresses_file}")
        logger.info(f"Output file: {self.output_file}")
    
    def load_addresses(self) -> pl.DataFrame:
        """
        Load addresses from CSV file.
        
        Returns:
            pl.DataFrame: DataFrame with columns: id, lat, lon, zone_type
            
        Raises:
            FileNotFoundError: If addresses file doesn't exist
            ValueError: If required columns are missing
        """
        if not self.addresses_file.exists():
            logger.error(f"Addresses file not found: {self.addresses_file}")
            raise FileNotFoundError(
                f"Addresses file not found: {self.addresses_file}"
            )
        
        logger.info(f"Loading addresses from {self.addresses_file}")
        df = pl.read_csv(self.addresses_file)
        
        # Validate required columns
        required_columns = {"id", "lat", "lon", "zone_type"}
        actual_columns = set(df.columns)
        
        if not required_columns.issubset(actual_columns):
            missing = required_columns - actual_columns
            logger.error(f"Missing required columns: {missing}")
            raise ValueError(f"Missing required columns: {missing}")
        
        logger.info(f"Loaded {len(df)} addresses successfully")
        return df
    
    def scrape_address(
        self,
        address_id: Any,
        lat: float,
        lon: float,
        zone_type: str,
        neighborhood: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Scrape data from all platforms for a single address.
        
        Args:
            address_id: Unique identifier for the address
            lat: Latitude coordinate
            lon: Longitude coordinate
            zone_type: Type of zone (e.g., residential, commercial)
            neighborhood: Optional neighborhood/colonia name
            
        Returns:
            List[Dict[str, Any]]: List of successful scraping results
        """
        results = []
        
        location_info = f"lat={lat}, lon={lon}, zone={zone_type}"
        if neighborhood:
            location_info += f", neighborhood={neighborhood}"
        
        logger.info(
            f"Processing address {address_id} ({location_info})"
        )
        
        for scraper_class in self.scrapers:
            platform_name = scraper_class.__name__.replace("Scraper", "")
            
            try:
                logger.info(
                    f"Scraping {platform_name} for address {address_id}"
                )
                
                # Instantiate scraper with neighborhood
                scraper: BaseScraper = scraper_class(
                    lat=lat, 
                    lon=lon, 
                    neighborhood=neighborhood
                )
                
                # Execute scraping workflow
                result = scraper.run()
                
                # Handle both single dict and list of dicts
                # (RappiScraper returns list, others return dict)
                if isinstance(result, list):
                    # Multiple products from single scraper
                    for item in result:
                        item["address_id"] = address_id
                        item["zone_type"] = zone_type
                        if neighborhood:
                            item["neighborhood"] = neighborhood
                        results.append(item)
                    logger.info(
                        f"✓ Successfully scraped {platform_name} for "
                        f"address {address_id} ({len(result)} products)"
                    )
                else:
                    # Single product
                    result["address_id"] = address_id
                    result["zone_type"] = zone_type
                    if neighborhood:
                        result["neighborhood"] = neighborhood
                    results.append(result)
                    logger.info(
                        f"✓ Successfully scraped {platform_name} for "
                        f"address {address_id}"
                    )
                
            except Exception as e:
                logger.error(
                    f"✗ Failed to scrape {platform_name} for "
                    f"address {address_id}: {str(e)}",
                    exc_info=True,
                )
                # Continue to next scraper without stopping
                continue
        
        logger.info(
            f"Completed address {address_id}: {len(results)}/{len(self.scrapers)} "
            f"scrapers successful"
        )
        
        return results
    
    def random_sleep(self) -> None:
        """
        Sleep for a random duration to avoid rate limiting.
        
        The sleep duration is randomly chosen between min_sleep and max_sleep
        to make requests appear more natural.
        """
        sleep_time = random.uniform(self.min_sleep, self.max_sleep)
        logger.debug(f"Sleeping for {sleep_time:.2f} seconds")
        time.sleep(sleep_time)
    
    def save_results(self, results: List[Dict[str, Any]]) -> None:
        """
        Save collected results to CSV file.
        
        Args:
            results: List of dictionaries containing scraping results
        """
        if not results:
            logger.warning("No results to save")
            return
        
        # Create DataFrame from results
        df = pl.DataFrame(results)
        
        # Ensure output directory exists
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to CSV
        df.write_csv(self.output_file)
        
        logger.info(
            f"Saved {len(results)} records to {self.output_file}"
        )
        logger.info(f"DataFrame shape: {df.shape}")
    
    def run(self) -> None:
        """
        Execute the complete data collection workflow.
        
        This method orchestrates the entire process:
        1. Load addresses from CSV
        2. Iterate through each address
        3. Scrape data from all platforms
        4. Handle errors gracefully
        5. Save results to output file
        """
        logger.info("=" * 80)
        logger.info("Starting Competitive Intelligence Data Collection")
        logger.info("=" * 80)
        
        try:
            # Load addresses
            addresses_df = self.load_addresses()
            total_addresses = len(addresses_df)
            
            # Store all successful results
            all_results: List[Dict[str, Any]] = []
            
            # Iterate through each address
            for idx, row in enumerate(addresses_df.iter_rows(named=True), 1):
                logger.info("-" * 80)
                logger.info(
                    f"Processing address {idx}/{total_addresses}"
                )
                
                # Scrape data for current address
                address_results = self.scrape_address(
                    address_id=row["id"],
                    lat=row["lat"],
                    lon=row["lon"],
                    zone_type=row["zone_type"],
                    neighborhood=row.get("neighborhood"),
                )
                
                # Add results to collection
                all_results.extend(address_results)
                
                # Sleep between addresses (except after the last one)
                if idx < total_addresses:
                    self.random_sleep()
            
            # Save all results
            logger.info("=" * 80)
            logger.info("Data collection completed. Saving results...")
            self.save_results(all_results)
            
            # Summary statistics
            total_scraped = len(all_results)
            expected_total = total_addresses * len(self.scrapers)
            success_rate = (total_scraped / expected_total * 100) if expected_total > 0 else 0
            
            logger.info("=" * 80)
            logger.info("COLLECTION SUMMARY")
            logger.info(f"Total addresses processed: {total_addresses}")
            logger.info(f"Total platforms: {len(self.scrapers)}")
            logger.info(f"Expected records: {expected_total}")
            logger.info(f"Successful records: {total_scraped}")
            logger.info(f"Success rate: {success_rate:.2f}%")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(
                f"Critical error in data collection workflow: {str(e)}",
                exc_info=True,
            )
            raise


def main() -> None:
    """
    Main entry point for the script.
    """
    try:
        collector = CompetitiveIntelligenceCollector(
            addresses_file="data/addresses.csv",
            output_file="data/raw_data.csv",
            min_sleep=2,
            max_sleep=5,
        )
        
        collector.run()
        
    except KeyboardInterrupt:
        logger.warning("Process interrupted by user (Ctrl+C)")
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
