import sys
import os

# Add src to python path to allow imports from pdf_converter
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from pdf_converter import bootstrap

if __name__ == "__main__":
    bootstrap()
