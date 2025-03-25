// /Users/vanshshah/Desktop/New_app/5th_WellAI/WellAI/src/styles/HomeScreenStyles.js

import { StyleSheet, Dimensions, PixelRatio } from 'react-native';
import theme from '../styles/theme';

// Get screen dimensions and aspect ratio
const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');
const ASPECT_RATIO = SCREEN_HEIGHT / SCREEN_WIDTH;

// Responsive scaling functions based on aspect ratio
const calcWidth = (percentage) => SCREEN_WIDTH * (percentage / 100);
const calcHeight = (percentage) => SCREEN_HEIGHT * (percentage / 100);

// Font scaling based on screen width and aspect ratio
const fontScale = PixelRatio.getFontScale();
const normalizeFont = (size) => {
  const baseSize = size / fontScale;
  const scaleFactor = Math.min(SCREEN_WIDTH / 375, SCREEN_HEIGHT / 812); // Limit maximum scaling
  return Math.round(baseSize * scaleFactor);
};

// Create scalable spacing units based on screen width
const createSpacing = (baseSize) => {
  const scaleFactor = Math.min(SCREEN_WIDTH / 375, 1.3); // Limit maximum scaling
  return Math.round(baseSize * scaleFactor);
};


const styles = StyleSheet.create({
    // container: {
    //   flex: 1,
    //   backgroundColor: '#000000',
    //   alignItems: 'center',
    //   position: 'relative',
    // },
    container: {
      flex: 1,
      // backgroundColor: theme.colors.background.quaternary.light,
      backgroundColor: '#F2F2F7',  // Fallback color
      alignItems: 'center',
      position: 'relative',
  },
    gradient: {
      flex: 1,
      backgroundColor: 'transparent',
      // background: 'radial-gradient(circle, #ffffff 30%,#f0f4ff 70%)',
    },
    // Modify the scrollView style:
    scrollView: {
      flex: 1,
      marginTop: calcHeight(-6), // 6% of screen height
      width: '100%',
      height: '100%',
    },
    // Add padding to scrollViewContent to account for the status bar:
    scrollViewContent: {
      flexGrow: 1,
      width: '100%',
      height: '100%',
    },
    appTitle: {
      ...theme.typography.apptitle,      
      color: theme.colors.text.primary.light,
      paddingHorizontal: theme.spacing.l,
      // paddingTop: theme.spacing.s,
    },
    // frostedGlass: {
    //     backgroundColor: theme.colors.background.frostedGlass || 'rgba(255,255,255,0.8)', // Ensure a solid background
    //     borderRadius: theme.layout.borderRadius.medium,
    //     // overflow: 'hidden',
    //     // ...theme.shadows.tiny,
    //   },

      frostedGlass: {
        backgroundColor: 'rgba(255, 255, 255, 0.7)',
        borderRadius: theme.layout.borderRadius.medium,
        // overflow: 'hidden',
        // ...theme.shadows.medium,
      },
    // mainCard: {
    //   padding: createSpacing(theme.spacing.l),
    //   margin: createSpacing(theme.spacing.m),
    //   flexDirection: 'row',
    //   justifyContent: 'space-between',
    //   alignItems: 'center',
    //   backgroundColor: theme.colors.background.secondary.light,
    //   // shadowColor: '#000',
    //   // shadowOffset: { width: 0, height: 2 },
    //   // shadowOpacity: 0.1,
    //   // shadowRadius: 80,
    //   // elevation: 4,
    //   ...theme.shadows.medium,
    // },
    mainCard: {
      padding: createSpacing(theme.spacing.l),
      margin: createSpacing(theme.spacing.m),
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      backgroundColor: theme.colors.background.secondary.light,
      borderRadius: theme.layout.borderRadius.xxl,
      ...theme.shadows.tiny,
    },
    caloriesContainer: {
      flex: 1,
    },
    caloriesLeft: {
      ...theme.typography.largeTitle,  // Instead of fontSize: normalizeFont(36)
      fontWeight: '50',
      // color: theme.colors.text.primary.light,
    },
    caloriesLabel: {
        ...theme.typography.callout,     // Instead of fontSize: normalizeFont(16)
        color: theme.colors.text.secondary.light,
    },
    macroContainer: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      paddingHorizontal: createSpacing(theme.spacing.l),
      // marginBottom: createSpacing(theme.spacing.s),
      backgroundColor: 'transparent', // or a solid color if needed
      borderRadius: theme.layout.borderRadius.xxl,

      ...theme.shadows.small,
    },
    recentlyEatenContainer: {
      padding: createSpacing(theme.spacing.m),
    },
    recentlyEatenCard: {
      padding: createSpacing(theme.spacing.m),
      flexDirection: 'row',
      ...theme.shadows.medium,

    },
    foodImage: {
      width: calcWidth(16), // 16% of screen width
      height: calcWidth(16), // Keep aspect ratio square
      borderRadius: createSpacing(theme.layout.borderRadius.medium),
      marginRight: createSpacing(theme.spacing.m),
    },
    recentlyEatenContent: {
      flex: 1,
      justifyContent: 'center',
    },
    recentlyEatenTitle: {
      ...theme.typography.headline,    // Instead of fontSize: normalizeFont(18)
      color: theme.colors.text.primary.light,
      marginBottom: theme.spacing.m,
      marginLeft: createSpacing(theme.spacing.l),
      marginTop:theme.spacing.l,
    },
    noMealText: {
      fontSize: normalizeFont(16),
      color: theme.colors.text.secondary.light,
      textAlign: 'center',
      marginTop: createSpacing(theme.spacing.l),
    },
    insightContainer: {
      padding: createSpacing(theme.spacing.s),
      margin: createSpacing(theme.spacing.m),
      borderRadius: createSpacing(theme.layout.borderRadius.medium),
    },
    insightText: {
      ...theme.typography.subhead,     // Instead of fontSize: normalizeFont(14)
      color: theme.colors.text.primary.light,
      textAlign: 'center',
    },
    errorContainer: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
      padding: createSpacing(theme.spacing.l),
    },
    errorText: {
      fontSize: normalizeFont(16),
      color: theme.colors.error.light,
      textAlign: 'center',
      marginBottom: createSpacing(theme.spacing.m),
    },
    retryButton: {
      padding: createSpacing(theme.spacing.m),
      backgroundColor: theme.colors.primary.light,
      borderRadius: createSpacing(theme.layout.borderRadius.medium),
    },
    retryButtonText: {
      fontSize: normalizeFont(16),
      color: theme.colors.text.primary.dark,
      fontWeight: '600',
    },
    signInContainer: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
      padding: createSpacing(theme.spacing.l),
    },
    signInText: {
      fontSize: normalizeFont(18),
      color: theme.colors.text.primary.light,
      textAlign: 'center',
    },
    emptyStateContainer: {
      alignItems: 'center',
      justifyContent: 'center',
      padding: createSpacing(theme.spacing.l),
      marginBottom: createSpacing(theme.spacing.l),
      marginTop: createSpacing(theme.spacing.l)
    },
    // lottieArrow: {
    //   width: 120,  // Start with 0 and adjust as needed
    //   height: 120, // Start with 0 and adjust as needed
    //   // position: 'absolute',
    //   bottom: -100,  // Adjust this to point to camera button
    //   alignSelf: 'center',
    //   transform: [{ rotate: '180deg' }]
      
    // }
  });

  export default styles; 
