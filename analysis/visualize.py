"""
Visualization Module for Competitive Intelligence.

Generates charts and visual comparisons to support strategic insights.
"""

import polars as pl
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Optional
from utils.logger import get_logger


logger = get_logger()

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10


class CompetitiveVisualizer:
    """
    Visualizer for competitive intelligence data.
    
    Creates charts and graphs for comparative analysis across platforms.
    
    Attributes:
        df (pl.DataFrame): Loaded data
        output_dir (Path): Directory for saving charts
    """
    
    def __init__(
        self,
        data_path: str = "data/raw_data.csv",
        output_dir: str = "analysis/charts"
    ):
        """
        Initialize visualizer.
        
        Args:
            data_path: Path to raw data CSV
            output_dir: Directory to save generated charts
        """
        self.data_path = Path(data_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.df = None
        
        logger.info(f"Initialized CompetitiveVisualizer")
        logger.info(f"Output directory: {self.output_dir}")
    
    def load_data(self) -> pl.DataFrame:
        """Load and clean data."""
        logger.info(f"Loading data from {self.data_path}")
        
        df = pl.read_csv(self.data_path)
        
        # Use real_price as fallback when price is null (for unavailable products)
        df = df.with_columns([
            pl.when(pl.col("price").is_null())
            .then(pl.col("real_price"))
            .otherwise(pl.col("price"))
            .alias("price")
        ])
        
        # Remove records where both price and real_price are null
        df = df.filter(pl.col("price").is_not_null())
        
        self.df = df
        logger.info(f"Loaded {len(df)} records for visualization")
        
        return df
    
    def plot_price_comparison(self, save: bool = True) -> Optional[str]:
        """
        Create bar chart comparing average prices across platforms.
        
        Chart 1: Price Comparison by Platform and Product
        
        Args:
            save: Whether to save the chart to file
            
        Returns:
            Optional[str]: Path to saved chart if save=True
        """
        logger.info("Creating price comparison chart")
        
        # Calculate average prices
        price_data = (
            self.df
            .group_by(["platform", "product_name"])
            .agg(pl.col("price").mean().alias("avg_price"))
        )
        
        # Convert to pandas for matplotlib compatibility
        price_pd = price_data.to_pandas()
        
        # Create figure
        fig, ax = plt.subplots(figsize=(14, 7))
        
        # Get unique products
        products = price_pd["product_name"].unique()
        
        # Set up bar positions
        x = range(len(products))
        width = 0.25
        
        platforms = ["Rappi", "Uber", "DiDi"]
        colors = {"Rappi": "#FF6B00", "Uber": "#5FB709", "DiDi": "#FF1493"}
        
        for i, platform in enumerate(platforms):
            platform_data = price_pd[price_pd["platform"] == platform]
            prices = [
                platform_data[platform_data["product_name"] == prod]["avg_price"].values[0]
                if len(platform_data[platform_data["product_name"] == prod]) > 0
                else 0
                for prod in products
            ]
            
            ax.bar(
                [xi + i * width for xi in x],
                prices,
                width,
                label=platform,
                color=colors[platform],
                alpha=0.8
            )
        
        ax.set_xlabel("Producto", fontsize=12, fontweight="bold")
        ax.set_ylabel("Precio Promedio (MXN)", fontsize=12, fontweight="bold")
        ax.set_title(
            "Comparación de Precios por Plataforma",
            fontsize=14,
            fontweight="bold",
            pad=20
        )
        ax.set_xticks([xi + width for xi in x])
        ax.set_xticklabels(products, rotation=15, ha="right")
        ax.legend(title="Plataforma", fontsize=10)
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        
        if save:
            output_path = self.output_dir / "01_price_comparison.png"
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            logger.info(f"Chart saved: {output_path}")
            plt.close()
            return str(output_path)
        else:
            plt.show()
            return None
    
    def plot_delivery_fee_by_zone(self, save: bool = True) -> Optional[str]:
        """
        Create grouped bar chart for delivery fees by zone.
        
        Chart 2: Delivery Fee Comparison by Zone Type
        
        Args:
            save: Whether to save the chart
            
        Returns:
            Optional[str]: Path to saved chart
        """
        logger.info("Creating delivery fee by zone chart")
        
        # Calculate average delivery fees
        delivery_data = (
            self.df
            .group_by(["zone_type", "platform"])
            .agg(pl.col("delivery_fee").mean().alias("avg_delivery_fee"))
        )
        
        delivery_pd = delivery_data.to_pandas()
        
        # Create figure
        fig, ax = plt.subplots(figsize=(16, 8))
        
        zones = sorted(delivery_pd["zone_type"].unique())
        x = range(len(zones))
        width = 0.25
        
        platforms = ["Rappi", "Uber", "DiDi"]
        colors = {"Rappi": "#FF6B00", "Uber": "#5FB709", "DiDi": "#FF1493"}
        
        for i, platform in enumerate(platforms):
            platform_data = delivery_pd[delivery_pd["platform"] == platform]
            fees = [
                platform_data[platform_data["zone_type"] == zone]["avg_delivery_fee"].values[0]
                if len(platform_data[platform_data["zone_type"] == zone]) > 0
                else 0
                for zone in zones
            ]
            
            ax.bar(
                [xi + i * width for xi in x],
                fees,
                width,
                label=platform,
                color=colors[platform],
                alpha=0.8
            )
        
        ax.set_xlabel("Tipo de Zona", fontsize=12, fontweight="bold")
        ax.set_ylabel("Delivery Fee Promedio (MXN)", fontsize=12, fontweight="bold")
        ax.set_title(
            "Comparación de Delivery Fees por Tipo de Zona",
            fontsize=14,
            fontweight="bold",
            pad=20
        )
        ax.set_xticks([xi + width for xi in x])
        ax.set_xticklabels(zones, rotation=45, ha="right")
        ax.legend(title="Plataforma", fontsize=10)
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        
        if save:
            output_path = self.output_dir / "02_delivery_fees_by_zone.png"
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            logger.info(f"Chart saved: {output_path}")
            plt.close()
            return str(output_path)
        else:
            plt.show()
            return None
    
    def plot_eta_comparison(self, save: bool = True) -> Optional[str]:
        """
        Create box plot comparing ETAs across platforms.
        
        Chart 3: ETA Distribution by Platform
        
        Args:
            save: Whether to save the chart
            
        Returns:
            Optional[str]: Path to saved chart
        """
        logger.info("Creating ETA comparison chart")
        
        # Convert to pandas for seaborn
        df_pd = self.df.to_pandas()
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 7))
        
        # Create box plot
        sns.boxplot(
            data=df_pd,
            x="platform",
            y="eta",
            palette={"Rappi": "#FF6B00", "Uber": "#5FB709", "DiDi": "#FF1493"},
            ax=ax
        )
        
        # Add mean markers
        means = df_pd.groupby("platform")["eta"].mean()
        positions = range(len(means))
        ax.scatter(
            positions,
            means,
            color='red',
            s=100,
            zorder=3,
            label='Promedio',
            marker='D'
        )
        
        ax.set_xlabel("Plataforma", fontsize=12, fontweight="bold")
        ax.set_ylabel("Tiempo Estimado de Entrega (minutos)", fontsize=12, fontweight="bold")
        ax.set_title(
            "Distribución de ETAs por Plataforma",
            fontsize=14,
            fontweight="bold",
            pad=20
        )
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        
        if save:
            output_path = self.output_dir / "03_eta_comparison.png"
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            logger.info(f"Chart saved: {output_path}")
            plt.close()
            return str(output_path)
        else:
            plt.show()
            return None
    
    def plot_price_heatmap_by_zone(self, save: bool = True) -> Optional[str]:
        """
        Create heatmap of average prices by zone and platform.
        
        Chart 4 (Bonus): Price Heatmap
        
        Args:
            save: Whether to save the chart
            
        Returns:
            Optional[str]: Path to saved chart
        """
        logger.info("Creating price heatmap by zone")
        
        # Calculate average prices by zone and platform
        heatmap_data = (
            self.df
            .group_by(["zone_type", "platform"])
            .agg(pl.col("price").mean().alias("avg_price"))
            .pivot(values="avg_price", index="zone_type", columns="platform")
        )
        
        heatmap_pd = heatmap_data.to_pandas().set_index("zone_type")
        
        # Ensure column order
        heatmap_pd = heatmap_pd[["Rappi", "Uber", "DiDi"]]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 12))
        
        sns.heatmap(
            heatmap_pd,
            annot=True,
            fmt=".2f",
            cmap="RdYlGn_r",
            cbar_kws={"label": "Precio Promedio (MXN)"},
            ax=ax,
            linewidths=0.5
        )
        
        ax.set_title(
            "Heatmap de Precios Promedio por Zona y Plataforma",
            fontsize=14,
            fontweight="bold",
            pad=20
        )
        ax.set_xlabel("Plataforma", fontsize=12, fontweight="bold")
        ax.set_ylabel("Tipo de Zona", fontsize=12, fontweight="bold")
        
        plt.tight_layout()
        
        if save:
            output_path = self.output_dir / "04_price_heatmap_by_zone.png"
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            logger.info(f"Chart saved: {output_path}")
            plt.close()
            return str(output_path)
        else:
            plt.show()
            return None
    
    def generate_all_charts(self):
        """Generate all visualization charts."""
        logger.info("Generating all visualization charts")
        
        self.load_data()
        
        charts = [
            ("Price Comparison", self.plot_price_comparison),
            ("Delivery Fees by Zone", self.plot_delivery_fee_by_zone),
            ("ETA Comparison", self.plot_eta_comparison),
            ("Price Heatmap", self.plot_price_heatmap_by_zone),
        ]
        
        generated = []
        for name, func in charts:
            try:
                path = func(save=True)
                generated.append(path)
                logger.info(f"✓ Generated: {name}")
            except Exception as e:
                logger.error(f"✗ Failed to generate {name}: {str(e)}")
        
        logger.info(f"Generated {len(generated)}/{len(charts)} charts successfully")
        
        return generated


def main():
    """Main entry point for visualization script."""
    visualizer = CompetitiveVisualizer()
    charts = visualizer.generate_all_charts()
    
    print("\n" + "=" * 80)
    print("VISUALIZATION COMPLETE")
    print("=" * 80)
    print(f"\nGenerated {len(charts)} charts:")
    for chart in charts:
        print(f"  - {chart}")
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
