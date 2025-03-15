import React, { useState, useEffect } from 'react';
import { generatePrompts } from '../api';
import './PromptSuggestions.css';

const PromptSuggestions = ({ brandData, onPromptSelect }) => {
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState('');
  const [error, setError] = useState(null);
  const [prompts, setPrompts] = useState([]);
  const [selectedPrompt, setSelectedPrompt] = useState(null);

  useEffect(() => {
    if (brandData) {
      console.log("PromptSuggestions - Initial brandData:", {
        has_raw_text: !!brandData.raw_text,
        raw_text_length: brandData.raw_text ? brandData.raw_text.length : 0,
        brand_name: brandData.brand_name,
        category: brandData.category
      });
      generatePromptSuggestions();
    }
  }, [brandData]);

  const generatePromptSuggestions = async () => {
    if (!brandData || !brandData.raw_text) {
      console.error("PromptSuggestions - brandData or raw_text is missing:", brandData);
      setError("Missing brand data text. Please try again or go back to the Brand Info step.");
      return;
    }

    setLoading(true);
    setError(null);
    setPrompts([]);
    setSelectedPrompt(null);

    try {
      // Show file processing steps
      if (brandData.source_url) {
        setLoadingStep('Processing scraped content...');
      } else if (brandData.file_name) {
        setLoadingStep(`Processing uploaded file: ${brandData.file_name}`);
      } else {
        setLoadingStep('Processing content...');
      }
      await new Promise(resolve => setTimeout(resolve, 1000)); // Visual feedback delay
      
      setLoadingStep('Analyzing brand document for meme ideas...');
      
      // As per the flow, just send the raw Word doc content directly to the API
      const wordDocContent = brandData.raw_text;
      console.log(`PromptSuggestions - Using original Word doc content (${wordDocContent.length} chars)`);
      
      const response = await generatePrompts({
        raw_text: wordDocContent,  // Send unmodified Word doc content
        brand_name: brandData.brand_name || '',
        category: brandData.category || '',
        country: brandData.country || ''
      });
      
      if (response.success && response.prompts) {
        setLoadingStep('Formatting meme suggestions...');
        await new Promise(resolve => setTimeout(resolve, 500)); // Visual feedback delay
        setPrompts(response.prompts);
      } else {
        setError(response.message || 'Failed to generate prompts');
      }
    } catch (err) {
      console.error('Error generating prompts:', err);
      setError('An error occurred while generating prompts. Please try again.');
    } finally {
      setLoading(false);
      setLoadingStep('');
    }
  };

  const handlePromptSelect = (prompt) => {
    setSelectedPrompt(prompt);
    if (onPromptSelect) {
      onPromptSelect(prompt.caption);
    }
  };

  if (!brandData) {
    return null;
  }

  return (
    <div className="card mb-4">
      <div className="card-header bg-primary text-white d-flex justify-content-between align-items-center">
        <h2 className="h5 mb-0">Select a Prompt</h2>
        <button
          className="btn btn-sm btn-light"
          onClick={generatePromptSuggestions}
          disabled={loading}
        >
          <i className="bi bi-arrow-clockwise me-2"></i>
          Regenerate All
        </button>
      </div>
      <div className="card-body">
        {error && (
          <div className="alert alert-danger" role="alert">
            {error}
          </div>
        )}

        {loading ? (
          <div className="text-center py-4">
            <div className="loading-container">
              <div className="spinner-border text-primary mb-3" role="status">
                <span className="visually-hidden">Loading...</span>
              </div>
              <div className="loading-step">
                <h5 className="mb-2">{loadingStep}</h5>
                <div className="progress" style={{ height: '4px', width: '200px', margin: '0 auto' }}>
                  <div 
                    className="progress-bar progress-bar-striped progress-bar-animated" 
                    style={{ width: '100%' }}
                  ></div>
                </div>
              </div>
            </div>
            <p className="text-muted mt-3">
              {brandData.source_url ? 
                `Processing content from: ${brandData.source_url}` : 
                brandData.file_name ? 
                  `Processing file: ${brandData.file_name}` : 
                  'Processing content...'}
            </p>
          </div>
        ) : (
          <div className="prompt-list">
            {prompts.map((prompt, index) => (
              <div
                key={index}
                className={`card mb-3 prompt-card ${selectedPrompt === prompt ? 'border-primary' : ''}`}
              >
                <div className="card-body">
                  <div className="d-flex align-items-start">
                    <div className="me-3">
                      <div className="prompt-number">
                        {index + 1}
                      </div>
                    </div>
                    <div className="flex-grow-1">
                      <h6 className="mb-2">Caption:</h6>
                      <p className="mb-3">{prompt.caption}</p>
                      <h6 className="mb-2">Suggestion:</h6>
                      <p className="mb-3 text-muted">{prompt.suggestion}</p>
                      <button
                        className="btn btn-sm btn-primary"
                        onClick={() => handlePromptSelect(prompt)}
                      >
                        Select
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default PromptSuggestions; 