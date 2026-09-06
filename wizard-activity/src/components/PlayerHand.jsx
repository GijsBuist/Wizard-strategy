import React from 'react';
import './PlayerHand.css';

export default function PlayerHand({ hand, onCardClick, disabled }) {
  return (
    <div className="player-hand-container">
      <h3>Your Hand</h3>
      <div className="cards-row">
        {hand && hand.length > 0 ? (
          hand.map((card, index) => (
            <button
              key={index}
              className={`card ${card.suit || 'special'} ${disabled ? 'disabled' : ''}`}
              onClick={() => !disabled && onCardClick(card)}
              disabled={disabled}
            >
              <span className="card-value">{card.value}</span>
              <span className="card-suit">{card.suit}</span>
            </button>
          ))
        ) : (
          <p className="no-cards">No cards in hand</p>
        )}
      </div>
    </div>
  );
}