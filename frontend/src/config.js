// Configuration for different environments
const config = {
  // When running locally
  development: {
    apiUrl: 'http://localhost:5000/api'
  },
  // When deployed to Render
  production: {
    // Construct the API URL from host environment variable
    // Make sure we don't add https:// if the host already includes it
    apiUrl: process.env.REACT_APP_API_HOST 
      ? (process.env.REACT_APP_API_HOST.startsWith('http') 
          ? `${process.env.REACT_APP_API_HOST}/api` 
          : `https://${process.env.REACT_APP_API_HOST}/api`)
      : '/api', // Fallback for direct deployment
    
    // No mock mode needed when we have a real backend
    isMockMode: false
  }
};

// Determine which environment we're in
const environment = process.env.NODE_ENV || 'development';

// Log the configuration for debugging
console.log('Using API URL:', config[environment].apiUrl);

// Export the configuration for the current environment
export default config[environment]; 