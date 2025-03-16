import axios from 'axios';

// Create an axios instance with default configs
const api = axios.create({
  baseURL: process.env.NODE_ENV === 'production' 
    ? '/api'  // In production, the API will be at the same host
    : 'http://localhost:5000/api',  // In development, use the local server with /api
  headers: {
    'Content-Type': 'application/json',
  },
  // Add timeout to prevent long-hanging requests
  timeout: 30000,
  // Disable credentials for development
  withCredentials: false
});

// Add response interceptor for better error handling
api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error.message);
    if (error.response) {
      console.error('Error response data:', error.response.data);
    } else if (error.request) {
      console.error('No response received:', error.request);
      // Log additional information for connection refused errors
      if (error.message.includes('Network Error') || error.message.includes('Connection refused')) {
        console.error('Connection refused. Please ensure the backend server is running on http://localhost:5000');
      }
    } else {
      console.error('Error setting up request:', error.message);
    }
    return Promise.reject(error);
  }
);

// Add request interceptor for debugging
api.interceptors.request.use(
  config => {
    console.log(`Making ${config.method.toUpperCase()} request to ${config.url}`);
    return config;
  },
  error => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Get news API call
const getNews = async (limit = 20) => {
  try {
    const response = await api.get('/news', {
      params: { limit }
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching news:', error);
    return {
      success: false,
      error: error.message,
      message: 'Failed to fetch news. Please try again.'
    };
  }
};

// Generate news-based meme prompt
const generateNewsPrompt = async (news, brandData) => {
  try {
    console.log('Generating news prompt with:', { 
      newsTitle: news?.title, 
      brandName: brandData?.name || 'Unknown'
    });
    
    const requestData = {
      news,
      brandData
    };
    
    console.log('Request data:', JSON.stringify(requestData).slice(0, 200) + '...');
    
    const response = await api.post('/generate-news-prompt', requestData);
    console.log('News prompt response:', response.status, response.statusText);
    
    if (response.data) {
      return response.data;
    }
    
    return {
      success: false,
      message: 'Empty response from server'
    };
  } catch (error) {
    console.error('Error generating news prompt:', error);
    if (error.response) {
      console.error('Response data:', error.response.data);
      console.error('Response status:', error.response.status);
      console.error('Response headers:', error.response.headers);
    } else if (error.request) {
      console.error('No response received:', error.request);
    } else {
      console.error('Error message:', error.message);
    }
    throw error;
  }
};

// Generate memes API call
const generateMeme = async (prompt, brandData) => {
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
const scrapeBrandData = async (url, category, country) => {
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
const generatePrompts = async (brandData) => {
  try {
    console.log('Sending generate prompts request with brand data:', {
      brand_name: brandData.brand_name,
      raw_text_length: brandData.raw_text ? brandData.raw_text.length : 0,
      category: brandData.category,
      country: brandData.country,
      prompt_count: brandData.prompt_count
    });
    
    // Increase timeout for this specific request
    const response = await api.post('/generate-prompts', brandData, {
      timeout: 120000 // 2 minutes timeout for prompt generation
    });
    
    console.log('Generate prompts response status:', response.status);
    if (response.data && !response.data.success) {
      console.error('API returned error:', response.data.error || response.data.message);
    }
    
    return response.data;
  } catch (error) {
    console.error('Error generating prompts:', error);
    if (error.response) {
      console.error('Error response data:', error.response.data);
      console.error('Error response status:', error.response.status);
      // Return the actual error from the server if available
      return {
        success: false,
        error: error.response.data.error || error.message,
        message: error.response.data.message || 'Failed to generate meme prompt suggestions. Please try again.'
      };
    }
    
    return {
      success: false,
      error: error.message || 'An error occurred',
      message: 'Failed to generate meme prompt suggestions. Please try again.'
    };
  }
};

// Get documents API call
const getDocuments = async (page = 1, per_page = 10) => {
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
const deleteDocument = async (docId) => {
  try {
    const response = await api.delete(`/documents/${docId}`);
    return response.data;
  } catch (error) {
    console.error('Error deleting document:', error);
    throw error;
  }
};

// Update document API call
const updateDocument = async (docId, content) => {
  try {
    const response = await api.put(`/documents/${docId}`, { content });
    return response.data;
  } catch (error) {
    console.error('Error updating document:', error);
    throw error;
  }
};

// Get document API call
const getDocument = async (docId) => {
  try {
    const response = await api.get(`/documents/${docId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching document:', error);
    throw error;
  }
};

// Upload brand file API call
const uploadBrandFile = async (file) => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/upload-brand-file', formData);
    return response.data;
  } catch (error) {
    console.error('Error uploading brand file:', error);
    throw error;
  }
};

// Export all API functions
export {
  getNews,
  generateNewsPrompt,
  generateMeme,
  scrapeBrandData,
  generatePrompts,
  getDocuments,
  deleteDocument,
  updateDocument,
  getDocument,
  uploadBrandFile
};

// Export the API
export default api; 