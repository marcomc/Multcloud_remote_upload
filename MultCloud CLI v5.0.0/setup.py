from setuptools import setup, find_packages

setup(
    name="multcloud-cli",
    version="5.0.0",
    packages=find_packages(),
    install_requires=[
        "pycryptodome>=3.19.0",
        "requests>=2.31.0",
    ],
    extras_require={
        "dev": ["pytest>=7.0", "pytest-cov", "ruff"],
    },
    entry_points={
        "console_scripts": ["multcloud=multcloud.cli:main"],
    },
    python_requires=">=3.9",
)
