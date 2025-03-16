# Meme-ify Your Brand

A fun meme generator that helps businesses create viral marketing content based on their brand.

Live demo: [https://shereeef1.github.io/meme-generator](https://shereeef1.github.io/meme-generator)

## Features

- Brand information scraping and analysis
- AI-powered meme text suggestions
- High-quality meme image generation
- Simple and intuitive UI
- Firebase integration for usage tracking

## Deployment Instructions

### GitHub Pages Deployment

The app is configured to deploy automatically to GitHub Pages using GitHub Actions.

When you push to the main/master branch, it will:

1. Build the React app
2. Deploy to GitHub Pages
3. The site will be available at `https://shereeef1.github.io/meme-generator`

### Manual Deployment

If you want to deploy manually:

```bash
# Clone the repo
git clone https://github.com/shereeef1/meme-generator.git
cd meme-generator

# Install dependencies
cd frontend
npm install

# Build and deploy
npm run deploy
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

## Local Development

```bash
# Start the development server
cd frontend
npm start
```

## License

This project is for demonstration purposes. Contact Sher at +91 7888117894 for commercial usage.
