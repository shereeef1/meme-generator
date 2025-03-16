import React, { useState, useEffect } from 'react';
import { generatePrompts } from '../api';
import './PromptSuggestions.css';

const PromptSuggestions = ({ brandData, onPromptSelect }) => {
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState('');
  const [error, setError] = useState(null);
  const [prompts, setPrompts] = useState([]);
  const [selectedPrompt, setSelectedPrompt] = useState(null);
  const [promptCount, setPromptCount] = useState(10); // Default to 10 prompts

  // Remove automatic prompt generation on component mount or brandData change
  useEffect(() => {
    if (brandData) {
      console.log("PromptSuggestions - Initial brandData:", {
        has_raw_text: !!brandData.raw_text,
        raw_text_length: brandData.raw_text ? brandData.raw_text.length : 0,
        brand_name: brandData.brand_name,
        category: brandData.category
      });
      // Removed: generatePromptSuggestions();
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
      
      setLoadingStep(`Analyzing brand document for meme ideas... (generating ${promptCount} prompts)`);
      console.log(`PromptSuggestions - Using content (${brandData.raw_text.length} chars) to generate ${promptCount} prompts`);
      
      // Create a timeout promise that will reject after 110 seconds
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error("Prompt generation is taking longer than expected.")), 110000)
      );
      
      // Race the API call against the timeout
      const response = await Promise.race([
        generatePrompts({
          raw_text: brandData.raw_text,
          brand_name: brandData.brand_name || '',
          category: brandData.category || '',
          country: brandData.country || '',
          prompt_count: promptCount
        }),
        timeoutPromise
      ]);
      
      if (response.success && response.prompts) {
        setLoadingStep('Formatting meme suggestions...');
        await new Promise(resolve => setTimeout(resolve, 500)); // Visual feedback delay
        console.log(`PromptSuggestions - Received ${response.prompts.length} prompts`);
        setPrompts(response.prompts);
      } else {
        // Display the specific error message from the API
        const errorMessage = response.message || response.error || 'Failed to generate prompts';
        console.error('Error from prompt generation API:', errorMessage);
        setError(errorMessage);
      }
    } catch (err) {
      console.error('Error generating prompts:', err);
      if (err.message === "Prompt generation is taking longer than expected.") {
        setError('Prompt generation is taking too long. Please try again or select a smaller number of prompts.');
      } else {
        setError('An error occurred while generating prompts. Please check the console for details and try again.');
      }
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

  const handlePromptCountChange = (e) => {
    const count = parseInt(e.target.value);
    setPromptCount(count);
  };

  if (!brandData) {
    return null;
  }

  return (
    <div className="card mb-4">
      <div className="card-header bg-primary text-white">
        <h2 className="h5 mb-0">Choose Your Weapon</h2>
      </div>
      <div className="card-body">
        {error && (
          <div className="alert alert-danger" role="alert">
            {error} (Don't panic, it's just AI having a meltdown)
          </div>
        )}

        {/* Add options section */}
        <div className="card mb-3">
          <div className="card-body">
            <h5 className="card-title mb-3">The Meme Factory Control Panel</h5>
            <div className="row g-3 align-items-end">
              <div className="col-md-6">
                <label htmlFor="promptCount" className="form-label">Number of Meme Ideas</label>
                <select 
                  id="promptCount" 
                  className="form-select" 
                  value={promptCount}
                  onChange={handlePromptCountChange}
                  disabled={loading}
                >
                  <option value="5">5 ideas (for beginners)</option>
                  <option value="10">10 ideas (casual memer)</option>
                  <option value="15">15 ideas (pro level)</option>
                  <option value="20">20 ideas (meme enthusiast)</option>
                  <option value="25">25 ideas (borderline obsessed)</option>
                  <option value="30">30 ideas (absolute madlad)</option>
                </select>
                <div className="form-text">More ideas = more chances to go viral</div>
              </div>
              <div className="col-md-6">
                <button
                  className="btn btn-primary w-100"
                  onClick={generatePromptSuggestions}
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-2" role="status"></span>
                      Brain.exe is processing...
                    </>
                  ) : (
                    <>
                      <i className="bi bi-lightning-charge-fill me-2"></i>
                      Unleash the Meme Ideas!
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>

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
                `Mining content from: ${brandData.source_url}` : 
                brandData.file_name ? 
                  `Extracting meme juice from: ${brandData.file_name}` : 
                  'Extracting meme potential...'}
            </p>
          </div>
        ) : prompts.length > 0 ? (
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
                      <h6 className="mb-2">The Words:</h6>
                      <p className="mb-3">{prompt.caption}</p>
                      <h6 className="mb-2">The Picture:</h6>
                      <p className="mb-3 text-muted">{prompt.suggestion}</p>
                      <button
                        className="btn btn-sm btn-primary"
                        onClick={() => handlePromptSelect(prompt)}
                      >
                        This One Sparks Joy
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-5">
            <div className="mb-4">
              <i className="bi bi-lightning-charge display-1 text-muted"></i>
            </div>
            <h4 className="mb-3">No Meme Ideas Yet</h4>
            <p className="text-muted">
              Click the "Unleash the Meme Ideas!" button above to summon marketing genius from the depths of AI.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default PromptSuggestions; 