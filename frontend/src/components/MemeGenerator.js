import React, { useState } from 'react';
import { generateMemes } from '../api';

const MemeGenerator = () => {
  // State for text input, loading status, memes, and selected meme
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [memes, setMemes] = useState([]);
  const [selectedMeme, setSelectedMeme] = useState(null);

  // Handle form submission to generate memes
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!text.trim()) {
      setError('Please enter some text for your meme');
      return;
    }
    
    // Reset states
    setError(null);
    setLoading(true);
    setMemes([]);
    setSelectedMeme(null);
    
    try {
      // Call the backend API to generate memes
      const response = await generateMemes(text);
      
      // Check if the request was successful
      if (response.success) {
        setMemes(response.meme_urls);
        if (response.meme_urls.length > 0) {
          setSelectedMeme(response.meme_urls[0]);
        }
      } else {
        setError(response.message || 'Failed to generate memes');
      }
    } catch (err) {
      console.error('Error generating memes:', err);
      setError('An error occurred while generating memes. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Handle selecting a meme from the gallery
  const handleSelectMeme = (meme) => {
    setSelectedMeme(meme);
  };

  return (
    <div className="row">
      <div className="col-md-6 mb-4">
        <div className="card">
          <div className="card-header bg-primary text-white">
            <h2 className="h5 mb-0">Generate Memes</h2>
          </div>
          <div className="card-body">
            {error && (
              <div className="alert alert-danger" role="alert">
                {error}
              </div>
            )}
            
            <form onSubmit={handleSubmit}>
              <div className="mb-3">
                <label htmlFor="memeText" className="form-label">
                  Enter text for your meme (max 300 characters)
                </label>
                <textarea
                  id="memeText"
                  className="form-control"
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="e.g., When your customer service is so good, customers think they're being pranked"
                  maxLength={300}
                  rows={4}
                  required
                />
                <div className="form-text">
                  {text.length}/300 characters
                </div>
              </div>
              
              <button
                type="submit"
                className="btn btn-primary"
                disabled={loading || !text.trim()}
              >
                {loading ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                    Generating...
                  </>
                ) : (
                  'Generate Memes'
                )}
              </button>
            </form>
          </div>
        </div>
        
        {/* Selected Meme Preview */}
        {selectedMeme && (
          <div className="card mt-4">
            <div className="card-header bg-success text-white">
              <h2 className="h5 mb-0">Selected Meme</h2>
            </div>
            <div className="card-body text-center">
              <img 
                src={selectedMeme} 
                alt="Selected meme" 
                className="img-fluid meme-preview"
              />
              <div className="mt-3">
                <a 
                  href={selectedMeme} 
                  className="btn btn-outline-primary me-2"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Open Full Size
                </a>
                <a 
                  href={selectedMeme} 
                  className="btn btn-outline-success"
                  download="meme.png"
                >
                  Download
                </a>
              </div>
            </div>
          </div>
        )}
      </div>
      
      <div className="col-md-6">
        {/* Meme Gallery */}
        {memes.length > 0 && (
          <div className="card">
            <div className="card-header bg-info text-white">
              <h2 className="h5 mb-0">Meme Gallery</h2>
            </div>
            <div className="card-body">
              <p>Click on a meme to select it:</p>
              
              <div className="meme-gallery">
                {memes.map((meme, index) => (
                  <div 
                    key={index} 
                    className={`card meme-card ${selectedMeme === meme ? 'selected-meme' : ''}`}
                    onClick={() => handleSelectMeme(meme)}
                  >
                    <img 
                      src={meme} 
                      alt={`Meme option ${index + 1}`} 
                      className="card-img-top p-2"
                    />
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MemeGenerator; 