import axios from 'axios';

// Create an axios instance with default configs
const api = axios.create({
  baseURL: process.env.NODE_ENV === 'production' 
    ? '/api'  // In production, the API will be at the same host
    : 'http://localhost:5000/api',  // In development, use the local server
  headers: {
    'Content-Type': 'application/json',
  },
});

// Generate memes API call
export const generateMemes = async (text) => {
  const response = await api.post('/generate-meme', { text });
  return response.data;
};

// Export the API
export default api; 