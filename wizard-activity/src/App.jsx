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
  const [myPlayerId, setMyPlayerId] = useState(null);

  useEffect(() => {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    const wsUrl = `${wsProtocol}${window.location.host}/ws`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => console.log("Connected to WebSocket");
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setGameState(data);
      
      // Infer our own player ID based on who has a hand or just pick the first unassigned matching client
      // For local testing, we can check matching hand sizes or grab keys. Let's find the player object that matches local session if stored, or default to the last joined.
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
  const playerEntries = Object.values(gameState.players);
  
  // Find current player data (using the last player or let's inspect hands)
  // To keep it simple for multi-tab testing, let's let the user pick which player profile they are controlling or display all hands if testing locally.
  
  return (
    <div className="p-6 text-white bg-gray-950 min-h-screen flex flex-col items-center">
      <h1 className="text-3xl font-bold mb-2">Wizard Game</h1>
      <p className="text-sm text-gray-400 mb-6">Connected Players: {playerCount} / 3 required</p>

      {gameState.status === 'waiting' && (
        <div className="bg-gray-900 p-6 rounded-lg border border-gray-800 text-center">
          <p className="mb-4">Waiting for at least 3 players to start the game.</p>
          <button
            onClick={handleStartGame}
            disabled={playerCount < 3}
            className={`px-4 py-2 rounded font-semibold cursor-pointer ${
              playerCount >= 3 ? 'bg-indigo-600 hover:bg-indigo-500' : 'bg-gray-700 opacity-50 cursor-not-allowed'
            }`}
          >
            Start Game
          </button>
        </div>
      )}

      {(gameState.status === 'bidding' || gameState.status === 'playing') && (
        <div className="w-full max-w-xl flex flex-col gap-6">
          <div className="bg-gray-900 p-6 rounded-lg border border-gray-800 text-center">
            <h2 className="text-xl font-semibold mb-2">Round {gameState.round}: Place Your Bid</h2>
            <p className="text-sm text-gray-400 mb-4">Review your cards below and choose how many tricks you will win.</p>
            
            <div className="flex justify-center gap-2 mb-4 flex-wrap">
              {Array.from({ length: gameState.round + 1 }, (_, i) => (
                <button
                  key={i}
                  onClick={() => setSelectedBid(i)}
                  className={`w-10 h-10 rounded font-bold cursor-pointer ${
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

          <div className="bg-gray-900 p-6 rounded-lg border border-gray-800">
            <h3 className="text-lg font-semibold mb-3">Players in Room</h3>
            <div className="flex flex-col gap-3">
              {playerEntries.map((p) => (
                <div key={p.id} className="p-3 bg-gray-800 rounded flex flex-col gap-2">
                  <div className="flex justify-between text-sm">
                    <span className="font-bold">{p.name}</span>
                    <span>Bid: {p.bid !== null ? p.bid : 'Pending'} | Won: {p.won}</span>
                  </div>
                  <div className="flex gap-2 flex-wrap">
                    {p.hand && p.hand.map((card, idx) => (
                      <div key={idx} className="px-3 py-2 bg-gray-700 rounded border border-gray-600 text-xs font-mono">
                        {card.type === 'wizard' ? '🧙 Wizard' : card.type === 'jester' ? '🃏 Jester' : `${card.suit.toUpperCase()} ${card.value}`}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}