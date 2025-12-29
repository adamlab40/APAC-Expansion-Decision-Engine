"""Setup script for APAC Expansion Decision Engine."""
from setuptools import setup, find_packages

setup(
    name="apac-expansion-engine",
    version="1.0.0",
    description="Data-driven APAC market expansion decision engine for B2B SaaS",
    author="Management Consulting Analytics",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "pyyaml>=6.0",
        "streamlit>=1.28.0",
        "plotly>=5.17.0",
        "python-pptx>=0.6.21",
        "scipy>=1.11.0",
        "openpyxl>=3.1.0",
    ],
    python_requires=">=3.8",
)

