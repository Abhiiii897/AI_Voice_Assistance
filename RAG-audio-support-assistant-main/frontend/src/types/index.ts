//defines the types of messages that my websocket can receive from the backend
export type WsMessageType =
  | "transcript_chunk"
  | "sentiment_update"
  | "category_update"
  | "solution_cards"
  | "call_started"
  | "call_ended";

//define the message contents and structure

//Transcript types
/**
 * A single message or chunk from the live conversation
 * Example: { speaker: "customer", text: "The spindle won't start", isFinal: true }
 */
export interface TranscriptChunk { //TODO: decide if the transcript will be sent in chunks or as a file (once the backend is done)
  id: string;
  timestamp: number;
  text: string;
  speaker: "agent" | "customer"; //Note: assumes that this will be speaker tags from deepgram, else it'll break TranscriptPanel
  isFinal: boolean;
}

//sentiment types
/**
 * Emotional state of the customer
 * updated by backend sentiment anlyzer aft speech breaks
 */
export interface SentimentUpdate {
  sentiment: "Positive" | "Neutral" | "Negative" | "Agitated";
  confidence: number;
  timestamp: number;
}
//category types
export type IssueCategoryType =
  | "Machine Operation"
  | "Maintenance & Parts"
  | "Technical Troubleshooting"
  | "Uncategorized";  // Explicitly handle the "we don't know yet" state;

  //determines which manual sections to search
export interface CategoryUpdate {
  category: IssueCategoryType;
  confidence: number;
  timestamp: number;
}

//solution card types
/**
 * A recommended solution retrieved from the vector DB
 * e.g.: { title: "Spindle Maintenance", steps: [...], source: {...} }
 */
export interface SolutionCard {
  id: string;
  title: string;    //solution title
  category: IssueCategoryType;    
  confidence: number;   //relevance score from vector db o/p (0.0 - 1.0)
  steps: string[];    //must analyze the chunks received to generate specific solution, also must have a summary of what the problem is
  source: {
    manual: string;     // e.g: "Rover 30 manual" - after matching chunks to actual manual pdfs
    section: string;    // e.g: "5.2 maintainence"
    page: number;     //42
  };
  timestamp: number;
}

//support agent profile (POC can be just gibberish)
export interface AgentProfile {
  id: string;
  name: string;
  email: string;
  profilePicture: string;
  department: string;
  phone: string;
}

//type for call logs - can be just jibberish for POC
export interface CallLog {
  id: string;
  callDate: number;
  duration: number;
  customerName: string;
  category: IssueCategoryType;
  resolution: string;
}

export interface Note {
  id: string;
  timestamp: number;
  text: string;
  isPinned: boolean;  //pinned notes to be displayed first/ float to the top
}

//all the things needed to render dashboard during call
//complete state management by zustand store
export interface DashboardState {
  //call metadata
  activeCallId: string | null;
  callStartTime: number | null;
  callDuration: number;

  //audio state
  isRecording: boolean;
  micPermissionGranted: boolean;

  //transcript
  transcript: TranscriptChunk[];

  //intelligence state
  currentSentiment: SentimentUpdate | null;
  currentCategory: CategoryUpdate | null;
  solutionCards: SolutionCard[];

  //notes
  notes: Note[];

  //connection states
  isConnected: boolean; //can be the same as is recording for POC
  wsLatency: number;   //can be gibberish of can give input audio to o/p response displayed latency
}

//websocket message:payload types 
//define message format

/**
 * Typed payloads for WebSocket messages
 * Backend sends JSON, these interfaces ensure type safety
 */
export interface WsMessage<T> {
  type: WsMessageType;
  payload: T;
}
