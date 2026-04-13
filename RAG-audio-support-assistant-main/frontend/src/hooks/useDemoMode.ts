/**
 * Demo mode hook for testing without backend
 * Usage: Add ?demo=true to URL to enable
 * 
 * When active:
 * - Auto-populates dashboard with mock data
 * - Simulates live updates (new transcripts, solutions every N seconds)
 * - Great for testing UI without running backend
 */

import { useEffect } from 'react';
import useDashboardStore from './useDashboardStore';
import {
  generateTranscriptChunk,
  generateSentimentUpdate,
  generateCategoryUpdate,
  generateSolutionCards,
  generateNote,
} from '../utils/mockData';

/**
 * Check if demo mode is enabled (URL param or localStorage)
 */
function isDemoModeEnabled(): boolean {
  // Check URL params
  const params = new URLSearchParams(globalThis.location.search);
  if (params.get('demo') === 'true') {
    localStorage.setItem('demoMode', 'true');
    return true;
  }

  /// If no ?demo=true in URL, clear localStorage and disable
  localStorage.removeItem('demoMode');
  return false;
}

/**
 * Hook to enable demo mode
 * Call this in root component (App.tsx) or specific pages
 */
export function useDemoMode(enabled: boolean = true) {
  const {
    addTranscriptChunk,
    updateSentiment,
    updateCategory,
    addSolutionCards,
    addNote,
    startCall,
  } = useDashboardStore();

  useEffect(() => {
    if (!enabled || !isDemoModeEnabled()) return;

    console.log('[Demo Mode] Enabled - Initializing demo data...');

    // Start call immediately
    startCall();

    // Add initial data
    addNote('Demo mode: Simulating live call with mock data');
    addTranscriptChunk(
      generateTranscriptChunk({
        speaker: 'customer',
        text: 'Hi, I need help with my machine.',
      })
    );

    // Simulate live updates every 2-5 seconds
    const liveUpdateInterval = setInterval(async () => {
      const random = Math.random();

      if (random < 0.5) {
        // Add transcript chunk
        addTranscriptChunk(generateTranscriptChunk());
      } else if (random < 0.7) {
        // Update sentiment
        updateSentiment(generateSentimentUpdate());
      } else if (random < 0.85) {
        // Update category
        updateCategory(generateCategoryUpdate());
      } else {
        // Add solutions + note
        addSolutionCards(generateSolutionCards(2));
        addNote(generateNote().text);
      }
    }, 1500); // Every 1.5 seconds

    console.log('[Demo Mode] Live updates started');

    return () => {
      clearInterval(liveUpdateInterval);
      console.log('[Demo Mode] Disabled');
    };
  }, [enabled, addTranscriptChunk, updateSentiment, updateCategory, addSolutionCards, addNote, startCall]);
}

/**
 * Toggle demo mode in localStorage
 * Requires page reload to take effect
 */
export function toggleDemoMode() {
  const current = localStorage.getItem('demoMode') === 'true';
  localStorage.setItem('demoMode', current ? 'false' : 'true');
  console.log(`[Demo Mode] ${current ? 'Disabled' : 'Enabled'} - Reload page to apply`);
  globalThis.location.reload();
}

/**
 * API for programmatic demo control
 */
export const DemoMode = {
  enable: () => {
    localStorage.setItem('demoMode', 'true');
    console.log('[Demo Mode] Enabled - Reload page to start');
  },

  disable: () => {
    localStorage.setItem('demoMode', 'false');
    console.log('[Demo Mode] Disabled - Reload page');
  },

  isEnabled: () => isDemoModeEnabled(),

  // Manually trigger a demo update (useful for testing specific scenarios)
  simulateTranscript: (text: string) => {
    const store = useDashboardStore.getState();
    store.addTranscriptChunk(
      generateTranscriptChunk({ text, speaker: 'customer', isFinal: true })
    );
  },

  simulateSentiment: () => {
    const store = useDashboardStore.getState();
    store.updateSentiment(generateSentimentUpdate());
  },

  simulateSolutions: () => {
    const store = useDashboardStore.getState();
    store.addSolutionCards(generateSolutionCards(3));
  },
};

// Export hook with demo check as default
export default function useDemoModeHook() {
  useDemoMode(true);
}