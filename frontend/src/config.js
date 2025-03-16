// Configuration for different environments
const config = {
  // When running locally
  development: {
    apiUrl: 'http://localhost:5000/api'
  },
  // When deployed to GitHub Pages
  production: {
    // For GitHub Pages deployment, we need to handle the lack of a backend server
    // Option 1: Use Firebase functions or another serverless backend
    // apiUrl: 'https://your-firebase-function-url.com/api'
    
    // Option 2: For demo purposes, we can use the same Firebase client-side functionality
    // This approach won't support the backend API calls, but will allow basic Firebase features to work
    apiUrl: window.location.origin + '/meme-generator/api',
    useLocalStorage: true,
    isMockMode: true
  }
};

// Determine which environment we're in
const environment = process.env.NODE_ENV || 'development';

// Export the configuration for the current environment
export default config[environment]; 