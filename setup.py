#!/usr/bin/env python3
"""
EasyWiki — Agent-Driven Knowledge Base
Setup script for pip installation with CLI entry point.
"""
from setuptools import setup, find_packages

setup(
    name="easywiki",
    version="1.0.0",
    description="Agent-Driven Organizational Knowledge Base",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "numpy>=1.24.0",
        "pyjwt>=2.8.0",
        "python-multipart>=0.0.6",
        "bcrypt>=4.0.0",
        "jieba>=0.42.1",
        "sentence-transformers>=2.2.0",
    ],
    entry_points={
        "console_scripts": [
            "easywiki=orgmind.cli:main",
        ],
    },
    python_requires=">=3.10",
)
