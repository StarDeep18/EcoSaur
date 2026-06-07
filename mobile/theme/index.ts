export const SPACING = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 40,
};

export const TYPOGRAPHY = {
  fontSize: {
    xs: 12,
    sm: 14,
    md: 16,
    lg: 18,
    xl: 20,
    xxl: 28,
    xxxl: 36,
  },
  fontWeight: {
    light: '300' as const,
    regular: '400' as const,
    medium: '500' as const,
    semibold: '600' as const,
    bold: '700' as const,
  },
};

export const THEME = {
  dark: {
    bg: '#09090A',
    card: '#161618',
    border: '#28282B',
    text: '#F2F2F7',
    muted: '#8A8A93',
    primary: '#10B981', // Emerald green
    primaryDark: '#059669',
    primaryLight: '#34D399',
    accentSoft: 'rgba(16, 185, 129, 0.12)',
    error: '#FF453A',
    warning: '#FFD60A',
    success: '#30D158',
    elevation: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.3,
      shadowRadius: 4,
      elevation: 3,
    }
  },
  light: {
    bg: '#FDFBF7', // Cream background
    card: '#F6F3EC', // Layered cream card
    border: '#EBE6DA',
    text: '#1C1C1E', // Slate/black typography
    muted: '#636366',
    primary: '#10B981',
    primaryDark: '#059669',
    primaryLight: '#34D399',
    accentSoft: 'rgba(16, 185, 129, 0.08)',
    error: '#FF3B30',
    warning: '#FFCC00',
    success: '#34C759',
    elevation: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.06,
      shadowRadius: 6,
      elevation: 2,
    }
  }
};
