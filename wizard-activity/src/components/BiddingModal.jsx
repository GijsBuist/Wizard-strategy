import React, { useState } from 'react';
import './BiddingModal.css';

export default function BiddingModal({ maxBids, onSubmitBid }) {
  const [selectedBid, setSelectedBid] = useState(0);

  const bids = Array.from({ length: maxBids + 1 }, (_, i) => i);

  return (
    <div className="bidding-modal-overlay">
      <div className="bidding-modal-content">
        <h3>Place Your Bid</h3>
        <p>How many tricks do you predict you will win this round?</p>
        <div className="bids-grid">
          {bids.map((bid) => (
            <button
              key={bid}
              className={`bid-btn ${selectedBid === bid ? 'selected' : ''}`}
              onClick={() => setSelectedBid(bid)}
            >
              {bid}
            </button>
          ))}
        </div>
        <button
          className="submit-bid-btn"
          onClick={() => onSubmitBid(selectedBid)}
        >
          Confirm Bid ({selectedBid})
        </button>
      </div>
    </div>
  );
}