import React, { useState, useEffect } from 'react';
import './App.css';

export default function App() {
  const [socket, setSocket] = useState(null);
  const [gameState, setGameState] = useState({
    status: 'waiting',
    round: 1,
    players: {}
  });
  const [selectedBid, setSelectedBid] = useState(0);

  useEffect(() => {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    const wsUrl = `${wsProtocol}${window.location.host}/ws`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => console.log("Connected to WebSocket");
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setGameState(data);
    };

    setSocket(ws);
    return () => ws.close();
  }, []);

  const handleStartGame = () => {
    if (socket) {
      socket.send(JSON.stringify({ type: "START_GAME" }));
    }
  };

  const handleConfirmBid = () => {
    if (socket) {
      socket.send(JSON.stringify({ type: "SUBMIT_BID", bid: selectedBid }));
    }
  };

  const playerCount = Object.keys(gameState.players).length;

  return (
    <div className="p-6 text-white bg-gray-950 min-h-screen flex flex-col items-center">
      <h1 className="text-3xl font-bold mb-2">Wizard Activity</h1>
      <p className="text-sm text-gray-400 mb-6">Connected Players: {playerCount} / 3 required</p>

      {gameState.status === 'waiting' && (
        <div className="bg-gray-900 p-6 rounded-lg border border-gray-800 text-center">
          <p className="mb-4">Waiting for at least 3 players to start the game.</p>
          <button
            onClick={handleStartGame}
            disabled={playerCount < 3}
            className={`px-4 py-2 rounded font-semibold ${
              playerCount >= 3 ? 'bg-indigo-600 hover:bg-indigo-500 cursor-pointer' : 'bg-gray-700 opacity-50 cursor-not-allowed'
            }`}
          >
            Start Game
          </button>
        </div>
      )}

      {gameState.status === 'bidding' && (
        <div className="bg-gray-900 p-6 rounded-lg border border-gray-800 w-96 text-center">
          <h2 className="text-xl font-semibold mb-2">Place Your Bid</h2>
          <p className="text-sm text-gray-400 mb-4">Round {gameState.round}: How many tricks will you win?</p>
          
          <div className="flex justify-center gap-2 mb-4 flex-wrap">
            {Array.from({ length: gameState.round + 1 }, (_, i) => (
              <button
                key={i}
                onClick={() => setSelectedBid(i)}
                className={`w-10 h-10 rounded font-bold ${
                  selectedBid === i ? 'bg-indigo-600 text-white' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                }`}
              >
                {i}
              </button>
            ))}
          </div>

          <button
            onClick={handleConfirmBid}
            className="w-full py-2 bg-green-600 hover:bg-green-500 rounded font-semibold text-white cursor-pointer"
          >
            Confirm Bid ({selectedBid})
          </button>
        </div>
      )}
    </div>
  );
}