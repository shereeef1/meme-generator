// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getFirestore } from "firebase/firestore";
import { getStorage } from "firebase/storage";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyBgJhW99HDgzT0OwLUm4ABD8v3AjgmxkOI",
  authDomain: "meme-d4709.firebaseapp.com",
  projectId: "meme-d4709",
  storageBucket: "meme-d4709.firebasestorage.app",
  messagingSenderId: "63393295594",
  appId: "1:63393295594:web:a65ea8895ec945a638fb93"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firestore and Storage
const db = getFirestore(app);
const storage = getStorage(app);

export { app, db, storage }; 