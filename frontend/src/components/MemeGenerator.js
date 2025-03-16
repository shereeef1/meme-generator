import React, { useState, useEffect, useRef } from 'react';
import { generateMeme } from '../api';
// Import confetti
import confetti from 'canvas-confetti';
// Import usage tracking services
import { checkRemainingGenerations, incrementUsageCount } from '../services/usageTracker';
import PaymentMessage from './PaymentMessage';

const MemeGenerator = ({ prompt = '', brandData = null }) => {
  const [text, setText] = useState(prompt || '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [memes, setMemes] = useState([]);
  const [selectedMeme, setSelectedMeme] = useState(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  // Add a state to store cached images
  const [cachedImages, setCachedImages] = useState({});
  // Usage tracking states
  const [usageInfo, setUsageInfo] = useState(null);
  const [isCheckingUsage, setIsCheckingUsage] = useState(false); // Start with false to prevent the spinner
  const [userId, setUserId] = useState(null);
  const isMounted = useRef(true);

  // Add immediate fix for loading state
  useEffect(() => {
    // Force apply default usage info to ensure app works even with Firebase errors
    setUsageInfo({
      remainingCount: 2,
      hasRemainingUses: true,
      totalUsed: 0,
      source: 'immediate-fix'
    });
    
    // Start usage check after providing default values
    checkUsageLimits();
    
    return () => {
      isMounted.current = false;
    };
  }, []);

  // Add a loading timeout effect with shorter timeout
  useEffect(() => {
    if (isCheckingUsage) {
      console.log('MemeGenerator - Loading spinner active, setting short timeout');
      // Set a timeout to force-disable the loading indicator if it takes too long
      const timeout = setTimeout(() => {
        if (isMounted.current && isCheckingUsage) {
          console.log('MemeGenerator - Force ending usage check due to timeout');
          setIsCheckingUsage(false);
          
          // Set a fallback usage state
          if (!usageInfo) {
            setUsageInfo({
              remainingCount: 2,
              hasRemainingUses: true,
              totalUsed: 0,
              source: 'forced-default'
            });
          }
        }
      }, 1000); // 1 second timeout since we know Firebase is working
      
      return () => clearTimeout(timeout);
    }
  }, [isCheckingUsage, usageInfo]);

  // Add function to check usage limits
  const checkUsageLimits = async () => {
    console.log('MemeGenerator - checkUsageLimits called');
    // Don't set loading state - we already have default values
    // setIsCheckingUsage(true);
    
    try {
      console.log('MemeGenerator - Requesting usage data');
      const usageData = await checkRemainingGenerations();
      console.log('MemeGenerator - Usage data received:', usageData);
      
      if (isMounted.current) {
        // Only update if we got valid data
        if (usageData && typeof usageData.remainingCount === 'number') {
          setUsageInfo(usageData);
          setUserId(usageData.userId);
        }
        
        // If this came from an error or localStorage (offline), show a warning
        if (usageData && (usageData.source === 'error' || usageData.source === 'localStorage')) {
          console.warn('MemeGenerator - Using fallback storage due to Firebase connection issues');
          setError('Warning: Using offline mode. Your usage limits might not be accurate until connection is restored.');
        }
      }
    } catch (error) {
      console.error('MemeGenerator - Error checking usage:', error);
      // Don't override our default values on error
    } finally {
      console.log('MemeGenerator - Finishing usage check');
      // Always ensure loading is false
      if (isMounted.current) {
        setIsCheckingUsage(false);
      }
    }
  };

  useEffect(() => {
    if (prompt) {
      const promptText = typeof prompt === 'object' && prompt.caption ? prompt.caption : prompt;
      setText(promptText);
      // We remove the auto-submit behavior here
    }
  }, [prompt]);

  // Add confetti celebration
  const celebrateSuccess = () => {
    // Celebrate with confetti!
    confetti({
      particleCount: 100,
      spread: 70,
      origin: { y: 0.6 },
      colors: ['#FF6B6B', '#4ECDC4', '#FFD166', '#6A4C93']
    });
    console.log('🎉 Meme generated successfully! 🎉');
  };

  // Add a function to preload and cache images
  const preloadImages = async (urls) => {
    console.log('MemeGenerator - Preloading images:', urls.length);

    const newCachedImages = {};

    const preloadPromises = urls.map((url, index) => {
      return new Promise((resolve) => {
        const img = new Image();
        img.crossOrigin = "anonymous"; // Try to avoid CORS issues
        img.onload = () => {
          console.log(`MemeGenerator - Image ${index + 1} loaded successfully:`, url.substring(0, 50) + '...');
          if (isMounted.current) {
            newCachedImages[url] = url; // Store the original URL
            resolve(url);
          }
        };
        img.onerror = (e) => {
          console.error(`MemeGenerator - Failed to load image ${index + 1}:`, url.substring(0, 50) + '...', e);
          // Do not use placeholder on error - let the error propagate
          resolve(null);
        };
        img.src = url;
      });
    });

    try {
      await Promise.all(preloadPromises);

      if (isMounted.current) {
        console.log('MemeGenerator - All images preloaded, updating cached images');
        setCachedImages((prev) => ({ ...prev, ...newCachedImages }));
      }
    } catch (err) {
      console.error('MemeGenerator - Error preloading images:', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const textStr = String(text || '');

    if (!textStr.trim()) {
      setError('Please enter some text for your meme');
      return;
    }

    // Check if user has remaining uses before proceeding
    if (!usageInfo || !usageInfo.hasRemainingUses) {
      console.log('MemeGenerator - No remaining uses, cannot generate meme');
      return;
    }

    setError(null);
    setLoading(true);
    setMemes([]);
    setSelectedMeme(null);

    console.log('MemeGenerator - Submitting prompt:', textStr.substring(0, 100) + (textStr.length > 100 ? '...' : ''));
    console.log('MemeGenerator - Brand data being sent:',
      brandData ? `Name: ${brandData.brand_name}, Category: ${brandData.category}` : 'No brand data available');

    try {
      const response = await generateMeme(textStr, brandData);

      console.log('MemeGenerator - Response received:', response);

      if (response && response.success) {
        // Handle both single meme_url and array of meme_urls
        if (response.meme_urls && Array.isArray(response.meme_urls)) {
          console.log('MemeGenerator - Received meme URLs:', response.meme_urls);

          // Store the memes first, then preload them
          setMemes(response.meme_urls);
          if (response.meme_urls.length > 0) {
            setSelectedMeme(response.meme_urls[0]);
          }

          // Preload and cache the images
          await preloadImages(response.meme_urls);
          
          // Increment usage count after successful generation
          await incrementUsageCount(userId);
          
          // Update the usage info after successful generation
          checkUsageLimits();
          
          // Celebrate with confetti!
          celebrateSuccess();
        } else if (response.meme_url) {
          // If we only have a single meme_url, create an array with it
          const memeArray = [response.meme_url];
          console.log('MemeGenerator - Received single meme URL:', response.meme_url);

          // Store the meme first, then preload it
          setMemes(memeArray);
          setSelectedMeme(response.meme_url);

          // Preload and cache the image
          await preloadImages(memeArray);
          
          // Increment usage count after successful generation
          await incrementUsageCount(userId);
          
          // Update the usage info after successful generation
          checkUsageLimits();
          
          // Celebrate with confetti!
          celebrateSuccess();
        } else {
          console.error('MemeGenerator - No meme URLs found in response');
          setError('No memes were generated. Please try again.');
        }
      } else {
        console.error('MemeGenerator - Failed to generate memes:', response?.message || 'Unknown error');
        setError((response && response.message) || 'Failed to generate memes');
      }
    } catch (err) {
      console.error('MemeGenerator - Error generating memes:', err);
      setError('An error occurred while generating memes. Please try again.');
    } finally {
      if (isMounted.current) {
        setLoading(false);
      }
    }
  };

  const handleSelectMeme = (meme) => {
    setSelectedMeme(meme);
  };

  const handleDownload = async (url) => {
    try {
      // Use cached image URL if available, otherwise use original URL
      const imageUrl = cachedImages[url] || url;
      console.log('MemeGenerator - Downloading image:', imageUrl);

      setError(null);

      const response = await fetch(imageUrl);
      if (!response.ok) {
        throw new Error(`Failed to fetch image: ${response.status} ${response.statusText}`);
      }

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = `meme-${Date.now()}.png`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(downloadUrl);
      document.body.removeChild(a);

      console.log('MemeGenerator - Download successful');
    } catch (err) {
      console.error('MemeGenerator - Error downloading meme:', err);
      setError(`Failed to download meme: ${err.message}`);
    }
  };

  const renderMemeImage = (url, index) => {
    const isSelected = selectedMeme === url;
    const borderClass = isSelected ? 'border-primary' : 'border-light';

    // Use cached image URL if available, otherwise use original URL
    const imageUrl = cachedImages[url] || url;

    return (
      <div
        key={index}
        className={`cursor-pointer mb-2 text-center p-2 border rounded ${borderClass}`}
        onClick={() => handleSelectMeme(url)}
      >
        <img
          src={imageUrl}
          alt={`Generated meme ${index + 1}`}
          className="img-fluid meme-thumbnail"
          style={{ maxHeight: '150px', width: '100%', objectFit: 'contain' }}
          onError={(e) => {
            console.error(`MemeGenerator - Error loading image ${index + 1} in render:`, url.substring(0, 50) + '...');
            // No fallback - let the error show
          }}
        />
        <div className="mt-1">
          <small>Meme {index + 1}</small>
        </div>
      </div>
    );
  };

  // Check if user has hit the limit
  if (usageInfo && !usageInfo.hasRemainingUses) {
    return <PaymentMessage />;
  }

  return (
    <div className="row">
      <div className="col-lg-8 mb-4">
        <div className="card">
          <div className="card-header bg-primary text-white d-flex justify-content-between align-items-center">
            <h2 className="h5 mb-0">Meme-ify This Bad Boy</h2>
            <div>
              {usageInfo && (
                <span className="badge bg-warning text-dark me-2">
                  {usageInfo.remainingCount} free {usageInfo.remainingCount === 1 ? 'generation' : 'generations'} left
                </span>
              )}
              <button
                className="btn btn-sm btn-light"
                onClick={() => setShowAdvanced(!showAdvanced)}
              >
                {showAdvanced ? 'Hide Nerdy Stuff' : 'Show Nerdy Stuff'}
              </button>
            </div>
          </div>
          <div className="card-body">
            {error && (
              <div className="alert alert-danger" role="alert">
                Oops! We broke the internet. {error}
              </div>
            )}
            
            {isCheckingUsage ? (
              <div className="text-center my-3">
                <div className="spinner-border text-primary" role="status">
                  <span className="visually-hidden">Loading...</span>
                </div>
                <p className="mt-2">Checking usage limits...</p>
                <div className="d-flex justify-content-center gap-2">
                  <button 
                    className="btn btn-sm btn-outline-secondary mt-3"
                    onClick={() => {
                      console.log('MemeGenerator - Manual skip clicked');
                      setIsCheckingUsage(false);
                      setUsageInfo({
                        hasRemainingUses: true,
                        remainingCount: 2,
                        source: 'manual-override'
                      });
                    }}
                  >
                    Skip Check
                  </button>
                  <button 
                    className="btn btn-sm btn-danger mt-3"
                    onClick={() => {
                      console.log('MemeGenerator - Force reset clicked');
                      // Force reset everything
                      setIsCheckingUsage(false);
                      setUsageInfo({
                        hasRemainingUses: true,
                        remainingCount: 2,
                        source: 'force-reset'
                      });
                      setError(null);
                      // Force a component re-render
                      setText(text => text + ' ');
                    }}
                  >
                    Force Reset
                  </button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleSubmit}>
                <div className="mb-3">
                  <label htmlFor="memeText" className="form-label">
                    {prompt ? 'Your Brilliant Idea:' : 'Type Something Hilarious Here:'}
                  </label>
                  <div className="input-group">
                    <textarea
                      id="memeText"
                      className="form-control"
                      value={text || ''}
                      onChange={(e) => setText(e.target.value)}
                      placeholder="Enter your meme text here... make it good or the AI will judge you"
                      maxLength={300}
                      rows={3}
                      disabled={loading}
                      required
                    />
                    {!prompt && (
                      <button
                        type="button"
                        className="btn btn-outline-secondary"
                        onClick={() => setText('')}
                        disabled={!text || loading}
                      >
                        Start Over
                      </button>
                    )}
                  </div>
                  <div className="form-text d-flex justify-content-between">
                    <span>{text ? text.length : 0}/300 characters</span>
                    {brandData && (
                      <span>Brand: {brandData.brand_name}</span>
                    )}
                  </div>
                </div>

                {showAdvanced && (
                  <div className="card mb-3">
                    <div className="card-body">
                      <h6 className="mb-3">Advanced Options (for Meme Experts Only)</h6>
                      <div className="row g-3">
                        <div className="col-md-6">
                          <label className="form-label">Style</label>
                          <select className="form-select" disabled={loading}>
                            <option value="modern">Super Modern</option>
                            <option value="classic">Old School Cool</option>
                            <option value="minimal">No Frills</option>
                          </select>
                        </div>
                        <div className="col-md-6">
                          <label className="form-label">Format</label>
                          <select className="form-select" disabled={loading}>
                            <option value="auto">AI Decides</option>
                            <option value="square">Square (For Boomers)</option>
                            <option value="portrait">Portrait (For TikTokers)</option>
                            <option value="landscape">Landscape (For Fancy People)</option>
                          </select>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                <div className="d-grid">
                  <button
                    type="submit"
                    className="btn btn-primary btn-lg"
                    disabled={loading || !text || !text.trim()}
                  >
                    {loading ? (
                      <>
                        <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                        Summoning Meme Gods...
                      </>
                    ) : (
                      'Generate Viral Content'
                    )}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>

        {selectedMeme && (
          <div className="card mt-4">
            <div className="card-header bg-success text-white d-flex justify-content-between align-items-center">
              <h2 className="h5 mb-0">Your Masterpiece</h2>
              <div className="btn-group">
                <button
                  className="btn btn-sm btn-light"
                  onClick={() => handleDownload(selectedMeme)}
                >
                  Save This Gem
                </button>
                <a
                  href={cachedImages[selectedMeme] || selectedMeme}
                  className="btn btn-sm btn-light"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Full Size Glory
                </a>
              </div>
            </div>
            <div className="card-body p-0">
              <div className="position-relative">
                <img
                  src={cachedImages[selectedMeme] || selectedMeme}
                  alt="Selected meme"
                  className="img-fluid w-100"
                  style={{ maxHeight: '500px', objectFit: 'contain', border: '1px solid #eee' }}
                  onError={(e) => {
                    console.error('MemeGenerator - Error loading selected meme:',
                      selectedMeme ? selectedMeme.substring(0, 50) + '...' : 'undefined');
                    // No fallback - let the error show
                  }}
                />
                {loading && (
                  <div className="position-absolute top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center bg-dark bg-opacity-50">
                    <div className="spinner-border text-light" role="status">
                      <span className="visually-hidden">Loading...</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="col-lg-4">
        {memes && memes.length > 0 && (
          <div className="card">
            <div className="card-header bg-info text-white">
              <h2 className="h5 mb-0">Alternative Universes</h2>
            </div>
            <div className="card-body p-2">
              <div className="row g-2">
                {memes.map((meme, index) => renderMemeImage(meme, index))}
              </div>
            </div>
          </div>
        )}
      </div>

      <style>{`
        .meme-thumbnail {
          height: 120px;
          object-fit: cover;
          border: 1px solid #ddd;
          border-radius: 4px;
          transition: transform 0.2s ease;
        }
        .meme-thumbnail:hover {
          transform: scale(1.05);
        }
        .cursor-pointer {
          cursor: pointer;
          transition: all 0.2s ease;
        }
        .cursor-pointer:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .cursor-pointer.border-primary {
          box-shadow: 0 0 0 2px #0d6efd;
        }
      `}</style>
    </div>
  );
};

export default MemeGenerator; 