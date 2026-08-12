# local-pdf2md

Convert a PDF into structured Markdown locally with [MinerU](https://github.com/opendatalab/MinerU) through a simple Python command-line wrapper.

MinerU performs the document parsing, including text, headings, equations in LaTeX, tables, and supported document structure. The wrapper manages input and output paths, hides MinerU's intermediate output, and preserves referenced image assets.

## Privacy

PDF conversion and model inference run on your computer. MinerU starts a temporary service bound to `127.0.0.1` as part of its local architecture; this is a loopback connection and not a cloud API.

Installation and the first conversion require internet access to download Python packages and MinerU model files. Documents are not uploaded by this project.

## Requirements

The primary supported environments are recent Linux distributions and WSL2.

- Python 3.10 through 3.13
- At least 16 GB system RAM; 32 GB or more is recommended
- At least 20 GB of available disk space; an SSD is recommended
- A current `pip` installation

A GPU is optional. When compatible local acceleration is available, the wrapper uses MinerU's high-accuracy hybrid backend. Otherwise, it uses MinerU's CPU-capable pipeline backend.

For GPU acceleration, MinerU recommends:

- An NVIDIA GPU with Volta architecture or newer, or supported Apple Silicon
- At least 8 GB of GPU memory for the VLM/hybrid backend
- A driver compatible with the CUDA runtime selected by PyTorch

CPU conversion is slower. Complex and scanned documents generally require more time and memory than native-text PDFs.

## Installation

Clone the repository and run the installer:

```bash
git clone https://github.com/FilipiKunz/local-pdf2md.git
cd local-pdf2md
./install.sh
```

The installer follows MinerU's recommended `uv` installation method and creates an isolated environment at `~/.venvs/local-pdf2md`. It does not install MinerU into the repository.

Verify the installation:

```bash
python verify_install.py
```

## Usage

Create Markdown beside the input PDF with the same basename:

```bash
python pdf_to_md.py input.pdf
```

Example:

```text
paper.pdf -> paper.md
```

Specify a different Markdown output path:

```bash
python pdf_to_md.py input.pdf output.md
```

If MinerU extracts images or other referenced files, the wrapper creates an `<output-name>_assets` directory beside the Markdown file and updates the references accordingly.

## Performance and GPU usage

The first conversion downloads the required MinerU models and takes longer than later runs. GPU inference requires enough free GPU memory when conversion starts. Other CUDA applications can prevent MinerU's inference engine from loading even when the GPU itself is supported.

The temporary MinerU API and model processes stop after each conversion. They do not reserve GPU memory between invocations.

## Troubleshooting

### MinerU is unavailable

Run the installer again:

```bash
./install.sh
```

### Engine core initialization failed

Check current GPU use:

```bash
nvidia-smi
```

Close or wait for other GPU workloads that consume most of the available GPU memory, then retry the conversion.

### CUDA is not detected

Run:

```bash
python verify_install.py
```

If PyTorch cannot access the GPU, the wrapper uses MinerU's CPU pipeline. Consult the [MinerU installation guide](https://opendatalab.github.io/MinerU/quick_start/) and the PyTorch installation instructions for the installed operating system and GPU.

## Third-party software and licenses

This repository contains only the wrapper and installation utilities. It does not contain or redistribute MinerU source code or model weights.

MinerU is downloaded separately during installation and is governed by the [MinerU Open Source License](https://github.com/opendatalab/MinerU/blob/master/LICENSE.md), which is based on Apache License 2.0 with additional terms. MinerU's dependencies and downloaded models may have their own licenses. The currently selected MinerU 2.5 Pro model is published under Apache License 2.0.

This project is an independent community wrapper and is not affiliated with or endorsed by the MinerU project or OpenDataLab.

The wrapper code in this repository is licensed under the MIT License. See [LICENSE](LICENSE).
