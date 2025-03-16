// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getFirestore, connectFirestoreEmulator, enableMultiTabIndexedDbPersistence } from "firebase/firestore";
import { getStorage } from "firebase/storage";
import { getAuth, onAuthStateChanged } from "firebase/auth";

// Check if Firebase config is available
const hasFirebaseConfig = process.env.REACT_APP_FIREBASE_API_KEY && 
                          process.env.REACT_APP_FIREBASE_PROJECT_ID;

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: process.env.REACT_APP_FIREBASE_API_KEY || "demo-key-for-initialization-only",
  authDomain: process.env.REACT_APP_FIREBASE_AUTH_DOMAIN || "demo-project.firebaseapp.com",
  projectId: process.env.REACT_APP_FIREBASE_PROJECT_ID || "demo-project-id",
  storageBucket: process.env.REACT_APP_FIREBASE_STORAGE_BUCKET || "demo-project.appspot.com",
  messagingSenderId: process.env.REACT_APP_FIREBASE_MESSAGING_SENDER_ID || "000000000000",
  appId: process.env.REACT_APP_FIREBASE_APP_ID || "1:000000000000:web:0000000000000000000000"
};

// Log configuration for debugging (remove in production)
console.log('Firebase config loaded from environment:', {
  apiKey: process.env.REACT_APP_FIREBASE_API_KEY ? 'Set' : 'Not set',
  authDomain: process.env.REACT_APP_FIREBASE_AUTH_DOMAIN ? 'Set' : 'Not set',
  projectId: process.env.REACT_APP_FIREBASE_PROJECT_ID ? 'Set' : 'Not set',
  storageBucket: process.env.REACT_APP_FIREBASE_STORAGE_BUCKET ? 'Set' : 'Not set',
  appId: process.env.REACT_APP_FIREBASE_APP_ID ? 'Set' : 'Not set',
  usingMockConfig: !hasFirebaseConfig
});

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase services with graceful degradation
let db, storage, auth;

try {
  // Initialize Firestore
  db = getFirestore(app);
  
  // Initialize Storage
  storage = getStorage(app);
  
  // Initialize Auth
  auth = getAuth(app);
  
  // Warning if using mock config
  if (!hasFirebaseConfig) {
    console.warn("Using mock Firebase configuration. Firebase features will be limited.");
  }
} catch (error) {
  console.error("Error initializing Firebase services:", error);
  // Create dummy objects to prevent errors elsewhere in the code
  db = { collection: () => ({ doc: () => ({ get: async () => ({ exists: false, data: () => ({}) }) }) }) };
  storage = { ref: () => ({ put: async () => ({}) }) };
  auth = { onAuthStateChanged: (callback) => callback(null) };
}

// Set up offline persistence only if Firestore was successfully initialized
if (db && typeof db.enablePersistence === 'function') {
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

// Get current user ID or generate a temporary one
const getFirebaseUserId = async () => {
  if (!auth || !hasFirebaseConfig) {
    // If auth is not available or using mock config, return anonymous ID
    let anonymousId = localStorage.getItem('anonymousUserId');
    if (!anonymousId) {
      anonymousId = 'anon_' + Math.random().toString(36).substring(2, 15);
      localStorage.setItem('anonymousUserId', anonymousId);
    }
    return anonymousId;
  }

  return new Promise((resolve) => {
    onAuthStateChanged(auth, (user) => {
      if (user) {
        // User is signed in
        resolve(user.uid);
      } else {
        // User is not signed in, use stored anonymous ID or generate one
        let anonymousId = localStorage.getItem('anonymousUserId');
        if (!anonymousId) {
          anonymousId = 'anon_' + Math.random().toString(36).substring(2, 15);
          localStorage.setItem('anonymousUserId', anonymousId);
        }
        resolve(anonymousId);
      }
    });
  });
};

export { app, db, storage, auth, getFirebaseUserId }; 