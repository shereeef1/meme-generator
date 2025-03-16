// Simple Firebase connection test

import { db } from './firebase';
import { collection, doc, getDoc, setDoc, getDocs } from 'firebase/firestore';

// Test basic operations
export async function testFirebase() {
  const results = {
    connection: false,
    write: false,
    read: false,
    error: null
  };

  try {
    console.log('Testing Firebase connection...');
    
    // Test document ID
    const testId = `test-${Date.now()}`;
    
    // Test collection and document reference
    const testCollection = collection(db, 'connection_test');
    const testDoc = doc(testCollection, testId);
    
    // Test writing data
    console.log('Testing write operation...');
    await setDoc(testDoc, {
      timestamp: new Date().toISOString(),
      test: 'data'
    });
    results.write = true;
    
    // Test reading the data back
    console.log('Testing read operation...');
    const readResult = await getDoc(testDoc);
    
    if (readResult.exists()) {
      results.read = true;
      results.connection = true;
      console.log('Firebase test successful!', readResult.data());
    } else {
      results.error = 'Document was written but could not be read back';
      console.error('Document was written but could not be read back');
    }
    
    // List all test documents
    console.log('Listing documents in collection...');
    const querySnapshot = await getDocs(testCollection);
    const docs = [];
    querySnapshot.forEach((doc) => {
      docs.push({ id: doc.id, ...doc.data() });
    });
    console.log('Documents in collection:', docs);
    
  } catch (error) {
    console.error('Firebase test failed:', error);
    results.error = `${error.code}: ${error.message}`;
  }
  
  return results;
}

// Execute the test if this file is loaded directly
if (typeof window !== 'undefined') {
  window.testFirebase = testFirebase;
  console.log('Firebase test function available as window.testFirebase()');
} 