import os
import sys
import tomllib
from typing import Any, Optional, Dict, List
from pathlib import Path
from pdf_converter.foundation.logger_service import logger
from pdf_converter.foundation.data_schemas import (
    AppSettings, DirectoriesConfig, PdfOutputStrategyConfig, 
    AutoGroupingConfig, ImageOutputStrategyConfig, ImageOutputConfig, ImageNamingConfig
)

class ConfigHandler:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.raw_data: Dict[str, Any] = {}

    def load(self) -> AppSettings:
        if not os.path.exists(self.config_path):
            logger.error(f"Config file not found: {self.config_path}")
            sys.exit(1)

        try:
            with open(self.config_path, "rb") as f:
                self.raw_data = tomllib.load(f)
        except Exception as e:
            logger.error(f"Failed to parse TOML: {e}")
            sys.exit(1)

        settings_dict = self.raw_data.get("Settings", {})
        if not settings_dict:
             logger.error("Missing [Settings] section in config.")
             sys.exit(1)

        return AppSettings(
            work_mode=self._get_required(settings_dict, "work_mode", ["img2pdf", "pdf2img"]),
            directories=self._parse_directories(settings_dict.get("Directories", {})),
            pdf_strategy=self._parse_pdf_strategy(settings_dict.get("PdfOutputStrategy", {})),
            img_strategy=self._parse_img_strategy(settings_dict.get("ImageOutputStrategy", {}))
        )

    def _get_required(self, data: Dict, key: str, choices: Optional[list] = None) -> Any:
        if key not in data:
            logger.error(f"Missing required config key: '{key}'")
            sys.exit(1)
        val = data[key]
        if choices and val not in choices:
            logger.error(f"Invalid value for '{key}': {val}. Expected one of {choices}")
            sys.exit(1)
        return val

    def _get_optional(self, data: Dict, key: str, default: Any, choices: Optional[list] = None) -> Any:
        if key not in data:
            logger.warning(f"Mandatory config '{key}' missing. Using default: {default}")
            return default
        
        val = data[key]
        if choices and val not in choices:
            logger.warning(f"[OPT] Invalid option for '{key}': {val}. Expected {choices}. Ignoring and using default: {default}")
            return default
        return val

    def _parse_directories(self, data: Dict) -> DirectoriesConfig:
        script_dir = Path(os.getcwd())
        
        ws_str = data.get("work_space", "")
        ws = Path(ws_str) if ws_str else script_dir
        if not ws_str:
            logger.warning("work_space not set. Using current directory.")

        inp_str = data.get("input_dir", "")
        inp = Path(inp_str) if inp_str else Path("assets/input")
        if not inp_str:
            logger.warning("input_dir not set. Using 'assets/input' in work_space.")

        out_str = data.get("output_dir", "")
        out = Path(out_str) if out_str else Path("assets/output")
        if not out_str:
             logger.warning("output_dir not set. Using 'assets/output' in work_space.")
            
        return DirectoriesConfig(work_space=ws, input_dir=inp, output_dir=out)

    def _parse_pdf_strategy(self, data: Dict) -> PdfOutputStrategyConfig:
        mode = self._get_optional(data, "mode", "many_to_one", ["many_to_one", "one_to_one", "auto_grouping"])
        out_name = self._get_optional(data, "output_name", "merged.pdf")
        overwrite = self._get_optional(data, "overwrite_existing", False)
        
        ag_data = data.get("AutoGrouping", {})
        ag_config = AutoGroupingConfig(
            enable=self._get_optional(ag_data, "enable", False),
            group_by=self._get_optional(ag_data, "group_by", "none", ["none", "prefix", "directory", "metadata"]),
            max_images_per_pdf=self._get_optional(ag_data, "max_images_per_pdf", 0)
        )
        
        return PdfOutputStrategyConfig(mode=mode, output_name=out_name, overwrite_existing=overwrite, auto_grouping=ag_config)

    def _parse_img_strategy(self, data: Dict) -> ImageOutputStrategyConfig:
        mode = self._get_optional(data, "mode", "one_to_one", ["one_to_one"])
        
        out_data = data.get("Output", {})
        img_out = ImageOutputConfig(
            image_format=self._get_optional(out_data, "image_format", "png", ["png", "jpg", "jpeg", "webp"]),
            dpi=self._get_optional(out_data, "dpi", 300),
            color_mode=self._get_optional(out_data, "color_mode", "rgb", ["rgb", "grayscale"]),
            overwrite_existing=self._get_optional(out_data, "overwrite_existing", False)
        )
        
        name_data = data.get("Naming", {})
        img_naming = ImageNamingConfig(
             page_naming=self._get_optional(name_data, "page_naming", "page_index", ["page_index", "original", "custom"]),
             start_index=self._get_optional(name_data, "start_index", 1)
        )
        
        return ImageOutputStrategyConfig(mode=mode, output=img_out, naming=img_naming)
