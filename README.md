# D2C Brand Meme Generator

A SaaS platform that helps direct-to-consumer (D2C) e-commerce brands create engaging memes by combining their brand identity with trending news and topics.

## Features

- Brand data scraping from website URLs
- Meme generation using Supreme Meme AI API
- News integration with trending topics
- Customization tools for memes
- Export options for sharing on social media

## Project Structure

```
project-root/
├── backend/              # Flask API backend
│   ├── modules/          # Functionality modules
│   ├── app.py            # Main Flask application
│   ├── config.py         # Configuration
│   ├── firebase_config.py # Firebase setup
│   └── requirements.txt  # Python dependencies
│
├── frontend/             # React frontend (to be implemented)
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

### Frontend Setup (Coming in Step 3)

Instructions for setting up the React frontend will be added after implementation.

## Implementation Progress

- [x] Step 1: Set up Flask backend with Firebase (in progress)
- [ ] Step 2: Integrate Supreme Meme AI API
- [ ] Step 3: Build basic React frontend
- [ ] Step 4: Implement brand data scraping
- [ ] Step 5: Add news integration
- [ ] Step 6: Develop customization tools
- [ ] Step 7: Enable export options
