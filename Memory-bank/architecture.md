# Architecture Overview

- **backend/**

  - `app.py`: Main Flask application file that handles routes and API requests.
  - `config.py`: Configuration file for environment variables and settings.
  - `firebase_config.py`: Firebase initialization and configuration.
  - `modules/`
    - `scraping.py`: Module for web scraping brand data from provided URLs.
    - `meme_generation.py`: Module for interacting with the Supreme Meme AI API to generate memes.
    - `news_integration.py`: Module for fetching and filtering trending news using NewsAPI.
    - `export.py`: Module for handling meme exports and storage.

- **frontend/**

  - `src/App.js`: Main React component that serves as the entry point for the frontend.
  - `src/firebase.js`: Firebase client configuration for the frontend.
  - `src/components/`
    - `BrandInput.js`: Component for entering brand URL and information.
    - `MemeGenerator.js`: Component for the meme generation interface.
    - `NewsSelector.js`: Component for selecting relevant news items.
    - `MemeCustomizer.js`: Component for meme customization tools.
    - `ExportOptions.js`: Component for exporting and sharing memes.

- **database/**
  - `models.py`: Database models for storing user data, brand information, and generated memes.
