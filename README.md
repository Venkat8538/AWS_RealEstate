# MLOps Lifecycle - House Price Prediction

## Architecture Overview

![MLOps Architecture](mlops-architecture.png)

This project demonstrates a complete MLOps lifecycle using AWS services for house price prediction. The architecture follows AWS best practices for multi-account MLOps deployment across development, staging, and production environments.

## Key Components

- **Data Account**: Centralized data sources and Amazon SageMaker Studio for data scientists
- **Development Account**: Feature development with SageMaker Feature Store and Model Registry
- **Artifact Account**: Container registry (ECR) and model artifacts storage (S3)
- **CI/CD Account**: Automated pipelines using CodeBuild and CodePipeline
- **Staging/Production Accounts**: Deployment environments with auto-scaling and monitoring

## Getting Started

1. **Setup Infrastructure**: Use Terraform configurations in `terraform/` directory
2. **Data Processing**: Run notebooks in `notebooks/` for data exploration and feature engineering
3. **Model Training**: Execute SageMaker pipelines for automated training
4. **Deployment**: Deploy using containerized applications with FastAPI and Streamlit

## Project Structure

```
├── notebooks/          # Jupyter notebooks for experimentation
├── src/               # Source code for ML pipeline
├── terraform/         # Infrastructure as Code
├── streamlit_app/     # Web application
└── .github/workflows/ # CI/CD pipelines
```