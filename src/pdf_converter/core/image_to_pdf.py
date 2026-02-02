import os
import datetime
from pathlib import Path
import img2pdf # type: ignore
from pdf_converter.foundation.logger_service import logger
from pdf_converter.foundation.data_schemas import AppSettings
from pdf_converter.utils.app_constants import IMG_EXTENSIONS

class ImageToPdfConverter:
    def __init__(self, config: AppSettings):
        self.cfg = config
        self.input_dir = config.directories.abs_input_dir
        self.output_dir = config.directories.abs_output_dir

    def run(self):
        logger.info(f"Starting ImageToPdfConverter in {self.input_dir}")
        if not self.input_dir.exists():
            logger.error(f"Input directory does not exist: {self.input_dir}")
            return

        self.output_dir.mkdir(parents=True, exist_ok=True)
        images = sorted([p for p in self.input_dir.glob("*") if p.suffix.lower() in IMG_EXTENSIONS and p.is_file()])
        
        if not images:
            logger.warning(f"No images found in {self.input_dir}")
            return

        mode = self.cfg.pdf_strategy.mode
        if mode == "many_to_one":
            self._process_many_to_one(images)
        elif mode == "one_to_one":
            self._process_one_to_one(images)
        else:
            logger.warning(f"[OPT] Mode '{mode}' not fully implemented. Falling back to many_to_one.")
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
            img_paths = [str(p) for p in images]
            with open(output_path, "wb") as f:
                f.write(img2pdf.convert(img_paths))
            logger.info(f"Successfully merged {len(images)} images -> {output_path}")
        except Exception as e:
            logger.error(f"Failed to merge images: {e}")

    def _process_one_to_one(self, images: list[Path]):
        for img_path in images:
            output_name = f"{img_path.stem}.pdf"
            output_path = self.output_dir / output_name
            if output_path.exists() and not self.cfg.pdf_strategy.overwrite_existing:
                continue
            try:
                with open(output_path, "wb") as f:
                    f.write(img2pdf.convert(str(img_path)))
                logger.info(f"Converted {img_path.name} -> {output_name}")
            except Exception as e:
                logger.error(f"Failed to convert {img_path.name}: {e}")
