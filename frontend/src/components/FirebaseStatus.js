import React, { useState, useEffect } from 'react';
import { db } from '../firebase';
import { enableNetwork, disableNetwork } from 'firebase/firestore';
import { testFirebase } from '../firebaseTest';

const FirebaseStatus = () => {
  const [status, setStatus] = useState('checking');
  const [error, setError] = useState(null);
  const [isOnline, setIsOnline] = useState(window.navigator.onLine);
  const [testResults, setTestResults] = useState(null);

  // Monitor online status
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Test the Firebase connection
  useEffect(() => {
    async function checkConnection() {
      try {
        setStatus('checking');
        setError(null);
        setTestResults(null);

        // Run the comprehensive test
        const results = await testFirebase();
        setTestResults(results);
        
        if (results.error) {
          setStatus('error');
          setError(results.error);
        } else if (results.connection) {
          setStatus('connected');
        } else {
          setStatus('error');
          setError('Unknown error in Firebase connection');
        }
      } catch (err) {
        console.error('Firebase connection test error:', err);
        setStatus('error');
        setError(err.message);
        setTestResults({ error: err.message });
      }
    }
    
    checkConnection();
  }, [isOnline]);

  // Toggle network
  const toggleNetwork = async () => {
    try {
      if (status === 'connected') {
        await disableNetwork(db);
        setStatus('offline');
      } else {
        await enableNetwork(db);
        setStatus('checking');
        // The previous effect will update the status once connected
      }
    } catch (err) {
      console.error('Error toggling network:', err);
      setError(err.message);
    }
  };

  const runTest = async () => {
    try {
      setStatus('checking');
      setError(null);
      setTestResults(null);
      
      const results = await testFirebase();
      setTestResults(results);
      
      if (results.error) {
        setStatus('error');
        setError(results.error);
      } else if (results.connection) {
        setStatus('connected');
      } else {
        setStatus('error');
        setError('Unknown error in Firebase connection');
      }
    } catch (err) {
      console.error('Firebase test error:', err);
      setStatus('error');
      setError(err.message);
    }
  };

  return (
    <div className="card mb-3">
      <div className="card-header bg-primary text-white">
        <h5 className="mb-0">Firebase Connection Status</h5>
      </div>
      <div className="card-body">
        <div className="d-flex align-items-center mb-3">
          <div 
            className={`status-indicator me-2 ${
              status === 'connected' 
                ? 'bg-success' 
                : status === 'checking' 
                  ? 'bg-warning' 
                  : 'bg-danger'
            }`}
          ></div>
          <div>
            <p className="mb-0">
              <strong>Status:</strong> {status === 'connected' 
                ? 'Connected to Firebase' 
                : status === 'checking' 
                  ? 'Checking connection...' 
                  : status === 'offline'
                    ? 'Offline mode enabled'
                    : 'Connection error'}
            </p>
            <p className="mb-0">
              <strong>Network:</strong> {isOnline ? 'Online' : 'Offline'}
            </p>
            {error && (
              <div className="small text-danger mt-1">
                Error: {error}
              </div>
            )}
          </div>
        </div>
        
        {testResults && (
          <div className="mb-3">
            <h6>Test Results:</h6>
            <ul className="list-group">
              <li className="list-group-item d-flex justify-content-between align-items-center">
                Connection
                <span className={`badge ${testResults.connection ? 'bg-success' : 'bg-danger'}`}>
                  {testResults.connection ? 'Success' : 'Failed'}
                </span>
              </li>
              <li className="list-group-item d-flex justify-content-between align-items-center">
                Write Operation
                <span className={`badge ${testResults.write ? 'bg-success' : 'bg-danger'}`}>
                  {testResults.write ? 'Success' : 'Failed'}
                </span>
              </li>
              <li className="list-group-item d-flex justify-content-between align-items-center">
                Read Operation
                <span className={`badge ${testResults.read ? 'bg-success' : 'bg-danger'}`}>
                  {testResults.read ? 'Success' : 'Failed'}
                </span>
              </li>
            </ul>
          </div>
        )}
        
        <div className="d-flex flex-wrap gap-2">
          <button 
            className="btn btn-sm btn-outline-primary" 
            onClick={toggleNetwork}
          >
            {status === 'connected' ? 'Go Offline' : 'Try to Connect'}
          </button>
          <button 
            className="btn btn-sm btn-outline-primary" 
            onClick={runTest}
          >
            Run Firebase Test
          </button>
          <button 
            className="btn btn-sm btn-outline-secondary" 
            onClick={() => window.location.reload()}
          >
            Reload Page
          </button>
        </div>
      </div>
      <style jsx>{`
        .status-indicator {
          width: 12px;
          height: 12px;
          border-radius: 50%;
        }
      `}</style>
    </div>
  );
};

export default FirebaseStatus; 