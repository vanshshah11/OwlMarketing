import React, { useState, useCallback, useRef, useEffect, useMemo } from 'react';
import {
  View,
  TouchableOpacity,
  StyleSheet,
  Platform,
  Animated,
  PanResponder,
  Dimensions,
  Modal,
  TouchableWithoutFeedback,
  Pressable,
  Text,
} from 'react-native';
import { addDays, subDays, differenceInDays } from 'date-fns';
import DateTimePicker from '@react-native-community/datetimepicker';
import { SFSymbol } from 'react-native-sfsymbols';
import ReactNativeHapticFeedback from 'react-native-haptic-feedback';
import { BlurView } from '@react-native-community/blur';
import { 
  formatLocalDate, 
  isLocalSameDay, 
  isLocalToday,
  getLocalDate,
  MemoizedDateText 
} from './timezone';
import theme from '../styles/theme';

// Constants moved outside component to prevent recreation
const DATE_BUTTON_SIZE = theme.layout.buttonHeight * 0.8;
const VISIBLE_DATES = 7;
const MIDDLE_INDEX = Math.floor(VISIBLE_DATES / 2);
const SCREEN_WIDTH = Dimensions.get('window').width;
const SWIPE_THRESHOLD = SCREEN_WIDTH / 4;

const hapticOptions = {
  enableVibrateFallback: true,
  ignoreAndroidSystemSettings: false,
};

// Move generateDatesArray outside the component
const generateDatesArray = (centerDate) => {
  const dates = [];
  for (let i = -MIDDLE_INDEX; i <= MIDDLE_INDEX; i++) {
    dates.push(getLocalDate(addDays(centerDate, i)));
  }
  return dates;
};

// Memoized date button component
const DateButton = React.memo(({ 
  date, 
  selectedDate, 
  isDateValid, 
  handleDatePress, 
  animations,
  isDarkMode,
  hideWeekdays,
  customDateStyle 
}) => (
  <TouchableOpacity
    style={[
      styles.dateButton,
      isLocalSameDay(date, selectedDate) && styles.selectedDate,
      isLocalToday(date) && styles.todayDate,
      !isDateValid(date) && styles.disabledDate,
      customDateStyle?.(date),
      {
        width: DATE_BUTTON_SIZE,
        height: DATE_BUTTON_SIZE,
        backgroundColor: isLocalSameDay(date, selectedDate)
          ? isDarkMode ? theme.colors.primary.dark : theme.colors.primary.light
          : 'transparent',
      },
    ]}
    onPress={() => handleDatePress(date)}
    disabled={!isDateValid(date)}
    activeOpacity={0.7}
  >
    <Animated.View style={[styles.dateContent, {
      opacity: animations.opacity,
      transform: [
        { scale: isLocalSameDay(date, selectedDate) ? animations.scale : 1 },
        {
          translateX: animations.slide.interpolate({
            inputRange: [-SCREEN_WIDTH, 0, SCREEN_WIDTH],
            outputRange: [-DATE_BUTTON_SIZE, 0, DATE_BUTTON_SIZE],
            extrapolate: 'clamp',
          }),
        },
      ],
    }]}>
      {!hideWeekdays && (
        <MemoizedDateText 
          date={date}
          formatString="EEEEE"
          style={[
            styles.dayText, 
            isLocalSameDay(date, selectedDate) && styles.selectedText
          ]}
        />
      )}
      <MemoizedDateText 
        date={date}
        formatString="d"
        style={[
          styles.dateText,
          isLocalSameDay(date, selectedDate) && styles.selectedText
        ]}
      />
    </Animated.View>
  </TouchableOpacity>
));

// Memoized navigation button component
const NavButton = React.memo(({ direction, onPress, isDarkMode }) => (
  <TouchableOpacity
    style={styles.navButton}
    onPress={onPress}
  >
    <SFSymbol
      name={`chevron.${direction}`}
      size={theme.layout.iconSize.small}
      color={isDarkMode ? theme.colors.text.primary.dark : theme.colors.text.primary.light}
      style={{ backgroundColor: 'transparent' }}
    />
  </TouchableOpacity>
));

const DateSelector = ({ 
  selectedDate, 
  onDateChange, 
  isDarkMode = false,
  compact = false,
  minDate,
  maxDate,
  disabledDates = [],
  onSwipeLeft,
  onSwipeRight,
  customDateStyle,
  hideWeekdays = false,
}) => {
  // Validate props early
  if (!selectedDate || !onDateChange) {
    console.error('DateSelector: selectedDate and onDateChange are required props');
    return null;
  }
  const [visibleDates, setVisibleDates] = useState(() => 
    generateDatesArray(selectedDate)
  );
  const [isDatePickerVisible, setDatePickerVisibility] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);
  const [error, setError] = useState(null);

  // Refs for animations
  const animations = useMemo(() => ({
    slide: new Animated.Value(0),
    scale: new Animated.Value(1),
    opacity: new Animated.Value(1),
    modal: new Animated.Value(0),
    overlay: new Animated.Value(0),
  }), []);

  const isDateValid = useCallback((date) => {
    if (!date) return false;
    if (minDate && date < minDate) return false;
    if (maxDate && date > maxDate) return false;
    return !disabledDates.some(disabledDate => 
      disabledDate && isLocalSameDay(date, disabledDate)
    );
  }, [minDate, maxDate, disabledDates]);

  // Effect to update visible dates
  useEffect(() => {
    try {
      setVisibleDates(generateDatesArray(selectedDate));
    } catch (err) {
      setError('Failed to generate dates array');
      console.error('DateSelector: Error generating dates array:', err);
    }
  }, [selectedDate]);

  const showCalendarModal = useCallback(() => {
    setDatePickerVisibility(true);
    Animated.parallel([
      Animated.timing(animations.modal, {
        toValue: 1,
        duration: 300,
        useNativeDriver: true
      }),
      Animated.timing(animations.overlay, {
        toValue: 0.5,
        duration: 300,
        useNativeDriver: true
      })
    ]).start();
  }, [animations]);

  const hideCalendarModal = useCallback((newDate) => {
    Animated.parallel([
      Animated.timing(animations.modal, {
        toValue: 0,
        duration: 200,
        useNativeDriver: true
      }),
      Animated.timing(animations.overlay, {
        toValue: 0,
        duration: 200,
        useNativeDriver: true
      })
    ]).start(() => {
      setDatePickerVisibility(false);
      if (newDate) {
        onDateChange(newDate);
      }
    });
  }, [animations, onDateChange]);

  // Improved navigation to date handler with better animation
  const navigateToDate = useCallback((direction, isUserInteraction = false) => {
    if (isAnimating) return;
    setIsAnimating(true);
    
    const offset = direction === 'next' ? 1 : -1;
    const newDate = addDays(selectedDate, offset);

    if (!isDateValid(newDate)) {
      Animated.spring(animations.slide, {
        toValue: 0,
        useNativeDriver: true,
        friction: 8,
        tension: 50,
        restDisplacementThreshold: 0.01,
      }).start(() => setIsAnimating(false));
      return;
    }

    // Only trigger haptic feedback if it's a user interaction
    if (isUserInteraction) {
      ReactNativeHapticFeedback.trigger('impactLight', hapticOptions);
    }

    // Calculate the animation target value based on direction
    const slideTarget = direction === 'next' ? -SCREEN_WIDTH : SCREEN_WIDTH;

    Animated.parallel([
      Animated.timing(animations.slide, {
        toValue: slideTarget,
        duration: 300,
        useNativeDriver: true,
      }),
      Animated.sequence([
        Animated.timing(animations.scale, {
          toValue: 0.9,
          duration: 150,
          useNativeDriver: true,
        }),
        Animated.timing(animations.scale, {
          toValue: 1,
          duration: 150,
          useNativeDriver: true,
        }),
      ]),
    ]).start(() => {
      if (direction === 'next' && onSwipeLeft) {
        onSwipeLeft();
      } else if (direction === 'prev' && onSwipeRight) {
        onSwipeRight();
      }
      onDateChange(newDate);
      animations.slide.setValue(0);
      setIsAnimating(false);
    });
  }, [isAnimating, selectedDate, isDateValid, onDateChange, animations, onSwipeLeft, onSwipeRight]);

  // Enhanced pan responder for swipe gestures
  const panResponder = useMemo(() => PanResponder.create({
    onStartShouldSetPanResponder: () => true,
    onMoveShouldSetPanResponder: (_, gestureState) => 
      Math.abs(gestureState.dx) > 10 && Math.abs(gestureState.dy) < 20,
    onPanResponderGrant: () => {
      // Start of the swipe gesture
      animations.opacity.setValue(0.95);
    },
    onPanResponderMove: (_, gestureState) => {
      // Update animation while swiping
      animations.slide.setValue(gestureState.dx);
    },
    onPanResponderRelease: (_, gestureState) => {
      // Reset opacity when swipe ends
      animations.opacity.setValue(1);

      if (isAnimating) return;
      
      if (gestureState.dx > SWIPE_THRESHOLD) {
        navigateToDate('prev', true);
      } else if (gestureState.dx < -SWIPE_THRESHOLD) {
        navigateToDate('next', true);
      } else {
        // If the swipe wasn't far enough, spring back to center
        Animated.spring(animations.slide, {
          toValue: 0,
          useNativeDriver: true,
          tension: 50,
          friction: 7,
        }).start();
      }
    },
    onPanResponderTerminate: () => {
      animations.opacity.setValue(1);
      Animated.spring(animations.slide, {
        toValue: 0,
        useNativeDriver: true,
      }).start();
    }
  }), [isAnimating, navigateToDate, animations]);

  // Enhanced date press handler with animation
  const handleDatePress = useCallback((date) => {
    if (!isDateValid(date) || isAnimating || isLocalSameDay(date, selectedDate)) {
      // If it's the same date or invalid, just provide haptic feedback
      if (isLocalSameDay(date, selectedDate)) {
        ReactNativeHapticFeedback.trigger('impactLight', hapticOptions);
      }
      return;
    }

    setIsAnimating(true);
    ReactNativeHapticFeedback.trigger('impactLight', hapticOptions);
    
    // Calculate the difference in days
    const daysDiff = differenceInDays(date, selectedDate);
    const direction = daysDiff > 0 ? 'next' : 'prev';
    
    // Direction-based animation
    const slideValue = direction === 'next' ? -SCREEN_WIDTH : SCREEN_WIDTH;
    
    Animated.parallel([
      Animated.timing(animations.slide, {
        toValue: slideValue,
        duration: 300,
        useNativeDriver: true,
      }),
      Animated.sequence([
        Animated.timing(animations.scale, {
          toValue: 0.9,
          duration: 150,
          useNativeDriver: true,
        }),
        Animated.timing(animations.scale, {
          toValue: 1,
          duration: 150,
          useNativeDriver: true,
        }),
      ]),
    ]).start(() => {
      // Trigger the appropriate swipe callback
      if (direction === 'next' && onSwipeLeft) {
        onSwipeLeft();
      } else if (direction === 'prev' && onSwipeRight) {
        onSwipeRight();
      }
      
      onDateChange(date);
      animations.slide.setValue(0);
      setIsAnimating(false);
    });
  }, [isDateValid, isAnimating, selectedDate, onDateChange, animations, onSwipeLeft, onSwipeRight]);

  if (error) {
    return (
      <View style={styles.errorContainer}>
        <Text style={styles.errorText}>{error}</Text>
      </View>
    );
  }

  return (
    <View style={[
      styles.container,
      isDarkMode && { backgroundColor: theme.colors.background.primary.dark },
      compact && styles.compactContainer,
    ]}>
      <View style={styles.weekContainer} {...panResponder.panHandlers}>
        <BlurView
          style={[styles.blurOverlay, styles.leftBlur]}
          blurType={isDarkMode ? 'dark' : 'light'}
          blurAmount={10}
        >
          <TouchableOpacity
            style={styles.navButton}
            onPress={() => !isAnimating && navigateToDate('prev', true)}
          >
            <SFSymbol
              name="chevron.left"
              size={theme.layout.iconSize.small}
              color={isDarkMode ? theme.colors.text.primary.dark : theme.colors.text.primary.light}
              style={{ backgroundColor: 'transparent' }}
            />
          </TouchableOpacity>
        </BlurView>

        <View style={styles.datesContainer}>
          {visibleDates.map((date, index) => (
            <DateButton
              key={`date-${index}`}
              date={date}
              selectedDate={selectedDate}
              isDateValid={isDateValid}
              handleDatePress={handleDatePress}
              animations={animations}
              isDarkMode={isDarkMode}
              hideWeekdays={hideWeekdays}
              customDateStyle={customDateStyle}
            />
          ))}
        </View>

        <BlurView
          style={[styles.blurOverlay, styles.rightBlur]}
          blurType={isDarkMode ? 'dark' : 'light'}
          blurAmount={10}
        >
          <TouchableOpacity
            style={styles.navButton}
            onPress={() => !isAnimating && navigateToDate('next', true)}
          >
            <SFSymbol
              name="chevron.right"
              size={theme.layout.iconSize.small}
              color={isDarkMode ? theme.colors.text.primary.dark : theme.colors.text.primary.light}
              style={{ backgroundColor: 'transparent' }}
            />
          </TouchableOpacity>
        </BlurView>
      </View>

      <Modal
        visible={isDatePickerVisible}
        transparent
        animationType="none"
        onRequestClose={() => hideCalendarModal()}
      >
        <Pressable 
          style={styles.modalOverlay}
          onPress={() => hideCalendarModal()}
        >
          <Animated.View 
            style={[
              StyleSheet.absoluteFill,
              {
                backgroundColor: theme.colors.background.camera.overlay,
                opacity: animations.overlay
              }
            ]} 
          />
          <Animated.View
            style={[
              styles.calendarModal,
              {
                opacity: animations.modal,
                transform: [{
                  scale: animations.modal.interpolate({
                    inputRange: [0, 1],
                    outputRange: [0.9, 1]
                  })
                }]
              }
            ]}
          >
            <TouchableWithoutFeedback>
              <View>
                <DateTimePicker
                  value={selectedDate}
                  mode="date"
                  display={Platform.OS === 'ios' ? 'inline' : 'default'}
                  onChange={(_, date) => {
                    if (date) {
                      hideCalendarModal(date);
                    }
                  }}
                  minimumDate={minDate}
                  maximumDate={maxDate}
                />
              </View>
            </TouchableWithoutFeedback>
          </Animated.View>
        </Pressable>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: 'transparent',
    borderRadius: theme.layout.borderRadius.large,
    ...theme.mixins.padding.all(theme.spacing.m),
    ...theme.shadows.small,
    width: '100%',
  },
  compactContainer: {
    width: theme.layout.minContentWidth,
    ...theme.mixins.padding.all(theme.spacing.s),
  },
  weekContainer: {
    height: DATE_BUTTON_SIZE,
  },
  datesContainer: {
    ...theme.mixins.row,
    justifyContent: 'center',
    flex: 1,
  },
  blurOverlay: {
    position: 'absolute',
    top: 0,
    bottom: 0,
    width: theme.spacing.m,
    ...theme.mixins.center,
    zIndex: theme.zIndex.overlay,
    backgroundColor: 'transparent',
    overflow: 'hidden', 
    opacity: 0.4,
  },
  leftBlur: {
    left: 0,
    borderTopLeftRadius: theme.layout.borderRadius.large,
    borderBottomLeftRadius: theme.layout.borderRadius.large,
  },
  rightBlur: {
    right: 0,
    borderTopRightRadius: theme.layout.borderRadius.large,
    borderBottomRightRadius: theme.layout.borderRadius.large,
  },
  navButton: {
    padding: theme.spacing.xxs,
    backgroundColor: 'transparent',
    width: '100%',
    height: '100%',
    ...theme.mixins.center,
  },
  dateButton: {
    borderRadius: theme.layout.borderRadius.circular,
    ...theme.mixins.center,
  },
  dateContent: {
    alignItems: 'center',
  },
  dayText: {
    ...theme.typography.footnote,
    marginBottom: theme.spacing.xxxs,
    color: '#000000',
  },
  compactText: {
    ...theme.typography.callout,
    marginBottom: theme.spacing.xxxs,
    color: theme.colors.text.primary.dark,
  },
  dateText: {
    fontWeight: '500',
    color: '#000000',
  },
  selectedDate: {
    opacity: 1,
  },
  selectedText: {
    color: theme.colors.text.primary.dark,
  },
  todayDate: {
    borderWidth: 1,
    borderColor: theme.colors.primary.light,
  },
  disabledDate: {
    opacity: 0.4,
  },
  errorContainer: {
    padding: theme.spacing.m,
    backgroundColor: theme.colors.background.primary.light,
    borderRadius: theme.layout.borderRadius.medium,
  },
  errorText: {
    ...theme.typography.body,
    color: theme.colors.text.error,
  },
  modalOverlay: {
    flex: 1,
    ...theme.mixins.center,
  },
  calendarModal: {
    backgroundColor: theme.colors.background.secondary.light,
    borderRadius: theme.layout.borderRadius.xl,
    ...theme.mixins.padding.all(theme.spacing.m),
    ...theme.shadows.large,
    maxWidth: '90%',
    width: 350,
    zIndex: theme.zIndex.modal,
  },
});


export default DateSelector;
