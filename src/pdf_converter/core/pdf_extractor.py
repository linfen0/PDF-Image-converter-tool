from pathlib import Path
from pdf2image import convert_from_path # type: ignore
from pdf_converter.foundation.logger_service import logger
from pdf_converter.foundation.data_schemas import AppSettings

class PDFExtractor:
    def __init__(self, config: AppSettings):
        self.cfg = config
        self.input_dir = config.directories.abs_input_dir
        self.output_dir = config.directories.abs_output_dir
        
    def run(self):
        logger.info(f"Starting PDF Extractor in {self.input_dir}")
        if not self.input_dir.exists():
             logger.error(f"Input directory does not exist: {self.input_dir}")
             return

        self.output_dir.mkdir(parents=True, exist_ok=True)
        pdfs = sorted([p for p in self.input_dir.glob("*.pdf") if p.is_file()])
        
        if not pdfs:
            logger.warning(f"No PDFs found in {self.input_dir}")
            return

        for pdf in pdfs:
            self._process_pdf(pdf)

    def _process_pdf(self, pdf_path: Path):
        strategy = self.cfg.img_strategy
        fmt = strategy.output.image_format
        dpi = strategy.output.dpi
        grayscale = (strategy.output.color_mode == "grayscale")
        
        logger.info(f"Extracting PDF: {pdf_path.name}")
        try:
            pdf_out_dir = self.output_dir / pdf_path.stem
            pdf_out_dir.mkdir(exist_ok=True)
            
            images = convert_from_path(str(pdf_path), dpi=dpi, grayscale=grayscale, fmt=fmt)
            
            start_idx = strategy.naming.start_index
            naming_mode = strategy.naming.page_naming
            
            for i, image in enumerate(images):
                idx = start_idx + i
                fname = f"page_{idx:03d}.{fmt}" if naming_mode != "original" else f"{pdf_path.stem}_page_{idx:03d}.{fmt}"
                out_path = pdf_out_dir / fname
                
                if out_path.exists() and not strategy.output.overwrite_existing:
                    continue
                    
                image.save(out_path)
                logger.info(f"  Saved {fname}")
        except Exception as e:
             logger.error(f"Failed to extract PDF {pdf_path.name}: {e}")
