//Zustand store hook - defines a single state of truth for my dashboard UI and the actions that mutate it
import { create } from "zustand";
import { devtools } from 'zustand/middleware';

import type {
  CategoryUpdate,
  DashboardState,
  Note,
  SentimentUpdate,
  SolutionCard,
  TranscriptChunk, //TODO: chunk or file problem to be addresses
} from "../types";

//function type declaration - that describes the shape of the store (so any DashboardStore obj must implement these fns with these defined params)
//extends store interface to have state+actions
interface DashboardStore extends DashboardState {
  //transcript actions
  addTranscriptChunk: (chunk: TranscriptChunk) => void;
  clearTranscript: () => void;

  //intelligence actions
  updateSentiment: (sentiment: SentimentUpdate) => void;
  updateCategory: (category: CategoryUpdate) => void;
  addSolutionCards: (cards: SolutionCard[]) => void;
  trimSolutionCards: (maxCards: number) => void;
  clearSolutions: () => void;
  //TODO: add a method to figure out solution card source

  //notes actions
  addNote: (text: string) => void;
  deleteNote: (id: string) => void;
  togglePinned: (id: string) => void;

  //call control actions (in [POC] mic recording actions)
  startCall: () => void; //same as start recording
  stopRecording: () => void;
  setCallDuration: (seconds: number) => void; //same as set current record duration in [POC]

  //connection actions - simulation
  setConnected: (connected: boolean) => void;
  setMicPermission: (granted: boolean) => void;
}

//make/create zustand store

/**
 * Global state management for the entire dashboard
 * 
 * Usage in components:
 * const { notes, addNote } = useDashboardStore();
 * const notes = useDashboardStore((state) => state.notes);
 */
const useDashboardStore = create<DashboardStore>()(
  devtools(
    (set) => ({
  //init state
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

  //transript actions
  // Add a new transcript chunk to the array
  addTranscriptChunk: (chunk) => //TODO: same chunk or file problem to be addresd
    set((state) => ({
    //   transcript: [...state.transcript, chunk].slice(-100),
      transcript: [...state.transcript, chunk], //removed the slice so that the UI can have the full transcript that is scrollable
    })), // remember to implement list virtualization later (e.g., react-virtual)  If performance becomes an issue

  clearTranscript: () => 
    set({ transcript: [] }), //just in case

 //intelligence
  updateSentiment: (sentiment) => 
    set({ currentSentiment: sentiment }),

  updateCategory: (category) => 
    set({ currentCategory: category }),

  addSolutionCards: (cards) =>
    set((state) => ({
      solutionCards: [...cards, ...state.solutionCards].slice(0, 15), //slicing just in case an absurd amout of solution cards come in 
    })),

  trimSolutionCards: (maxCards) =>
    set((state) => ({
      // New cards are prepended in `addSolutionCards`, so index 0 is "top/newest".
      // Keeping slice(0, maxCards) preserves the newest `maxCards` and drops older ones.
      solutionCards: state.solutionCards.slice(0, Math.max(0, maxCards)),
    })),

  clearSolutions: () => 
    set({ solutionCards: [] }),

  //notes actions

  addNote: (text) =>
  set((state) => {
    const new_note: Note = { // Note used explicitly by typing the new note object 
      id: `note-${Date.now()}`,
      timestamp: Date.now(),
      text,
      isPinned: false,
    };

    return {
      notes: [new_note, ...state.notes], 
    };
  }),

  //delete note by id
  deleteNote: (id) =>
    set((state) => ({
      notes: state.notes.filter((note) => note.id !== id),
    })),

  // pinning logic
  togglePinned: (id) =>
    set((state) => ({
      notes: state.notes.map((note) =>
        note.id === id ? { ...note, isPinned: !note.isPinned } : note
      ),
    })),

  // call control actions
  startCall: () => // [POC] Simulates call start by capturing local mic
    set({
      activeCallId: `call-${Date.now()}`, // [POC] sample call id using date
      callStartTime: Date.now(),
      isRecording: true,
      callDuration: 0,
      transcript: [],   //clear old transcripts upon new call
      notes: [],    //clear notes
      solutionCards: [],    //clear solu
    }),

  stopRecording: () => // [POC] Stops mic capture
    set({
      isRecording: false,
      activeCallId: null,
    }),

  setCallDuration: (seconds) =>  //call every 1 sec
    set({ callDuration: seconds }),

  //connection actions
  setConnected: (connected) => 
    set({ isConnected: connected }),

  //mic permission (on the browser)
  setMicPermission: (granted) => 
    set({ micPermissionGranted: granted }),
}),
  { name: 'DashboardStore' } // DevTools debugging name
  )
);

export default useDashboardStore;
