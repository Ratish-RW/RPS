import { useState, useEffect, useRef } from "react";
import {io} from "socket.io-client";
const socket = io("https://rps-sema.onrender.com/"); 

export default function App() {
  const [playerMove, setPlayerMove] = useState(null);
  const [computerMove, setComputerMove] = useState(null);
  const [score, setScore] = useState({ player: 0, computer: 0 });
  const [countdown, setCountdown] = useState(0);
  const [gameRunning, setGameRunning] = useState(false);
  const [matches, setMatches] = useState(0);
  const [roundResult, setRoundResult] = useState(null);
  const [matchWinner, setMatchWinner] = useState(null);
  const [gameComplete, setGameComplete] = useState(false);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const timerRef = useRef(null);
  const gameRunningRef = useRef(false);
  const TARGET_SCORE = 5;

  useEffect(() => {
    async function setupCamera() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      } catch (err) {
        console.error("Webcam not available:", err);
      }
    }
    setupCamera();

  }, []);

  useEffect(() => {
  socket.on("result", (data) => {
    console.log("Server result:", data);

    // update UI
    setPlayerMove(data.player_move);
    setComputerMove(data.computer_move);
    setRoundResult(data.outcome);

    setMatches((prev) => prev + 1);
    let newScore = { ...score };
    
    if (data.outcome === "Player Wins") {
      newScore.player = score.player + 1;
      setScore(newScore);
    } else if (data.outcome === "Computer Wins") {
      newScore.computer = score.computer + 1;
      setScore(newScore);
    }
    else if(data.outcome === "No Hand Detected"){
      setMatches((prev) => prev - 1);
      newScore = score; // Keep score unchanged
    }

    // Check if match is complete
    if (newScore.player >= TARGET_SCORE || newScore.computer >= TARGET_SCORE) {
      const winner = newScore.player >= TARGET_SCORE ? "Player" : "Computer";
      setMatchWinner(winner);
      setGameComplete(true);
      setGameRunning(false);
      gameRunningRef.current = false;
      return;
    }

    // trigger next round after delay - use gameRunning state, not ref
    if (gameRunning) {
      setTimeout(runRound, 2000);
    }
  });

  return () => {
    socket.off("result");
  };
}, [gameRunning, score]);

  const startGame = () => {
    if (!gameRunning) {
      setGameRunning(true);
      gameRunningRef.current = true;
      setGameComplete(false);
      setMatchWinner(null);
      runRound();
    }
  };

  const stopGame = () => {
    setGameRunning(false);
    gameRunningRef.current = false;
    setCountdown(0);
    
    // Clear any running timer
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    
    // Determine current leader for early stop results
    if (score.player > 0 || score.computer > 0) {
      if (score.player > score.computer) {
        setMatchWinner("Player");
      } else if (score.computer > score.player) {
        setMatchWinner("Computer");
      } else {
        setMatchWinner("Tie");
      }
      setGameComplete(true);
    } else {
      // No rounds played yet
      setRoundResult(null);
      setPlayerMove(null);
      setComputerMove(null);
      setMatchWinner(null);
      setGameComplete(false);
    }
  };

  const resetGame = () => {
    setRoundResult(null);
    setPlayerMove(null);
    setComputerMove(null);
    setScore({ player: 0, computer: 0 });
    setMatches(0);
    setMatchWinner(null);
    setGameComplete(false);
  };

  const runRound = () => {
    let i = 3;
    setCountdown(i);

    const timer = () => {
      i--;
      if (i === 0) {
        setCountdown(0);
        captureImage(); 
      } else {
        setCountdown(i);
        setTimeout(timer,1000)
      }
    }
    setTimeout(timer,1000)
  };

  const captureImage = () => {
    // Double check if game is still running before capturing
    if (!gameRunningRef.current) {
      return;
    }
    
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (video && canvas) {
      const ctx = canvas.getContext("2d");
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      const dataUrl = canvas.toDataURL("image/jpeg");
      socket.emit("game", dataUrl);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-blue-100 to-purple-200 text-gray-800 p-6">
      {/* Video Screen */}
      <div className="mb-6 relative">
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="w-80 h-60 rounded-2xl shadow-lg border-4 border-white object-cover"
        />
        {/* Countdown overlay */}
        {gameRunning &&
          (countdown > 0 ? (
            <div className="absolute inset-0 flex items-center justify-center text-6xl font-bold text-red-600">
            {countdown}
          </div>
          ) : null)
        }
      </div>
      
      {/* Hidden canvas for capture */}
      <canvas ref={canvasRef} style={{ display: "none" }} />

      {/* Target Score Display */}
      <div className="mb-4 text-lg font-semibold text-purple-700">
        First to {TARGET_SCORE} wins the match!
      </div>

      {/* Scoreboard */}
      <div className="flex gap-10 mb-4">
        <div className="text-center">
          <h2 className="text-2xl font-bold">Player</h2>
          <p className="text-3xl">{score.player}</p>
        </div>
        <div className="text-center">
          <h2 className="text-2xl font-bold">Computer</h2>
          <p className="text-3xl">{score.computer}</p>
        </div>
      </div>

      {/* Total Matches */}
      <div className="mb-4 text-xl font-semibold">
        Rounds Played: {matches}
      </div>

      {/* Current Moves */}
      <div className="flex gap-12 mb-4">
        <div className="text-center">
          <h3 className="font-semibold">Your Move</h3>
          <p className="text-xl">{playerMove || "-"}</p>
        </div>
        <div className="text-center">
          <h3 className="font-semibold">Computer's Move</h3>
          <p className="text-xl">{computerMove || "-"}</p>
        </div>
      </div>

      {/* Round Result */}
      {roundResult && !gameComplete && (
        <div className="mb-6 text-2xl font-bold text-blue-700">
          {roundResult}
        </div>
      )}

      {/* Match Winner Display */}
      {gameComplete && matchWinner && (
        <div className="mb-6 text-center">
          <div className={`text-3xl font-bold mb-2 ${
            matchWinner === "Player" ? "text-green-600" : 
            matchWinner === "Computer" ? "text-red-600" : "text-purple-600"
          }`}>
            {matchWinner === "Tie" ? "Match Tied!" : `${matchWinner} Wins the Match!`}
          </div>
          <div className="text-lg text-gray-700">
            Final Score: Player {score.player} - {score.computer} Computer
          </div>
        </div>
      )}
      
      {/* Start / Stop / Reset Buttons */}
      <div className="flex gap-6">
        {!gameRunning && !gameComplete ? (
          <button
            onClick={startGame}
            className="px-8 py-3 rounded-xl bg-green-500 text-white shadow-md hover:scale-105 transition text-lg font-semibold"
          >
            Start Game
          </button>
        ) : gameRunning ? (
          <button
            onClick={stopGame}
            className="px-8 py-3 rounded-xl bg-red-500 text-white shadow-md hover:scale-105 transition text-lg font-semibold"
          >
            Stop Game
          </button>
        ) : (
          <div className="flex gap-4">
            {/* <button
              onClick={startGame}
              className="px-8 py-3 rounded-xl bg-green-500 text-white shadow-md hover:scale-105 transition text-lg font-semibold"
            >
              Play Again
            </button> */}
            <button
              onClick={resetGame}
              className="px-8 py-3 rounded-xl bg-gray-500 text-white shadow-md hover:scale-105 transition text-lg font-semibold"
            >
              Reset
            </button>
          </div>
        )}
      </div>
    </div>
  );
}