/**
 * Centralized theme & color constants
 * Single source of truth for all colors, spacing, and theme values
 * Update here, reflects everywhere
 */

// ============================================
// COLOR PALETTE - Sentiment
// ============================================

export const SENTIMENT_COLORS = {
  Positive: {
    hex: '#10B981',
    tw: 'emerald',
    bg: 'bg-emerald-500/20',
    text: 'text-emerald-300',
    border: 'border-emerald-500',
  },
  Neutral: {
    hex: '#6B7280',
    tw: 'gray',
    bg: 'bg-gray-500/20',
    text: 'text-gray-300',
    border: 'border-gray-500',
  },
  Negative: {
    hex: '#F97316',
    tw: 'orange',
    bg: 'bg-orange-500/20',
    text: 'text-orange-300',
    border: 'border-orange-500',
  },
  Agitated: {
    hex: '#EF4444',
    tw: 'red',
    bg: 'bg-red-500/20',
    text: 'text-red-300',
    border: 'border-red-500',
  },
} as const;

// ============================================
// COLOR PALETTE - Issue Categories
// ============================================

export const CATEGORY_COLORS = {
  'Machine Operation': {
    hex: '#A855F7',
    tw: 'purple',
    bg: 'bg-purple-500/20',
    text: 'text-purple-300',
    border: 'border-purple-500',
  },
  'Maintenance & Parts': {
    hex: '#FBBF24',
    tw: 'amber',
    bg: 'bg-amber-500/20',
    text: 'text-amber-300',
    border: 'border-amber-500',
  },
  'Technical Troubleshooting': {
    hex: '#FB923C',
    tw: 'orange',
    bg: 'bg-orange-500/20',
    text: 'text-orange-300',
    border: 'border-orange-500',
  },
  'Uncategorized': {
    hex: '#6B7280',
    tw: 'gray',
    bg: 'bg-gray-500/20',
    text: 'text-gray-300',
    border: 'border-gray-500',
  },
} as const;

// ============================================
// COLOR PALETTE - UI Elements
// ============================================

export const UI_COLORS = {
  // Backgrounds
  bg: {
    primary: '#111827', // gray-900
    secondary: '#1F2937', // gray-800
    tertiary: '#374151', // gray-700
  },

  // Borders
  border: {
    light: '#4B5563', // gray-600
    dark: '#1F2937', // gray-800
  },

  // Text
  text: {
    primary: '#F3F4F6', // white
    secondary: '#D1D5DB', // gray-300
    muted: '#9CA3AF', // gray-400
  },

  // Status
  status: {
    success: '#10B981', // emerald
    error: '#EF4444', // red
    warning: '#F97316', // orange
    info: '#3B82F6', // blue
  },

  // Actions
  action: {
    primary: '#3B82F6', // blue
    danger: '#DC2626', // red
    secondary: '#6B7280', // gray
  },
} as const;

// ============================================
// SPACING & SIZING
// ============================================

export const SPACING = {
  xs: '0.25rem', // 4px
  sm: '0.5rem', // 8px
  md: '1rem', // 16px
  lg: '1.5rem', // 24px
  xl: '2rem', // 32px
  '2xl': '2.5rem', // 40px
  '3xl': '3rem', // 48px
} as const;

export const PANEL_SIZES = {
  headerHeight: '52px',
  headerPadding: '12px 16px',
  contentPadding: '16px',
  gapBetweenPanels: '16px',
} as const;

// ============================================
// SHADOWS (Depth)
// ============================================

export const SHADOWS = {
  none: 'none',
  sm: '0 1px 2px rgba(0, 0, 0, 0.05)',
  base: '0 1px 3px rgba(0, 0, 0, 0.1)',
  md: '0 4px 6px rgba(0, 0, 0, 0.1)',
  lg: '0 10px 15px rgba(0, 0, 0, 0.1)',
  xl: '0 20px 25px rgba(0, 0, 0, 0.1)',
  '2xl': '0 25px 50px rgba(0, 0, 0, 0.25)',
} as const;

// ============================================
// BORDER RADIUS
// ============================================

export const RADIUS = {
  none: '0',
  sm: '0.125rem', // 2px
  base: '0.25rem', // 4px
  md: '0.375rem', // 6px
  lg: '0.5rem', // 8px
  xl: '0.75rem', // 12px
  '2xl': '1rem', // 16px
  full: '9999px',
} as const;

// ============================================
// TRANSITIONS & ANIMATIONS
// ============================================

export const TRANSITIONS = {
  fast: '0.15s ease-in-out',
  base: '0.2s ease-in-out',
  slow: '0.3s ease-in-out',
  verySlow: '0.5s ease-in-out',
} as const;

// ============================================
// BREAKPOINTS (Responsive)
// ============================================

export const BREAKPOINTS = {
  mobile: '640px',
  tablet: '1024px',
  desktop: '1280px',
} as const;

// ============================================
// Z-INDEX (Stacking Order)
// ============================================

export const Z_INDEX = {
  base: 0,
  dropdown: 10,
  sticky: 20,
  fixed: 30,
  modalBackdrop: 40,
  modal: 50,
  tooltip: 60,
  notification: 70,
} as const;

// ============================================
// HELPER FUNCTIONS
// ============================================

/**
 * Get sentiment colors object by sentiment name
 * Usage: getSentimentColorsByName('Agitated')
 */
export function getSentimentColorsByName(sentiment: string) {
  return SENTIMENT_COLORS[sentiment as keyof typeof SENTIMENT_COLORS] || SENTIMENT_COLORS.Neutral;
}

/**
 * Get category colors object by category name
 */
export function getCategoryColorsByName(category: string) {
  return CATEGORY_COLORS[category as keyof typeof CATEGORY_COLORS] || CATEGORY_COLORS.Uncategorized;
}

/**
 * Create inline style with theme color
 * Usage: createColorStyle(SENTIMENT_COLORS.Agitated)
 */
export function createColorStyle(color: { hex: string; bg: string; text: string; border: string }) {
  return {
    backgroundColor: `${color.hex}20`, // 20% opacity
    borderLeftColor: color.hex,
  };
}