import React , { useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Platform, Image, ActivityIndicator } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { BlurView } from '@react-native-community/blur';
import theme from '../styles/theme';
import LazyImage from '../Components/LazyImage';
import ReactNativeHapticFeedback from 'react-native-haptic-feedback';
import Animated, { 
  useAnimatedStyle, 
  useSharedValue,
  withSpring,
  withTiming,
  interpolate,
  Easing,
  withRepeat,
  withSequence
} from 'react-native-reanimated';

const FrostedGlassCard = ({ children, style }) => {
  if (Platform.OS === 'ios') {
    return (
      <View style={[styles.frostedContainer, style]}>
        <BlurView
          style={StyleSheet.absoluteFill}
          blurType="light"
          blurAmount={200}
          reducedTransparencyFallbackColor="white"
        />
        {children}
      </View>
    );
  }

  // Fallback for Android
  return (
    <View style={[styles.frostedContainer, style, { backgroundColor: 'rgba(255, 255, 255, 0.85)' }]}>
      {children}
    </View>
  );
};

const RecentlyEatenCard = ({ item }) => {
  const navigation = useNavigation();
  const scale = useSharedValue(1);
  const pressed = useSharedValue(false);
  const glimmerOpacity = useSharedValue(0.3);
  const spinnerRotation = useSharedValue(0);
  
  // Check if the item is pending (processing)
  const isPending = item.status === 'pending' || item.syncStatus === 'pending';
  
  // Simulate a progress percentage (in a real app this would come from the backend)
  // This is a random percentage between 20-90 to simulate progress for the demo
  const randomProgress = React.useMemo(() => {
    return Math.floor(Math.random() * 70) + 20;
  }, []);

  useEffect(() => {
    if (isPending) {
      // Start the glimmer animation
      glimmerOpacity.value = withRepeat(
        withSequence(
          withTiming(0.6, { duration: 800, easing: Easing.inOut(Easing.ease) }),
          withTiming(0.3, { duration: 800, easing: Easing.inOut(Easing.ease) })
        ),
        -1, // infinite repeat
        false // don't reverse animation
      );
      
      // Rotating spinner animation
      spinnerRotation.value = withRepeat(
        withTiming(360, { 
          duration: 1500, 
          easing: Easing.linear 
        }),
        -1, // infinite repeat
        false // don't reverse
      );
    }
  }, [isPending, glimmerOpacity, spinnerRotation]);

  const animatedStyles = useAnimatedStyle(() => {
    return {
      transform: [
        { scale: withSpring(scale.value) },
        { 
          translateY: interpolate(
            pressed.value,
            [0, 1],
            [0, -5]
          )
        }
      ]
    };
  });

  const glimmerStyles = useAnimatedStyle(() => {
    return {
      opacity: glimmerOpacity.value,
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: theme.colors.primary.light
    };
  });

  const spinnerStyles = useAnimatedStyle(() => {
    return {
      transform: [{ rotate: `${spinnerRotation.value}deg` }]
    };
  });

  const handlePressIn = () => {
    scale.value = withSpring(0.95);
    pressed.value = withTiming(1);
    ReactNativeHapticFeedback.trigger('impactLight', {
      enableVibrateFallback: true,
      ignoreAndroidSystemSettings: false
    });
  };

  const handlePressOut = () => {
    scale.value = withSpring(1);
    pressed.value = withTiming(0);
  };

  const handlePress = () => {

    const nutritionData = {
      mealName: item.name,
      calories: item.calories,
      carbs: item.nutrients.carbs,
      protein: item.nutrients.protein,
      fat: item.nutrients.fat,
      fiber: item.nutrients.fiber || 0,
      sugar: item.nutrients.sugar || 0,
    };

    navigation.navigate('Results', {
      image: item.imageUrl,
      barcode: item.barcode,
      existingData: nutritionData,
      originalItem: item,
      isPrefetched: true
    });
  };

  return (
    <TouchableOpacity
      onPress={handlePress}
      onPressIn={handlePressIn}
      onPressOut={handlePressOut}
      activeOpacity={1}
      style={styles.touchableContainer}
    >
      <Animated.View style={[styles.card, animatedStyles]}>
        <FrostedGlassCard style={styles.cardContent}>
          {isPending && (
            <Animated.View style={glimmerStyles} />
          )}
          
          {isPending ? (
            <View style={styles.loadingContainer}>
              <Animated.View style={spinnerStyles}>
                <View style={styles.spinner}>
                  <View style={styles.spinnerInner} />
                </View>
              </Animated.View>
              <View style={styles.loadingTextContainer}>
                <Text style={styles.processingText}>Processing...</Text>
                <View style={styles.progressContainer}>
                  <View style={[styles.progressBar, { width: `${randomProgress}%` }]} />
                  <Text style={styles.progressText}>{randomProgress}%</Text>
                </View>
              </View>
            </View>
          ) : (
            <>
              <LazyImage
                source={{ uri: item.imageUrl || 'https://via.placeholder.com/60' }}
                style={styles.foodImage}
              />
              <View style={styles.contentContainer}>
                <View style={styles.mainContent}>
                  <Text style={styles.foodName} numberOfLines={1}>
                    {item.name}
                  </Text>
                  <Text style={styles.caloriesText}>
                    {item.calories} calories
                  </Text>
                  <View style={styles.macrosContainer}>
                    <Text style={styles.macroText}>
                      P: {item.nutrients.protein}g
                    </Text>
                    <Text style={styles.macroText}>
                      C: {item.nutrients.carbs}g
                    </Text>
                    <Text style={styles.macroText}>
                      F: {item.nutrients.fat}g
                    </Text>
                  </View>
                </View>
                <Text style={styles.timestamp}>
                  {formatTimestamp(item.timestamp)}
                </Text>
              </View>
            </>
          )}
        </FrostedGlassCard>
      </Animated.View>
    </TouchableOpacity>
  );
};

const formatTimestamp = (timestamp) => {
  const now = new Date().getTime();
  const mealTime = timestamp.seconds * 1000 + timestamp.nanoseconds / 1000000;
  const timeDiff = now - mealTime;

  const minute = 60 * 1000;
  const hour = 60 * minute;
  const day = 24 * hour;

  if (timeDiff < minute) {
    return 'Just now';
  } else if (timeDiff < hour) {
    return `${Math.floor(timeDiff / minute)}m`;
  } else if (timeDiff < day) {
    return `${Math.floor(timeDiff / hour)}h`;
  } else {
    return `${Math.floor(timeDiff / day)}d`;
  }
};

const styles = StyleSheet.create({
  touchableContainer: {
    marginHorizontal: theme.spacing.m,
    marginBottom: theme.spacing.s,
  },
  frostedContainer: {
    borderRadius: theme.layout.borderRadius.medium,
    overflow: 'hidden',
    ...Platform.select({
      ios: {
        ...theme.shadows.small,
      },
      android: {
        elevation: 3,
      },
    }),
  },
  card: {
    width: '100%',
  },
  cardContent: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: theme.spacing.m,
    backgroundColor: '#F0F0F0',
    borderColor: '#E0E0E0',
  },
  foodImage: {
    width: theme.layout.recentlyeatenimage,
    height: theme.layout.recentlyeatenimage,
    borderRadius: theme.layout.borderRadius.small,
  },
  contentContainer: {
    flex: 1,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginLeft: theme.spacing.m,
  },
  mainContent: {
    flex: 1,
    marginRight: theme.spacing.s,
  },
  foodName: {
    ...theme.typography.callout,
    fontWeight: '600',
    color: theme.colors.text.primary.light,
    marginBottom: 2,
  },
  caloriesText: {
    ...theme.typography.subhead,
    color: theme.colors.text.secondary.light,
    marginBottom: 2,
  },
  macrosContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  macroText: {
    ...theme.typography.footnote,
    color: theme.colors.text.secondary.light,
    marginRight: theme.spacing.s,
    fontWeight: '500',
  },
  timestamp: {
    ...theme.typography.footnote,
    color: theme.colors.text.secondary.light,
    fontWeight: '500',
    alignSelf: 'flex-start',
  },
  loadingContainer: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'flex-start',
    padding: theme.spacing.m,
  },
  loadingTextContainer: {
    flex: 1,
    justifyContent: 'center',
  },
  spinner: {
    width: 40,
    height: 40,
    borderRadius: 20,
    borderWidth: 2,
    borderColor: theme.colors.background.primary.light,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: theme.spacing.m,
  },
  spinnerInner: {
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: theme.colors.primary.light,
  },
  processingText: {
    ...theme.typography.callout,
    fontWeight: '600',
    color: theme.colors.text.primary.light,
    marginBottom: 4,
  },
  progressContainer: {
    height: 16,
    backgroundColor: theme.colors.background.tertiary.light,
    borderRadius: 8,
    marginTop: 4,
    overflow: 'hidden',
    position: 'relative',
  },
  progressBar: {
    height: '100%',
    backgroundColor: theme.colors.primary.light,
    borderRadius: 8,
  },
  progressText: {
    ...theme.typography.caption,
    color: theme.colors.text.primary.light,
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    textAlign: 'center',
    textAlignVertical: 'center',
    fontWeight: '600',
  },
});

export default RecentlyEatenCard;