//STUB TODO: Make a real one aft backend is pushed
//Dev comment: I HAVE NO IDEA WHAT IS GOING ON IN HERE AS IT IS A STUB

import { useEffect } from 'react';
import useDashboardStore from './useDashboardStore';

/**
 * Hook to manage WebSocket connection to backend
 * Listens for: transcript, sentiment, category, solutions updates
 *
 * For now: stub with console logs
 */
function useWebSocket(url: string) {
  const {
    addTranscriptChunk,
    updateSentiment,
    updateCategory,
    addSolutionCards,
    setConnected,
  } = useDashboardStore();

  useEffect(() => {
    if (!url) return;

    console.log(`[WebSocket] Attempting to connect to ${url}`);

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log('[WebSocket] Connected');
        setConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const messageType = data.type;

          // Route messages to appropriate handlers
          switch (messageType) {
            case 'transcript_chunk':
              console.log('[WebSocket] Transcript received:', data.payload);
              addTranscriptChunk(data.payload);
              break;

            case 'sentiment_update':
              console.log('[WebSocket] Sentiment update:', data.payload);
              updateSentiment(data.payload);
              break;

            case 'category_update':
              console.log('[WebSocket] Category update:', data.payload);
              updateCategory(data.payload);
              break;

            case 'solution_cards':
              console.log('[WebSocket] Solutions received:', data.payload);
              addSolutionCards(data.payload);
              break;

            default:
              console.warn('[WebSocket] Unknown message type:', messageType);
          }
        } catch (error) {
          console.error('[WebSocket] Parse error:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('[WebSocket] Error:', error);
        setConnected(false);
      };

      ws.onclose = () => {
        console.log('[WebSocket] Disconnected');
        setConnected(false);
      };

      // Cleanup: close connection when hook unmounts
      return () => {
        console.log('[WebSocket] Closing connection');
        ws.close();
      };
    } catch (error) {
      console.error('[WebSocket] Connection failed:', error);
      setConnected(false);
    }
  }, [url, addTranscriptChunk, updateSentiment, updateCategory, addSolutionCards, setConnected]);
}

export default useWebSocket;