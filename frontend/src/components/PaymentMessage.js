import React from 'react';
import { getPaymentMessage } from '../services/usageTracker';

const PaymentMessage = () => {
  return (
    <div className="payment-message-container card">
      <div className="card-header bg-primary text-white">
        <h3 className="mb-0">
          <span role="img" aria-label="Stop">⛔</span> Free Limit Reached
        </h3>
      </div>
      <div className="card-body">
        <div className="text-center mb-4">
          <span role="img" aria-label="Money" style={{ fontSize: '4rem' }}>💰</span>
        </div>
        <p className="lead text-center">{getPaymentMessage()}</p>
        <div className="text-center mt-4">
          <a 
            href={`https://wa.me/917888117894?text=I%20want%20to%20upgrade%20my%20meme%20generator%20access!`} 
            target="_blank" 
            rel="noopener noreferrer"
            className="btn btn-success btn-lg"
          >
            <span role="img" aria-label="WhatsApp">💬</span> Contact on WhatsApp
          </a>
        </div>
      </div>
      <div className="card-footer text-center text-muted">
        <small>Upgrade now to unlock unlimited meme generation!</small>
      </div>
    </div>
  );
};

export default PaymentMessage; 