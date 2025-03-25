import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Dimensions } from 'react-native';
import { SFSymbol } from 'react-native-sfsymbols';
import { db } from '../utils/firebase';
import theme from '../styles/theme';
import Animated, {
  withTiming,
  useAnimatedStyle,
  useSharedValue,
  interpolate,
  Extrapolate,
  runOnJS,
} from 'react-native-reanimated';

const { height: SCREEN_HEIGHT } = Dimensions.get('window');

const StreakCard = ({ currentStreak, longestStreak, lastActiveDate, streakDates = [] }) => {
  // Ensure we always have valid values
  const safeCurrentStreak = Number(currentStreak) || 0;
  const safeLongestStreak = Number(longestStreak) || 0;
  const safeStreakDates = Array.isArray(streakDates) ? streakDates : [];

  const [modalVisible, setModalVisible] = useState(false);
  const animationProgress = useSharedValue(0);
  const glowOpacity = useSharedValue(0);

  // Calculate streak statistics
  const getStreakStats = () => {
    const totalDays = safeStreakDates.length;

    // Prevent division by zero
    const averageEntriesPerDay = totalDays > 0
      ? safeStreakDates.reduce((acc, date) => acc + (Number(date.entries) || 0), 0) / totalDays
      : 0;

    return {
      totalDays,
      averageEntriesPerDay: averageEntriesPerDay.toFixed(1),
      activeDaysPercentage: totalDays > 0
        ? ((totalDays / 30) * 100).toFixed(1)
        : '0.0', // Last 30 days
    };
  };

  // Handle opening the modal with animations
  const handleLongPress = () => {
    setModalVisible(true);
    glowOpacity.value = withTiming(1, { duration: 300 });
    animationProgress.value = withTiming(1, { duration: 800 });
  };

  // Handle closing the modal with animations
  const handleClose = () => {
    glowOpacity.value = withTiming(0, { duration: 300 });
    animationProgress.value = withTiming(0, { duration: 500 }, () => {
      runOnJS(setModalVisible)(false);
    });
  };

  // Animated styles for the modal
  const modalAnimatedStyle = useAnimatedStyle(() => {
    const scale = interpolate(
      animationProgress.value,
      [0, 1],
      [0.1, 1],
      Extrapolate.CLAMP
    );

    const translateY = interpolate(
      animationProgress.value,
      [0, 1],
      [SCREEN_HEIGHT / 2, 0],
      Extrapolate.CLAMP
    );

    return {
      transform: [
        { scale },
        { translateY },
      ],
      opacity: animationProgress.value,
    };
  });

  // Animated styles for the glow effect
  const glowAnimatedStyle = useAnimatedStyle(() => ({
    opacity: glowOpacity.value,
    transform: [
      { scale: interpolate(glowOpacity.value, [0, 1], [1, 1.5]) },
    ],
  }));

  return (
    <>
      <TouchableOpacity
        onLongPress={handleLongPress}
        style={styles.container}
      >
        <View style={styles.streakContainer}>
          <Animated.View style={[styles.glowEffect, glowAnimatedStyle]} />
          <SFSymbol
            name="flame.fill"
            weight="medium"
            scale="medium"
            color="#FF9500"
            size={24}
            style={styles.icon}
          />
          <Text style={styles.streakText}>   {safeCurrentStreak}</Text>
        </View>
      </TouchableOpacity>

      {modalVisible && (
        <View style={styles.modalOverlay}>
          <Animated.View style={[styles.modalContent, modalAnimatedStyle]}>
            <View style={styles.modalHeader}>
              <SFSymbol
                name="flame.fill"
                weight="medium"
                scale="large"
                color="#FF9500"
                size={32}
                style={styles.modalIcon}
              />
              <Text style={styles.modalTitle}>Streak Statistics</Text>
            </View>

            <View style={styles.statContainer}>
              <Text style={styles.statLabel}>Current Streak</Text>
              <Text style={styles.statValue}>{safeCurrentStreak} days</Text>
            </View>

            <View style={styles.statContainer}>
              <Text style={styles.statLabel}>Longest Streak</Text>
              <Text style={styles.statValue}>{safeLongestStreak} days</Text>
            </View>

            <View style={styles.statContainer}>
              <Text style={styles.statLabel}>Last Active</Text>
              <Text style={styles.statValue}>
                {lastActiveDate ? new Date(lastActiveDate).toLocaleDateString() : 'None'}
              </Text>
            </View>

            <View style={styles.divider} />

            <View style={styles.statContainer}>
              <Text style={styles.statLabel}>Total Active Days</Text>
              <Text style={styles.statValue}>{getStreakStats().totalDays}</Text>
            </View>

            <View style={styles.statContainer}>
              <Text style={styles.statLabel}>Avg Entries/Day</Text>
              <Text style={styles.statValue}>
                {getStreakStats().averageEntriesPerDay}
              </Text>
            </View>

            <View style={styles.statContainer}>
              <Text style={styles.statLabel}>30-Day Activity</Text>
              <Text style={styles.statValue}>
                {getStreakStats().activeDaysPercentage}%
              </Text>
            </View>

            <TouchableOpacity
              style={styles.closeButton}
              onPress={handleClose}
            >
              <Text style={styles.closeButtonText}>Close</Text>
            </TouchableOpacity>
          </Animated.View>
        </View>
      )}
    </>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: theme.spacing.s,
    right: theme.spacing.m,
    zIndex: theme.zIndex.header,
    alignSelf: 'flex-end',
  },
  streakContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: theme.spacing.s,
    borderRadius: theme.layout.borderRadius.large,
    ...theme.shadows.small,
    overflow: 'visible',
    marginTop: -theme.spacing.s,
  },
  icon: {
    marginRight: theme.spacing.xxs,
  },
  modalIcon: {
    marginRight: theme.spacing.xs,
  },
  streakText: {
    ...theme.typography.callout,
    fontSize: theme.typography.callout.fontSize + 2,
    color: '#000000',
  },
  modalOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: theme.colors.background.secondary.light,
    borderRadius: theme.layout.borderRadius.xl,
    padding: theme.spacing.l,
    width: '80%',
    maxWidth: 400,
    ...theme.shadows.medium,
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: theme.spacing.l,
  },
  modalTitle: {
    ...theme.typography.title2,
    color: theme.colors.text.primary.light,
    textAlign: 'center',
  },
  statContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginVertical: theme.spacing.xs,
  },
  statLabel: {
    ...theme.typography.callout,
    color: theme.colors.text.secondary.light,
  },
  statValue: {
    ...theme.typography.callout,
    fontWeight: '600',
    color: theme.colors.text.primary.light,
  },
  divider: {
    height: 1,
    backgroundColor: theme.colors.background.tertiary.light,
    marginVertical: theme.spacing.m,
  },
  closeButton: {
    backgroundColor: theme.colors.primary.light,
    padding: theme.spacing.m,
    borderRadius: theme.layout.borderRadius.medium,
    marginTop: theme.spacing.l,
  },
  closeButtonText: {
    ...theme.typography.button2,
    color: theme.colors.text.primary.dark,
    textAlign: 'center',
  },
  glowEffect: {
    position: 'absolute',
    top: -10,
    left: -10,
    right: -10,
    bottom: -10,
    backgroundColor: theme.colors.primary.light,
    borderRadius: theme.layout.borderRadius.xl,
    opacity: 0.2,
  },
});

export default StreakCard;