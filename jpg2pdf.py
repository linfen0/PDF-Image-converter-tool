import os
import sys
import tomllib
import logging
import argparse
import datetime
from dataclasses import dataclass, field
from typing import Any, Optional, Literal, Dict
from pathlib import Path
import img2pdf # type: ignore
from pdf2image import convert_from_path # type: ignore
from PIL import Image

# -----------------------------------------------------------------------------
# Constants & Enums
# -----------------------------------------------------------------------------

# Colors for Logging
class LogColors:
    RESET = "\033[0m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"

# Supported Extensions
IMG_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}

# -----------------------------------------------------------------------------
# Logging Infrastructure
# -----------------------------------------------------------------------------

class CustomFormatter(logging.Formatter):
    """
    Custom formatter to support specific timestamp format and colors.
    """
    def formatTime(self, record: logging.LogRecord, datefmt: Optional[str] = None) -> str:
        # UTC time with microseconds +00:00 (Manual formatting to match requirement)
        # Format: 2026-02-02 18:57:50.123456+00:00
        dt = datetime.datetime.fromtimestamp(record.created, datetime.timezone.utc)
        return dt.strftime('%Y-%m-%d %H:%M:%S.%f') + "+00:00"

    def format(self, record: logging.LogRecord) -> str:
        # Apply colors based on level
        original_msg = record.msg
        if record.levelno == logging.ERROR:
            record.msg = f"{LogColors.RED}ERROR: {original_msg}{LogColors.RESET}"
        elif record.levelno == logging.WARNING:
            # Check if it's a "Blue" warning (Optional setting issue) vs "Yellow" warning (Default fallback)
            # We'll use a convention: if msg starts with "[OPT]", it's blue.
            if original_msg.startswith("[OPT]"):
                record.msg = f"{LogColors.BLUE}WARNING: {original_msg}{LogColors.RESET}"
            else:
                record.msg = f"{LogColors.YELLOW}WARNING: {original_msg}{LogColors.RESET}"
        
        # Format the rest
        res = super().format(record)
        
        # Restore original message to avoid side effects if record is reused
        record.msg = original_msg
        return res

def setup_logger() -> logging.Logger:
    logger = logging.getLogger("AppLogger")
    logger.setLevel(logging.DEBUG)
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    
    # Format: Time - Message (Simplified for this specific requirement)
    # Requirement: "按时间戳的顺序排列... 并报告此设置不生效"
    # We will put the timestamp at the beginning.
    formatter = CustomFormatter(fmt="%(asctime)s - %(message)s")
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    return logger

logger = setup_logger()

# -----------------------------------------------------------------------------
# Configuration Models
# -----------------------------------------------------------------------------

@dataclass(frozen=True)
class AutoGroupingConfig:
    enable: bool
    group_by: str
    max_images_per_pdf: int

@dataclass(frozen=True)
class PdfOutputStrategyConfig:
    mode: Literal["many_to_one", "one_to_one", "auto_grouping"]
    output_name: str
    overwrite_existing: bool
    auto_grouping: AutoGroupingConfig

@dataclass(frozen=True)
class ImageOutputConfig:
    image_format: str
    dpi: int
    color_mode: str
    overwrite_existing: bool

@dataclass(frozen=True)
class ImageNamingConfig:
    page_naming: str
    start_index: int

@dataclass(frozen=True)
class ImageOutputStrategyConfig:
    mode: str
    output: ImageOutputConfig
    naming: ImageNamingConfig

@dataclass(frozen=True)
class DirectoriesConfig:
    work_space: Path
    input_dir: Path
    output_dir: Path

    @property
    def abs_input_dir(self) -> Path:
        return self.work_space / self.input_dir

    @property
    def abs_output_dir(self) -> Path:
        return self.work_space / self.output_dir

@dataclass(frozen=True)
class AppSettings:
    work_mode: Literal["img2pdf", "pdf2img"]
    directories: DirectoriesConfig
    pdf_strategy: PdfOutputStrategyConfig
    img_strategy: ImageOutputStrategyConfig

# -----------------------------------------------------------------------------
# Configuration Loader & Validator
# -----------------------------------------------------------------------------

class ConfigError(Exception):
    """Custom exception for configuration related errors."""
    pass

class ConfigLoader:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.raw_data: Dict[str, Any] = {}

    def load(self) -> AppSettings:
        if not os.path.exists(self.config_path):
            raise ConfigError(f"Config file not found: {self.config_path}")

        try:
            with open(self.config_path, "rb") as f:
                self.raw_data = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            logger.exception(f"Failed to parse TOML at {self.config_path}")
            raise ConfigError(f"Invalid TOML format: {e}") from e
        except Exception as e:
            logger.exception(f"Unexpected error reading config: {e}")
            raise ConfigError(f"Failed to load config: {e}") from e

        if "Settings" not in self.raw_data:
             raise ConfigError("Missing [Settings] section in config.")
        
        settings_dict = self.raw_data.get("Settings")
        if settings_dict is None:
             raise ConfigError("[Settings] section is explicitly set to null/empty in config.")
        
        if not isinstance(settings_dict, dict):
             raise ConfigError("[Settings] must be a table (dictionary).")

        return AppSettings(
            work_mode=self._get_required(settings_dict, "work_mode", ["img2pdf", "pdf2img"]),
            directories=self._parse_directories(settings_dict.get("Directories", {})),
            pdf_strategy=self._parse_pdf_strategy(settings_dict.get("PdfOutputStrategy", {})),
            img_strategy=self._parse_img_strategy(settings_dict.get("ImageOutputStrategy", {}))
        )

    def _get_required(self, data: Dict, key: str, choices: Optional[list] = None) -> Any:
        if key not in data:
            raise ConfigError(f"Missing required config key: '{key}'")
        val = data[key]
        if choices and val not in choices:
            raise ConfigError(f"Invalid value for '{key}': {val}. Expected one of {choices}")
        return val

    def _get_optional(self, data: Dict, key: str, default: Any, choices: Optional[list] = None) -> Any:
        if key not in data:
            logger.warning(f"Optional config '{key}' missing. Using default: {default}")
            return default
        
        val = data[key]
        if choices and val not in choices:
            logger.warning(f"[OPT] Invalid option for '{key}': {val}. Expected {choices}. Ignoring and using default: {default}")
            return default
        return val

    def _parse_directories(self, data: Dict) -> DirectoriesConfig:
        # Special logic for directories: default to current script dir/input/output if missing
        script_dir = Path(os.getcwd())
        
        ws_str = data.get("work_space", "")
        if not ws_str:
            logger.warning("work_space not set. Using current directory.")
            ws = script_dir
        else:
            ws = Path(ws_str)

        inp_str = data.get("input_dir", "")
        if not inp_str:
            logger.warning("input_dir not set. Using 'input' in work_space.")
            inp = Path("input")
        else:
            inp = Path(inp_str)

        out_str = data.get("output_dir", "")
        if not out_str:
             logger.warning("output_dir not set. Using 'output' in work_space.")
             out = Path("output")
        else:
            out = Path(out_str)
            
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

# -----------------------------------------------------------------------------
# Executors
# -----------------------------------------------------------------------------

class Img2PdfExecutor:
    def __init__(self, config: AppSettings):
        self.cfg = config
        self.input_dir = config.directories.abs_input_dir
        self.output_dir = config.directories.abs_output_dir
    
    def run(self):
        logger.info(f"Starting img2pdf mode in {self.input_dir}")
        
        if not self.input_dir.exists():
            logger.error(f"Input directory does not exist: {self.input_dir}")
            return

        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Gather images
        images = sorted([
            p for p in self.input_dir.glob("*") 
            if p.suffix.lower() in IMG_EXTENSIONS and p.is_file()
        ])
        
        if not images:
            logger.warning(f"No images found in {self.input_dir}")
            return

        mode = self.cfg.pdf_strategy.mode
        if mode == "many_to_one":
            self._process_many_to_one(images)
        elif mode == "one_to_one":
            self._process_one_to_one(images)
        elif mode == "auto_grouping":
            logger.warning("[OPT] Auto grouping not fully implemented. Falling back to many_to_one.")
            self._process_many_to_one(images)
            
    def _process_many_to_one(self, images: list[Path]):
        output_name = self.cfg.pdf_strategy.output_name or "merged.pdf"
        output_path = self.output_dir / output_name
        
        if output_path.exists() and not self.cfg.pdf_strategy.overwrite_existing:
            base, ext = os.path.splitext(output_name)
            output_name = f"{base}_{int(datetime.datetime.now().timestamp())}{ext}"
            output_path = self.output_dir / output_name
            logger.warning(f"Output file exists. Renaming to {output_name}")

        try:
            # Prepare image data
            # img2pdf requires bytes or paths. Paths are safer for large files.
            # Convert paths to strings
            img_paths = [str(p) for p in images]
            
            with open(output_path, "wb") as f:
                f.write(img2pdf.convert(img_paths))
            logger.info(f"Successfully created: {output_path}")
        except Exception as e:
            logger.error(f"Failed to create PDF: {e}")

    def _process_one_to_one(self, images: list[Path]):
        for img_path in images:
            output_name = f"{img_path.stem}.pdf"
            output_path = self.output_dir / output_name
            
            if output_path.exists() and not self.cfg.pdf_strategy.overwrite_existing:
                 logger.info(f"Skipping {output_path} (exists)")
                 continue
            
            try:
                with open(output_path, "wb") as f:
                    f.write(img2pdf.convert(str(img_path)))
                logger.info(f"Converted {img_path.name} -> {output_name}")
            except Exception as e:
                logger.error(f"Failed to convert {img_path.name}: {e}")

class Pdf2ImgExecutor:
    def __init__(self, config: AppSettings):
        self.cfg = config
        self.input_dir = config.directories.abs_input_dir
        self.output_dir = config.directories.abs_output_dir
        
    def run(self):
        logger.info(f"Starting pdf2img mode in {self.input_dir}")
        
        if not self.input_dir.exists():
             logger.error(f"Input directory does not exist: {self.input_dir}")
             return

        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        pdfs = sorted([
            p for p in self.input_dir.glob("*.pdf")
            if p.is_file()
        ])
        
        if not pdfs:
            logger.warning(f"No PDFs found in {self.input_dir}")
            return

        for pdf in pdfs:
            self._process_pdf(pdf)

    def _process_pdf(self, pdf_path: Path):
        strategy = self.cfg.img_strategy
        
        # Handle Output Config
        fmt = strategy.output.image_format
        dpi = strategy.output.dpi
        mode = strategy.output.color_mode # rgb / grayscale
        
        grayscale = (mode == "grayscale")
        
        logger.info(f"Processing PDF: {pdf_path.name}")
        
        try:
            # sub-folder for each PDF to avoid clutter
            pdf_out_dir = self.output_dir / pdf_path.stem
            pdf_out_dir.mkdir(exist_ok=True)
            
            images = convert_from_path(
                str(pdf_path),
                dpi=dpi,
                grayscale=grayscale,
                fmt=fmt
            )
            
            start_idx = strategy.naming.start_index
            naming_mode = strategy.naming.page_naming
            
            for i, image in enumerate(images):
                idx = start_idx + i
                
                if naming_mode == "page_index":
                    fname = f"page_{idx:03d}.{fmt}"
                elif naming_mode == "original":
                    fname = f"{pdf_path.stem}_page_{idx:03d}.{fmt}"
                else:
                    # Fallback
                    fname = f"page_{idx:03d}.{fmt}"
                
                out_path = pdf_out_dir / fname
                
                if out_path.exists() and not strategy.output.overwrite_existing:
                    logger.info(f"Skipping {fname} (exists)")
                    continue
                    
                image.save(out_path)
                logger.info(f"  Saved {fname}")
                
        except Exception as e:
             logger.error(f"Failed to convert PDF {pdf_path.name}: {e}")

# -----------------------------------------------------------------------------
# Main Application
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="PDF/Image Converter Tool")
    parser.add_argument("--config", default="config.toml", help="Path to config file")
    args = parser.parse_args()
    
    # Load Config
    try:
        loader = ConfigLoader(args.config)
        settings = loader.load()
    except ConfigError as e:
        logger.error(f"Configuration Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"An unexpected error occurred during initialization: {e}")
        sys.exit(1)
    
    logger.info(f"Work Mode: {settings.work_mode}")
    
    # Execute
    if settings.work_mode == "img2pdf":
        executor = Img2PdfExecutor(settings)
        executor.run()
    elif settings.work_mode == "pdf2img":
        executor = Pdf2ImgExecutor(settings)
        executor.run()
    else:
        logger.error(f"Unknown work mode: {settings.work_mode}")

if __name__ == "__main__":
    main()