import { baseColors, typography, spacing } from './theme';

const darkTheme = {
  colors: {
    ...baseColors,
    background: '#121212',
    text: '#FFFFFF',
    // Override other colors for dark theme as needed
  },
  typography,
  spacing,
};

export default darkTheme;