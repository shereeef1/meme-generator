// Configuration for different environments
const config = {
  // When running locally
  development: {
    apiUrl: 'http://localhost:5000/api'
  },
  // When deployed to Render
  production: {
    // Construct the API URL from host and port environment variables
    apiUrl: process.env.REACT_APP_API_HOST && process.env.REACT_APP_API_PORT
      ? `https://${process.env.REACT_APP_API_HOST}:${process.env.REACT_APP_API_PORT}/api`
      : process.env.REACT_APP_API_HOST 
        ? `https://${process.env.REACT_APP_API_HOST}/api`
        : '/api', // Fallback for direct deployment
    
    // No mock mode needed when we have a real backend
    isMockMode: false
  }
};

// Determine which environment we're in
const environment = process.env.NODE_ENV || 'development';

// Export the configuration for the current environment
export default config[environment]; 