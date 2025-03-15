import React, { useState } from 'react';
import MemeGenerator from './components/MemeGenerator';
import './App.css';

function App() {
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
        <MemeGenerator />
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