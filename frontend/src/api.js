const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

// Helper function to create a fetch request with timeout
const fetchWithTimeout = async (url, options, timeout = 60000) => {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);
  
  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    
    clearTimeout(id);
    return response;
  } catch (error) {
    clearTimeout(id);
    throw error;
  }
};

export const scrapeBrandData = async (url, category, country) => {
  try {
    console.log(`API - Scraping brand data from ${url} with timeout protection`);
    
    // Use the fetchWithTimeout helper with a 90-second timeout for scraping
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/scrape-brand`, 
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url,
          category,
          country
        }),
        mode: 'cors',
        credentials: 'same-origin'
      },
      90000 // 90 seconds timeout for scraping operations
    );

    if (!response.ok) {
      // Try to get error details from the response
      const errorData = await response.json().catch(() => ({}));
      console.error('API - Scraping failed:', response.status, errorData);
      throw new Error(errorData.message || `Server error: ${response.status}`);
    }

    const data = await response.json();
    console.log(`API - Scraping successful, received data for: ${data.brand_name || url}`);
    return data;
  } catch (error) {
    // Check for timeout (AbortError)
    if (error.name === 'AbortError') {
      console.error('API - Scraping request timed out:', error);
      return {
        success: false,
        error: 'Request timed out',
        message: 'The scraping operation took too long. Please try again with a smaller website or upload a file instead.'
      };
    }
    
    console.error('API - Error scraping brand data:', error);
    return {
      success: false,
      error: error.message || 'An unknown error occurred',
      message: 'Failed to scrape brand data. Please check the URL or try uploading a file instead.'
    };
  }
};

export const generatePrompts = async (brandData) => {
  try {
    console.log('API - Raw text being sent to server:', 
      brandData.raw_text ? 
      `${brandData.raw_text.substring(0, 100)}... (${brandData.raw_text.length} chars)` : 
      'No raw_text');
    
    const requestData = {
      raw_text: brandData.raw_text,
      brand_name: brandData.brand_name,
      category: brandData.category,
      country: brandData.country
    };
    
    console.log('API - Full request data:', requestData);
    
    const response = await fetch(`${API_BASE_URL}/generate-prompts`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestData),
    });

    if (!response.ok) {
      throw new Error('Network response was not ok');
    }

    return await response.json();
  } catch (error) {
    console.error('Error generating prompts:', error);
    return {
      success: false,
      message: 'Failed to generate prompts. Please try again.'
    };
  }
};

export const generateMeme = async (prompt, brandData) => {
  try {
    console.log('API - generateMeme called with prompt length:', prompt?.length);
    console.log('API - generateMeme first 100 chars of prompt:', prompt?.substring(0, 100));
    
    if (!prompt || !prompt.trim()) {
      console.error('API - generateMeme called with empty prompt');
      return {
        success: false,
        message: 'Prompt cannot be empty'
      };
    }
    
    const payload = {
      prompt,
      brand_name: brandData?.brand_name || '',
      category: brandData?.category || ''
    };
    
    console.log('API - Sending meme generation request with payload:', payload);
    
    const response = await fetch(`${API_BASE_URL}/generate-meme`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
      mode: 'cors',
      credentials: 'same-origin'
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('API - Meme generation failed:', response.status, errorData);
      return {
        success: false,
        message: errorData.message || `Server error: ${response.status}`
      };
    }

    const result = await response.json();
    console.log('API - Meme generation successful, received:', result);
    
    // Validate that we got proper meme URLs
    if (result.success && result.meme_urls && Array.isArray(result.meme_urls)) {
      console.log(`API - Validating ${result.meme_urls.length} meme URLs received`);
      if (result.meme_urls.length === 0) {
        console.warn('API - Empty meme URLs array returned');
      } else {
        // Log the first URL (truncated) for debugging
        console.log('API - First meme URL example:', 
          result.meme_urls[0].substring(0, 50) + '...');
      }
    } else if (result.success) {
      console.warn('API - Success response missing meme_urls array');
    }
    
    return result;
  } catch (error) {
    console.error('API - Error generating meme:', error);
    return {
      success: false,
      message: 'Failed to generate meme. Please try again.'
    };
  }
};

export const uploadBrandFile = async (file, category, country) => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    if (category) formData.append('category', category);
    if (country) formData.append('country', country);

    const response = await fetch(`${API_BASE_URL}/upload-file`, {
      method: 'POST',
      body: formData,
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.message || 'Failed to upload file');
    }
    
    return data;
  } catch (error) {
    console.error('Error uploading file:', error);
    return {
      success: false,
      error: error.message,
      message: 'Failed to upload and process the file'
    };
  }
};

export const fetchNews = async (limit = 20) => {
  try {
    console.log(`API - Fetching ${limit} news articles`);
    
    // Use fetchWithTimeout for a 30-second timeout
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/news?limit=${limit}`, 
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        mode: 'cors',
        credentials: 'same-origin'
      },
      30000 // 30-second timeout
    );

    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }

    const data = await response.json();
    
    if (!data.success) {
      throw new Error(data.message || 'Failed to fetch news');
    }
    
    console.log(`API - Successfully fetched ${data.news.length} news articles`);
    return data;
  } catch (error) {
    // Check for timeout (AbortError)
    if (error.name === 'AbortError') {
      console.error('API - News fetch request timed out:', error);
      return {
        success: false,
        news: [],
        message: 'The request timed out. Please try again later.'
      };
    }
    
    console.error('API - Error fetching news:', error);
    return {
      success: false,
      news: [],
      message: error.message || 'An unknown error occurred while fetching news'
    };
  }
};

export const getDocuments = async (page = 1, perPage = 10) => {
  try {
    const response = await fetch(`${API_BASE_URL}/documents?page=${page}&per_page=${perPage}`);
    
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error fetching documents:', error);
    throw error;
  }
};

export const getDocument = async (docId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/documents/${docId}`);
    
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    
    return await response.blob();
  } catch (error) {
    console.error('Error fetching document:', error);
    throw error;
  }
};

export const updateDocument = async (docId, content) => {
  try {
    const response = await fetch(`${API_BASE_URL}/documents/${docId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ content }),
    });
    
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error updating document:', error);
    throw error;
  }
};

export const deleteDocument = async (docId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/documents/${docId}`, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error deleting document:', error);
    throw error;
  }
};

export const enhancedBrandResearch = async (brandName, category = null, country = null, options = {}) => {
  try {
    console.log(`API - Starting enhanced research for ${brandName}`);
    
    // Prepare options with defaults
    const includeCompetitors = options.includeCompetitors !== false;
    const includeTrends = options.includeTrends !== false;
    
    // Use the fetchWithTimeout helper with a 120-second timeout for enhanced research
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/enhanced-brand-research`, 
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          brand_name: brandName,
          category,
          country,
          include_competitors: includeCompetitors,
          include_trends: includeTrends
        }),
        mode: 'cors',
        credentials: 'same-origin'
      },
      120000 // 120 seconds timeout for enhanced research operations
    );

    if (!response.ok) {
      // Try to get error details from the response
      const errorData = await response.json().catch(() => ({}));
      console.error('API - Enhanced research failed:', response.status, errorData);
      throw new Error(errorData.message || `Server error: ${response.status}`);
    }

    const data = await response.json();
    console.log(`API - Enhanced research successful for: ${data.brand_name || brandName}`);
    
    // Log some details about what was found
    if (data.competitors && data.competitors.length > 0) {
      console.log(`API - Found ${data.competitors.length} competitors`);
    }
    
    if (data.industry_trends && data.industry_trends.length > 0) {
      console.log(`API - Found ${data.industry_trends.length} industry trends`);
    }
    
    return data;
  } catch (error) {
    // Check for timeout (AbortError)
    if (error.name === 'AbortError') {
      console.error('API - Enhanced research request timed out:', error);
      return {
        success: false,
        error: 'Request timed out',
        message: 'The enhanced research operation took too long. Please try with a more specific brand name.'
      };
    }
    
    console.error('API - Error during enhanced brand research:', error);
    return {
      success: false,
      error: error.message || 'An unknown error occurred',
      message: 'Failed to perform enhanced brand research. Please try again later.'
    };
  }
}; 