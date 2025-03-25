import { StyleSheet, Dimensions } from 'react-native';
import theme from '../styles/theme';
import { calcWidth, calcHeight } from '../styles/theme'; // Add this import

const { width, height } = Dimensions.get('window');

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background.secondary.light,
  },
  scrollView: {
    // flexGrow: 1,
  },
  previewContainer: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  slide: {
    width: width,  // Dynamic screen width
    height: '100%',
  },
  slideImage: {// the image in the carousel
    width: '100%',
    height: height * 0.7,
    resizeMode: 'cover',
  },
  content: {
    flex: 1,
    justifyContent: 'space-between',
  },
  textContainer: {
    top: theme.spacing.xxxs,
    paddingTop: theme.spacing.xxs,
    width: '90%',  // Dynamic width instead of hardcoded value
    alignSelf: 'center',  // Center the container horizontally
  },
  getStartedButton: {
    position: 'absolute',
    bottom: theme.spacing.xl,
    left: theme.spacing.m,
    right: theme.spacing.m,
    backgroundColor: theme.colors.primary.light,
    paddingVertical: theme.spacing.m,
    borderRadius: theme.layout.borderRadius.large,
    alignItems: 'center',
  },
  getStartedButtonText: {
    ...theme.typography.button,
    color: theme.colors.background.secondary.light,
  },
  headerContainer: {
  flexDirection: 'row',
  alignItems: 'center',
  paddingHorizontal: theme.spacing.s,
  paddingTop: theme.spacing.xs,
  marginBottom: theme.spacing.s,
  width: '100%',
},
  backButtonImage: {
    width: theme.layout.iconSize.medium,    // Using predefined icon sizing
    height: theme.layout.iconSize.medium,   // This will be 24 by default but scales responsively
    tintColor: theme.colors.text.primary.light,
},
  progressFill: {
    height: '100%',
    backgroundColor: theme.colors.background.primary.dark,
  },
  // backButton: {
  //   position: 'absolute',
  //   alignSelf: 'flex-start',
  //   top: theme.responsive.height(7), // Use theme's responsive helper
  //   left: theme.spacing.m, // Use theme's spacing system
  //   zIndex: theme.zIndex.header,
  // },
  // progressBarContainer: {
  //   width: theme.layout.maxContentWidth, // Use predefined layout width
  //   alignSelf: 'center',
  //   marginTop: theme.spacing.xs,
  //   marginBottom: theme.spacing.xs,
  // },
  // progressBar: {
  //   height: theme.layout.progressBar.medium,
  //   backgroundColor: theme.colors.background.tertiary.light,
  //   borderRadius: theme.layout.borderRadius.medium,
  //   overflow: 'hidden',
  //   width: '85%',
  //   alignSelf: 'left',
  //   marginVertical: theme.spacing.s,
  //   // marginVertical: height * 0.000,  // Use dynamic margin based on screen height
  //   marginLeft: theme.spacing.huge,
  //   // height * 0.068,
  //   marginTop: theme.spacing.xxxs,
  //   // height * 0.0016,
  //   marginBottom: theme.spacing.s,
  //   // height * 0.015,
  // },
  backButton: {
    padding: theme.spacing.xxxs,
  },
  progressBarContainer: {
    flex: 1,
    marginLeft: theme.spacing.s,
  },
  progressBar: {
    height: theme.layout.progressBar.medium,
    backgroundColor: theme.colors.background.tertiary.light,
    borderRadius: theme.layout.borderRadius.medium,
    overflow: 'hidden',
    width: '95%',
  },
  title: {
    ...theme.typography.bigTitle,
    color: theme.colors.text.primary.light,
    marginBottom: theme.spacing.m,
  },
  description: {
    ...theme.typography.body,
    color: theme.colors.text.secondary.light,
    marginBottom: theme.spacing.l,
  },
  input: {
    width: '90%',
    height: theme.layout.buttonHeight,
    borderColor: theme.colors.background.tertiary.light,
    borderWidth: 1,
    borderRadius: theme.layout.borderRadius.medium,
    marginBottom: theme.spacing.m,
    paddingHorizontal: theme.spacing.m,
    ...theme.typography.body,
    color: theme.colors.text.primary.light,
    backgroundColor: theme.colors.background.secondary.light,
  },
  nameinput:{
      width: '90%',
      alignItems: 'center',
      // overflow: 'hidden',
      justifyContent: 'center',
      padding:theme.spacing.m,
      marginLeft: theme.spacing.m,
      marginTop: theme.spacing.m,
      height: theme.layout.buttonHeight,
      borderColor: theme.colors.background.tertiary.light,
      borderWidth: 1,
      borderRadius: theme.layout.borderRadius.medium,
      marginBottom: theme.spacing.m,
      paddingHorizontal: theme.spacing.m,
      ...theme.typography.body,
      color: theme.colors.text.primary.light,
      backgroundColor: theme.colors.background.secondary.light,
  },
  inputHint: {
    ...theme.typography.footnote,
    color: theme.colors.text.secondary.light,
    marginBottom: theme.spacing.m,
  },
  genderContainer: {
    marginVertical: theme.spacing.m,
    borderRadius: theme.layout.borderRadius.large,
    overflow: 'hidden',
    ...theme.shadows.tiny,
    justifyContent: 'space-between',
    // height: theme.layout.buttonHeight * 4,//space between buttons
    alignItems: 'center',
    // marginBottom:theme.spacing.m
  },
  genderButton: {
    height: theme.layout.buttonHeight,
    justifyContent: 'center',
    alignItems: 'center',
    // backgroundColor: '#FAFAFA',// #FAFAFA   E6E6E1
    // backgroundColor: '#Fffff5',
    borderRadius: theme.layout.borderRadius.medium,//curve edges
    marginHorizontal: theme.spacing.x,
    marginVertical: theme.spacing.xs, // Add vertical margin
    borderColor: theme.colors.background.tertiary.light,
    // padding:theme.spacing.l,
    width: '90%',

  },
  genderButtonActive: {
    backgroundColor: theme.colors.primary.dark,
    // marginVertical: theme.spacing.m,
    marginHorizontal: theme.spacing.m,
    borderRadius: theme.layout.borderRadius.large,
  },
  genderButtonText: {
    ...theme.typography.button,
    color: theme.colors.text.primary.light,
  },
  genderButtonTextActive: {
    color: theme.colors.background.secondary.light,
  },  
  optionContent: {
    alignItems: 'center',
  },
  optionDescription: {
    ...theme.typography.caption,
    color: theme.colors.text.secondary.light,
    marginTop: theme.spacing.xs,
  },
  encouragementContainer: {
    width: '90%',
    backgroundColor: theme.colors.background.secondary.light,
    borderRadius: theme.layout.borderRadius.large,
    padding: theme.spacing.m,
    ...theme.shadows.medium,
    },
  encouragementText: {
    ...theme.typography.body,
    color: theme.colors.text.primary.light,
    marginBottom: theme.spacing.m,
    textAlign: 'center',
    lineHeight: 24, // Adjust this value for better readability
    },
  nextButton: {
    marginHorizontal: theme.spacing.m,
    marginBottom: theme.spacing.s,
    backgroundColor: theme.colors.primary.dark,
    // backgroundColor: '#FAFAFA',
    paddingVertical: height * 0.02,  // Responsive vertical padding
    paddingHorizontal: theme.spacing.m,
    borderRadius: theme.layout.borderRadius.circular,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: theme.spacing.m,
  },
  nextButtonInactive: {
    backgroundColor: '#CCCCCC', // Grey color for inactive state
  },
  nextButtonText: {
    ...theme.typography.button,
    color: theme.colors.background.primary.light,
  },
  nextButtonTextInactive: {
    color: '#888888', // Darker grey for inactive text
  },
  inputError: {
    borderColor: theme.colors.error.light,
  },
  errorContainer: {
    marginTop: theme.spacing.s,
  },
  errorText: {
    ...theme.typography.footnote,
    color: theme.colors.error.light,
  },
  choicesContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: theme.spacing.s,
  },
  choiceButton: {
    backgroundColor: theme.colors.primary.light,
    padding: theme.spacing.s,
    borderRadius: theme.layout.borderRadius.medium,
  },
  choiceText: {
    ...theme.typography.button,
    color: theme.colors.background.secondary.light,
  },
  oldConfirmContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    ...theme.mixins.padding.all(theme.spacing.xl),
  },
  holdConfirmTitle: {
    ...theme.typography.title1,
    color: theme.colors.text.primary.light,
    marginBottom: theme.spacing.m,
    textAlign: 'center',
  },
  holdConfirmDescription: {
    ...theme.typography.body,
    color: theme.colors.text.secondary.light,
    textAlign: 'center',
    marginBottom: theme.spacing.xl,
    maxWidth: theme.layout.maxContentWidth,
  },
});

export { styles };


//
  // backButton: {
  //   position: 'absolute',
  //   alignSelf: 'right',  // Center it horizontally
  //   top: height * 0.055, // This positions the button a bit lower based on the height
  //   left: theme.spacing.m, // Fixed spacing for left instead of using height
  //   zIndex: theme.zIndex.header, // Keep it above other elements
  // },
    // progressBarContainer: {
  //     paddingHorizontal: theme.spacing.m,
  //     marginTop: theme.spacing.s,
  // },
  // progressBar: {
  //   height: theme.layout.progressBar.medium,
  //   backgroundColor: theme.colors.background.tertiary.light,
  //   borderRadius: theme.layout.borderRadius.medium,
  //   overflow: 'hidden',
  //   width: '80%',  // Set width dynamically
  //   alignSelf: 'right',  // Center it horizontally
  //   // marginVertical: height * 0.000,  // Use dynamic margin based on screen height
  //   marginLeft: height * 0.068,
  //   marginTop: height * 0.0016,
  //   marginBottom: height * 0.015,
  // },