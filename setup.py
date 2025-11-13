"""
Setup script for package installation
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding='utf-8') if readme_file.exists() else ""

setup(
    name="file-purge-system",
    version="1.0.0",
    author="Team 13",
    author_email="team13@cecs451.edu",
    description="AI-powered file management system using machine learning",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/team13/file-purge-system",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: System :: Filesystems",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.21.0",
        "pandas>=1.3.0",
        "scikit-learn>=1.0.0",
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=3.0.0',
            'black>=22.0.0',
            'flake8>=4.0.0',
            'pyinstaller>=5.0.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'file-purge=main:main',
        ],
    },
    include_package_data=True,
    zip_safe=False,
)