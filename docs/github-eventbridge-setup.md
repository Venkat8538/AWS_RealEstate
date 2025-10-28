# GitHub Actions + EventBridge Setup

## Overview
This setup enables automatic triggering of SageMaker pipelines when code changes are pushed to the main branch.

## Flow
1. **GitHub Push** → **GitHub Actions** → **EventBridge** → **SageMaker Pipeline**

## Setup Steps

### 1. Configure GitHub Secrets
Add these secrets to your GitHub repository:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

### 2. Deploy Infrastructure
```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### 3. Test the Integration
Push changes to main branch in these paths:
- `src/`
- `notebooks/`
- `data/`

## Event Structure
```json
{
  "Source": "github.mlops",
  "DetailType": "ML Pipeline Trigger",
  "Detail": {
    "repository": "your-org/house-price-predictor",
    "commit": "abc123...",
    "branch": "main",
    "trigger": "code_change"
  }
}
```

## Pipeline Parameters
The EventBridge rule passes these parameters to SageMaker Pipeline:
- `GitCommit`: The commit SHA that triggered the pipeline
- `GitBranch`: The branch name (usually 'main')

## Monitoring
- Check GitHub Actions logs for event sending status
- Monitor EventBridge rules in AWS Console
- View SageMaker Pipeline executions in SageMaker Studio