import { create } from "zustand";
import { devtools } from 'zustand/middleware';

import type {
    CategoryUpdate,
    DashboardState,
    Note,
    SentimentUpdate,
    SolutionCard,
    TranscriptChunk,
} from "../types";

interface DashboardStore extends DashboardState {
    // Transcript actions
    addTranscriptChunk: (chunk: TranscriptChunk) => void;
    clearTranscript: () => void;

    // Intelligence actions
    updateSentiment: (sentiment: SentimentUpdate) => void;
    updateCategory: (category: CategoryUpdate) => void;
    addSolutionCards: (cards: SolutionCard[]) => void;
    trimSolutionCards: (maxCards: number) => void;
    clearSolutions: () => void;

    // Notes actions
    addNote: (text: string) => void;
    deleteNote: (id: string) => void;
    togglePinned: (id: string) => void;

    // Call control actions
    startCall: () => void;
    stopRecording: () => void;
    toggleRecording: () => void;
    setCallDuration: (seconds: number) => void;

    // Connection actions
    setConnected: (connected: boolean) => void;
    setMicPermission: (granted: boolean) => void;
}

const useDashboardStore = create<DashboardStore>()(
    devtools(
        (set) => ({
            // Initial state
            activeCallId: null,
            callStartTime: null,
            callDuration: 0,
            isRecording: false,
            micPermissionGranted: false,
            transcript: [],
            currentSentiment: null,
            currentCategory: null,
            solutionCards: [],
            notes: [],
            isConnected: false,
            wsLatency: 0,

            // Transcript actions
            addTranscriptChunk: (chunk) =>
                set((state) => ({
                    transcript: [...state.transcript, chunk],
                })),

            clearTranscript: () =>
                set({ transcript: [] }),

            // Intelligence actions
            updateSentiment: (sentiment) =>
                set({ currentSentiment: sentiment }),

            updateCategory: (category) =>
                set({ currentCategory: category }),

            addSolutionCards: (cards) =>
                set((state) => ({
                    solutionCards: [...cards, ...state.solutionCards].slice(0, 15),
                })),

            trimSolutionCards: (maxCards) =>
                set((state) => ({
                    solutionCards: state.solutionCards.slice(0, Math.max(0, maxCards)),
                })),

            clearSolutions: () =>
                set({ solutionCards: [] }),

            // Notes actions
            addNote: (text) =>
                set((state) => {
                    const new_note: Note = {
                        id: `note-${Date.now()}`,
                        timestamp: Date.now(),
                        text,
                        isPinned: false,
                    };

                    return {
                        notes: [new_note, ...state.notes],
                    };
                }),

            deleteNote: (id) =>
                set((state) => ({
                    notes: state.notes.filter((note) => note.id !== id),
                })),

            togglePinned: (id) =>
                set((state) => ({
                    notes: state.notes.map((note) =>
                        note.id === id ? { ...note, isPinned: !note.isPinned } : note
                    ),
                })),

            // Call control actions
            startCall: () =>
                set({
                    activeCallId: `call-${Date.now()}`,
                    callStartTime: Date.now(),
                    isRecording: true,
                    callDuration: 0,
                    transcript: [],
                    notes: [],
                    solutionCards: [],
                }),

            stopRecording: () =>
                set({
                    isRecording: false,
                }),

            toggleRecording: () =>
                set((state) => ({ isRecording: !state.isRecording })),

            setCallDuration: (seconds) =>
                set({ callDuration: seconds }),

            // Connection actions
            setConnected: (connected) =>
                set({ isConnected: connected }),

            setMicPermission: (granted) =>
                set({ micPermissionGranted: granted }),
        }),
        { name: 'DashboardStore' }
    )
);

export default useDashboardStore;
