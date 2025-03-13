## Introduction to the Project

The Real Estate Data Crawler is a specialized Python tool designed to extract, process, and analyze property listings from various real estate websites. This tool leverages web scraping technologies to collect valuable data such as property prices, addresses, square footage, number of bedrooms and bathrooms, and other relevant metrics from multiple sources. By automating the data collection process, this tool enables comprehensive real estate market analysis and tracking of property trends over time.

The decision to utilize Poetry for environment management provides several advantages over traditional Python package management approaches. Poetry offers deterministic builds, dependency resolution, and simplified project configuration through a single `pyproject.toml` file. This enables developers to create isolated, reproducible environments with precise control over dependencies, ensuring consistency across development, testing, and production environments.

## Poetry Installation and Environment Setup

Before setting up the project environment, ensure that Python (version 3.7 or higher) is installed on your system. The initial step involves installing Poetry, which can be accomplished through the official installation script. For most Unix-based systems, the following command is recommended:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

For Windows users, Poetry can be installed using PowerShell:

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

After installing Poetry, verify the installation by checking the version:

```bash
poetry --version
```

Once Poetry is successfully installed, create a new project directory and navigate to it. You can initialize a new Poetry project using the `poetry init` command, which will guide you through creating a `pyproject.toml` file interactively. This file serves as the central configuration for your project, defining metadata and dependencies:

```bash
mkdir real-estate-crawler
cd real-estate-crawler
poetry init
```

During the initialization process, you will be prompted to provide essential project information such as the name, version, description, author, license, and Python version compatibility. For our real estate crawler, appropriate responses might include:

```
name: real-estate-crawler
version: 0.1.0
description: A tool for scraping and analyzing real estate data
author: Your Name <your.email@example.com>
license: MIT
python: ^3.9
```

The `pyproject.toml` file will be created with this basic configuration. According to Poetry's documentation, at minimum, the name and version fields are required for package mode projects.

## Dependencies Configuration

After initializing the project, the next step involves adding the necessary dependencies for the real estate crawler. For web scraping functionality, several key libraries are essential:

```bash
poetry add requests beautifulsoup4 selenium pandas 
```

For more advanced data processing and visualization requirements, additional packages can be incorporated:

```bash
poetry add numpy matplotlib streamlit
```

These dependencies will be automatically added to your `pyproject.toml` file, along with their specific versions. Poetry creates a `poetry.lock` file that locks the exact versions of all dependencies, ensuring reproducible builds across different environments.

To install development dependencies that are not required in production, such as testing frameworks or linters, use the `--group dev` flag:

```bash
poetry add pytest black isort mypy --group dev
```

This configuration ensures that your project is well-structured and ready for development, testing, and deployment.

## Using the Poetry Virtual Environment

One of Poetry's key strengths is its ability to create and manage virtual environments. To activate the Poetry-managed virtual environment for your project, use:

```bash
poetry shell
```

This command spawns a new shell with the virtual environment activated. Alternatively, you can run commands within the virtual environment without activating it using:

```bash
poetry run python -m real_estate_crawler.main
```

To add your package in development mode, allowing changes to be immediately reflected without reinstallation, use:

```bash
poetry install
```

This command installs your package and all its dependencies in the virtual environment based on the pyproject.toml file[^7].

## Customizing the pyproject.toml File

The pyproject.toml file can be further customized to include additional project metadata and configuration options. According to the Poetry documentation, the following fields can be added[^7]:

```toml
[tool.poetry]
name = "real-estate-crawler"
version = "0.1.0"
description = "A Python tool for scraping and analyzing real estate data"
authors = ["Your Name <your.email@example.com>"]
readme = "README.md"
license = "MIT"
repository = "https://github.com/yourusername/real-estate-crawler"
documentation = "https://real-estate-crawler.readthedocs.io"
keywords = ["real estate", "web scraping", "data analysis"]

[tool.poetry.dependencies]
python = "^3.9"
requests = "^2.28.0"
beautifulsoup4 = "^4.11.0"
selenium = "^4.2.0"
pandas = "^1.4.0"
numpy = "^1.22.0"
matplotlib = "^3.5.0"
streamlit = "^1.10.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.0.0"
black = "^22.3.0"
isort = "^5.10.0"
mypy = "^0.961"

[tool.poetry.scripts]
real-estate-crawler = "real_estate_crawler.main:main"

[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"
```

The `[tool.poetry.scripts]` section defines entry points for your package, allowing users to run the crawler directly from the command line after installation[^7].

## Advanced Configuration Options

For more complex projects, Poetry offers additional configuration options that can be useful:

### Python Version Management

Poetry can manage multiple Python versions for your project:

```toml
[tool.poetry.dependencies]
python = ">=3.8,<3.11"
```

This configuration ensures compatibility with Python versions 3.8, 3.9, and 3.10[^7].

[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)
