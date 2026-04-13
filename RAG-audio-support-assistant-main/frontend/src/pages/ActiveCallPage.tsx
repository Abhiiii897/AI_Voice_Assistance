import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mic, Square } from 'lucide-react';
//import all the new components we just build
import NotesPanel from '../components/activecall/NotesPanel';
import TranscriptPanel from '../components/activecall/TranscriptPanel';
import SolutionPanel from '../components/activecall/SolutionPanel';
import useDashboardStore from '../hooks/useDashboardStore';
import useCallDuration from '../hooks/useCallDuration';
import useWebSocket from '../hooks/useWebSocket';
//import demo mode
import { useDemoMode } from '../hooks/useDemoMode';

function ActiveCallPage() {
  const navigate = useNavigate();

  // Enable demo mode if ?demo=true in URL
  useDemoMode(true);

  // actual componets - subscribing to the zustand store
  const currentSentiment = useDashboardStore((state) => state.currentSentiment);
  const currentCategory = useDashboardStore((state) => state.currentCategory);
  const stopRecording = useDashboardStore((state) => state.stopRecording);
  const isRecording = useDashboardStore((state) => state.isRecording);
  const callStartTime = useDashboardStore((state) => state.callStartTime); //used to calculate duration
  const activeCallId = useDashboardStore((state) => state.activeCallId);


  const handleStopRecording = () => {
    // (DONE): implement stop mic capture, close WebSocket logic
    stopRecording(); //updates state in zustand store
    navigate('/');
  };

  // Call duration hook
  const { displayDuration } = useCallDuration(callStartTime); //cals the call duration hook we just built

  // WebSocket hook (will receive transcript, sentiment, solutions from backend)
  useWebSocket('ws://localhost:8000/ws'); // TODO: Use env var for URL

 // Redirect if no active call (with grace period for demo mode init)
useEffect(() => {
  const timer = setTimeout(() => {
    if (!callStartTime) {
      navigate('/');
    }
  }, 100); // 100ms grace period for demo mode to initialize
  
  return () => clearTimeout(timer);
}, [callStartTime, navigate]);

  // sentiment to color mapper
  const sentimentColors: Record<string, string> = {
    Positive: '#10B981',
    Neutral: '#3f3f3f',
    Negative: '#F97316',
    Agitated: '#EF4444',
  };

  //I HATE EMOJIS - but I thought it would be better to provide more emotional info
   const sentimentEmojis: Record<string, string> = {
    Positive: '😊',
    Neutral: '🙂',
    Negative: '😕',
    Agitated: '😤',
  };

  //current sentiment picker
  // the '||' is a fallback operator, if no first part then part after ||
  const sentimentColor = sentimentColors[currentSentiment?.sentiment || 'Neutral'] || sentimentColors.Neutral; // fallback to neutral
  const sentimentEmoji = sentimentEmojis[currentSentiment?.sentiment || 'Neutral'] || '😐'; //intentionally left a different emoji, so if we ever see this emoji Know that this is a fallback mechanism

  return (
    <div className="h-screen bg-black text-white overflow-hidden flex flex-col">
      {/* Top Bar - Sentiment-aware with color border */}
      <div
  className="px-6 py-3 flex items-center justify-between"
  style={{
    backgroundColor: `${sentimentColor}40`, // subtle full-bar tint
    borderBottom: `3px solid ${sentimentColor}`,
  }}
      >
        {/* Left Section - Recording Indicator */}
        <div className="flex items-center gap-2 bg-neutral-900 rounded-full px-3 py-1.5">
          <Mic className="w-4 h-4 text-red-500 animate-pulse" />
          <span className="text-sm font-medium">Recording</span>
        </div>

        {/* Center Section - Metrics Badges */}
        <div className="flex items-center gap-3">
          {/* Sentiment Badge */}
          <div
            className="px-3 py-1.5 rounded-full text-sm font-medium flex items-center gap-2"
            style={{
              backgroundColor: `${sentimentColor}20`,
              borderLeft: `3px solid ${sentimentColor}`,
            }}
          >
            <span>{sentimentEmoji}</span>
            <span>{currentSentiment?.sentiment || 'Neutral'}</span> {/**fall back to Neutal if null */}
          </div>

          {/* Category Badge */}
          <div className="px-3 py-1.5 rounded-full text-sm font-medium bg-blue-500/20 border-l-2 border-blue-500">
            {currentCategory?.category || "NOT CLASSIFIED"}
          </div>

          {/* Call Number Badge */}
          <div className="px-3 py-1.5 rounded-full text-sm font-mono bg-purple-500/20 border-l-2 border-purple-500">
            CALL ID {activeCallId?.slice(-9) || '000000000'}
          </div>

          {/* Duration Timer */}
          <div className="px-3 py-1.5 rounded-full text-sm font-mono bg-green-500/20 border-l-2 border-green-500">
            {displayDuration}
          </div>
        </div>

        {/* Right Section - Stop Button */}
        <button
          onClick={handleStopRecording}
          className="flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white px-4 py-1.5 rounded-full font-medium transition-colors"
        >
          <Square className="w-4 h-4" />
          Stop Recording
        </button>
      </div>

      {/* Three-Panel Grid - Full Height, No Vertical Scroll */}
      <div className="flex-1 grid grid-cols-3 gap-4 p-4 overflow-hidden">
        {/* Left Panel: Notes */}
        <div className="bg-neutral-950 rounded-xl overflow-hidden border border-neutral-800 flex flex-col">
          <NotesPanel />
        </div>

        {/* Center Panel: Live Transcript */}
        <div className="bg-neutral-950 rounded-xl overflow-hidden border border-neutral-800 flex flex-col">
          <TranscriptPanel />
        </div>

        {/* Right Panel: Solution Cards */}
        <div className="bg-neutral-950 rounded-xl overflow-hidden border border-neutral-800 flex flex-col">
          <SolutionPanel />
        </div>
      </div>
    </div>
  );
}

export default ActiveCallPage;