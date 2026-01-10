#!/usr/bin/env python3
"""Setup script for California Court Case Tracker."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ca-court-tracker",
    version="1.0.0",
    author="CA Court Tracker",
    description="California Court Case Tracking Application",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Legal Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "ca-court-tracker=ca_court_tracker.cli:main",
        ],
    },
)
