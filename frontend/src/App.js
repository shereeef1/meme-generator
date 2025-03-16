import React, { useState } from 'react';
import './App.css';
import BrandInput from './components/BrandInput';
import MemeGenerator from './components/MemeGenerator';
import PromptSuggestions from './components/PromptSuggestions';
import TopicalNews from './components/TopicalNews';
import { generatePrompts } from './api';

function App() {
  const [brandData, setBrandData] = useState(null);
  const [activeTab, setActiveTab] = useState('brand-input');
  const [selectedPrompt, setSelectedPrompt] = useState('');
  const [prompts, setPrompts] = useState([]);
  const [loadingPrompts, setLoadingPrompts] = useState(false);
  const [promptError, setPromptError] = useState(null);

  // Add meme patterns for visual flair
  const memePatterns = {
    headerEmoji: "🤣",
    footerEmoji: "👽",
  };

  const handleBrandData = (data) => {
    console.log('App - Received brand data with raw_text:', 
      data.raw_text ? 
      `${data.raw_text.substring(0, 100)}... (${data.raw_text.length} chars)` : 
      'No raw_text');
    
    if (data && data.success) {
      if (!data.raw_text || data.raw_text.trim() === '') {
        console.error('WARNING: Brand data is missing raw_text or it is empty!', data);
        data.raw_text = `Brand Name: ${data.brand_name || 'Unknown brand'}\nCategory: ${data.category || 'Unknown category'}\nCountry: ${data.country || 'Unknown country'}`;
        console.log('Added minimal fallback text:', data.raw_text);
      }
      
      setBrandData(data);
      // Remove automatic prompt generation - this will now be triggered by a button click
      // generateMemePrompts(data);
      setActiveTab('prompt-selection');
    } else {
      console.error('Invalid brand data received:', data);
    }
  };
  
  const generateMemePrompts = async (data) => {
    console.log('App - generateMemePrompts called with raw_text:', 
      data.raw_text ? 
      `${data.raw_text.substring(0, 100)}... (${data.raw_text.length} chars)` : 
      'No raw_text');
    
    setLoadingPrompts(true);
    setPromptError(null);
    
    try {
      const result = await generatePrompts(data);
      
      if (result.success && result.prompts && result.prompts.length > 0) {
        setPrompts(result.prompts);
      } else {
        setPromptError(result.message || 'Failed to generate prompt suggestions');
      }
    } catch (err) {
      console.error('Error generating prompts:', err);
      setPromptError('An error occurred while generating prompt suggestions');
    } finally {
      setLoadingPrompts(false);
    }
  };

  const handleSelectPrompt = (prompt) => {
    setSelectedPrompt(prompt);
    // Auto-advance to meme generation when a prompt is selected
    setActiveTab('generate-meme');
  };

  // Original function to generate meme text suggestions based on brand data
  const getMemeTextSuggestions = () => {
    if (!brandData || !brandData.success) return [];
    
    const suggestions = [];
    const brandName = brandData.brand_name || '';
    const tagline = brandData.tagline || '';
    const products = brandData.products || [];
    
    if (tagline) {
      suggestions.push(`When ${brandName} says "${tagline}"`);
      suggestions.push(`${brandName}: "${tagline}" Me:`);
    }
    
    if (products && products.length > 0) {
      suggestions.push(`Me after using ${brandName}'s ${products[0]} for the first time`);
      if (products.length > 1) {
        suggestions.push(`Choosing between ${products[0]} and ${products[1]} from ${brandName}`);
      }
    }
    
    suggestions.push(`Everyone else: Normal brands. ${brandName}:`);
    
    return suggestions;
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="container">
          <h1 className="display-4 text-center mb-3">{memePatterns.headerEmoji} Meme-ify Your Brand or Die Trying {memePatterns.headerEmoji}</h1>
          <p className="lead text-center">Making boring brands go viral since 5 minutes ago</p>
        </div>
      </header>
      
      <main className="container my-4">
        <ul className="nav nav-tabs mb-4">
          <li className="nav-item">
            <button 
              className={`nav-link ${activeTab === 'brand-input' ? 'active' : ''}`}
              onClick={() => setActiveTab('brand-input')}
            >
              1. Brand Info (The Boring Part)
            </button>
          </li>
          <li className="nav-item">
            <button 
              className={`nav-link ${activeTab === 'prompt-selection' ? 'active' : ''}`}
              onClick={() => setActiveTab('prompt-selection')}
              disabled={!brandData}
            >
              2. Select Prompt (Get Creative... or Else)
            </button>
          </li>
          <li className="nav-item">
            <button 
              className={`nav-link ${activeTab === 'topical-news' ? 'active' : ''}`}
              onClick={() => setActiveTab('topical-news')}
              disabled={!brandData}
            >
              3. News (Things That Happened IRL)
            </button>
          </li>
          <li className="nav-item">
            <button 
              className={`nav-link ${activeTab === 'generate-meme' ? 'active' : ''}`}
              onClick={() => setActiveTab('generate-meme')}
              disabled={!selectedPrompt}
            >
              4. Meme Magic (The Good Stuff)
            </button>
          </li>
        </ul>
        
        <div className="tab-content">
          {activeTab === 'brand-input' && (
            <BrandInput onBrandData={handleBrandData} />
          )}
          
          {activeTab === 'prompt-selection' && (
            <PromptSuggestions
              brandData={brandData}
              onPromptSelect={handleSelectPrompt}
            />
          )}
          
          {activeTab === 'topical-news' && (
            <TopicalNews
              brandData={brandData}
              onPromptGenerated={handleSelectPrompt}
            />
          )}
          
          {activeTab === 'generate-meme' && (
            <MemeGenerator
              prompt={selectedPrompt}
              brandData={brandData}
            />
          )}
        </div>
      </main>
      
      <footer className="app-footer mt-auto py-3">
        <div className="container text-center">
          <p className="text-light mb-0">
            {memePatterns.footerEmoji} {new Date().getFullYear()} Meme Factory HQ - Making serious brands look ridiculous since now {memePatterns.footerEmoji}
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App; 