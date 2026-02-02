import argparse
from pdf_converter.foundation.config_handler import ConfigHandler
from pdf_converter.core.engine import ConversionEngine
from pdf_converter.foundation.logger_service import logger

def bootstrap():
    parser = argparse.ArgumentParser(description="Professional PDF/Image Converter Tool")
    parser.add_argument("--config", default="config.toml", help="Path to config file")
    args = parser.parse_args()
    
    handler = ConfigHandler(args.config)
    settings = handler.load()
    
    engine = ConversionEngine(settings)
    engine.execute()

if __name__ == "__main__":
    bootstrap()
