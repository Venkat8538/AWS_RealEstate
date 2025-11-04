from setuptools import setup, find_packages

setup(
    name="house-price-training",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "xgboost==1.7.5",
        "scikit-learn>=1.3.0", 
        "pandas>=2.0.0",
        "numpy>=1.26.4",
        "mlflow>=2.8.0",
        "boto3>=1.34.0"
    ]
)