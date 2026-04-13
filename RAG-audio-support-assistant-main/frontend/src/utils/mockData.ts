/**
 * Mock data generators for POC testing and development
 * All data is realistic but fictional
 * Use to test UI without backend connection
 */

import type {
  TranscriptChunk,
  SentimentUpdate,
  CategoryUpdate,
  SolutionCard,
  Note,
  AgentProfile,
  CallLog,
} from '../types';

// ============================================
// MOCK TRANSCRIPT DATA
// ============================================

/**
 * Generate a mock transcript chunk
 * Useful for simulating live transcription
 */
export function generateTranscriptChunk(overrides?: Partial<TranscriptChunk>): TranscriptChunk {
  const mockTexts = [
    'The spindle is overheating again.',
    'I need to calibrate the Z-axis.',
    'Is there a way to reset the error code?',
    'The vacuum pump is making a strange noise.',
    'Can you help me troubleshoot this issue?',
    'I checked the cooling system already.',
    'What do you recommend?',
    'Understood, let me try that now.',
    'That seems to be working better.',
    'Thank you for your help.',
  ];

  const randomText = mockTexts[Math.floor(Math.random() * mockTexts.length)];
  const speaker = Math.random() > 0.5 ? 'agent' : 'customer';

  return {
    id: `chunk-${Date.now()}-${Math.random()}`,
    timestamp: Date.now(),
    text: randomText,
    speaker,
    isFinal: Math.random() > 0.3, // 70% final, 30% interim
    ...overrides,
  };
}

/**
 * Generate array of transcript chunks (simulating a conversation)
 */
export function generateTranscriptConversation(count: number = 10): TranscriptChunk[] {
  const chunks: TranscriptChunk[] = [];

  for (let i = 0; i < count; i++) {
    chunks.push(
      generateTranscriptChunk({
        id: `chunk-${i}`,
        timestamp: Date.now() - (count - i) * 2000, // Stagger timestamps
      })
    );
  }

  return chunks;
}

// ============================================
// MOCK SENTIMENT DATA
// ============================================

/**
 * Generate a mock sentiment update
 */
export function generateSentimentUpdate(overrides?: Partial<SentimentUpdate>): SentimentUpdate {
  const sentiments = ['Positive', 'Neutral', 'Negative', 'Agitated'] as const;
  const randomSentiment = sentiments[Math.floor(Math.random() * sentiments.length)];

  return {
    sentiment: randomSentiment,
    confidence: Math.random() * 0.5 + 0.5, // 0.5 - 1.0
    timestamp: Date.now(),
    ...overrides,
  };
}

/**
 * Generate sentiment sequence (for testing changing emotions)
 */
export function generateSentimentSequence(): SentimentUpdate[] {
  return [
    { sentiment: 'Neutral', confidence: 0.85, timestamp: Date.now() - 30000 },
    { sentiment: 'Negative', confidence: 0.72, timestamp: Date.now() - 20000 },
    { sentiment: 'Agitated', confidence: 0.95, timestamp: Date.now() },
  ];
}

// ============================================
// MOCK CATEGORY DATA
// ============================================

/**
 * Generate a mock category update
 */
export function generateCategoryUpdate(overrides?: Partial<CategoryUpdate>): CategoryUpdate {
  const categories = [
    'Machine Operation',
    'Maintenance & Parts',
    'Technical Troubleshooting',
    'Uncategorized',
  ] as const;
  const randomCategory = categories[Math.floor(Math.random() * categories.length)];

  return {
    category: randomCategory,
    confidence: Math.random() * 0.5 + 0.5, // 0.5 - 1.0
    timestamp: Date.now(),
    ...overrides,
  };
}

// ============================================
// MOCK SOLUTION CARDS
// ============================================

/**
 * Generate a single mock solution card
 */
export function generateSolutionCard(overrides?: Partial<SolutionCard>): SolutionCard {
  const solutions = [
    {
      title: 'Check Spindle Cooling System',
      steps: [
        'Verify coolant level in reservoir',
        'Check if cooling fan is operational',
        'Run diagnostic report to identify blockages',
        'Replace coolant if contaminated',
      ],
      category: 'Machine Operation' as const,
    },
    {
      title: 'Calibrate Z-Axis',
      steps: [
        'Home the machine to factory position',
        'Use calibration tool to adjust Z-offset',
        'Run test cut on scrap material',
        'Fine-tune if needed and save settings',
      ],
      category: 'Machine Operation' as const,
    },
    {
      title: 'Replace Vacuum Pump Filter',
      steps: [
        'Turn off machine and release pressure',
        'Locate filter cartridge on pump',
        'Unscrew old filter and inspect seal',
        'Install new filter with proper orientation',
        'Test suction before resuming operations',
      ],
      category: 'Maintenance & Parts' as const,
    },
    {
      title: 'Troubleshoot Error Code E405',
      steps: [
        'Check inverter connections for loose wires',
        'Measure voltage at inverter input',
        'Review system logs for error patterns',
        'Contact support if issue persists',
      ],
      category: 'Technical Troubleshooting' as const,
    },
  ];

  const solution = solutions[Math.floor(Math.random() * solutions.length)];

  return {
    id: `solution-${Date.now()}-${Math.random()}`,
    title: solution.title,
    category: solution.category,
    confidence: Math.random() * 0.3 + 0.7, // 0.7 - 1.0
    steps: solution.steps,
    source: {
      manual: 'Rover 30 Technical Manual',
      section: `${Math.floor(Math.random() * 10)}.${Math.floor(Math.random() * 10)} Maintenance`,
      page: Math.floor(Math.random() * 500) + 1,
    },
    timestamp: Date.now(),
    ...overrides,
  };
}

/**
 * Generate array of solution cards
 */
export function generateSolutionCards(count: number = 3): SolutionCard[] {
  return Array.from({ length: count }, () => generateSolutionCard());
}

// ============================================
// MOCK NOTES
// ============================================

/**
 * Generate a mock note
 */
export function generateNote(overrides?: Partial<Note>): Note {
  const noteTexts = [
    'Customer unable to start spindle - investigating cooling system',
    'Z-axis calibration drifted - need recalibration',
    'Vacuum pump making noise - likely filter issue',
    'Error E405 on inverter - requested maintenance check',
    'Remember to follow up after customer applies fix',
  ];

  const randomText = noteTexts[Math.floor(Math.random() * noteTexts.length)];

  return {
    id: `note-${Date.now()}-${Math.random()}`,
    timestamp: Date.now() - Math.random() * 300000,
    text: randomText,
    isPinned: Math.random() > 0.7, // 30% pinned
    ...overrides,
  };
}

/**
 * Generate array of notes
 */
export function generateNotes(count: number = 5): Note[] {
  return Array.from({ length: count }, () => generateNote());
}

// ============================================
// MOCK PROFILES & LOGS
// ============================================

/**
 * Generate mock agent profile
 */
export function generateAgentProfile(overrides?: Partial<AgentProfile>): AgentProfile {
  const agents = [
    {
      name: 'Sarah Johnson',
      email: 'sarah.johnson@support.ai',
      profilePicture: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Sarah',
      department: 'Technical Support',
      phone: '+1-555-0123',
    },
    {
      name: 'Mike Chen',
      email: 'mike.chen@support.ai',
      profilePicture: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Mike',
      department: 'Field Service',
      phone: '+1-555-0124',
    },
    {
      name: 'Emma Rodriguez',
      email: 'emma.rodriguez@support.ai',
      profilePicture: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Emma',
      department: 'Quality Assurance',
      phone: '+1-555-0125',
    },
  ];

  const agent = agents[Math.floor(Math.random() * agents.length)];

  return {
    id: `agent-${Date.now()}`,
    ...agent,
    ...overrides,
  };
}

/**
 * Generate mock call log
 */
export function generateCallLog(overrides?: Partial<CallLog>): CallLog {
  const categories = [
    'Machine Operation',
    'Maintenance & Parts',
    'Technical Troubleshooting',
  ] as const;
  const randomCategory = categories[Math.floor(Math.random() * categories.length)];

  const customers = [
    'Acme Corp',
    'Global Manufacturing',
    'TechWorks Inc',
    'Precision Industries',
  ];
  const randomCustomer = customers[Math.floor(Math.random() * customers.length)];

  return {
    id: `call-${Date.now()}-${Math.random()}`,
    callDate: Date.now() - Math.random() * 86400000, // Random time in last 24 hours
    duration: Math.floor(Math.random() * 2400) + 300, // 5-40 minutes
    customerName: randomCustomer,
    category: randomCategory,
    resolution: 'Issue resolved - customer satisfied',
    ...overrides,
  };
}

/**
 * Generate array of call logs
 */
export function generateCallLogs(count: number = 5): CallLog[] {
  return Array.from({ length: count }, () => generateCallLog());
}

// ============================================
// COMBINED SCENARIOS
// ============================================

/**
 * Generate complete "live call" scenario with all data
 * Useful for end-to-end testing
 */
export function generateCallScenario() {
  return {
    agent: generateAgentProfile(),
    callLogs: generateCallLogs(5),
    activeCall: {
      transcript: generateTranscriptConversation(8),
      sentiment: generateSentimentUpdate(),
      category: generateCategoryUpdate(),
      solutions: generateSolutionCards(3),
      notes: generateNotes(4),
    },
  };
}

// ============================================
// UTILITIES
// ============================================

/**
 * Simulate realistic time delays (for animations, latency)
 */
export function delayMs(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Generate random delay in range (e.g., simulate backend latency)
 */
export function randomDelay(minMs: number = 100, maxMs: number = 800): Promise<void> {
  const delay = Math.random() * (maxMs - minMs) + minMs;
  return delayMs(delay);
}