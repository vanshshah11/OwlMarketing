import { Platform, Dimensions, PixelRatio } from 'react-native';
import ReactNativeHapticFeedback from 'react-native-haptic-feedback';

const options = {
  enableVibrateFallback: true,
  ignoreAndroidSystemSettings: false
};

// Get screen dimensions and aspect ratio
const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');
const ASPECT_RATIO = SCREEN_HEIGHT / SCREEN_WIDTH;

// Responsive scaling functions
const calcWidth = (percentage) => SCREEN_WIDTH * (percentage / 100);
const calcHeight = (percentage) => SCREEN_HEIGHT * (percentage / 100);

// Font scaling based on screen width with maximum limits
const normalizeFont = (size) => {
  const baseSize = size / PixelRatio.getFontScale();
  const scaleFactor = Math.min(SCREEN_WIDTH / 375, SCREEN_HEIGHT / 812);
  return Math.round(baseSize * scaleFactor);
};

// Create scalable spacing units
const createSpacing = (baseSize) => {
  const scaleFactor = Math.min(SCREEN_WIDTH / 375, 1.3); // Limit maximum scaling
  return Math.round(baseSize * scaleFactor);
};

const fontFamily = Platform.select({
  ios: '-apple-system',
  android: 'Roboto',
  default: 'System',
});

// Typography with normalized font sizes
export const typography = {
  bigTitle: {
    fontFamily,
    fontSize: normalizeFont(50),
    fontWeight: '600',
    lineHeight: normalizeFont(60),
  },
  largeTitle: {
    fontFamily,
    fontSize: normalizeFont(40),
    fontWeight: '600',
    lineHeight: normalizeFont(48),
  },
  title1: {
    fontFamily,
    fontSize: normalizeFont(32),
    fontWeight: '600',
    lineHeight: normalizeFont(38),
  },
  title1_1: {
    fontFamily,
    fontSize: normalizeFont(26),
    fontWeight: '500',
    lineHeight: normalizeFont(32),
  },
  title2: {
    fontFamily,
    fontSize: normalizeFont(24),
    fontWeight: '500',
    lineHeight: normalizeFont(30),
  },
  title3: {
    fontFamily,
    fontSize: normalizeFont(20),
    fontWeight: '600',
    lineHeight: normalizeFont(26),
  },
  headline: {
    fontFamily,
    fontSize: normalizeFont(18),
    fontWeight: '600',
    lineHeight: normalizeFont(24),
  },
  body: {
    fontFamily,
    fontSize: normalizeFont(20),
    fontWeight: '400',
    lineHeight: normalizeFont(26),
  },
  callout: {
    fontFamily,
    fontSize: normalizeFont(16),
    fontWeight: '400',
    lineHeight: normalizeFont(22),
  },
  subhead: {
    fontFamily,
    fontSize: normalizeFont(14),
    fontWeight: '400',
    lineHeight: normalizeFont(20),
  },
  footnote: {
    fontFamily,
    fontSize: normalizeFont(12),
    fontWeight: '400',
    lineHeight: normalizeFont(18),
  },
  caption: {
    fontFamily,
    fontSize: normalizeFont(12),
    fontWeight: '400',
    lineHeight: normalizeFont(18),
  },
  button: {
    fontFamily,
    fontSize: normalizeFont(20),
    fontWeight: '600',
    lineHeight: normalizeFont(26),
  },
  button2: {
    fontFamily,
    fontSize: normalizeFont(16),
    fontWeight: '600',
    lineHeight: normalizeFont(22),
  },
  apptitle: {
    fontFamily,
    fontSize: normalizeFont(30),
    fontWeight: '500',
    lineHeight: normalizeFont(38),
  },
};

// Enhanced colors with camera-specific additions
export const colors = {
  primary: {
    light: '#CECECE',
    dark: '#000000',
  },
  background: {
    // primary: {
    //   light: '#F5F5F5',//basically white
    //   dark: '#1C1C1E',//basically black
    // },
    //i am changing this because background humare simulators mai bht white ho rhe h
    //if F5F5F5 he karan kuch bada change aaye, toh go back too it.
    primary: {
      light: '#EBE9E8',//basically white
      dark: '#1C1C1E',//basically black
    },
    secondary: {
      light: '#FFFFFF',
      dark: '#2C2C2E',
    },
    tertiary: {
      light: '#E5E5EA',//greyish
      dark: '#3A3A3C', //darkgrey
    },
    quaternary: {
      light: '#E0E0E0',
      dark: '#3A3A3C',
    },
    camera: {
      overlay: 'rgba(0, 0, 0, 0.5)',
      controls: 'rgba(255, 255, 255, 0.3)',
      captureButton: 'rgba(255, 255, 255, 0.5)',
      frameGuide: 'rgba(255, 255, 255, 0.3)',
    },
    stuffimadeup:'#F8F7F8',// E6e6e6
    frostedGlass: 'rgba(255, 255, 255, 0.7)',
  },
  text: {
    primary: {
      light: '#000000',
      dark: '#FFFFFF',
    },
    secondary: {
      light: '#666666',
      dark: '#EBEBF5',
    },
  },
  macro: {
    protein: '#FF3B30',
    carbs: '#FF9500',
    fat: '#5AC8FA',
  },
  card: {
    background: {
      light: '#FFFFFF',
      dark: '#2C2C2E',
    },
    shadow: '#000000',
  },
  success: {
    light: '#34C759',
    dark: '#30D158',
  },
  error: {
    light: '#FF3B30',
    dark: '#FF453A',
  },
  warning: {
    light: '#FF9500',
    dark: '#FF9F0A',
  },
  border: {
    primary: {
      light: '#E5E5EA',
      dark: '#3A3A3C',
    }
  },
};

// Enhanced spacing with additional values
export const spacing = {
  xxxxs: createSpacing(-10),
  xxxs: createSpacing(2),
  xxs: createSpacing(4),
  xs: createSpacing(8),
  s: createSpacing(12),
  m: createSpacing(16),
  l: createSpacing(20),
  xl: createSpacing(24),
  xxl: createSpacing(32),
  xxxl: createSpacing(40),
  huge: createSpacing(48),
  giant: createSpacing(56),
};

// Enhanced layout with camera-specific additions
export const layout = {
  borderRadius: {
    tiny: createSpacing(2),
    small: createSpacing(4),
    medium: createSpacing(8),
    large: createSpacing(12),
    xl: createSpacing(16),
    xxl: createSpacing(24),
    circular: 999,
  },
  buttonHeight: createSpacing(56),
  foodimage: createSpacing(72),
  iconSize: {
    tiny: createSpacing(16),
    small: createSpacing(20),
    medium: createSpacing(24),
    large: createSpacing(28),
    xl: createSpacing(32),
  },
  sliderContentWidth: calcWidth(150),
  maxContentWidth: calcWidth(90),
  minContentWidth: calcWidth(85),
  containerPadding: createSpacing(16),
  cardSpacing: createSpacing(12),
  camera: {
    frameGuideThickness: 2.5,
    frameCornerLength: createSpacing(40),
    captureButtonSize: createSpacing(72),
    holdwidthButtonSize:createSpacing(90),
    holdheightButtonSize: createSpacing(100),
    // controlButtonSize: createSpacing(50),
    controlButtonSize: createSpacing(40),
    modalMaxHeight: calcHeight(70),
  },
  progressBar: {
    tiny: createSpacing(2),    
    small: createSpacing(4),   
    medium: createSpacing(6),
    large: createSpacing(8)
  },
  recentlyeatenimage: createSpacing(65),
};

// Enhanced shadows
export const shadows = {
  tiny: {
    // shadowColor: colors.card.shadow,
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 1,
  },
  small: {
    // shadowColor: colors.card.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 3,
    elevation: 2,
  },
  medium: {
    // shadowColor: colors.card.shadow,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 6,
    elevation: 4,
  },
  large: {
    // shadowColor: colors.card.shadow,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 8,
  },
  float: {
    // shadowColor: colors.card.shadow,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.25,
    shadowRadius: 12,
    elevation: 12,
  },
};

export const zIndex = {
  base: 1,
  card: 10,
  header: 20,
  modal: 30,
  overlay: 40,
  popover: 50,
  toast: 60,
  camera: {
    overlay: 5,
    controls: 10,
    guide: 15,
  },
};

export const haptics = {
  light: () => ReactNativeHapticFeedback.trigger('impactLight', options),
  medium: () => ReactNativeHapticFeedback.trigger('impactMedium', options),
  heavy: () => ReactNativeHapticFeedback.trigger('impactHeavy', options),
  success: () => ReactNativeHapticFeedback.trigger('notificationSuccess', options),
  warning: () => ReactNativeHapticFeedback.trigger('notificationWarning', options),
  error: () => ReactNativeHapticFeedback.trigger('notificationError', options),
}; 

// Animation durations
export const animationDurations = {
  shortest: 150,
  shorter: 200,
  short: 250,
  medium: 300,
  long: 400,
  longer: 500,
  longest: 750,
};

// Enhanced mixins with additional patterns
export const mixins = {
  padding: {
    all: (size = spacing.m) => ({
      padding: size,
    }),
    horizontal: (size = spacing.m) => ({
      paddingHorizontal: size,
    }),
    vertical: (size = spacing.m) => ({
      paddingVertical: size,
    }),
    top: (size = spacing.m) => ({
      paddingTop: size,
    }),
    bottom: (size = spacing.m) => ({
      paddingBottom: size,
    }),
  },
  margin: {
    all: (size = spacing.m) => ({
      margin: size,
    }),
    horizontal: (size = spacing.m) => ({
      marginHorizontal: size,
    }),
    vertical: (size = spacing.m) => ({
      marginVertical: size,
    }),
    top: (size = spacing.m) => ({
      marginTop: size,
    }),
    bottom: (size = spacing.m) => ({
      marginBottom: size,
    }),
  },
  absoluteFill: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
  },
  center: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  camera: {
    frame: {
      borderWidth: layout.camera.frameGuideThickness,
      borderColor: colors.text.primary.dark,
    },
    control: {
      backgroundColor: colors.background.camera.controls,
      ...Platform.select({
        ios: shadows.small,
        android: {
          elevation: 3,
        },
      }),
    },
  },
};

// Helper functions
export const getProgressColor = (progress) => {
  if (progress < 0.3) return colors.macro.protein;
  if (progress < 0.7) return colors.macro.carbs;
  return colors.macro.fat;
};

// Screen breakpoints for responsive design
export const breakpoints = {
  phone: 0,
  tablet: 768,
  desktop: 1024,
};

// Device type detection
export const getDeviceType = () => {
  if (SCREEN_WIDTH >= breakpoints.desktop) return 'desktop';
  if (SCREEN_WIDTH >= breakpoints.tablet) return 'tablet';
  return 'phone';
};

// Responsive sizing helper
export const responsive = {
  width: (percentage) => calcWidth(percentage),
  height: (percentage) => calcHeight(percentage),
  fontSize: (size) => normalizeFont(size),
};

const theme = {
  typography,
  colors,
  spacing,
  layout,
  shadows,
  zIndex,
  animationDurations,
  getProgressColor,
  mixins,
  breakpoints,
  getDeviceType,
  responsive,
};

export default theme;