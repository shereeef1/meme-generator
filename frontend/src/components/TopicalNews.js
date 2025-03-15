import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './TopicalNews.css';

// Import just the generatePrompts function we need for meme creation
import { generatePrompts } from '../api';

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

  // Function to fetch news directly from Google News
  const fetchGoogleNews = async () => {
    setLoading(true);
    setError(null);

    try {
      // Use sample data directly since we won't rely on the API
      const googleNewsItems = [
        {
          id: 1,
          title: "India's Technology Sector Sees Record Growth in 2025",
          description: "Technology companies in India report unprecedented growth with investments in AI and cloud computing leading the charge.",
          content: "India's tech sector has experienced remarkable growth with companies focusing on artificial intelligence, machine learning, and cloud technologies.",
          source: "Google News - Technology",
          publishedAt: new Date().toISOString(),
          url: "https://news.google.com/topics/technology",
          imageUrl: "https://via.placeholder.com/450x200?text=Tech+News"
        },
        {
          id: 2,
          title: "Global Renewable Energy Investments Reach All-Time High",
          description: "Solar and wind energy projects attract record funding as countries accelerate their transition to clean energy.",
          content: "Investments in renewable energy have reached unprecedented levels globally, with solar and wind projects leading the transition to sustainable power generation.",
          source: "Google News - Business",
          publishedAt: new Date().toISOString(),
          url: "https://news.google.com/topics/business",
          imageUrl: "https://via.placeholder.com/450x200?text=Energy+News"
        },
        {
          id: 3,
          title: "New AI Tool Transforms How Companies Approach Marketing",
          description: "Breakthrough artificial intelligence system helps businesses create more effective, targeted marketing campaigns.",
          content: "An innovative AI-powered tool is changing the landscape of digital marketing by enabling more personalized content creation and better audience targeting.",
          source: "Google News - Technology",
          publishedAt: new Date().toISOString(),
          url: "https://news.google.com/topics/technology",
          imageUrl: "https://via.placeholder.com/450x200?text=AI+Marketing"
        },
        {
          id: 4,
          title: "E-commerce Growth Continues to Accelerate in Emerging Markets",
          description: "Online shopping platforms see explosive growth in developing regions as internet access and digital payment options expand.",
          content: "E-commerce adoption is surging in emerging markets, driven by increasing internet penetration, smartphone usage, and innovative payment solutions.",
          source: "Google News - Business",
          publishedAt: new Date().toISOString(),
          url: "https://news.google.com/topics/business",
          imageUrl: "https://via.placeholder.com/450x200?text=E-commerce"
        },
        {
          id: 5,
          title: "Health Tech Innovations Making Healthcare More Accessible",
          description: "New digital health platforms and telemedicine services are transforming healthcare delivery worldwide.",
          content: "Technology innovations in healthcare are improving access to medical services, particularly in underserved regions, through telemedicine and digital health solutions.",
          source: "Google News - Health",
          publishedAt: new Date().toISOString(),
          url: "https://news.google.com/topics/health",
          imageUrl: "https://via.placeholder.com/450x200?text=Health+Tech"
        }
      ];
      
      setNews(googleNewsItems);
    } catch (e) {
      console.error('Error fetching Google News:', e);
      setError('An error occurred while fetching news');
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

  return (
    <div className="topical-news-container">
      <h2>Topical News</h2>
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
                        <h6 className="card-subtitle mb-2 text-muted">{article.source}</h6>
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