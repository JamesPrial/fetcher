"""Storage module for persisting model data."""

import json
import csv
from pathlib import Path
from typing import Optional, List
import yaml

from .models import ModelCatalog, ModelInfo


class Storage:
    """Handle storage and retrieval of model catalogs."""

    def __init__(self, data_dir: Path = Path("data")):
        """
        Initialize storage.

        Args:
            data_dir: Directory for storing data files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.catalog_path = self.data_dir / "models.json"

    def load_catalog(self) -> ModelCatalog:
        """
        Load the model catalog from disk.

        Returns:
            ModelCatalog object (empty if file doesn't exist)
        """
        if not self.catalog_path.exists():
            return ModelCatalog()

        try:
            with open(self.catalog_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return ModelCatalog(**data)
        except Exception as e:
            print(f"Warning: Failed to load catalog: {e}")
            return ModelCatalog()

    def save_catalog(self, catalog: ModelCatalog) -> None:
        """
        Save the model catalog to disk.

        Args:
            catalog: ModelCatalog to save
        """
        try:
            with open(self.catalog_path, "w", encoding="utf-8") as f:
                json.dump(
                    catalog.model_dump(),
                    f,
                    indent=2,
                    ensure_ascii=False,
                    default=str,
                )
            print(f"✓ Saved catalog to {self.catalog_path}")
        except Exception as e:
            raise Exception(f"Failed to save catalog: {e}")

    def merge_models(self, new_models: List[ModelInfo]) -> ModelCatalog:
        """
        Merge new models with existing catalog.

        Args:
            new_models: List of new ModelInfo objects

        Returns:
            Updated ModelCatalog
        """
        catalog = self.load_catalog()

        # Create a set of existing model IDs for quick lookup
        existing_ids = {model.model_id for model in catalog.models}

        # Add new models and update existing ones
        for new_model in new_models:
            if new_model.model_id in existing_ids:
                # Update existing model
                for i, model in enumerate(catalog.models):
                    if model.model_id == new_model.model_id:
                        catalog.models[i] = new_model
                        break
            else:
                # Add new model
                catalog.add_model(new_model)

        return catalog

    def export_to_csv(self, output_path: Optional[Path] = None) -> Path:
        """
        Export catalog to CSV format.

        Args:
            output_path: Optional custom output path

        Returns:
            Path to the created CSV file
        """
        if output_path is None:
            output_path = self.data_dir / "models.csv"

        catalog = self.load_catalog()

        try:
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                if not catalog.models:
                    return output_path

                # Define CSV columns
                fieldnames = [
                    "model_id",
                    "name",
                    "provider",
                    "context_length",
                    "price_prompt",
                    "price_completion",
                    "supports_vision",
                    "supports_function_calling",
                    "modalities",
                    "description",
                ]

                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for model in catalog.models:
                    writer.writerow(
                        {
                            "model_id": model.model_id,
                            "name": model.name,
                            "provider": model.provider,
                            "context_length": model.context_length or "",
                            "price_prompt": (model.pricing.prompt if model.pricing else ""),
                            "price_completion": (model.pricing.completion if model.pricing else ""),
                            "supports_vision": model.capabilities.supports_vision,
                            "supports_function_calling": (
                                model.capabilities.supports_function_calling
                            ),
                            "modalities": ",".join(model.capabilities.modalities),
                            "description": model.description or "",
                        }
                    )

            print(f"✓ Exported catalog to {output_path}")
            return output_path

        except Exception as e:
            raise Exception(f"Failed to export to CSV: {e}")

    def export_to_yaml(self, output_path: Optional[Path] = None) -> Path:
        """
        Export catalog to YAML format.

        Args:
            output_path: Optional custom output path

        Returns:
            Path to the created YAML file
        """
        if output_path is None:
            output_path = self.data_dir / "models.yaml"

        catalog = self.load_catalog()

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    catalog.model_dump(),
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                )

            print(f"✓ Exported catalog to {output_path}")
            return output_path

        except Exception as e:
            raise Exception(f"Failed to export to YAML: {e}")
