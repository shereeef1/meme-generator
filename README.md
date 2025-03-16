# D2C Brand Meme Generator

A SaaS platform that helps direct-to-consumer (D2C) e-commerce brands create engaging memes by combining their brand identity with trending news and topics.

## Features

- Brand data scraping from website URLs
- Upload brand information documents
- **Enhanced brand research** with Wikipedia and search engine integration
- **Competitor analysis** for brand comparison
- **Industry trend detection** for relevant meme creation
- Meme generation using Supreme Meme AI API
- News integration with trending topics
- Customization tools for memes
- Export options for sharing on social media

## Project Structure

```
project-root/
├── backend/                    # Flask API backend
│   ├── modules/                # Functionality modules
│   │   ├── research_sources/   # Enhanced research sources
│   │   ├── enhanced_research.py # Multi-source brand research
│   │   ├── scraping.py         # Website scraping
│   │   └── ...                 # Other modules
│   ├── app.py                  # Main Flask application
│   ├── config.py               # Configuration
│   ├── firebase_config.py      # Firebase setup
│   └── requirements.txt        # Python dependencies
│
├── frontend/                   # React frontend
    ├── src/                    # React source code
    ├── public/                 # Public assets
    └── package.json            # NPM dependencies
```

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:

   ```
   cd backend
   ```

2. Create a virtual environment:

   ```
   python -m venv venv
   ```

3. Activate the virtual environment:

   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`

4. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

5. Create a `.env` file based on `.env.example` with your actual API keys and Firebase credentials.

6. Firebase Setup:

   - Create a Firebase project at https://console.firebase.google.com/
   - Set up Firestore and Storage
   - Download your service account credentials
   - Update the `.env` file with the path to your credentials

7. Run the Flask application:
   ```
   python app.py
   ```

### Frontend Setup

1. Navigate to the frontend directory:

   ```
   cd frontend
   ```

2. Install dependencies:

   ```
   npm install
   ```

3. Start the development server:
   ```
   npm start
   ```

## Enhanced Brand Research

The platform now offers an advanced brand research capability that collects information from multiple sources:

1. **Wikipedia Data**: Extracts brand information, history, and key facts from Wikipedia.
2. **Search Engine Results**: Gathers relevant brand information from DuckDuckGo search results.
3. **Competitor Analysis**: Identifies and analyzes top competitors in the same industry.
4. **Industry Trends**: Detects current trends and topics related to the brand's industry.

### How to Use Enhanced Research:

1. Select "Enhanced Research" option in the Brand Information step.
2. Enter the brand name (e.g., "Nike", "Apple").
3. Optionally select category and country.
4. Toggle competitor analysis and industry trends as needed.
5. Click "Start Enhanced Research" to begin the process.

This enhanced data improves meme creation by providing deeper context about the brand and its competitive landscape.

## Implementation Progress

- [x] Step 1: Set up Flask backend with Firebase
- [x] Step 2: Integrate Supreme Meme AI API
- [x] Step 3: Build basic React frontend
- [x] Step 4: Implement brand data scraping
- [x] Step 5: Add news integration
- [x] Step 6: Add enhanced brand research capabilities
- [ ] Step 7: Develop advanced customization tools
- [ ] Step 8: Enable export options
