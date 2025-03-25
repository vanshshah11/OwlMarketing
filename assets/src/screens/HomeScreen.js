// in homescreen, i want to add a lottie animation when there is ListEmptyComponent={<Text style={styles.noMealText}>No meals logged today</Text>}

// and i want to adjust how it's shown. could you make the code such that i can adjust the size, or maybe revolve it as i want to? initialize with zero and then i will make adjustments acorrdingly.
// /Users/vanshshah/Desktop/New_app/5th_WellAI/WellAI/src/screens/HomeScreen.js
import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import {
  View,
  Text,
  SafeAreaView,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  Dimensions,
  AppState,
  Animated,
  ActivityIndicator,
  StyleSheet,
  Pressable
} from 'react-native';
import { 
  collection, 
  query, 
  where, 
  onSnapshot,
  doc, 
  getDoc, 
  updateDoc
} from 'firebase/firestore';
import { auth, db, fetchUserData } from '../utils/firebase';
import { onAuthStateChanged } from 'firebase/auth';
import { useAccessibilityInfo } from '@react-native-community/hooks';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import LinearGradient from 'react-native-linear-gradient';
import { BlurView } from '@react-native-community/blur';
import Logger from '../utils/logger';
import LottieView from 'lottie-react-native';
import { getLocalDate, getLocalStartOfDay, getLocalEndOfDay } from '../homecomponents/timezone';

import StreakCard from '../homecomponents/StreakCard';
import DateSelector from '../homecomponents/DateSelector';
import ProgressCircle from '../homecomponents/ProgressCircle';
import MacroCard from '../homecomponents/MacroCard';
import RecentlyEatenCard from '../homecomponents/RecentlyEatenCard';
import styles from '../styles/HomeScreen.styles';
import theme from '../styles/theme';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const logger = new Logger('HomeScreen');

const FrostedGlassView = React.memo(({ style, children }) => (
  <View style={[styles.frostedGlass, style]}>
    {children}
  </View>
));

const HomeScreen = () => {
  // Refs
  const isMounted = useRef(true);
  const [streakData, setStreakData] = useState({
    currentStreak: 0,
    longestStreak: 0,
    lastActiveDate: null,
    streakDates: []
  });
  const dataLoadTimestamp = useRef(Date.now());
  const realtimeUnsubscribe = useRef(null);

  // State
  const [user, setUser] = useState(null);
  const [userData, setUserData] = useState(null);
  const [selectedDate, setSelectedDate] = useState(getLocalDate());

  const [nutritionData, setNutritionData] = useState({
    caloriesLeft: 0,
    consumed: {
      calories: 0,
      protein: 0,
      carbs: 0,
      fat: 0
    },
    remaining: {
      protein: 0,
      carbs: 0,
      fat: 0
    }
  });
  const [recentMeals, setRecentMeals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [isOffline, setIsOffline] = useState(false);
  const recentMealAnimations = useRef([]).current;
  const [animatedRecentMeals, setAnimatedRecentMeals] = useState([]);

  // UI state and hooks
  const dateOffset = useRef(new Animated.Value(0)).current;
  const { isScreenReaderEnabled } = useAccessibilityInfo();
  const insets = useSafeAreaInsets();

  // Load user data
  const loadUserData = useCallback(async (userId) => {
    logger.info('Loading user data');
    try {
      const data = await fetchUserData(userId);
      if (!data) throw new Error('No user data found');
      
      logger.info('Fetched user data:', data);
      
      if (isMounted.current && JSON.stringify(data) !== JSON.stringify(userData)) {
        setUserData(data);
        
        // Also update streak data to ensure it's in sync
        setStreakData({
          currentStreak: Number(data.currentStreak) || 0,
          longestStreak: Number(data.longestStreak) || 0,
          lastActiveDate: data.lastActiveDate || null,
          streakDates: Array.isArray(data.streakDates) ? data.streakDates : []
        });
        
        logger.info('User data updated');
      }
    } catch (error) {
      logger.error('Failed to load user data:', error);
      if (isMounted.current) {
        setError(`Failed to load user profile: ${error.message}`);
      }
    } finally {
      if (isMounted.current) {
        setLoading(false);
      }
    }
  }, [userData]);

  const calculateAndUpdateNutrition = useCallback((entries) => {
    if (!userData) return;
    
    // Always call updateStreak, even with empty entries
    updateStreak(entries);
    
    const goals = {
      calories: Number(userData.dailyCalorieGoal) || 2500,
      protein: Number(userData.dailyProteinGoal) || 180,
      carbs: Number(userData.dailyCarbsGoal) || 300,
      fat: Number(userData.dailyFatGoal) || 80
    };

    // Filter out temporary/pending entries
    const validEntries = entries.filter(entry => 
      !entry.id.startsWith('temp_') || entry.syncStatus === 'synced'
    );
    
    const consumed = validEntries.reduce((acc, entry) => ({
      calories: acc.calories + Number(entry.calories || 0),
      protein: acc.protein + (entry.nutrients?.protein || 0),
      carbs: acc.carbs + (entry.nutrients?.carbs || 0),
      fat: acc.fat + (entry.nutrients?.fat || 0)
    }), { calories: 0, protein: 0, carbs: 0, fat: 0 });

    const remaining = {
      calories: Math.max(0, goals.calories - consumed.calories),
      protein: Math.max(0, goals.protein - consumed.protein),
      carbs: Math.max(0, goals.carbs - consumed.carbs),
      fat: Math.max(0, goals.fat - consumed.fat)
    };

    setNutritionData({
      caloriesLeft: remaining.calories,
      consumed,
      remaining
    });

    if (validEntries?.length > 0) {
      const sortedEntries = validEntries.map(entry => ({
        id: entry.id,
        name: entry.name || 'Unknown Food',
        calories: Number(entry.calories || 0),
        imageUrl: entry.imageUrl,
        timestamp: entry.createdAt || new Date(),
        nutrients: {
          protein: Number(entry.nutrients?.protein || 0),
          carbs: Number(entry.nutrients?.carbs || 0),
          fat: Number(entry.nutrients?.fat || 0),
          fiber: Number(entry.nutrients?.fiber || 0)
        }
      })).sort((a, b) => {
        const dateA = a.timestamp?.toDate?.() || a.timestamp;
        const dateB = b.timestamp?.toDate?.() || b.timestamp;
        return dateB - dateA;
      });
      
      setRecentMeals(sortedEntries);
    } else {
      setRecentMeals([]);
    }
  }, [userData, updateStreak]);

  const setupRealtimeUpdates = useCallback(() => {
    if (!user?.uid || !userData) return;

    const startOfDay = getLocalStartOfDay(selectedDate);
    const endOfDay = getLocalEndOfDay(selectedDate);

    logger.info('Setting up realtime updates', {
      userId: user.uid,
      date: selectedDate,
      startOfDay,
      endOfDay
    });

    if (realtimeUnsubscribe.current) {
      realtimeUnsubscribe.current();
    }

    const calorieEntriesRef = collection(db, 'calories');
    const q = query(
      calorieEntriesRef,
      where('userId', '==', user.uid),
      where('dateKey', '==', selectedDate.toISOString().split('T')[0])
    );

    logger.info('Firestore Query Details', {
      userId: user.uid,
      dateKey: selectedDate.toISOString().split('T')[0]
    });

    realtimeUnsubscribe.current = onSnapshot(q, 
      (snapshot) => {
        const entries = snapshot.docs.map(doc => ({
          id: doc.id,
          ...doc.data()
        }));
        
        logger.info('Received entries from Firebase', {
          entriesCount: entries.length,
          entries
        });
        
        calculateAndUpdateNutrition(entries);
      },
      (error) => {
        logger.error('Real-time update error', error);
        setError(`Failed to get real-time updates: ${error.message}`);
      }
    );

    return realtimeUnsubscribe.current;
  }, [user?.uid, userData, selectedDate]);

  useEffect(() => {
    const unsubscribeAuth = onAuthStateChanged(auth, async (currentUser) => {
      if (!isMounted.current) return;
      
      if (currentUser) {
        logger.info('User authenticated:', { userId: currentUser.uid });
        setUser(currentUser);
        await loadUserData(currentUser.uid);
      } else {
        logger.warn('No user authenticated');
        setUser(null);
        setLoading(false);
      }
    });

    return () => {
      logger.info('Cleaning up auth subscription');
      isMounted.current = false;
      unsubscribeAuth();
    };
  }, []);

  // Initialize real-time updates
  useEffect(() => {
    if (!user?.uid || !userData) return;

    const unsubscribe = setupRealtimeUpdates();
    return () => {
      if (unsubscribe) unsubscribe();
    };
  }, [user?.uid, userData, selectedDate]);

  // AppState handler
  useEffect(() => {
    const subscription = AppState.addEventListener('change', nextAppState => {
      if (nextAppState === 'active' && user?.uid && userData) {
        logger.info('App came to foreground, refreshing data');
        setupRealtimeUpdates();
      }
    });

    return () => {
      subscription.remove();
    };
  }, [user?.uid, userData]);

  // Animation effect for recently eaten items
  useEffect(() => {
    // Reset animations when meals change
    recentMealAnimations.length = 0;
    
    // Create a new animation value for each meal
    const animations = recentMeals.map(() => ({
      opacity: new Animated.Value(0),
      translateY: new Animated.Value(50)
    }));

    // Store the animations
    animations.forEach((anim) => recentMealAnimations.push(anim));
    setAnimatedRecentMeals(recentMeals);

    // Staggered animation
    Animated.stagger(100, 
      animations.map((anim) => 
        Animated.parallel([
          Animated.timing(anim.opacity, {
            toValue: 1,
            duration: 500,
            useNativeDriver: true
          }),
          Animated.timing(anim.translateY, {
            toValue: 0,
            duration: 500,
            useNativeDriver: true
          })
        ])
      )
    ).start();
  }, [recentMeals]);

  // Date change handler
  const handleDateChange = useCallback((newDate) => {
    logger.info('Date changed:', newDate);
    setSelectedDate(getLocalDate(newDate)); // Ensure we're using local date
    setupRealtimeUpdates();
  }, [setupRealtimeUpdates]);

  // Refresh handler
  const handleRefresh = useCallback(async () => {
    logger.info('Starting manual refresh');
    setRefreshing(true);
    await setupRealtimeUpdates();
    setRefreshing(false);
    logger.info('Manual refresh completed');
  }, [setupRealtimeUpdates]);

  const updateStreak = useCallback(async (entries) => {
    logger.info('Update Streak Called', {
      entriesCount: entries.length,
      userId: user?.uid,
      today: getLocalDate().toISOString().split('T')[0],
      userData: {
        currentStreak: userData?.currentStreak,
        longestStreak: userData?.longestStreak,
        lastActiveDate: userData?.lastActiveDate
      }
    });
  
    if (!user?.uid) {
      logger.warn('No user ID found, cannot update streak');
      return;
    }
  
    try {
      const userRef = doc(db, 'users', user.uid);
      const today = getLocalDate().toISOString().split('T')[0];
      
      // Always fetch the latest user data to avoid conflicts
      const userDoc = await getDoc(userRef);
      if (!userDoc.exists()) {
        logger.warn('User document does not exist, cannot update streak');
        return;
      }
      
      const userData = userDoc.data();
      
      let { 
        currentStreak = 0, 
        longestStreak = 0, 
        lastActiveDate = null, 
        streakDates = [] 
      } = userData;
      
      // Convert lastActiveDate to YYYY-MM-DD format for comparison
      const lastActive = lastActiveDate 
        ? new Date(lastActiveDate).toISOString().split('T')[0] 
        : null;
      
      // Calculate yesterday's date
      const yesterday = new Date(getLocalDate());
      yesterday.setDate(yesterday.getDate() - 1);
      const yesterdayStr = yesterday.toISOString().split('T')[0];
      
      // Calculate two days ago for edge cases
      const twoDaysAgo = new Date(getLocalDate());
      twoDaysAgo.setDate(twoDaysAgo.getDate() - 2);
      const twoDaysAgoStr = twoDaysAgo.toISOString().split('T')[0];
      
      logger.info('Streak Calculation Details', {
        lastActive,
        yesterdayStr,
        twoDaysAgoStr,
        currentStreak,
        longestStreak
      });
      
      // Check if we have entries for today
      const hasEntriesForToday = entries.length > 0;
  
      // If already logged today, update entry count but preserve streak
      if (lastActive === today) {
        logger.info('Already logged today, updating entry count');
        
        // Update streak dates array for today's entries
        const existingDateIndex = streakDates.findIndex(d => d.date === today);
        if (existingDateIndex >= 0) {
          streakDates[existingDateIndex].entries = entries.length;
        } else if (hasEntriesForToday) {
          streakDates.push({ date: today, entries: entries.length });
        }
        
        // Keep only last 30 days
        streakDates = streakDates
          .sort((a, b) => new Date(b.date) - new Date(a.date))
          .slice(0, 30);
        
        // Update Firestore with just the updated streak dates
        await updateDoc(userRef, { streakDates });
        
        // Update local state
        setStreakData(prevState => ({
          ...prevState,
          streakDates
        }));
        
        return;
      }
  
      // Logic for maintaining or incrementing streak
      if (lastActive === yesterdayStr) {
        // Logged yesterday, increment streak only if we have entries today
        if (hasEntriesForToday) {
          currentStreak++;
          logger.info(`Streak incremented to ${currentStreak}`);
        }
      } else if (lastActive === twoDaysAgoStr && !hasEntriesForToday) {
        // Edge case: User logged two days ago, but has no entries today
        // Keep the streak as is, since they're just viewing but not logging
        logger.info('Viewing with no entries, preserving streak');
      } else if (hasEntriesForToday) {
        // Streak broken or first time logging, but we have entries today
        currentStreak = 1;
        logger.info('Streak reset or started with entries today');
      } else {
        // No entries today and streak was already broken
        // Keep streak at 0 until they log something
        currentStreak = 0;
        logger.info('No active streak, waiting for entries');
      }
      
      // Update longest streak if needed
      longestStreak = Math.max(currentStreak, longestStreak);
      
      // Update streak dates array
      const existingDateIndex = streakDates.findIndex(d => d.date === today);
      if (existingDateIndex >= 0) {
        streakDates[existingDateIndex].entries = entries.length;
      } else if (hasEntriesForToday) {
        streakDates.push({ date: today, entries: entries.length });
      }
      
      // Keep only last 30 days
      streakDates = streakDates
        .sort((a, b) => new Date(b.date) - new Date(a.date))
        .slice(0, 30);
      
      // Update Firestore only if we have made changes
      await updateDoc(userRef, {
        currentStreak,
        longestStreak,
        lastActiveDate: hasEntriesForToday ? today : lastActiveDate,
        streakDates
      });
      
      // Update local state
      setStreakData({
        currentStreak,
        longestStreak,
        lastActiveDate: hasEntriesForToday ? today : lastActiveDate,
        streakDates
      });
  
      logger.info('Streak Update Completed', {
        newCurrentStreak: currentStreak,
        newLongestStreak: longestStreak,
        hasEntriesForToday
      });
    } catch (error) {
      logger.error('Failed to update streak', error);
    }
  }, [user?.uid, userData, streakData]);

  const renderAnimatedItem = useCallback(({ item, index }) => {
    if (index >= animatedRecentMeals.length) return null;
  
    const animationValues = recentMealAnimations[index];
    
    return (
      <Animated.View 
        style={{
          opacity: animationValues.opacity,
          transform: [{ 
            translateY: animationValues.translateY 
          }]
        }}
      >
        <RecentlyEatenCard item={item} />
      </Animated.View>
    );
  }, [animatedRecentMeals, recentMealAnimations]);

  // Memoized header component
  const HeaderComponent = React.memo(() => (
    <>
    
      <Text style={[styles.appTitle, { marginTop: theme.spacing.xs }]}>Optimal AI</Text>
      <StreakCard
        currentStreak={Number(streakData?.currentStreak) || 0}
        longestStreak={Number(streakData?.longestStreak) || 0}
        lastActiveDate={streakData?.lastActiveDate || null}
        streakDates={Array.isArray(streakData?.streakDates) ? streakData.streakDates : []}
      />
      <DateSelector 
        selectedDate={selectedDate}
        onDateChange={handleDateChange}
        isDarkMode={false}
        compact={false}
        minDate={new Date('2024-01-01')}
        maxDate={new Date('2024-12-31')}
        onSwipeLeft={() => {
          logger.info('Swiped left');
        }}
        onSwipeRight={() => {
          logger.info('Swiped right');
        }}
      />
      <FrostedGlassView style={styles.mainCard}>
        <View style={[styles.caloriesContainer, { backgroundColor: 'white' }]}>
          <Text style={styles.caloriesLeft}>{nutritionData.caloriesLeft}</Text>
          <Text style={styles.caloriesLabel}>Calories left</Text>
        </View>
        <ProgressCircle  
          consumed={nutritionData.consumed.calories}
          goal={Number(userData?.dailyCalorieGoal)}
          color="#FF9500"
          size={60}
          strokeWidth={4}
          duration={1500}
          backgroundColor="#E5E5E5"
          style={styles.progressCircle}
        />
      </FrostedGlassView>

      <View style={[styles.macroContainer, { backgroundColor: 'transparent' }]}>
        <MacroCard 
          title="Protein left" 
          color="#FF3B30"
          consumed={nutritionData.consumed.protein}
          remaining={nutritionData.remaining.protein}
          goal={Number(userData?.dailyProteinGoal) || 180}

        />
        <MacroCard 
          title="Carbs left" 
          color="#FF9500"
          consumed={nutritionData.consumed.carbs}
          remaining={nutritionData.remaining.carbs}
          goal={Number(userData?.dailyCarbsGoal) || 300}
        />
        <MacroCard 
          title="Fat left" 
          color="#007AFF"
          consumed={nutritionData.consumed.fat}
          remaining={nutritionData.remaining.fat}
          goal={Number(userData?.dailyFatGoal) || 80}
        />
      </View>

      <Text style={styles.recentlyEatenTitle}>Recently eaten</Text>
    </>
  ));

  // Error state
  if (error) {
    logger.error('Rendering error state:', error);
    return (
      <View style={styles.errorContainer}>
        <Text style={styles.errorText}>{error}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={setupRealtimeUpdates}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // Authentication state
  if (!user) {
    return (
      <View style={styles.signInContainer}>
        <Text style={styles.signInText}>Please sign in to view your data</Text>
      </View>
    );
  }

  // Loading state
  if (loading) {
    logger.info('Rendering loading state');
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  // Main render
  logger.info('Rendering main screen');
  return (
    <SafeAreaView style={styles.container}>
      <BlurView
        style={StyleSheet.absoluteFill}
        blurType="light"
        blurAmount={20}
        reducedTransparencyFallbackColor="white"
      />
      
      <View style={styles.scrollView}>
        <LinearGradient
          colors={['rgba(250, 250, 250, 0.8)', 'rgba(255, 255, 255, 0.8)']}
          style={{ flex: 1 }}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          locations={[0.3, 0.7]}
        >
          <FlatList
            data={animatedRecentMeals}
            renderItem={renderAnimatedItem}
            keyExtractor={(item) => item.id}
            ListHeaderComponent={HeaderComponent}
            ListEmptyComponent={
              <View style={styles.emptyStateContainer}>
                <Text style={styles.noMealText}>No meals logged today</Text>
                {/* <LottieView
                  source={require('../../assets/animations/arrow.json')}
                  style={styles.lottieArrow}
                  autoPlay
                  loop
                  // To control animation speed (1 is normal speed)
                  speed={1}
                  // Initialize with size 0 then adjust as needed
                  resizeMode="contain"
                /> */}
              </View>
            } 
            contentContainerStyle={{
              paddingTop: insets.top,
            }}
            refreshControl={
              <RefreshControl
                refreshing={refreshing}
                onRefresh={handleRefresh}
                tintColor="#000000"
              />
            }
          />
        </LinearGradient>
      </View>
    </SafeAreaView>
  );
};

export default React.memo(HomeScreen);