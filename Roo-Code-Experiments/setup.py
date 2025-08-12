from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ltm-validation-pipeline",
    version="0.1.0",
    author="LTM Pipeline Team",
    description="Experimental pipeline to validate Phase 1 of a long-term memory system for coding assistants",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ltm-validation-pipeline",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "dataclasses-json>=0.6.3",
        "pydantic>=2.5.0",
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "nltk>=3.8.1",
        "spacy>=3.7.0",
        "textdistance>=4.6.0",
        "scikit-learn>=1.3.0",
        "scipy>=1.11.0",
        "structlog>=23.2.0",
        "rich>=13.7.0",
        "python-dotenv>=1.0.0",
        "click>=8.1.7",
        "tqdm>=4.66.0",
        "jsonschema>=4.20.0",
        "pyyaml>=6.0.1",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.12.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "ltm-pipeline=scripts.run_pipeline:main",
            "ltm-generate-data=scripts.generate_data:main",
            "ltm-evaluate=scripts.evaluate_results:main",
        ],
    },
)