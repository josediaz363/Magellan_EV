# Magellan EV Tracker v3.0 Deployment Guide

## Overview
This document provides instructions for deploying the Magellan EV Tracker v3.0 application to Railway.app.

## Prerequisites
- Railway.app account
- Git installed on your local machine

## Deployment Steps

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd <repository-directory>
```

### 2. Upload the Deployment Package
- Extract the provided `v3.0_deployment.zip` file
- Copy all files to your repository directory
- Commit and push the changes:
```bash
git add .
git commit -m "Add Magellan EV Tracker v3.0 deployment files"
git push
```

### 3. Deploy to Railway.app
1. Log in to your Railway.app account
2. Create a new project
3. Select "Deploy from GitHub repo"
4. Connect your GitHub account if not already connected
5. Select the repository containing the Magellan EV Tracker code
6. Configure the following settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python simple_app.py`

### 4. Configure Environment Variables
Add the following environment variables in the Railway.app dashboard:
- `FLASK_APP=simple_app.py`
- `FLASK_ENV=production`
- `SECRET_KEY=your-secret-key` (replace with a secure random string)

### 5. Database Configuration
The application uses SQLite by default, which is recommended for simplicity and stability as per your preferences. No additional database configuration is required.

### 6. Verify Deployment
Once deployed, Railway.app will provide a URL to access your application. Open this URL in your browser to verify that the application is running correctly.

## Troubleshooting
- If you encounter any issues with the deployment, check the Railway.app logs for error messages
- Ensure all required files and directories are included in the deployment package
- Verify that the `requirements.txt` file includes all necessary dependencies

## Support
For additional support or questions, please contact the development team.
