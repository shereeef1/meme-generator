// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getFirestore, connectFirestoreEmulator, enableMultiTabIndexedDbPersistence } from "firebase/firestore";
import { getStorage } from "firebase/storage";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: process.env.REACT_APP_FIREBASE_API_KEY,
  authDomain: process.env.REACT_APP_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.REACT_APP_FIREBASE_PROJECT_ID,
  storageBucket: process.env.REACT_APP_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.REACT_APP_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.REACT_APP_FIREBASE_APP_ID
};

// Log configuration for debugging (remove in production)
console.log('Firebase config loaded from environment:', {
  apiKey: process.env.REACT_APP_FIREBASE_API_KEY ? 'Set' : 'Not set',
  authDomain: process.env.REACT_APP_FIREBASE_AUTH_DOMAIN ? 'Set' : 'Not set',
  projectId: process.env.REACT_APP_FIREBASE_PROJECT_ID ? 'Set' : 'Not set',
  storageBucket: process.env.REACT_APP_FIREBASE_STORAGE_BUCKET ? 'Set' : 'Not set',
  appId: process.env.REACT_APP_FIREBASE_APP_ID ? 'Set' : 'Not set',
});

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firestore and Storage
const db = getFirestore(app);
const storage = getStorage(app);

// Set up better offline persistence
try {
  // Use multi-tab persistence when possible
  enableMultiTabIndexedDbPersistence(db)
    .then(() => {
      console.log("Firestore multi-tab persistence initialized");
    })
    .catch((err) => {
      if (err.code === 'failed-precondition') {
        // Multiple tabs open, only use single-tab persistence
        console.warn("Firestore persistence unavailable in multiple tabs");
      } else if (err.code === 'unimplemented') {
        // Browser doesn't support persistence
        console.warn("This browser doesn't support firestore persistence");
      } else {
        console.error("Error enabling firestore persistence:", err);
      }
    });
} catch (err) {
  console.error("Error setting up Firestore persistence:", err);
}

// Use local emulator if in development
if (process.env.NODE_ENV === 'development' && process.env.REACT_APP_USE_FIREBASE_EMULATOR === 'true') {
  try {
    connectFirestoreEmulator(db, 'localhost', 8080);
    console.log("Connected to Firestore emulator");
  } catch (err) {
    console.error("Failed to connect to Firestore emulator:", err);
  }
}

export { app, db, storage }; 