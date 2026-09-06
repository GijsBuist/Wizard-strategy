import React from 'react';
import './ScoreBoard.css';

export default function ScoreBoard({ scores, currentRound }) {
  return (
    <div className="scoreboard-container">
      <h3>Scoreboard (Round {currentRound})</h3>
      <table className="scoreboard-table">
        <thead>
          <tr>
            <th>Player</th>
            <th>Bid</th>
            <th>Won</th>
            <th>Score</th>
          </tr>
        </thead>
        <tbody>
          {scores && scores.length > 0 ? (
            scores.map((player, index) => (
              <tr key={index}>
                <td>{player.name}</td>
                <td>{player.bid ?? '-'}</td>
                <td>{player.tricksWon}</td>
                <td className="total-score">{player.totalScore}</td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan="4">No scores recorded yet</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}