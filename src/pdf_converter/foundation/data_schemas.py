from dataclasses import dataclass
from typing import Literal
from pathlib import Path

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
