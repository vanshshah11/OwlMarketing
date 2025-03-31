import React, { useState, useCallback, useEffect } from 'react';
import { View, Text, StyleSheet, Pressable } from 'react-native';
import Tooltip from '../Components/ToolTip';
import ProgressCircle from './ProgressCircle';
import theme from '../styles/theme';
import PropTypes from 'prop-types';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withSequence,
  withDelay
} from 'react-native-reanimated';

const logger = {
  warn: (...args) => {
    if (__DEV__) {
      console.warn('[MacroCard]', ...args);
    }
  }
};

const FrostedGlassView = ({ style, children }) => {
  const scale = useSharedValue(1);
  const opacity = useSharedValue(1);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
    opacity: opacity.value,
  }));

  const handlePressIn = () => {
    scale.value = withSpring(0.95, {
      damping: 15,
      stiffness: 400,
    });
  };

  const handlePressOut = () => {
    scale.value = withSpring(1, {
      damping: 15,
      stiffness: 400,
    });
  };

  return (
    <Pressable onPressIn={handlePressIn} onPressOut={handlePressOut}>
      <Animated.View style={[styles.frostedGlass, style, animatedStyle]}>
        {children}
      </Animated.View>
    </Pressable>
  );
};

const MacroCard = React.memo(function MacroCard({
  title,
  color = theme.colors.macro.protein,
  remaining,
  goal
}) {
  const consumed = Math.max(0, goal - remaining);
  const isCompleted = remaining <= 0;
  const progress = useSharedValue(0);
  const textScale = useSharedValue(1);

  // Helper function to determine type based on title
  const getMacroType = (title) => {
    const titleLower = title.toLowerCase();
    if (titleLower.includes('protein')) return 'protein';
    if (titleLower.includes('carbs')) return 'carbs';
    if (titleLower.includes('fat')) return 'fat';
    return 'calories';
  };

  useEffect(() => {
    // Animate progress on mount and when values change
    progress.value = withDelay(
      300,
      withSpring(consumed / goal, {
        damping: 15,
        stiffness: 100,
      })
    );

    // Pulse animation when completed
    if (isCompleted) {
      textScale.value = withSequence(
        withSpring(1.1, { damping: 10, stiffness: 200 }),
        withSpring(1, { damping: 10, stiffness: 200 })
      );
    }
  }, [consumed, goal, isCompleted]);

  const animatedTextStyle = useAnimatedStyle(() => ({
    transform: [{ scale: textScale.value }],
  }));

  return (
    <Tooltip
      content={
        <View style={styles.tooltipContainer}>
          <Text style={styles.tooltipText}>
            {`${Math.round(consumed)}g consumed of ${goal}g goal`}
          </Text>
        </View>
      }
    >
      <FrostedGlassView style={styles.macroCard}>
        <View style={styles.contentContainer}>
          <Animated.View style={[styles.textContainer, animatedTextStyle]}>
            <Text style={styles.macroValue}>{`${Math.round(remaining)}g`}</Text>
            <Text style={styles.macroTitle}>{title}</Text>
          </Animated.View>
          <View style={styles.progressContainer}>
            <ProgressCircle
              consumed={isCompleted ? goal : consumed}
              goal={goal}
              size={40}
              strokeWidth={3}
              duration={1000}
              color={color}
              backgroundColor="#E5E5E5"
              style={styles.progressCircle}
              type={getMacroType(title)}
            />
          </View>
        </View>
      </FrostedGlassView>
    </Tooltip>
  );
});

const styles = StyleSheet.create({
  frostedGlass: {
    backgroundColor: theme.colors.background.frostedGlass,
    borderRadius: theme.layout.borderRadius.medium,
    overflow: 'hidden',
    ...theme.shadows.small,
  },
  macroCard: {
    padding: theme.spacing.m,
    alignItems: 'center',
    backgroundColor: theme.colors.background.secondary.light,
    flex: 1,
    marginHorizontal: theme.spacing.xs,
    borderRadius: theme.layout.borderRadius.xl,
    ...theme.shadows.small,
  },
  contentContainer: {
    width: '100%',
    alignItems: 'center',
  },
  textContainer: {
    alignItems: 'center',
    marginBottom: theme.spacing.xs,
  },
  macroValue: {
    ...theme.typography.headline,
    marginBottom: theme.spacing.xxs,
    color: theme.colors.text.primary.light,
    textAlign: 'center',
  },
  macroTitle: {
    ...theme.typography.footnote,
    color: theme.colors.text.secondary.light,
  },
  progressContainer: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  progressCircle: {
    marginTop: theme.spacing.xs,
  },
  tooltipContainer: {
    padding: theme.spacing.xs,
    borderRadius: theme.layout.borderRadius.small,
  },
  tooltipText: {
    ...theme.typography.callout,
    color: theme.colors.text.primary.dark,
  },
});

MacroCard.propTypes = {
  title: PropTypes.string.isRequired,
  color: PropTypes.string,
  remaining: PropTypes.number.isRequired,
  goal: PropTypes.number.isRequired,
};

export default MacroCard;
