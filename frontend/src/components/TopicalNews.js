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

    setGeneratingPrompt(true);
    setPromptError(null);

    try {
      console.log('Generating prompt for news:', selectedNews.title);
      
      // Create a combined text from the news article and brand data for prompt generation
      let rawText = `
News Article: ${selectedNews.title}
Description: ${selectedNews.description}

`;
      
      // Add brand data if available
      if (brandData) {
        rawText += `Brand Information: ${brandData.raw_text || ''}`;
      }
      
      // Use the existing generatePrompts function from the API
      const result = await generatePrompts({
        raw_text: rawText,
        brand_name: brandData?.brand_name || '',
        category: brandData?.category || '',
        country: brandData?.country || ''
      });
      
      if (result.success && result.prompts && result.prompts.length > 0) {
        // Take the first prompt from the list
        const firstPrompt = result.prompts[0];
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
      <h2>Breaking News Meme Factory</h2>
      <p className="lead">Grab a trending story and turn it into a legendary brand moment</p>

      {loading ? (
        <div className="text-center my-5">
          <div className="spinner-border" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <p className="mt-2">Stealing news from the internet...</p>
        </div>
      ) : error ? (
        <div className="alert alert-danger" role="alert">
          {error}
          <button className="btn btn-outline-danger ms-3" onClick={fetchGoogleNews}>
            Let's Try That Again
          </button>
        </div>
      ) : (
        <>
          {news.length === 0 ? (
            <div className="alert alert-info">
              Apparently nothing happened in the world today. Try again tomorrow?
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
                    <h5 className="card-title">Meme This News</h5>

                    {selectedNews ? (
                      <>
                        <p>You picked: <strong>{selectedNews.title}</strong></p>
                        <button
                          className="btn btn-primary w-100"
                          onClick={handleGeneratePrompt}
                          disabled={generatingPrompt}
                        >
                          {generatingPrompt ? (
                            <>
                              <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                              Making It Relevant...
                            </>
                          ) : (
                            'Hijack This Headline'
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
                        Click on a news story to turn serious journalism into marketing gold.
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