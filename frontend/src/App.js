import React, { useState } from 'react';
import MemeGenerator from './components/MemeGenerator';
import BrandInput from './components/BrandInput';
import './App.css';

function App() {
  const [brandData, setBrandData] = useState(null);
  const [activeTab, setActiveTab] = useState('brand'); // 'brand' or 'meme'

  const handleBrandData = (data) => {
    setBrandData(data);
    // After getting brand data, switch to the meme generator tab
    setActiveTab('meme');
  };

  // Helper to generate meme text suggestions from brand data
  const getMemeTextSuggestions = () => {
    if (!brandData) return [];

    const suggestions = [];
    const name = brandData.brand_name;
    
    if (brandData.tagline) {
      suggestions.push(`When ${name}'s slogan "${brandData.tagline}" actually comes true`);
    }
    
    if (brandData.products && brandData.products.length > 0) {
      const product = brandData.products[0];
      suggestions.push(`When you finally get your hands on ${name}'s new ${product}`);
    }
    
    suggestions.push(`When people ask why you love ${name} so much`);
    suggestions.push(`${name} customer service be like...`);
    
    return suggestions;
  };

  return (
    <div className="App">
      <header className="bg-dark text-white p-4 mb-4">
        <div className="container">
          <h1 className="display-4">D2C Brand Meme Generator</h1>
          <p className="lead">
            Generate engaging memes for your brand in seconds
          </p>
        </div>
      </header>
      
      <main className="container mb-5">
        <ul className="nav nav-tabs mb-4">
          <li className="nav-item">
            <button 
              className={`nav-link ${activeTab === 'brand' ? 'active' : ''}`} 
              onClick={() => setActiveTab('brand')}
            >
              1. Brand Information
            </button>
          </li>
          <li className="nav-item">
            <button 
              className={`nav-link ${activeTab === 'meme' ? 'active' : ''}`} 
              onClick={() => setActiveTab('meme')}
              disabled={!brandData}
            >
              2. Generate Memes
            </button>
          </li>
        </ul>
        
        {activeTab === 'brand' ? (
          <BrandInput onBrandData={handleBrandData} />
        ) : (
          <div>
            {brandData && (
              <div className="alert alert-success mb-4">
                <h3 className="h5">Using Brand: {brandData.brand_name}</h3>
                <p className="mb-0">
                  Now create memes based on your brand information!
                  <button 
                    className="btn btn-sm btn-outline-primary ms-3"
                    onClick={() => setActiveTab('brand')}
                  >
                    Change Brand
                  </button>
                </p>
              </div>
            )}
            <MemeGenerator 
              brandData={brandData}
              textSuggestions={getMemeTextSuggestions()}
            />
          </div>
        )}
      </main>
      
      <footer className="bg-dark text-white p-3 text-center">
        <div className="container">
          <p className="mb-0">
            &copy; {new Date().getFullYear()} D2C Brand Meme Generator
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App; 