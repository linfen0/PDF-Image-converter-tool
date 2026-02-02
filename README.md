# PDF-Image Converter Tool

一款专业、可配置的 Python 工具，用于在 PDF 文件和图片之间进行转换。基于 Python 3.12 构建并使用 `uv` 管理。

## 核心功能

- **图片转 PDF (img2pdf)**:
  - 支持多图合并为一个 PDF (`many_to_one`)。
  - 支持单图转换为单个 PDF (`one_to_one`)。
  - 支持自动重命名以防止覆盖。
- **PDF 转图片 (pdf2img)**:
  - 将 PDF 的每一页转换为独立图片。
  - 支持自定义 DPI 和颜色模式（RGB/灰度）。
  - 支持多种输出格式 (PNG, JPG, WebP)。
- **配置驱动**: 所有运行参数均通过 `config.toml` 控制。
- **专业日志**: 支持 UTC 时间戳和彩色终端输出，通过颜色区分日志级别和警告类型。

---

## 环境准备

本项使用 `uv` 进行依赖和环境管理。

### 1. 安装 uv
如果尚未安装 `uv`，请根据操作系统执行以下操作：
- **Windows**: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`
- **macOS/Linux**: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 2. 安装前置依赖 (Poppler)
`pdf2img` 功能依赖于 `Poppler` 库。请根据您的操作系统进行安装：

#### **Windows**
推荐使用 **Uniget Desktop** (图形界面) 或包管理器安装以自动配置环境变量：
1. **Uniget Desktop (推荐)**: 访问 [Uniget Desktop 官网](https://unigetui.com/) 下载并安装。在程序内搜索 `poppler` 并安装，它会自动配置 PATH。
2. **Winget**: `winget install poppler`
3. **Uniget (CLI)**: `uniget install poppler`

亦可手动安装：
1. 访问 [Poppler for Windows](https://github.com/oschwartz10612/poppler-windows/releases)。
2. 下载最新版本的二进制压缩包（如 `Release-xx.x.x-x.zip`）。
3. 解压并将 `bin` 文件夹路径添加至系统的 **环境变量 (PATH)** 中。

#### **macOS**
使用 Homebrew 安装：
```bash
brew install poppler
```

#### **Linux (Ubuntu/Debian)**
使用 apt 安装：
```bash
sudo apt-get update
sudo apt-get install poppler-utils
```

---

## 快速上手

### 1. 初始化环境与安装依赖
在项目根目录下运行：
```bash
uv sync
```

### 2. 配置程序
修改根目录下的 `config.toml` 文件：
- 设置 `work_mode` ("img2pdf" 或 "pdf2img")。
- 设置 `input_dir` (输入目录) 和 `output_dir` (输出目录)。
- 根据需要调整 PDF 或图片的输出策略。

### 3. 运行程序
```bash
uv run python jpg2pdf.py
```
或者指定配置文件：
```bash
uv run python jpg2pdf.py --config custom_config.toml
```

---

## 许可证
MIT License
