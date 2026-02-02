from pdf_converter.foundation.logger_service import logger
from pdf_converter.foundation.data_schemas import AppSettings
from pdf_converter.core.image_to_pdf import ImageToPdfConverter
from pdf_converter.core.pdf_to_image import PdfToImageConverter

class ConversionEngine:
    def __init__(self, settings: AppSettings):
        self.settings = settings

    def execute(self):
        logger.info(f"Engine Work Mode: {self.settings.work_mode}")
        
        if self.settings.work_mode == "img2pdf":
            worker = ImageToPdfConverter(self.settings)
            worker.run()
        elif self.settings.work_mode == "pdf2img":
            worker = PdfToImageConverter(self.settings)
            worker.run()
        else:
            logger.error(f"Unsupported work mode: {self.settings.work_mode}")
