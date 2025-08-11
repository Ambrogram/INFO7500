#!/usr/bin/env python3
"""
Setup script for Bitcoin Text-to-SQL System
"""

from setuptools import setup, find_packages
import os

# Read README for long description
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="bitcoin-text-to-sql",
    version="1.0.0",
    author="Bitcoin Text-to-SQL Team",
    author_email="your.email@example.com",
    description="A comprehensive system that converts natural language questions about Bitcoin blockchain data into SQL queries",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/text-to-sql-bitcoin",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Database",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.2.0",
            "pytest-cov>=2.12.0",
            "black>=21.0.0",
            "flake8>=3.9.0",
            "mypy>=0.910",
        ],
        "web": [
            "fastapi>=0.68.0",
            "uvicorn>=0.15.0",
            "jinja2>=3.0.0",
        ],
        "analysis": [
            "pandas>=1.3.0",
            "matplotlib>=3.4.0",
            "plotly>=5.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "bitcoin-etl=etl.etl_sync:main",
            "bitcoin-text2sql=text2sql.text_to_sql:main",
            "bitcoin-validator=text2sql.validator:main",
            "bitcoin-tests=tests.run_tests:main",
            "bitcoin-reorg-check=etl.reorg_check:main",
            "bitcoin-demo=demo:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.sql", "*.json", "*.yml", "*.yaml", "*.conf", "*.sh"],
    },
    zip_safe=False,
    keywords="bitcoin, blockchain, sql, text-to-sql, etl, database, cryptocurrency",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/text-to-sql-bitcoin/issues",
        "Source": "https://github.com/yourusername/text-to-sql-bitcoin",
        "Documentation": "https://github.com/yourusername/text-to-sql-bitcoin#readme",
    },
) 