from setuptools import setup, find_packages

setup(
    name="hr_parser",
    version="0.1.0",
    description="Drop-in resume -> Canonical JSON -> Mongo module",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.12",
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "pydantic>=2.0.0",
        "openai>=1.0.0",
        "tenacity>=8.0.0",
        "pymongo>=4.0.0",
        "python-dotenv>=1.0.0",
        "pymupdf>=1.23.0",
        "python-docx>=0.8.11",
        "pytesseract>=0.3.10",
        "numpy>=1.24.0",
        "scikit-learn>=1.3.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
        ],
    },
)
