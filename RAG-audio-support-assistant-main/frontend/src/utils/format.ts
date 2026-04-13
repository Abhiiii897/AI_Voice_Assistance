/**
 * Formatting utilities for consistent data display across UI
 * All functions are pure (no side effects)
 */

// ============================================
// TIME & DURATION FORMATTING
// ============================================

/**
 * Format seconds as HH:MM:SS or MM:SS
 * Examples:
 *   125 → "2:05"
 *   3661 → "1:01:01"
 */
export function formatDuration(seconds: number): string {
  if (seconds < 0) return '0:00';

  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  }
  return `${minutes}:${String(secs).padStart(2, '0')}`;
}

/**
 * Format timestamp as HH:MM:SS (12-hour or 24-hour)
 * Examples:
 *   1707923400000 → "14:30:45" (24h) or "2:30:45 PM" (12h)
 */
export function formatTime(timestamp: number, use12Hour: boolean = false): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: use12Hour,
  });
}

/**
 * Format timestamp as readable date
 * Examples:
 *   1707923400000 → "Feb 14, 2026"
 */
export function formatDate(timestamp: number): string {
  const date = new Date(timestamp);
  return date.toLocaleDateString([], {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

/**
 * Format timestamp as "X time ago"
 * Examples:
 *   10 seconds ago → "Just now"
 *   120000ms ago → "2m ago"
 *   3600000ms ago → "1h ago"
 *   86400000ms ago → "1d ago"
 */
export function formatTimeAgo(timestamp: number): string {
  const now = Date.now();
  const diffMs = now - timestamp;
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSeconds < 30) return 'Just now';
  if (diffSeconds < 60) return `${diffSeconds}s ago`;
  if (diffMinutes < 60) return `${diffMinutes}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return formatDate(timestamp);
}

// ============================================
// CONFIDENCE & SCORE FORMATTING
// ============================================

/**
 * Format confidence score (0-1) as percentage
 * Examples:
 *   0.95 → "95%"
 *   0.876 → "88%" (rounded)
 */
export function formatConfidence(score: number): string {
  const percentage = Math.round(score * 100);
  return `${percentage}%`;
}

/**
 * Get confidence color for UI display
 * Returns Tailwind color class
 * Examples:
 *   0.9 → "text-green-400" (high confidence)
 *   0.5 → "text-yellow-400" (medium)
 *   0.2 → "text-red-400" (low)
 */
export function getConfidenceColor(score: number): string {
  if (score >= 0.8) return 'text-green-400';
  if (score >= 0.6) return 'text-yellow-400';
  return 'text-red-400';
}

// ============================================
// TEXT FORMATTING
// ============================================

/**
 * Truncate text to max length with ellipsis
 * Examples:
 *   "Hello World", 8 → "Hello..."
 */
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + '...';
}

/**
 * Capitalize first letter of string
 * Examples:
 *   "hello" → "Hello"
 *   "technical troubleshooting" → "Technical troubleshooting"
 */
export function capitalize(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/**
 * Format category name for display
 * Examples:
 *   "Machine Operation" → "Mach Op" (abbreviated)
 *   "Machine Operation" → "Machine Operation" (full)
 */
export function formatCategory(
  category: string,
  abbreviated: boolean = false
): string {
  if (!abbreviated) return category;

  const abbrevs: Record<string, string> = {
    'Machine Operation': 'Mach Op',
    'Maintenance & Parts': 'Maint',
    'Technical Troubleshooting': 'Tech',
    'Uncategorized': 'Unknown',
  };

  return abbrevs[category] || category;
}

// ============================================
// SENTIMENT UTILITIES
// ============================================

/**
 * Get emoji for sentiment
 */
export function getSentimentEmoji(sentiment: string): string {
  const emojis: Record<string, string> = {
    'Positive': '😊',
    'Neutral': '😐',
    'Negative': '😕',
    'Agitated': '😤',
  };
  return emojis[sentiment] || '😐';
}

/**
 * Get Tailwind color class for sentiment
 */
export function getSentimentColor(sentiment: string): string {
  const colors: Record<string, string> = {
    'Positive': '#10B981', // emerald
    'Neutral': '#6B7280', // gray
    'Negative': '#F97316', // orange
    'Agitated': '#EF4444', // red
  };
  return colors[sentiment] || colors['Neutral'];
}

// ============================================
// VALIDATION
// ============================================

/**
 * Check if string is valid note (not just whitespace)
 */
export function isValidNote(text: string): boolean {
  return text.trim().length > 0;
}

/**
 * Check if string is valid search query
 */
export function isValidQuery(query: string): boolean {
  return query.trim().length >= 2;
}