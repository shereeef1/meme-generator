import FingerprintJS from '@fingerprintjs/fingerprintjs';
import { db } from '../firebase';
import { doc, getDoc, setDoc, increment, enableIndexedDbPersistence } from 'firebase/firestore';

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

// Check if the user has remaining free generations
export const checkRemainingGenerations = async () => {
  try {
    const userId = await getUserId();
    
    // Add a timeout to prevent indefinite waiting
    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => reject(new Error('Firestore timeout')), 3000);
    });
    
    try {
      // Try Firestore first with a timeout
      const firestorePromise = (async () => {
        const userRef = doc(db, USAGE_COLLECTION, userId);
        const userDoc = await getDoc(userRef);
        
        if (userDoc.exists()) {
          const data = userDoc.data();
          const usedCount = data.meme_generations || 0;
          
          // Update local storage as backup
          updateLocalStorageUsage(userId, {
            meme_generations: usedCount,
            last_used: data.last_used || new Date().toISOString()
          });
          
          return {
            remainingCount: Math.max(0, MAX_FREE_GENERATIONS - usedCount),
            totalUsed: usedCount,
            hasRemainingUses: usedCount < MAX_FREE_GENERATIONS,
            userId,
            source: 'firestore'
          };
        }
        
        // Document doesn't exist but connection worked
        return {
          remainingCount: MAX_FREE_GENERATIONS,
          totalUsed: 0,
          hasRemainingUses: true,
          userId,
          source: 'firestore-new'
        };
      })();
      
      // Race between Firestore query and timeout
      const result = await Promise.race([firestorePromise, timeoutPromise]);
      return result;
    } catch (firestoreError) {
      console.error('Error checking usage limits from Firestore:', firestoreError);
      console.log('Falling back to localStorage due to:', firestoreError.message);
      // If Firestore fails, fall back to localStorage
    }
    
    // Fallback to localStorage
    const localData = getLocalStorageUsage(userId);
    if (localData) {
      const usedCount = localData.meme_generations || 0;
      return {
        remainingCount: Math.max(0, MAX_FREE_GENERATIONS - usedCount),
        totalUsed: usedCount,
        hasRemainingUses: usedCount < MAX_FREE_GENERATIONS,
        userId,
        source: 'localStorage'
      };
    }
      
    // New user or no data available
    return {
      remainingCount: MAX_FREE_GENERATIONS,
      totalUsed: 0,
      hasRemainingUses: true,
      userId,
      source: 'default'
    };
  } catch (error) {
    console.error('Error checking usage limits:', error);
    // If there's an error, we'll be cautious and allow only one use
    return {
      remainingCount: 1,
      totalUsed: 0,
      hasRemainingUses: true,
      error: 'Failed to check usage limits',
      source: 'error'
    };
  }
};

// Increment usage count after successful generation
export const incrementUsageCount = async (userId) => {
  try {
    if (!userId) {
      userId = await getUserId();
    }
    
    try {
      // Try Firestore first
      const userRef = doc(db, USAGE_COLLECTION, userId);
      
      // Get current document to check if it exists
      const userDoc = await getDoc(userRef);
      
      if (userDoc.exists()) {
        // Update existing document with increment
        await setDoc(userRef, {
          meme_generations: increment(1),
          last_used: new Date().toISOString()
        }, { merge: true });
      } else {
        // Create new document
        await setDoc(userRef, {
          meme_generations: 1,
          last_used: new Date().toISOString(),
          first_used: new Date().toISOString()
        });
      }
    } catch (firestoreError) {
      console.error('Error incrementing usage count in Firestore:', firestoreError);
      // If Firestore fails, fall back to localStorage
    }
    
    // Always update localStorage as a backup
    const localData = getLocalStorageUsage(userId) || { meme_generations: 0 };
    updateLocalStorageUsage(userId, {
      meme_generations: (localData.meme_generations || 0) + 1,
      last_used: new Date().toISOString(),
      first_used: localData.first_used || new Date().toISOString()
    });
    
    return true;
  } catch (error) {
    console.error('Error incrementing usage count:', error);
    return false;
  }
};

// Get a formatted payment message
export const getPaymentMessage = () => {
  return "You've used all your free meme generations! Contact Sher at +91 7888117894 to upgrade and keep the memes flowing.";
}; 