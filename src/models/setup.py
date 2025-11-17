from setuptools import setup, find_packages

setup(
    name="house-price-training",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "xgboost==1.7.5"
    ]
)