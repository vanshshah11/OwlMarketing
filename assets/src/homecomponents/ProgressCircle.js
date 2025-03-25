import React, { useEffect, useState } from 'react';
import { View, Animated, StyleSheet } from 'react-native';
import Svg, { Circle, Path } from 'react-native-svg';
import { SFSymbol } from 'react-native-sfsymbols';
import PropTypes from 'prop-types';
import theme from '../styles/theme';
import ReactNativeHapticFeedback from 'react-native-haptic-feedback';

const SYMBOL_MAP = {
  calories: 'tuningfork',
  protein: 'bolt.fill',
  carbs: 'leaf.fill',
  fat: 'drop.fill'
};

const ProgressCircle = ({
  consumed = 0,
  goal = 100,
  color = theme.colors.macro.protein,
  size = theme.layout.iconSize.large,
  strokeWidth = theme.layout.progressBar.small,
  duration = theme.animationDurations.medium,
  backgroundColor = theme.colors.background.tertiary.light,
  style,
  type = 'calories',
  shadow = true
}) => {
  const [animatedProgress, setAnimatedProgress] = useState(0);

  useEffect(() => {
    // Animate progress
    const animation = new Animated.Value(0);
    Animated.timing(animation, {
      toValue: consumed,
      duration: 1000,
      useNativeDriver: false
    }).start();

    // Update animatedProgress smoothly
    animation.addListener((value) => {
      setAnimatedProgress(value.value);
    });

    // Haptic feedback
    // if (consumed > 0) {
    //   if (consumed >= goal) {
    //   } else if (consumed >= goal * 0.8) {
    //   }
    // }

    // Cleanup listener
    return () => {
      animation.removeAllListeners();
    };
  }, [consumed, goal]);

  const getProgressCirclePath = (radius, percentage) => {
    // For zero progress, return an empty path
    if (percentage <= 0) {
      return '';
    }
    
    if (percentage >= 100) {
      const pathRadius = radius - strokeWidth / 2;
      return ` M ${radius} ${strokeWidth/2} A ${pathRadius} ${pathRadius} 0 1 1 ${radius-0.001} ${strokeWidth/2} `;
    }

    const startAngle = -90;
    const angleInRadians = ((percentage / 100) * 360 + startAngle) * (Math.PI / 180);
    const centerX = radius;
    const centerY = radius;
    const pathRadius = radius - strokeWidth / 2;
    const endX = centerX + pathRadius * Math.cos(angleInRadians);
    const endY = centerY + pathRadius * Math.sin(angleInRadians);
    const largeArcFlag = percentage > 50 ? 1 : 0;
    const startX = centerX;
    const startY = centerY - pathRadius;
    
    return `M ${startX} ${startY} A ${pathRadius} ${pathRadius} 0 ${largeArcFlag} 1 ${endX} ${endY}`;
  };

  const radius = size / 2;
  const progressPercentage = Math.min((animatedProgress / goal) * 100, 100);
  const progressPath = getProgressCirclePath(radius, progressPercentage);
  const symbolSize = size * 0.3;

  return (
    <View style={[styles.container, style]}>
      <Svg width={size} height={size}>
        {/* Background circle - always visible */}
        <Circle
          cx={radius}
          cy={radius}
          r={radius - strokeWidth / 2}
          stroke={backgroundColor}
          strokeWidth={strokeWidth}
          fill="none"
        />
        {/* Progress arc - only visible when there's progress */}
        {progressPercentage > 0 && (
          <Path
            d={progressPath}
            stroke={color}
            strokeWidth={strokeWidth}
            fill="none"
            strokeLinecap="round"
          />
        )}
      </Svg>
      <View style={[styles.symbolContainer, { width: size, height: size }]}>
        <SFSymbol
          name={SYMBOL_MAP[type]}
          weight="semibold"
          scale="large"
          color={'#000000'}
          size={symbolSize}
          resizeMode="center"
          multicolor={false}
        />
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  symbolContainer: {
    position: 'absolute',
    justifyContent: 'center',
    alignItems: 'center',
  },
  iconBackground: {
    backgroundColor: '#F0F0F0',
    borderRadius: 1000,
    justifyContent: 'center',
    alignItems: 'center',
  }
});

ProgressCircle.propTypes = {
  consumed: PropTypes.number,
  goal: PropTypes.number,
  color: PropTypes.string,
  size: PropTypes.number,
  strokeWidth: PropTypes.number,
  duration: PropTypes.number,
  backgroundColor: PropTypes.string,
  style: PropTypes.object,
  type: PropTypes.oneOf(['calories', 'protein', 'carbs', 'fat']),
};

export default React.memo(ProgressCircle);

// import React, { useEffect, useRef } from 'react';
// import { View, Animated, StyleSheet } from 'react-native';
// import Svg, { Circle, Path } from 'react-native-svg';
// import { SFSymbol } from 'react-native-sfsymbols';
// import PropTypes from 'prop-types';
// import theme from '../styles/theme';
// import ReactNativeHapticFeedback from 'react-native-haptic-feedback';

// const SYMBOL_MAP = {
//   calories: 'tuningfork',
//   protein: 'bolt.fill',
//   carbs: 'leaf.fill',
//   fat: 'drop.fill'
// };

// const ProgressCircle = ({
//   consumed = 0,
//   goal = 100,
//   color = theme.colors.macro.protein,
//   size = theme.layout.iconSize.large,
//   strokeWidth = theme.layout.progressBar.small,
//   duration = theme.animationDurations.medium,
//   backgroundColor = theme.colors.background.tertiary.light,
//   style,
//   type = 'calories',
//   shadow = true
// }) => {
//   const animatedValue = useRef(new Animated.Value(0)).current;
//   const prevConsumed = useRef(consumed);

//   useEffect(() => {
//     if (consumed > prevConsumed.current) {
//       if (consumed >= goal) {
//         ReactNativeHapticFeedback.trigger('notificationSuccess', {
//           enableVibrateFallback: true,
//           ignoreAndroidSystemSettings: false,
//         });
//       } else if (consumed >= goal * 0.8) {
//         ReactNativeHapticFeedback.trigger('impactMedium', {
//           enableVibrateFallback: true,
//           ignoreAndroidSystemSettings: false,
//         });
//       }
//     }
//     prevConsumed.current = consumed;

//     Animated.spring(animatedValue, {
//       toValue: consumed,
//       duration,
//       friction: 8,
//       tension: 40,
//       useNativeDriver: true,
//     }).start();
//   }, [consumed, duration]);

//   const getProgressCirclePath = (radius, percentage) => {
//     // For zero progress, return an empty path
//     if (percentage <= 0) {
//       return '';
//     }
    
//     if (percentage >= 100) {
//       const pathRadius = radius - strokeWidth / 2;
//       return ` M ${radius} ${strokeWidth/2} A ${pathRadius} ${pathRadius} 0 1 1 ${radius-0.001} ${strokeWidth/2} `;
//     }

//     const startAngle = -90;
//     const angleInRadians = ((percentage / 100) * 360 + startAngle) * (Math.PI / 180);
//     const centerX = radius;
//     const centerY = radius;
//     const pathRadius = radius - strokeWidth / 2;
//     const endX = centerX + pathRadius * Math.cos(angleInRadians);
//     const endY = centerY + pathRadius * Math.sin(angleInRadians);
//     const largeArcFlag = percentage > 50 ? 1 : 0;
//     const startX = centerX;
//     const startY = centerY - pathRadius;
    
//     return `M ${startX} ${startY} A ${pathRadius} ${pathRadius} 0 ${largeArcFlag} 1 ${endX} ${endY}`;
//   };

//   const radius = size / 2;
//   const progressPercentage = Math.min((consumed / goal) * 100, 100);
//   const progressPath = getProgressCirclePath(radius, progressPercentage);
//   const symbolSize = size * 0.3;

//   return (
//     <View style={[styles.container, style]}>
//       <Svg width={size} height={size}>
//         {/* Background circle - always visible */}
//         <Circle
//           cx={radius}
//           cy={radius}
//           r={radius - strokeWidth / 2}
//           stroke={backgroundColor}
//           strokeWidth={strokeWidth}
//           fill="none"
//         />
//         {/* Progress arc - only visible when there's progress */}
//         {progressPercentage > 0 && (
//           <Path
//             d={progressPath}
//             stroke={color}
//             strokeWidth={strokeWidth}
//             fill="none"
//             strokeLinecap="round"
//           />
//         )}
//       </Svg>
//       <View style={[styles.symbolContainer, { width: size, height: size }]}>
//         {/* <View style={[styles.iconBackground, { width: symbolSize * 1.6, height: symbolSize * 1.6 }]}> */}
//           <SFSymbol
//             name={SYMBOL_MAP[type]}
//             weight="semibold"
//             scale="large"
//             color={'#000000'}
//             size={symbolSize}
//             resizeMode="center"
//             multicolor={false}
//           />
//         </View>
//       </View>
//     // </View>
//   );
// };

// const styles = StyleSheet.create({
//   container: {
//     alignItems: 'center',
//     justifyContent: 'center',
//     position: 'relative',
//   },
//   symbolContainer: {
//     position: 'absolute',
//     justifyContent: 'center',
//     alignItems: 'center',
//   },
//   iconBackground: {
//     backgroundColor: '#F0F0F0',
//     borderRadius: 1000,
//     justifyContent: 'center',
//     alignItems: 'center',
//   }
// });

// ProgressCircle.propTypes = {
//   consumed: PropTypes.number,
//   goal: PropTypes.number,
//   color: PropTypes.string,
//   size: PropTypes.number,
//   strokeWidth: PropTypes.number,
//   duration: PropTypes.number,
//   backgroundColor: PropTypes.string,
//   style: PropTypes.object,
//   type: PropTypes.oneOf(['calories', 'protein', 'carbs', 'fat']),
// };

// export default React.memo(ProgressCircle);




// import React, { useEffect, useRef } from 'react';
// import { View, Animated, StyleSheet } from 'react-native';
// import Svg, { Circle, Path } from 'react-native-svg';
// import PropTypes from 'prop-types';
// import theme from '../styles/theme';
// import ReactNativeHapticFeedback from 'react-native-haptic-feedback';

// const ProgressCircle = ({
//   consumed = 0,
//   goal = 100,
//   color = theme.colors.macro.protein,
//   size = theme.layout.iconSize.large,
//   strokeWidth = theme.layout.progressBar.small,
//   duration = theme.animationDurations.medium,
//   backgroundColor = theme.colors.background.tertiary.light,
//   style
// }) => {
//   const animatedValue = useRef(new Animated.Value(0)).current;
//   const prevConsumed = useRef(consumed);
  
//   useEffect(() => {
//     // Only trigger haptic if value increased
//     if (consumed > prevConsumed.current) {
//       if (consumed >= goal) {
//         ReactNativeHapticFeedback.trigger('notificationSuccess', {
//           enableVibrateFallback: true,
//           ignoreAndroidSystemSettings: false
//         });
//       } else if (consumed >= goal * 0.8) {
//         ReactNativeHapticFeedback.trigger('impactMedium', {
//           enableVibrateFallback: true,
//           ignoreAndroidSystemSettings: false
//         });
//       }
//     }
    
//     prevConsumed.current = consumed;

//     Animated.spring(animatedValue, {
//       toValue: consumed,
//       duration,
//       friction: 8,
//       tension: 40,
//       useNativeDriver: true,
//     }).start();
//   }, [consumed, duration]);

//   const getProgressCirclePath = (radius, percentage) => {
//     // When percentage is 100 or more, return a complete circle path
//     if (percentage >= 100) {
//       const pathRadius = radius - strokeWidth / 2;
//       return `
//         M ${radius} ${strokeWidth/2}
//         A ${pathRadius} ${pathRadius} 0 1 1 ${radius-0.001} ${strokeWidth/2}
//       `;
//     }

//     const startAngle = -90;
//     const angleInRadians = ((percentage / 100) * 360 + startAngle) * (Math.PI / 180);
    
//     const centerX = radius;
//     const centerY = radius;
//     const pathRadius = radius - strokeWidth / 2;
    
//     const endX = centerX + pathRadius * Math.cos(angleInRadians);
//     const endY = centerY + pathRadius * Math.sin(angleInRadians);
    
//     const largeArcFlag = percentage > 50 ? 1 : 0;
    
//     const startX = centerX;
//     const startY = centerY - pathRadius;
    
//     return `M ${startX} ${startY} A ${pathRadius} ${pathRadius} 0 ${largeArcFlag} 1 ${endX} ${endY}`;
//   };

//   // Early return if nothing consumed
//   if (consumed <= 0) {
//     return null;
//   }

//   const radius = size / 2;
//   // Ensure percentage calculation handles values over 100%
//   const progressPercentage = Math.min((consumed / goal) * 100, 100);
//   const progressPath = getProgressCirclePath(radius, progressPercentage);

//   return (
//     <View style={[styles.container, { width: size, height: size }, style]}>
//       <Svg width={size} height={size}>
//         <Circle
//           cx={radius}
//           cy={radius}
//           r={radius - strokeWidth / 2}
//           stroke={backgroundColor}
//           strokeWidth={strokeWidth}
//           fill="none"
//         />
//         <Path
//           d={progressPath}
//           stroke={color}
//           strokeWidth={strokeWidth}
//           fill="none"
//           strokeLinecap="round"
//         />
//       </Svg>
//     </View>
//   );
// };

// const styles = StyleSheet.create({
//   container: {
//     ...theme.mixins.center,
//   }
// });

// ProgressCircle.propTypes = {
//   consumed: PropTypes.number,
//   goal: PropTypes.number,
//   color: PropTypes.string,
//   size: PropTypes.number,
//   strokeWidth: PropTypes.number,
//   duration: PropTypes.number,
//   backgroundColor: PropTypes.string,
//   style: PropTypes.object,
// };

// export default React.memo(ProgressCircle);





// import React, { useEffect, useRef } from 'react';
// import { View, Animated, StyleSheet } from 'react-native';
// import Svg, { Circle, Path } from 'react-native-svg';
// import SFSymbol from 'react-native-sfsymbols';
// import PropTypes from 'prop-types';
// import theme from '../styles/theme';
// import ReactNativeHapticFeedback from 'react-native-haptic-feedback';

// const SYMBOL_MAP = {
//   calories: 'flame.fill',
//   protein: 'fish.fill',
//   carbs: 'leaf.fill',
//   fat: 'drop.fill'
// };

// const ProgressCircle = ({
//   consumed = 0,
//   goal = 100,
//   color = theme.colors.macro.protein,
//   size = theme.layout.iconSize.large,
//   strokeWidth = theme.layout.progressBar.small,
//   duration = theme.animationDurations.medium,
//   backgroundColor = theme.colors.background.tertiary.light,
//   style,
//   type = 'calories'
// }) => {
//   const animatedValue = useRef(new Animated.Value(0)).current;
//   const prevConsumed = useRef(consumed);

//   useEffect(() => {
//     if (consumed > prevConsumed.current) {
//       if (consumed >= goal) {
//         ReactNativeHapticFeedback.trigger('notificationSuccess', {
//           enableVibrateFallback: true,
//           ignoreAndroidSystemSettings: false,
//         });
//       } else if (consumed >= goal * 0.8) {
//         ReactNativeHapticFeedback.trigger('impactMedium', {
//           enableVibrateFallback: true,
//           ignoreAndroidSystemSettings: false,
//         });
//       }
//     }
//     prevConsumed.current = consumed;

//     Animated.spring(animatedValue, {
//       toValue: consumed,
//       duration,
//       friction: 8,
//       tension: 40,
//       useNativeDriver: true,
//     }).start();
//   }, [consumed, duration]);

//   const getProgressCirclePath = (radius, percentage) => {
//     if (percentage >= 100) {
//       const pathRadius = radius - strokeWidth / 2;
//       return ` M ${radius} ${strokeWidth/2} A ${pathRadius} ${pathRadius} 0 1 1 ${radius-0.001} ${strokeWidth/2} `;
//     }

//     const startAngle = -90;
//     const angleInRadians = ((percentage / 100) * 360 + startAngle) * (Math.PI / 180);
//     const centerX = radius;
//     const centerY = radius;
//     const pathRadius = radius - strokeWidth / 2;
//     const endX = centerX + pathRadius * Math.cos(angleInRadians);
//     const endY = centerY + pathRadius * Math.sin(angleInRadians);
//     const largeArcFlag = percentage > 50 ? 1 : 0;
//     const startX = centerX;
//     const startY = centerY - pathRadius;
    
//     return `M ${startX} ${startY} A ${pathRadius} ${pathRadius} 0 ${largeArcFlag} 1 ${endX} ${endY}`;
//   };

//   const radius = size / 2;
//   const progressPercentage = Math.min((consumed / goal) * 100, 100);
//   const progressPath = getProgressCirclePath(radius, progressPercentage);
//   const symbolSize = size * 0.45;

//   // Calculate symbol opacity based on consumed value
//   const symbolOpacity = consumed === 0 ? 0.5 : 1;

//   return (
//     <View style={[styles.container, style]}>
//       <Svg width={size} height={size}>
//         {/* Background circle - always visible */}
//         <Circle
//           cx={radius}
//           cy={radius}
//           r={radius - strokeWidth / 2}
//           stroke={backgroundColor}
//           strokeWidth={strokeWidth}
//           fill="none"
//         />
//         {/* Progress circle - only visible when there's progress */}
//         {consumed > 0 && (
//           <Path
//             d={progressPath}
//             stroke={color}
//             strokeWidth={strokeWidth}
//             fill="none"
//             strokeLinecap="round"
//           />
//         )}
//       </Svg>
//       <View style={[styles.symbolContainer, { width: size, height: size }]}>
//         <SFSymbol
//           name={SYMBOL_MAP[type]}
//           weight="semibold"
//           scale="large"
//           color={color}
//           size={symbolSize}
//           resizeMode="center"
//           multicolor={false}
//           style={{ opacity: symbolOpacity }}
//         />
//       </View>
//     </View>
//   );
// };

// const styles = StyleSheet.create({
//   container: {
//     ...theme.mixins.center,
//     position: 'relative',
//   },
//   symbolContainer: {
//     position: 'absolute',
//     justifyContent: 'center',
//     alignItems: 'center',
//   }
// });

// ProgressCircle.propTypes = {
//   consumed: PropTypes.number,
//   goal: PropTypes.number,
//   color: PropTypes.string,
//   size: PropTypes.number,
//   strokeWidth: PropTypes.number,
//   duration: PropTypes.number,
//   backgroundColor: PropTypes.string,
//   style: PropTypes.object,
//   type: PropTypes.oneOf(['calories', 'protein', 'carbs', 'fat']),
// };

// export default React.memo(ProgressCircle);


//when the values are zero, the progresscircle doesn't even appear. make it so it does appear when the values are zero.

// import React, { useEffect, useRef } from 'react';
// import { View, Animated, StyleSheet } from 'react-native';
// import Svg, { Circle, Path } from 'react-native-svg';
// import {SFSymbol }from 'react-native-sfsymbols';
// import PropTypes from 'prop-types';
// import theme from '../styles/theme';
// import ReactNativeHapticFeedback from 'react-native-haptic-feedback';

// const SYMBOL_MAP = {
//   calories: 'flame.fill',
//   protein: 'fish.fill',
//   carbs: 'leaf.fill',
//   fat: 'drop.fill'
// };

// const ProgressCircle = ({
//   consumed = 0,
//   goal = 100,
//   color = theme.colors.macro.protein,
//   size = theme.layout.iconSize.large,
//   strokeWidth = theme.layout.progressBar.small,
//   duration = theme.animationDurations.medium,
//   backgroundColor = theme.colors.background.tertiary.light,
//   style,
//   type = 'calories'
// }) => {
//   const animatedValue = useRef(new Animated.Value(0)).current;
//   const prevConsumed = useRef(consumed);

//   useEffect(() => {
//     if (consumed > prevConsumed.current) {
//       if (consumed >= goal) {
//         ReactNativeHapticFeedback.trigger('notificationSuccess', {
//           enableVibrateFallback: true,
//           ignoreAndroidSystemSettings: false,
//         });
//       } else if (consumed >= goal * 0.8) {
//         ReactNativeHapticFeedback.trigger('impactMedium', {
//           enableVibrateFallback: true,
//           ignoreAndroidSystemSettings: false,
//         });
//       }
//     }
//     prevConsumed.current = consumed;

//     Animated.spring(animatedValue, {
//       toValue: consumed,
//       duration,
//       friction: 8,
//       tension: 40,
//       useNativeDriver: true,
//     }).start();
//   }, [consumed, duration]);

//   const getProgressCirclePath = (radius, percentage) => {
//     if (percentage >= 100) {
//       const pathRadius = radius - strokeWidth / 2;
//       return ` M ${radius} ${strokeWidth/2} A ${pathRadius} ${pathRadius} 0 1 1 ${radius-0.001} ${strokeWidth/2} `;
//     }

//     const startAngle = -90;
//     const angleInRadians = ((percentage / 100) * 360 + startAngle) * (Math.PI / 180);
//     const centerX = radius;
//     const centerY = radius;
//     const pathRadius = radius - strokeWidth / 2;
//     const endX = centerX + pathRadius * Math.cos(angleInRadians);
//     const endY = centerY + pathRadius * Math.sin(angleInRadians);
//     const largeArcFlag = percentage > 50 ? 1 : 0;
//     const startX = centerX;
//     const startY = centerY - pathRadius;
    
//     return `M ${startX} ${startY} A ${pathRadius} ${pathRadius} 0 ${largeArcFlag} 1 ${endX} ${endY}`;
//   };

//   if (consumed <= 0) return null;

//   const radius = size / 2;
//   const progressPercentage = Math.min((consumed / goal) * 100, 100);
//   const progressPath = getProgressCirclePath(radius, progressPercentage);
//   const symbolSize = size * 0.25; // Slightly larger than emoji version for better visibility

//   return (
//     <View style={[styles.container, style]}>
//       <Svg width={size} height={size}>
//         <Circle
//           cx={radius}
//           cy={radius}
//           r={radius - strokeWidth / 2}
//           stroke={backgroundColor}
//           strokeWidth={strokeWidth}
//           fill="none"
//         />
//         <Path
//           d={progressPath}
//           stroke={color}
//           strokeWidth={strokeWidth}
//           fill="none"
//           strokeLinecap="round"
//         />
//       </Svg>
//       <View style={[styles.symbolContainer, { width: size, height: size }]}>
//         <SFSymbol
//           name={SYMBOL_MAP[type]}
//           weight="semibold"
//           scale="large"
//           color={color}
//           size={symbolSize}
//           resizeMode="center"
//           multicolor={false}
//         />
//       </View>
//     </View>
//   );
// };

// const styles = StyleSheet.create({
//   container: {
//     ...theme.mixins.center,
//     position: 'relative',
//   },
//   symbolContainer: {
//     position: 'absolute',
//     justifyContent: 'center',
//     alignItems: 'center',
//   }
// });

// ProgressCircle.propTypes = {
//   consumed: PropTypes.number,
//   goal: PropTypes.number,
//   color: PropTypes.string,
//   size: PropTypes.number,
//   strokeWidth: PropTypes.number,
//   duration: PropTypes.number,
//   backgroundColor: PropTypes.string,
//   style: PropTypes.object,
//   type: PropTypes.oneOf(['calories', 'protein', 'carbs', 'fat']),
// };

// export default React.memo(ProgressCircle);


