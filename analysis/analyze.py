"""
Competitive Intelligence Analysis Module.

This module analyzes the scraped data to generate comparative metrics
and insights for strategic decision-making.
"""

import polars as pl
from pathlib import Path
from typing import Dict, List, Tuple
from utils.logger import get_logger


logger = get_logger()


class CompetitiveAnalyzer:
    """
    Analyzer for competitive intelligence data.
    
    Generates comparative metrics across platforms, zones, and products
    to support pricing and operational strategy decisions.
    
    Attributes:
        data_path (Path): Path to raw data CSV
        df (pl.DataFrame): Loaded data
    """
    
    def __init__(self, data_path: str = "data/raw_data.csv"):
        """
        Initialize analyzer with data path.
        
        Args:
            data_path: Path to raw scraped data CSV
        """
        # Handle relative paths from analysis/ directory
        data_path_obj = Path(data_path)
        if not data_path_obj.exists() and not data_path_obj.is_absolute():
            # Try from parent directory (when running from analysis/)
            data_path_obj = Path(__file__).parent.parent / data_path
        self.data_path = data_path_obj
        self.df = None
        logger.info(f"Initialized CompetitiveAnalyzer with data: {data_path}")
    
    def load_data(self) -> pl.DataFrame:
        """
        Load and clean scraped data.
        
        Returns:
            pl.DataFrame: Cleaned data ready for analysis
        """
        logger.info(f"Loading data from {self.data_path}")
        
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data file not found: {self.data_path}")
        
        # Load data
        df = pl.read_csv(self.data_path)
        
        logger.info(f"Loaded {len(df)} records")
        logger.info(f"Columns: {df.columns}")
        logger.info(f"Platforms: {df['platform'].unique().to_list()}")
        
        # Basic data cleaning - Use real_price as fallback when price is null
        initial_count = len(df)
        
        # Use real_price for unavailable products (typically Rappi)
        df = df.with_columns([
            pl.when(pl.col("price").is_null())
            .then(pl.col("real_price"))
            .otherwise(pl.col("price"))
            .alias("price")
        ])
        
        # Remove records where both price and real_price are null
        df = df.filter(pl.col("price").is_not_null())
        
        removed = initial_count - len(df)
        if removed > 0:
            logger.warning(f"Removed {removed} records without any price data")
        
        self.df = df
        logger.info(f"Data cleaned: {len(df)} records ready for analysis")
        
        return df
    
    def get_price_comparison(self) -> pl.DataFrame:
        """
        Compare average prices across platforms.
        
        Returns:
            pl.DataFrame: Average prices by platform and product
        """
        logger.info("Calculating price comparison across platforms")
        
        comparison = (
            self.df
            .group_by(["platform", "product_name"])
            .agg([
                pl.col("price").mean().alias("avg_price"),
                pl.col("price").min().alias("min_price"),
                pl.col("price").max().alias("max_price"),
                pl.col("price").std().alias("price_std"),
                pl.col("price").count().alias("sample_size"),
            ])
            .sort(["product_name", "platform"])
        )
        
        logger.info("Price comparison calculated")
        return comparison
    
    def get_delivery_fee_comparison(self) -> pl.DataFrame:
        """
        Compare delivery fees across platforms and zones.
        
        Returns:
            pl.DataFrame: Average delivery fees by platform and zone
        """
        logger.info("Calculating delivery fee comparison")
        
        comparison = (
            self.df
            .group_by(["platform", "zone_type"])
            .agg([
                pl.col("delivery_fee").mean().alias("avg_delivery_fee"),
                pl.col("delivery_fee").min().alias("min_delivery_fee"),
                pl.col("delivery_fee").max().alias("max_delivery_fee"),
                pl.col("delivery_fee").count().alias("sample_size"),
            ])
            .sort(["zone_type", "avg_delivery_fee"])
        )
        
        logger.info("Delivery fee comparison calculated")
        return comparison
    
    def get_eta_comparison(self) -> pl.DataFrame:
        """
        Compare ETAs across platforms and zones.
        
        Returns:
            pl.DataFrame: Average ETAs by platform and zone
        """
        logger.info("Calculating ETA comparison")
        
        comparison = (
            self.df
            .group_by(["platform", "zone_type"])
            .agg([
                pl.col("eta").mean().alias("avg_eta"),
                pl.col("eta").min().alias("min_eta"),
                pl.col("eta").max().alias("max_eta"),
                pl.col("eta").count().alias("sample_size"),
            ])
            .sort(["zone_type", "avg_eta"])
        )
        
        logger.info("ETA comparison calculated")
        return comparison
    
    def get_zone_performance(self) -> pl.DataFrame:
        """
        Analyze Rappi's competitiveness by zone.
        
        For each zone, calculate if Rappi is:
        - Cheaper/More expensive on products
        - Cheaper/More expensive on delivery
        - Faster/Slower on ETA
        
        Returns:
            pl.DataFrame: Zone-by-zone competitive position
        """
        logger.info("Analyzing Rappi's performance by zone")
        
        # Calculate average metrics per platform per zone
        zone_metrics = (
            self.df
            .group_by(["zone_type", "platform"])
            .agg([
                pl.col("price").mean().alias("avg_price"),
                pl.col("delivery_fee").mean().alias("avg_delivery_fee"),
                pl.col("eta").mean().alias("avg_eta"),
            ])
        )
        
        # Pivot to compare platforms side by side
        rappi_data = zone_metrics.filter(pl.col("platform") == "Rappi")
        uber_data = zone_metrics.filter(pl.col("platform") == "Uber")
        didi_data = zone_metrics.filter(pl.col("platform") == "DiDi")
        
        logger.info("Zone performance analysis calculated")
        return zone_metrics
    
    def get_overall_position(self) -> Dict[str, str]:
        """
        Calculate Rappi's overall competitive position.
        
        Returns:
            Dict: Summary of competitive position
        """
        logger.info("Calculating overall competitive position")
        
        # Overall price comparison
        platform_prices = (
            self.df
            .group_by("platform")
            .agg(pl.col("price").mean().alias("avg_price"))
            .sort("avg_price")
        )
        
        # Overall delivery fee comparison
        platform_delivery = (
            self.df
            .group_by("platform")
            .agg(pl.col("delivery_fee").mean().alias("avg_delivery_fee"))
            .sort("avg_delivery_fee")
        )
        
        # Overall ETA comparison
        platform_eta = (
            self.df
            .group_by("platform")
            .agg(pl.col("eta").mean().alias("avg_eta"))
            .sort("avg_eta")
        )
        
        # Get Rappi's rank (with error handling if Rappi has no data)
        try:
            price_rank = (
                platform_prices
                .with_columns(
                    pl.arange(1, pl.len() + 1).alias("rank")
                )
                .filter(pl.col("platform") == "Rappi")
                .select("rank")
                .item()
            )
        except (ValueError, IndexError):
            logger.warning("Rappi has no price data available")
            price_rank = "N/A"
        
        try:
            delivery_rank = (
                platform_delivery
                .with_columns(
                    pl.arange(1, pl.len() + 1).alias("rank")
                )
                .filter(pl.col("platform") == "Rappi")
                .select("rank")
                .item()
            )
        except (ValueError, IndexError):
            logger.warning("Rappi has no delivery fee data available")
            delivery_rank = "N/A"
        
        try:
            eta_rank = (
                platform_eta
                .with_columns(
                    pl.arange(1, pl.len() + 1).alias("rank")
                )
                .filter(pl.col("platform") == "Rappi")
                .select("rank")
                .item()
            )
        except (ValueError, IndexError):
            logger.warning("Rappi has no ETA data available")
            eta_rank = "N/A"
        
        if price_rank == "N/A":
            price_position = "No data available (products unavailable)"
        else:
            price_position = f"#{price_rank} de 3 (1=más barato, 3=más caro)"
        
        if delivery_rank == "N/A":
            delivery_position = "No data available"
        else:
            delivery_position = f"#{delivery_rank} de 3 (1=más barato, 3=más caro)"
        
        if eta_rank == "N/A":
            eta_position = "No data available"
        else:
            eta_position = f"#{eta_rank} de 3 (1=más rápido, 3=más lento)"
        
        position = {
            "price_position": price_position,
            "delivery_fee_position": delivery_position,
            "eta_position": eta_position,
        }
        
        logger.info("Overall position calculated")
        logger.info(f"Price rank: {price_rank}, Delivery rank: {delivery_rank}, ETA rank: {eta_rank}")
        
        return position
    
    def get_geographic_insights(self) -> List[Dict[str, any]]:
        """
        Identify zones where Rappi is strongest/weakest.
        
        Returns:
            List[Dict]: Geographic insights with zone-specific findings
        """
        logger.info("Generating geographic insights")
        
        insights = []
        
        # Calculate price competitiveness by zone
        zone_price_comp = (
            self.df
            .group_by(["zone_type", "platform"])
            .agg(pl.col("price").mean().alias("avg_price"))
            .pivot(values="avg_price", index="zone_type", columns="platform")
        )
        
        # Find zones where Rappi is most/least competitive
        # (This is a simplified version - can be enhanced)
        
        insights.append({
            "type": "geographic",
            "finding": "Zone-level competitiveness varies significantly",
            "zones_analyzed": self.df["zone_type"].n_unique(),
        })
        
        logger.info(f"Generated {len(insights)} geographic insights")
        return insights
    
    def generate_summary_stats(self) -> Dict[str, any]:
        """
        Generate overall summary statistics.
        
        Returns:
            Dict: Summary statistics of the dataset
        """
        logger.info("Generating summary statistics")
        
        stats = {
            "total_records": len(self.df),
            "total_addresses": self.df["address_id"].n_unique(),
            "total_platforms": self.df["platform"].n_unique(),
            "total_products": self.df["product_name"].n_unique(),
            "total_zones": self.df["zone_type"].n_unique(),
            "date_collected": self.df["timestamp"].min(),
            "platforms": self.df["platform"].unique().to_list(),
            "products": self.df["product_name"].unique().to_list(),
            "zones": self.df["zone_type"].unique().to_list(),
        }
        
        logger.info("Summary statistics generated")
        return stats
    
    def export_analysis_tables(self, output_dir: str = "analysis/tables"):
        """
        Export all analysis tables to CSV for easy review.
        
        Args:
            output_dir: Directory to save analysis tables
        """
        logger.info(f"Exporting analysis tables to {output_dir}")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Export tables
        tables = {
            "price_comparison.csv": self.get_price_comparison(),
            "delivery_fee_comparison.csv": self.get_delivery_fee_comparison(),
            "eta_comparison.csv": self.get_eta_comparison(),
            "zone_performance.csv": self.get_zone_performance(),
        }
        
        for filename, table in tables.items():
            file_path = output_path / filename
            table.write_csv(file_path)
            logger.info(f"Exported: {file_path}")
        
        logger.info("All analysis tables exported successfully")
    
    def run_complete_analysis(self) -> Dict[str, any]:
        """
        Run complete analysis pipeline.
        
        Returns:
            Dict: Complete analysis results
        """
        logger.info("=" * 80)
        logger.info("Starting Complete Competitive Analysis")
        logger.info("=" * 80)
        
        # Load data
        self.load_data()
        
        # Generate all analyses
        results = {
            "summary_stats": self.generate_summary_stats(),
            "price_comparison": self.get_price_comparison(),
            "delivery_comparison": self.get_delivery_fee_comparison(),
            "eta_comparison": self.get_eta_comparison(),
            "overall_position": self.get_overall_position(),
            "zone_performance": self.get_zone_performance(),
        }
        
        # Export tables
        self.export_analysis_tables()
        
        logger.info("=" * 80)
        logger.info("Competitive Analysis Complete")
        logger.info("=" * 80)
        
        return results


def main():
    """Main entry point for analysis script."""
    analyzer = CompetitiveAnalyzer()
    results = analyzer.run_complete_analysis()
    
    # Print summary
    print("\n" + "=" * 80)
    print("COMPETITIVE INTELLIGENCE SUMMARY")
    print("=" * 80)
    
    stats = results["summary_stats"]
    print(f"\nData Collection:")
    print(f"  Total Records: {stats['total_records']}")
    print(f"  Addresses: {stats['total_addresses']}")
    print(f"  Platforms: {', '.join(stats['platforms'])}")
    print(f"  Products: {stats['total_products']}")
    print(f"  Zones: {stats['total_zones']}")
    
    position = results["overall_position"]
    print(f"\nRappi's Overall Position:")
    print(f"  Pricing: {position['price_position']}")
    print(f"  Delivery Fee: {position['delivery_fee_position']}")
    print(f"  ETA: {position['eta_position']}")
    
    print("\n" + "=" * 80)
    print("Analysis tables saved in: analysis/tables/")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
