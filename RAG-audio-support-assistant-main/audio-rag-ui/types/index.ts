// Defines the types of messages that the websocket can receive from the backend
export type WsMessageType =
  | "transcript_chunk"
  | "sentiment_update"
  | "category_update"
  | "solution_cards"
  | "call_started"
  | "call_ended";

// Transcript types
export interface TranscriptChunk {
  id: string;
  timestamp: number;
  text: string;
  speaker: "agent" | "customer";
  isFinal: boolean;
}

// Sentiment types
export interface SentimentUpdate {
  sentiment: "Positive" | "Neutral" | "Negative" | "Agitated";
  confidence: number;
  timestamp: number;
}

// Category types
export type IssueCategoryType =
  | "Machine Operation"
  | "Maintenance & Parts"
  | "Technical Troubleshooting"
  | "Uncategorized";

export interface CategoryUpdate {
  category: IssueCategoryType;
  confidence: number;
  timestamp: number;
}

// Solution card types
export interface SolutionCard {
  id: string;
  title: string;
  category: IssueCategoryType;
  confidence: number;
  steps: string[];
  source: {
    manual: string;
    section: string;
    page: number;
  };
  timestamp: number;
}

// Support agent profile
export interface AgentProfile {
  id: string;
  name: string;
  email: string;
  profilePicture: string;
  department: string;
  phone: string;
}

// Call logs
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
  isPinned: boolean;
}

// Dashboard state
export interface DashboardState {
  activeCallId: string | null;
  callStartTime: number | null;
  callDuration: number;
  isRecording: boolean;
  micPermissionGranted: boolean;
  transcript: TranscriptChunk[];
  currentSentiment: SentimentUpdate | null;
  currentCategory: CategoryUpdate | null;
  solutionCards: SolutionCard[];
  notes: Note[];
  isConnected: boolean;
  wsLatency: number;
}

export interface WsMessage<T> {
  type: WsMessageType;
  payload: T;
}
