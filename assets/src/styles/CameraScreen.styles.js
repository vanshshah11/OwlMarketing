// /Users/vanshshah/Desktop/New_app/5th_WellAI/WellAI/src/styles/CameraScreen.styles.js

import { StyleSheet } from 'react-native';
import theme from '../styles/theme';

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background.primary.dark,
  },
  overlay: {
    ...theme.mixins.absoluteFill,
    backgroundColor: 'transparent',
  },
  header: {
    ...theme.mixins.row,
    padding: theme.spacing.m,
  },
  backButton: {
    width: theme.layout.camera.controlButtonSize,
    height: theme.layout.camera.controlButtonSize,
    borderRadius: theme.layout.borderRadius.circular,
    ...theme.mixins.center,
  },
  headerText: {
    marginLeft: theme.spacing.m,
    color: theme.colors.text.primary.dark,
  },
  framingGuide: {
    position: 'absolute',
    backgroundColor: 'transparent',
    borderRadius: theme.layout.borderRadius.medium,
    overflow: 'hidden',
  },
  corner: {
    position: 'absolute',
    width: theme.layout.camera.frameCornerLength,
    height: theme.layout.camera.frameCornerLength,
    borderColor: theme.colors.text.primary.dark,
    borderWidth: theme.layout.camera.frameGuideThickness,
    borderRadius: theme.layout.borderRadius.tiny,
  },
  topLeft: {
    top: theme.spacing.xs,
    left: theme.spacing.xs,
    borderRightWidth: 0,
    borderBottomWidth: 0,
  },
  topRight: {
    top: theme.spacing.xs,
    right: theme.spacing.xs,
    borderLeftWidth: 0,
    borderBottomWidth: 0,
  },
  bottomLeft: {
    bottom: theme.spacing.xs,
    left: theme.spacing.xs,
    borderRightWidth: 0,
    borderTopWidth: 0,
  },
  bottomRight: {
    bottom: theme.spacing.xs,
    right: theme.spacing.xs,
    borderLeftWidth: 0,
    borderTopWidth: 0,
  },
  // controls: {
  //   ...theme.mixins.row,
  //   justifyContent: 'center',
  //   alignItems: 'center', 
  //   paddingHorizontal: theme.spacing.m,
  //   position: 'absolute',
  //   bottom: theme.spacing.xxxl,
  //   left: 0,
  //   right: 0,
  // },
  controls: {
    ...theme.mixins.row,
    justifyContent: 'center', // Changed from 'center'
    alignItems: 'center',
    paddingHorizontal: theme.spacing.m,
    position: 'absolute',
    bottom: theme.spacing.xxxl, // Keeping vertical position the same
    left: 0,
    right: 0,
  },
  controlButton: {
    width: theme.layout.camera.controlButtonSize,
    height: theme.layout.camera.controlButtonSize,
    borderRadius: theme.layout.borderRadius.circular,
    ...theme.mixins.center,
    marginHorizontal: theme.spacing.m,
    marginBottom: theme.spacing.m,
  },
  captureButton: {
    width: theme.layout.camera.captureButtonSize,
    height: theme.layout.camera.captureButtonSize,
    borderRadius: theme.layout.borderRadius.circular,
    ...theme.mixins.center,
    marginHorizontal: theme.spacing.m,
    marginBottom: theme.spacing.m,
  },
  captureButtonInner: {
    width: theme.layout.camera.captureButtonSize - theme.spacing.xs,
    height: theme.layout.camera.captureButtonSize - theme.spacing.xs,
    borderRadius: theme.layout.borderRadius.circular,
    backgroundColor: theme.colors.text.primary.dark,
  },
  modalContainer: {
    flex: 1,
    ...theme.mixins.center,
  },
  modalContent: {
    width: theme.layout.maxContentWidth,
    backgroundColor: theme.colors.background.secondary.light,
    borderRadius: theme.layout.borderRadius.xl,
    padding: theme.spacing.m,
    alignItems: 'center',
  },
  foodList: {
    width: '100%',
    maxHeight: theme.layout.camera.modalMaxHeight,
  },
  foodItem: {
    ...theme.mixins.row,
    justifyContent: 'space-between',
    padding: theme.spacing.m,
    borderBottomWidth: 1,
  },
  errorContainer: {
    position: 'absolute',
    top: theme.spacing.xxxl,
    left: theme.spacing.m,
    right: theme.spacing.m,
    padding: theme.spacing.s,
    borderRadius: theme.layout.borderRadius.small,
    zIndex: theme.zIndex.toast,
  },
  errorText: {
    color: theme.colors.text.primary.dark,
    textAlign: 'center',
  },
  permissionContainer: {
    flex: 1,
    backgroundColor: theme.colors.background.primary.light,
  },
  permissionContent: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: theme.spacing.l,
  },
  permissionTitle: {
    marginTop: theme.spacing.m,
    marginBottom: theme.spacing.s, 
    textAlign: 'center',
  },
  permissionText: {
    textAlign: 'center',
    marginBottom: theme.spacing.l,
    color: theme.colors.text.secondary.dark,
  },
  permissionButtons: {
    width: '100%',
    gap: theme.spacing.s,
  },
  permissionButton: {
    width: '100%',
    paddingVertical: theme.spacing.m,
    borderRadius: theme.layout.borderRadius.medium,
  },
  permissionButtonText: {
    textAlign: 'center',
  }
});

export { styles };


// import { StyleSheet, Dimensions } from 'react-native';
// import theme from '../styles/theme';

// const styles = StyleSheet.create({
//   container: {
//     flex: 1,
//     backgroundColor: theme.colors.background.primary.dark,
//   },
//   overlay: {
//     ...theme.mixins.absoluteFill,
//     backgroundColor: 'transparent',
//   },
//   header: {
//     ...theme.mixins.row,
//     padding: theme.spacing.m,
//   },
//   backButton: {
//     width: theme.layout.camera.controlButtonSize,
//     height: theme.layout.camera.controlButtonSize,
//     borderRadius: theme.layout.borderRadius.circular,
//     ...theme.mixins.center,
//   },
//   headerText: {
//     marginLeft: theme.spacing.m,
//     color: theme.colors.text.primary.dark,
//   },
//   framingGuide: {
//     position: 'absolute',
//     backgroundColor: 'transparent',
//     borderRadius: theme.layout.borderRadius.medium,
//     overflow: 'hidden',
//   },
//   corner: {
//     position: 'absolute',
//     width: theme.layout.camera.frameCornerLength,
//     height: theme.layout.camera.frameCornerLength,
//     borderColor: theme.colors.text.primary.dark,
//     borderWidth: theme.layout.camera.frameGuideThickness,
//     borderRadius: theme.layout.borderRadius.tiny,
//   },
//   topLeft: {
//     top: theme.spacing.xs,
//     left: theme.spacing.xs,
//     borderRightWidth: 0,
//     borderBottomWidth: 0,
//   },
//   topRight: {
//     top: theme.spacing.xs,
//     right: theme.spacing.xs,
//     borderLeftWidth: 0,
//     borderBottomWidth: 0,
//   },
//   bottomLeft: {
//     bottom: theme.spacing.xs,
//     left: theme.spacing.xs,
//     borderRightWidth: 0,
//     borderTopWidth: 0,
//   },
//   bottomRight: {
//     bottom: theme.spacing.xs,
//     right: theme.spacing.xs,
//     borderLeftWidth: 0,
//     borderTopWidth: 0,
//   },
//   controls: {
//     ...theme.mixins.row,
//     justifyContent: 'space-between',
//     paddingHorizontal: theme.spacing.m,
//     position: 'absolute',
//     bottom: theme.spacing.xxxl,
//     left: 0,
//     right: 0,
//   },
//   controlButton: {
//     width: theme.layout.camera.controlButtonSize,
//     height: theme.layout.camera.controlButtonSize,
//     borderRadius: theme.layout.borderRadius.circular,
//     ...theme.mixins.center,
//     marginHorizontal: theme.spacing.m,
//     marginBottom: theme.spacing.m,
//   },
//   captureButton: {
//     width: theme.layout.camera.captureButtonSize,
//     height: theme.layout.camera.captureButtonSize,
//     borderRadius: theme.layout.borderRadius.circular,
//     ...theme.mixins.center,
//     marginHorizontal: theme.spacing.m,
//     marginBottom: theme.spacing.m,
//   },
//   captureButtonInner: {
//     width: theme.layout.camera.captureButtonSize - theme.spacing.xs,
//     height: theme.layout.camera.captureButtonSize - theme.spacing.xs,
//     borderRadius: theme.layout.borderRadius.circular,
//     backgroundColor: theme.colors.text.primary.dark,
//   },
//   modalContainer: {
//     flex: 1,
//     ...theme.mixins.center,
//   },
//   modalContent: {
//     width: theme.layout.maxContentWidth,
//     backgroundColor: theme.colors.background.secondary.light,
//     borderRadius: theme.layout.borderRadius.xl,
//     padding: theme.spacing.m,
//     alignItems: 'center',
//   },
//   foodList: {
//     width: '100%',
//     maxHeight: theme.layout.camera.modalMaxHeight,
//   },
//   foodItem: {
//     ...theme.mixins.row,
//     justifyContent: 'space-between',
//     padding: theme.spacing.m,
//     borderBottomWidth: 1,
//   },
//   errorContainer: {
//     position: 'absolute',
//     top: theme.spacing.xxxl,
//     left: theme.spacing.m,
//     right: theme.spacing.m,
//     padding: theme.spacing.s,
//     borderRadius: theme.layout.borderRadius.small,
//     zIndex: theme.zIndex.toast,
//   },
//   errorText: {
//     color: theme.colors.text.primary.dark,
//     textAlign: 'center',
//   },
// });

// export { styles };
