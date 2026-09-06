import React from 'react';
import './TrickArea.css';

export default function TrickArea({ currentTrick }) {
  return (
    <div className="trick-area-container">
      <h3>Current Trick</h3>
      <div className="table-felt">
        {currentTrick && currentTrick.length > 0 ? (
          currentTrick.map((play, index) => (
            <div key={index} className="played-card-wrapper">
              <div className="card played">
                <span className="card-value">{play.card.value}</span>
                <span className="card-suit">{play.card.suit}</span>
              </div>
              <span className="player-name">{play.playerName}</span>
            </div>
          ))
        ) : (
          <p className="waiting-text">Waiting for plays...</p>
        )}
      </div>
    </div>
  );
}