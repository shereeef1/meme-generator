import React, { useState } from 'react';
import { scrapeBrandData } from '../api';

const CATEGORIES = [
  { value: '', label: 'Select a category (optional)' },
  { value: 'fashion', label: 'Fashion & Apparel' },
  { value: 'beauty', label: 'Beauty & Cosmetics' },
  { value: 'tech', label: 'Technology & Electronics' },
  { value: 'food', label: 'Food & Beverage' },
  { value: 'health', label: 'Health & Wellness' },
  { value: 'home', label: 'Home & Decor' },
  { value: 'other', label: 'Other' }
];

const COUNTRIES = [
  { value: '', label: 'Select a country (optional)' },
  { value: 'us', label: 'United States' },
  { value: 'uk', label: 'United Kingdom' },
  { value: 'ca', label: 'Canada' },
  { value: 'au', label: 'Australia' },
  { value: 'de', label: 'Germany' },
  { value: 'fr', label: 'France' },
  { value: 'jp', label: 'Japan' },
  { value: 'in', label: 'India' },
  { value: 'br', label: 'Brazil' },
  { value: 'other', label: 'Other' }
];

const BrandInput = ({ onBrandData }) => {
  const [url, setUrl] = useState('');
  const [category, setCategory] = useState('');
  const [country, setCountry] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [brandData, setBrandData] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!url.trim()) {
      setError('Please enter a valid URL');
      return;
    }
    
    // Clear previous results
    setError(null);
    setBrandData(null);
    setLoading(true);
    
    try {
      // Add protocol if missing
      let formattedUrl = url;
      if (!url.startsWith('http://') && !url.startsWith('https://')) {
        formattedUrl = `https://${url}`;
      }
      
      // Call the API to scrape brand data
      const data = await scrapeBrandData(formattedUrl, category || undefined, country || undefined);
      
      if (data.success) {
        setBrandData(data);
        
        // Pass the brand data to the parent component
        if (onBrandData && typeof onBrandData === 'function') {
          onBrandData(data);
        }
      } else {
        setError(data.message || 'Failed to scrape brand data');
      }
    } catch (err) {
      console.error('Error scraping brand data:', err);
      setError('An error occurred while scraping the brand data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card mb-4">
      <div className="card-header bg-primary text-white">
        <h2 className="h5 mb-0">Brand Information</h2>
      </div>
      <div className="card-body">
        {error && (
          <div className="alert alert-danger" role="alert">
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label htmlFor="brandUrl" className="form-label">
              Enter Brand Website URL
            </label>
            <input
              type="text"
              id="brandUrl"
              className="form-control"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="e.g., nike.com or https://www.apple.com"
              required
            />
            <div className="form-text">
              We'll scrape brand information to create relevant memes.
            </div>
          </div>
          
          <div className="row">
            <div className="col-md-6 mb-3">
              <label htmlFor="category" className="form-label">
                Brand Category
              </label>
              <select
                id="category"
                className="form-select"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
              >
                {CATEGORIES.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            
            <div className="col-md-6 mb-3">
              <label htmlFor="country" className="form-label">
                Primary Market
              </label>
              <select
                id="country"
                className="form-select"
                value={country}
                onChange={(e) => setCountry(e.target.value)}
              >
                {COUNTRIES.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
          
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading || !url.trim()}
          >
            {loading ? (
              <>
                <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                Scraping...
              </>
            ) : (
              'Get Brand Data'
            )}
          </button>
        </form>
        
        {/* Display brand data if available */}
        {brandData && (
          <div className="mt-4">
            <h3 className="h5 mb-3">Brand Information</h3>
            <div className="card bg-light">
              <div className="card-body">
                <h4 className="h6">{brandData.brand_name}</h4>
                {brandData.tagline && (
                  <p className="fst-italic mb-2">"{brandData.tagline}"</p>
                )}
                
                {brandData.description && (
                  <div className="mb-3">
                    <strong>Description:</strong>
                    <p className="small mb-2">{brandData.description}</p>
                  </div>
                )}
                
                {brandData.products && brandData.products.length > 0 && (
                  <div className="mb-3">
                    <strong>Products/Keywords:</strong>
                    <ul className="list-unstyled mb-0">
                      {brandData.products.map((product, index) => (
                        <li key={index} className="badge bg-primary me-2 mb-2">
                          {product}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                
                <div className="d-flex justify-content-between mt-3 small text-muted">
                  <span>
                    Category: {brandData.category || 'Not specified'}
                  </span>
                  <span>
                    Source: <a href={brandData.source_url} target="_blank" rel="noopener noreferrer">Website</a>
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default BrandInput; 