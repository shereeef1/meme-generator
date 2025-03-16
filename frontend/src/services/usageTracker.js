import FingerprintJS from '@fingerprintjs/fingerprintjs';
import { db } from '../firebase';
import { doc, getDoc, setDoc, increment, enableIndexedDbPersistence } from 'firebase/firestore';
import config from '../config';
import { getFirebaseUserId } from '../firebase';
import { updateDoc } from 'firebase/firestore';

// Enable offline persistence
try {
  enableIndexedDbPersistence(db)
    .then(() => console.log('Offline persistence enabled'))
    .catch((err) => console.error('Error enabling offline persistence:', err));
} catch (e) {
  console.error('Error enabling offline persistence:', e);
}

// Collection name for usage tracking
const USAGE_COLLECTION = 'usage_limits';

// Maximum allowed free generations
const MAX_FREE_GENERATIONS = 2;

// Initialize FingerprintJS
let fpPromise = null;

const initializeFingerprint = () => {
  if (!fpPromise) {
    fpPromise = FingerprintJS.load();
  }
  return fpPromise;
};

// Get the user's unique identifier
export const getUserId = async () => {
  try {
    const fp = await initializeFingerprint();
    const result = await fp.get();
    return result.visitorId;
  } catch (error) {
    console.error('Error generating fingerprint:', error);
    // Generate a fallback ID if fingerprinting fails
    return `fallback-${Date.now()}-${Math.random().toString(36).substring(2, 15)}`;
  }
};

// Local storage fallback for offline mode
const getLocalStorageUsage = (userId) => {
  try {
    const data = localStorage.getItem(`usage_${userId}`);
    if (data) {
      return JSON.parse(data);
    }
  } catch (err) {
    console.error('Error reading from localStorage:', err);
  }
  return null;
};

const updateLocalStorageUsage = (userId, data) => {
  try {
    localStorage.setItem(`usage_${userId}`, JSON.stringify(data));
    return true;
  } catch (err) {
    console.error('Error writing to localStorage:', err);
    return false;
  }
};

// Constants
const DEFAULT_FREE_USES = 2;
const CACHE_KEY = 'meme_generator_usage_data';
const COLLECTION_PATH = 'meme_generator_usage';
const USAGE_TIMEOUT = 10000; // 10 second timeout for Firestore operations

// Helper function to get data from localStorage
const getStoredUsageData = () => {
  try {
    const stored = localStorage.getItem(CACHE_KEY);
    if (stored) {
      return JSON.parse(stored);
    }
  } catch (error) {
    console.error('Error reading from localStorage:', error);
  }
  return null;
};

// Helper function to save data to localStorage
const saveUsageDataToStorage = (data) => {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify(data));
    return true;
  } catch (error) {
    console.error('Error saving to localStorage:', error);
    return false;
  }
};

// Get payment message from random templates
export const getPaymentMessage = () => {
  const messages = [
    'You\'ve used up all your free meme generations! Contact Sher to unlock unlimited powers.',
    'Your meme supply has run dry. Upgrade to continue your meme journey!',
    'Want more memes? Time to upgrade your account!',
    'You\'ve reached the free limit. Serious marketers upgrade now!'
  ];
  return messages[Math.floor(Math.random() * messages.length)];
};

// Main function to check remaining generations
export const checkRemainingGenerations = async () => {
  try {
    console.log('usageTracker - Checking meme generation limits');
    
    // If we're in mock mode or GitHub Pages, use local storage
    if (config.isMockMode) {
      console.log('usageTracker - Using mock/localStorage mode');
      return checkRemainingGenerationsLocalStorage();
    }
    
    // We'll attempt to get data from Firestore with a timeout
    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => reject(new Error('Firestore timeout')), USAGE_TIMEOUT);
    });
    
    try {
      // Race the Firestore fetch against the timeout
      const usageData = await Promise.race([
        checkRemainingGenerationsFirestore(),
        timeoutPromise
      ]);
      
      return usageData;
    } catch (error) {
      console.error('Error checking usage limits from Firestore:', error);
      console.log('Falling back to localStorage due to:', error.message);
      
      // Fallback to localStorage if Firestore fails
      return checkRemainingGenerationsLocalStorage();
    }
  } catch (error) {
    console.error('Fatal error in checkRemainingGenerations:', error);
    
    // Last resort fallback - always give at least some generations
    return {
      hasRemainingUses: true,
      remainingCount: DEFAULT_FREE_USES,
      totalUsed: 0,
      userId: 'fallback-user',
      source: 'error-fallback'
    };
  }
};

// Function to check remaining generations from Firestore
const checkRemainingGenerationsFirestore = async () => {
  // Get user ID from Firebase Auth or generate one
  const userId = await getFirebaseUserId();
  console.log('usageTracker - Retrieved userId:', userId);
  
  // Get the user's document from Firestore
  const userDocRef = doc(db, COLLECTION_PATH, userId);
  const docSnap = await getDoc(userDocRef);
  
  if (docSnap.exists()) {
    // User exists, get their usage data
    const userData = docSnap.data();
    const totalUsed = userData.total_used || 0;
    const remainingCount = Math.max(0, DEFAULT_FREE_USES - totalUsed);
    
    console.log('usageTracker - Existing user data:', {
      totalUsed,
      remainingCount,
      lastUsed: userData.last_used?.toDate()
    });
    
    // Create the response data
    const usageData = {
      hasRemainingUses: remainingCount > 0,
      remainingCount,
      totalUsed,
      userId,
      source: 'firestore'
    };
    
    // Cache in localStorage as backup
    saveUsageDataToStorage({
      ...usageData,
      timestamp: Date.now()
    });
    
    return usageData;
  } else {
    // User doesn't exist yet, create initial document
    console.log('usageTracker - Creating new user record in Firestore');
    const initialData = {
      total_used: 0,
      created_at: new Date(),
      last_used: new Date()
    };
    
    try {
      await setDoc(userDocRef, initialData);
    } catch (error) {
      console.error('Error creating new user record:', error);
    }
    
    const usageData = {
      hasRemainingUses: true,
      remainingCount: DEFAULT_FREE_USES,
      totalUsed: 0,
      userId,
      source: 'firestore'
    };
    
    // Cache in localStorage as backup
    saveUsageDataToStorage({
      ...usageData,
      timestamp: Date.now()
    });
    
    return usageData;
  }
};

// Function to check remaining generations from localStorage
const checkRemainingGenerationsLocalStorage = () => {
  // Check if we have data in localStorage
  const storedData = getStoredUsageData();
  
  if (storedData && storedData.userId) {
    // Calculate if the data is still valid (less than 24 hours old)
    const isDataFresh = storedData.timestamp && 
      (Date.now() - storedData.timestamp < 24 * 60 * 60 * 1000);
    
    if (isDataFresh) {
      console.log('usageTracker - Using cached usage data from localStorage');
      
      // Return the cached data with the localStorage source
      return {
        hasRemainingUses: storedData.hasRemainingUses,
        remainingCount: storedData.remainingCount,
        totalUsed: storedData.totalUsed,
        userId: storedData.userId,
        source: 'localStorage'
      };
    }
  }
  
  // If no valid stored data, create new data
  console.log('usageTracker - Creating new usage data in localStorage');
  
  // Generate a simple user ID for localStorage
  const localUserId = `local-${Math.random().toString(36).substring(2, 10)}`;
  
  const newData = {
    hasRemainingUses: true,
    remainingCount: DEFAULT_FREE_USES,
    totalUsed: 0,
    userId: localUserId,
    timestamp: Date.now(),
    source: 'localStorage'
  };
  
  // Save to localStorage
  saveUsageDataToStorage(newData);
  
  return {
    ...newData,
    source: 'localStorage'
  };
};

// Increment the usage count
export const incrementUsageCount = async (userId) => {
  try {
    console.log('usageTracker - Incrementing usage count for user:', userId);
    
    // If we're in mock mode or GitHub Pages, use local storage
    if (config.isMockMode) {
      console.log('usageTracker - Using mock/localStorage mode for increment');
      return incrementUsageCountLocalStorage();
    }
    
    // Try Firestore first
    try {
      await incrementUsageCountFirestore(userId);
    } catch (error) {
      console.error('Error incrementing Firestore count:', error);
      // Fallback to localStorage
      incrementUsageCountLocalStorage();
    }
  } catch (error) {
    console.error('Fatal error in incrementUsageCount:', error);
  }
};

// Function to increment usage count in Firestore
const incrementUsageCountFirestore = async (userId) => {
  if (!userId) {
    throw new Error('No userId provided for incrementing');
  }
  
  const userDocRef = doc(db, COLLECTION_PATH, userId);
  
  try {
    await updateDoc(userDocRef, {
      total_used: increment(1),
      last_used: new Date()
    });
    console.log('usageTracker - Successfully incremented usage in Firestore');
    
    // Also update localStorage as backup
    const storedData = getStoredUsageData();
    if (storedData) {
      storedData.totalUsed = (storedData.totalUsed || 0) + 1;
      storedData.remainingCount = Math.max(0, DEFAULT_FREE_USES - storedData.totalUsed);
      storedData.hasRemainingUses = storedData.remainingCount > 0;
      storedData.timestamp = Date.now();
      saveUsageDataToStorage(storedData);
    }
  } catch (error) {
    console.error('Error updating usage count in Firestore:', error);
    throw error;
  }
};

// Function to increment usage count in localStorage
const incrementUsageCountLocalStorage = () => {
  const storedData = getStoredUsageData();
  
  if (storedData) {
    // Increment the usage count
    storedData.totalUsed = (storedData.totalUsed || 0) + 1;
    storedData.remainingCount = Math.max(0, DEFAULT_FREE_USES - storedData.totalUsed);
    storedData.hasRemainingUses = storedData.remainingCount > 0;
    storedData.timestamp = Date.now();
    
    // Save back to localStorage
    saveUsageDataToStorage(storedData);
    console.log('usageTracker - Successfully incremented usage in localStorage');
    return storedData;
  }
  
  // If no stored data, create a new entry
  return checkRemainingGenerationsLocalStorage();
}; 