import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './TopicalNews.css';

// Import the API functions we need
import { generatePrompts, fetchNews } from '../api';

// No need for this anymore since we're using the fetchNews function
// const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

function TopicalNews({ brandData, onPromptGenerated }) {
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedNews, setSelectedNews] = useState(null);
  const [generatingPrompt, setGeneratingPrompt] = useState(false);
  const [promptError, setPromptError] = useState(null);

  useEffect(() => {
    console.log("TopicalNews - Component mounted with brandData:", {
      exists: !!brandData,
      has_raw_text: brandData ? !!brandData.raw_text : false,
      raw_text_length: brandData && brandData.raw_text ? brandData.raw_text.length : 0,
      brand_name: brandData ? brandData.brand_name : null
    });
    fetchGoogleNews();
  }, []);

  // Function to fetch news from our backend API
  const fetchGoogleNews = async () => {
    setLoading(true);
    setError(null);

    try {
      // Use the fetchNews API function to get 20 trending news articles from the last 14 days
      console.log("TopicalNews - Fetching trending news from the last 14 days");
      const result = await fetchNews(20, 14); // 20 articles, last 14 days
      
      if (!result.success) {
        throw new Error(result.message || 'Failed to fetch news');
      }
      
      console.log(`TopicalNews - Successfully fetched ${result.news.length} trending news articles`);
      setNews(result.news);
    } catch (e) {
      console.error('Error fetching news:', e);
      setError(`An error occurred while fetching news: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectNews = (article) => {
    setSelectedNews(article);
    setPromptError(null);
  };

  // Generate a meme prompt based on the selected news and brand data
  const handleGeneratePrompt = async () => {
    if (!selectedNews) {
      setPromptError('Please select a news article first');
      return;
    }

    if (!brandData || !brandData.raw_text) {
      setPromptError('Brand information is missing. Please go back to the Brand Info step.');
      return;
    }

    setGeneratingPrompt(true);
    setPromptError(null);

    try {
      console.log('TopicalNews - Selected news article:', selectedNews.title);
      console.log('TopicalNews - Using brand Word doc content:', 
        `${brandData.raw_text.substring(0, 100)}... (${brandData.raw_text.length} chars total)`);
      
      // First, prepare the news article section
      let newsSection = `
=========== NEWS ARTICLE ===========
Title: ${selectedNews.title}
Description: ${selectedNews.description}
Content: ${selectedNews.content || ''}
Source: ${selectedNews.source || ''}
URL: ${selectedNews.url || ''}
===============================

`;
      
      // Now combine the news section with the original Word doc content
      const combinedText = newsSection + brandData.raw_text;
      
      console.log('TopicalNews - Combined content length:', combinedText.length);
      console.log('TopicalNews - First 200 chars of combined content:', combinedText.substring(0, 200) + '...');
      
      // Generate a prompt based on the combined content
      const result = await generatePrompts({
        raw_text: combinedText,
        brand_name: brandData.brand_name || '',
        category: brandData.category || '',
        country: brandData.country || ''
      });
      
      if (result.success && result.prompts && result.prompts.length > 0) {
        // Take the first prompt from the list
        const firstPrompt = result.prompts[0];
        console.log('TopicalNews - Prompt generated:', firstPrompt.caption);
        onPromptGenerated(firstPrompt.caption);
      } else {
        setPromptError(result.message || 'Failed to generate prompt');
      }
    } catch (e) {
      console.error('Error in handleGeneratePrompt:', e);
      setPromptError('An error occurred while generating the prompt');
    } finally {
      setGeneratingPrompt(false);
    }
  };

  // Handler for opening news link in new tab
  const handleNewsLinkClick = (e, url) => {
    e.stopPropagation(); // Prevent the card click event from firing
    if (url) {
      window.open(url, '_blank', 'noopener,noreferrer');
    }
  };

  return (
    <div className="topical-news-container">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h2>Topical News</h2>
        <button 
          className="btn btn-outline-primary" 
          onClick={fetchGoogleNews}
          disabled={loading}
        >
          {loading ? (
            <>
              <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
              Loading...
            </>
          ) : (
            <>
              <i className="bi bi-arrow-clockwise me-2"></i>
              Refresh News
            </>
          )}
        </button>
      </div>
      <p className="lead">Select a news article to generate a meme prompt related to your brand</p>

      {loading ? (
        <div className="text-center my-5">
          <div className="spinner-border" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <p className="mt-2">Loading news articles...</p>
        </div>
      ) : error ? (
        <div className="alert alert-danger" role="alert">
          {error}
          <button className="btn btn-outline-danger ms-3" onClick={fetchGoogleNews}>
            Try Again
          </button>
        </div>
      ) : (
        <>
          {news.length === 0 ? (
            <div className="alert alert-info">
              No news articles available at the moment. Please try again later.
            </div>
          ) : (
            <div className="row">
              <div className="col-md-8">
                <div className="news-list">
                  {news.map((article) => (
                    <div
                      key={article.id || article.url}
                      className={`news-item card mb-3 ${selectedNews === article ? 'selected' : ''}`}
                      onClick={() => handleSelectNews(article)}
                    >
                      <div className="card-body">
                        <h5 className="card-title">{article.title}</h5>
                        <h6 className="card-subtitle mb-2 text-muted">
                          {article.source}
                          {article.url && (
                            <span className="ms-2">
                              <a
                                href="#"
                                onClick={(e) => handleNewsLinkClick(e, article.url)}
                                className="news-link"
                              >
                                <i className="bi bi-link-45deg"></i> Read full article
                              </a>
                            </span>
                          )}
                        </h6>
                        <p className="card-text">{article.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="col-md-4">
                <div className="news-actions card">
                  <div className="card-body">
                    <h5 className="card-title">Generate Meme Prompt</h5>

                    {selectedNews ? (
                      <>
                        <p>Selected article: <strong>{selectedNews.title}</strong></p>
                        {selectedNews.url && (
                          <p className="news-url">
                            <a
                              href="#"
                              onClick={(e) => handleNewsLinkClick(e, selectedNews.url)}
                              className="news-link"
                            >
                              <i className="bi bi-link-45deg"></i> View original article
                            </a>
                          </p>
                        )}
                        <button
                          className="btn btn-primary w-100"
                          onClick={handleGeneratePrompt}
                          disabled={generatingPrompt}
                        >
                          {generatingPrompt ? (
                            <>
                              <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                              Generating...
                            </>
                          ) : (
                            'Generate Meme Prompt'
                          )}
                        </button>

                        {promptError && (
                          <div className="alert alert-danger mt-3">
                            {promptError}
                          </div>
                        )}
                      </>
                    ) : (
                      <p className="text-muted">
                        Select a news article from the list to generate a meme prompt related to your brand.
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default TopicalNews; 