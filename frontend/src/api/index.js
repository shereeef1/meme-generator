import axios from 'axios';

// Create an axios instance with default configs
const api = axios.create({
  baseURL: process.env.NODE_ENV === 'production' 
    ? '/api'  // In production, the API will be at the same host
    : 'http://localhost:5000/api',  // In development, use the local server
  headers: {
    'Content-Type': 'application/json',
  },
  // Add timeout to prevent long-hanging requests
  timeout: 30000,
});

// Add response interceptor for better error handling
api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error.message);
    if (error.response) {
      console.error('Error response data:', error.response.data);
    }
    return Promise.reject(error);
  }
);

// Generate memes API call
export const generateMeme = async (prompt, brandData) => {
  try {
    const response = await api.post('/generate-meme', { prompt, brandData });
    return response.data;
  } catch (error) {
    console.error('Error generating memes:', error);
    return {
      success: false,
      error: error.message,
      message: 'Failed to generate memes. Please try again.'
    };
  }
};

// Scrape brand data API call
export const scrapeBrandData = async (url, category, country) => {
  try {
    console.log('Sending scrape request with:', { url, category, country });
    const response = await api.post('/scrape-brand', { 
      url,
      category,
      country
    });
    return response.data;
  } catch (error) {
    console.error('Error scraping brand data:', error);
    return {
      success: false,
      error: error.message || 'An error occurred',
      message: 'Failed to scrape brand data. Please check the URL and try again.'
    };
  }
};

// Generate prompts API call
export const generatePrompts = async (brandData) => {
  try {
    console.log('Sending generate prompts request with brand data');
    const response = await api.post('/generate-prompts', brandData);
    return response.data;
  } catch (error) {
    console.error('Error generating prompts:', error);
    return {
      success: false,
      error: error.message || 'An error occurred',
      message: 'Failed to generate meme prompt suggestions. Please try again.'
    };
  }
};

// Get documents API call
export const getDocuments = async (page = 1, per_page = 10) => {
  try {
    const response = await api.get('/documents', {
      params: { page, per_page }
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching documents:', error);
    throw error;
  }
};

// Delete document API call
export const deleteDocument = async (docId) => {
  try {
    const response = await api.delete(`/documents/${docId}`);
    return response.data;
  } catch (error) {
    console.error('Error deleting document:', error);
    throw error;
  }
};

// Update document API call
export const updateDocument = async (docId, content) => {
  try {
    const response = await api.put(`/documents/${docId}`, { content });
    return response.data;
  } catch (error) {
    console.error('Error updating document:', error);
    throw error;
  }
};

// Export the API
export default api; 