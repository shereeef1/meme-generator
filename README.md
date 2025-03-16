# Meme-ify Your Brand

A fun meme generator that helps businesses create viral marketing content based on their brand.

## Features

- Brand information scraping and analysis
- AI-powered meme text suggestions
- High-quality meme image generation
- Simple and intuitive UI
- Firebase integration for usage tracking

## Deployment Instructions

### Render.com One-Click Deployment (Recommended)

This app is configured for easy deployment on Render.com using the `render.yaml` file:

1. Fork/clone this repository to your GitHub account
2. Create a Render.com account and connect it to your GitHub
3. Click "New Blueprint" in your Render dashboard
4. Select the repository with this code
5. Render will automatically detect the `render.yaml` and set up both:
   - The Python Flask backend API
   - The React frontend static site
6. Add your environment variables (Firebase configuration)
7. Click "Apply" to deploy both services at once

The `render.yaml` file handles all the configuration for you! Both services will be deployed and linked automatically.

### GitHub Pages Deployment

For a static demo version (without backend functionality):

```bash
# Clone the repo
git clone https://github.com/shereeef1/meme-generator.git
cd meme-generator

# Install dependencies
cd frontend
npm install

# Update config.js to use isMockMode: true
# Then build and deploy
npm run deploy
```

### Manual Deployment

If you want to deploy services individually:

```bash
# Backend deployment
cd backend
pip install -r requirements.txt
python app.py

# Frontend deployment
cd frontend
npm install
npm run build
```

## Environment Setup

For local development:

1. Create a `.env` file in the `frontend` directory with:

```
REACT_APP_FIREBASE_API_KEY=your_firebase_api_key
REACT_APP_FIREBASE_AUTH_DOMAIN=your_firebase_auth_domain
REACT_APP_FIREBASE_PROJECT_ID=your_firebase_project_id
REACT_APP_FIREBASE_STORAGE_BUCKET=your_firebase_storage_bucket
REACT_APP_FIREBASE_MESSAGING_SENDER_ID=your_firebase_messaging_sender_id
REACT_APP_FIREBASE_APP_ID=your_firebase_app_id
```

2. Create a `.env` file in the `backend` directory with similar Firebase configuration.

## Local Development

```bash
# Start the backend server
cd backend
python app.py

# In a separate terminal, start the frontend
cd frontend
npm start
```

## License

This project is for demonstration purposes. Contact Sher at +91 7888117894 for commercial usage.
