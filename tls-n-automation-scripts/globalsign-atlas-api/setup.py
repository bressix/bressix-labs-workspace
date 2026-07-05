# setup.py
from setuptools import setup, find_packages

setup(
    name="atlas-cli",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'requests>=2.31.0',
        'cryptography>=41.0.0',
        'python-dotenv>=1.0.0',
        'pyyaml>=6.0',
    ],
    entry_points={
        'console_scripts': [
            'atlas=bin.atlas_cli:main',
        ],
    },
    author="bressix LABs",
    description="CLI para API GlobalSign Atlas - Automação de certificados TLS/mTLS",
    license="GPL-3.0",
    python_requires=">=3.8",
)
