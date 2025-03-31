import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { 
  View, Text, StyleSheet, Dimensions, TouchableOpacity, 
  SafeAreaView, ScrollView, RefreshControl, Animated
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { auth, db } from '../utils/firebase';
import { fetchUserData, fetchStatsForAnalytics } from '../utils/firebase';
import { 
  collection, query, where, getDocs,
  orderBy
} from 'firebase/firestore';
import theme from '../styles/theme';
import LoadingSpinner from '../Components/LoadingSpinner';
import ErrorMessage from '../Components/ErrorMessage';
import OverallProgressChart from '../analyticscomponents/OverallProgressChart_ProgressSummary';
import ProgressSummary from '../analyticscomponents/ProgressSummary';

// Screen dimensions for responsive design
const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

// Responsive sizing helpers
const getResponsiveWidth = (percentage) => SCREEN_WIDTH * (percentage / 100);
const getResponsiveHeight = (percentage) => SCREEN_HEIGHT * (percentage / 100);
const getResponsiveButtonWidth = () => {
  const baseWidth = 100;
  const scaleFactor = Math.min(SCREEN_WIDTH / 375, 1.3);
  return Math.round(baseWidth * scaleFactor);
};

const logger = {
  debug: (message, data = {}) => {
    if (__DEV__) {
      console.debug(`[AnalyticsScreen] ${message}`, { timestamp: new Date().toISOString(), ...data });
    }
  },
  info: (message, data = {}) => {
    console.info(`[AnalyticsScreen] ${message}`, { timestamp: new Date().toISOString(), ...data });
  },
  warn: (message, data = {}) => {
    console.warn(`[AnalyticsScreen] ${message}`, { timestamp: new Date().toISOString(), ...data });
  },
  error: (message, error) => {
    console.error(`[AnalyticsScreen] ${message}`, { 
      timestamp: new Date().toISOString(),
      error: error?.message || error,
      stack: error?.stack
    });
  },
  performance: (message, startTime) => {
    const duration = Date.now() - startTime;
    console.info(`[AnalyticsScreen] 🕒 ${message}`, { 
      timestamp: new Date().toISOString(),
      duration: `${duration}ms`
    });
  },
  lifecycle: (message, data = {}) => {
    if (__DEV__) {
      console.log(`[AnalyticsScreen] 🔄 ${message}`, {
        timestamp: new Date().toISOString(),
        ...data
      });
    }
  },
  data: (message, data = {}) => {  // Added missing data method
    if (__DEV__) {
      console.log(`[AnalyticsScreen] 📊 ${message}`, {
        timestamp: new Date().toISOString(),
        ...data
      });
    }
  },
  interaction: (message, data = {}) => {  // Added interaction method for completeness
    console.log(`[AnalyticsScreen] 👆 ${message}`, {
      timestamp: new Date().toISOString(),
      ...data
    });
  }
};

// Memoized Header component
const Header = React.memo(() => (
  <View style={styles.header}>
    <Text style={[styles.title, { fontSize: theme.typography.title1.fontSize }]}>
      Analytics
    </Text>
  </View>
));

// Memoized TimeFrameSelector component
const TimeFrameSelector = React.memo(({ timeFrame, onTimeFrameChange }) => {
  const slideAnim = useMemo(() => new Animated.Value(0), []);
  const frames = ['day', 'week', 'month'];
  const buttonWidth = getResponsiveButtonWidth();
  
  useEffect(() => {
    const toValue = frames.indexOf(timeFrame);
    Animated.spring(slideAnim, {
      toValue,
      speed: 12,
      bounciness: 0,
      useNativeDriver: true,
    }).start();
  }, [timeFrame, slideAnim]);

  return (
    <View style={[styles.timeFrameSelector, { height: getResponsiveHeight(5) }]}>
      <Animated.View
        style={[
          styles.slider,
          {
            width: buttonWidth,
            transform: [{
              translateX: slideAnim.interpolate({
                inputRange: [0, 1, 2],
                outputRange: [0, buttonWidth, buttonWidth * 2]
              })
            }]
          }
        ]}
      />
      {frames.map((frame) => (
        <TouchableOpacity
          key={frame}
          style={[styles.timeFrameButton, { width: buttonWidth }]}
          onPress={() => onTimeFrameChange(frame)}
        >
          <Text style={[
            styles.timeFrameText,
            timeFrame === frame && styles.activeTimeFrameText
          ]}>
            {frame.charAt(0).toUpperCase() + frame.slice(1)}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );
});

// Main AnalyticsScreen component
const AnalyticsScreen = () => {
  const [statsData, setStatsData] = useState(null);
  const [timeFrame, setTimeFrame] = useState('week');
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastFetch, setLastFetch] = useState(null);
  const [userData, setUserData] = useState(null);
  const contentOpacity = useMemo(() => new Animated.Value(1), []);
  const timeFrameScale = useMemo(() => new Animated.Value(1), []);

  const fetchTimeFrameData = useCallback(async () => {
    const startTime = Date.now();
    logger.info('Fetching time frame data', { timeFrame });
  
    try {
      const userId = auth.currentUser?.uid;
      if (!userId) throw new Error('No authenticated user found');
  
      const now = new Date();
      let startDate = new Date(now);
  
      // Calculate date range based on timeFrame
      switch (timeFrame) {
        case 'day':
          startDate.setHours(0, 0, 0, 0);
          break;
        case 'week':
          startDate.setDate(now.getDate() - 7);
          break;
        case 'month':
          startDate.setDate(now.getDate() - 30);
          break;
      }
  
      const formattedStartDate = startDate.toISOString().split('T')[0];
      const formattedEndDate = now.toISOString().split('T')[0];
  
      const stats = await fetchStatsForAnalytics(
        userId,
        formattedStartDate,
        formattedEndDate
      );
  
      // Log the fetched stats data
      console.log('Fetched Stats Data:', JSON.stringify(stats, null, 2));
  
      // Create a map of dates to entries for easy lookup
      const entriesMap = stats.dailyEntries.reduce((acc, entry) => {
        acc[entry.dateKey] = entry;
        return acc;
      }, {});
  
      let chartData;
      if (timeFrame === 'day') {
        // Get today's entry
        const todayEntry = entriesMap[formattedEndDate] || {
          calories: 0,
          nutrients: { protein: 0, carbs: 0, fat: 0 }
        };
  
        chartData = {
          type: 'daily',
          data: {
            calories: todayEntry.calories || 0,
            protein: todayEntry.nutrients?.protein || 0,
            carbs: todayEntry.nutrients?.carbs || 0,
            fat: todayEntry.nutrients?.fat || 0
          }
        };
      } else {
        // For week/month view, generate array of dates
        // In fetchTimeFrameData function
        let currentDate = new Date(startDate);
        currentDate.setUTCHours(0, 0, 0, 0); // UTC date handling

        // When creating dates array
        const dates = [];
        while (currentDate <= now) {
          const dateString = currentDate.toISOString().split('T')[0];
          dates.push(dateString);
          currentDate.setUTCDate(currentDate.getUTCDate() + 1); // UTC increment
          console.log('[Analytics] Generated Date:', dateString);
        }
  
        chartData = {
          type: 'timeline',
          entries: dates.map(date => ({
            date,
            ...(entriesMap[date] || {  // Handle missing entries
              calories: 0,
              nutrients: {
                protein: 0,
                carbs: 0,
                fat: 0
              }
            })
          }))
        };
      }
      // After setting chartData but before setStatsData
      console.log('[Analytics] ChartData Structure:', {
        type: chartData.type,
        entriesCount: chartData.entries?.length || 0,
        firstEntryDate: chartData.entries?.[0]?.date,
        lastEntryDate: chartData.entries?.[chartData.entries?.length - 1]?.date,
        firestoreEntries: stats.dailyEntries.map(e => e.dateKey)
      });
  
      setStatsData({
        chartData,
        summary: {
          totalDays: stats.totalDays,
          averageCalories: stats.averageCaloriesPerDay,
          averageNutrients: {
            protein: stats.averageProtein,
            carbs: stats.averageCarbs,
            fat: stats.averageFat
          }
        }
      });
  
      setLastFetch(Date.now());
  
    } catch (error) {
      logger.error('Failed to fetch time frame data', error);
      setError(error.message || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }, [timeFrame, userData]);

  // Get user data
  const getUserData = useCallback(async () => {
    const startTime = Date.now();
    logger.info('Fetching user data');
  
    try {
      const userId = auth.currentUser?.uid;
      if (!userId) throw new Error('No authenticated user found');
  
      const userData = await fetchUserData(userId);
      if (!userData) throw new Error('User document not found');
  
      // Log the fetched user data
      console.log('Fetched User Data:', JSON.stringify(userData, null, 2));
  
      setUserData(userData);
      logger.performance('User data fetch completed', startTime);
    } catch (error) {
      logger.error('Failed to fetch user data', error);
      setError(error.message || 'Failed to load user data');
    }
  }, []);

  // Handle refresh
  const onRefresh = useCallback(async () => {
    logger.info('Manual refresh triggered');
    const startTime = Date.now();
    setRefreshing(true);
    await Promise.all([fetchTimeFrameData(), getUserData()]);
    setRefreshing(false);
    logger.performance('Manual refresh completed', startTime);
  }, [fetchTimeFrameData, getUserData]);

  // Handle time frame change
  const handleTimeFrameChange = useCallback((frame) => {
    logger.interaction('Time frame changed', { from: timeFrame, to: frame });
    setTimeFrame(frame);
    Animated.sequence([
      Animated.timing(timeFrameScale, {
        toValue: 0.95,
        duration: 100,
        useNativeDriver: true,
      }),
      Animated.timing(timeFrameScale, {
        toValue: 1,
        duration: 100,
        useNativeDriver: true,
      })
    ]).start();
  }, [timeFrame, timeFrameScale]);

  // Focus effect
  useFocusEffect(
    useCallback(() => {
      logger.lifecycle('Screen focused', {
        lastFetch,
        timeSinceLastFetch: lastFetch ? Date.now() - lastFetch : null,
        hasUserData: !!userData
      });
      
      if (!lastFetch || Date.now() - lastFetch > 5 * 60 * 1000 || !userData) {
        logger.debug('Triggering fetch due to stale data or missing user data');
        Promise.all([fetchTimeFrameData(), getUserData()]);
      }
    }, [fetchTimeFrameData, lastFetch, userData, getUserData])
  );

  // Component mount effect
  useEffect(() => {
    logger.lifecycle('Component mounted');
    return () => logger.lifecycle('Component will unmount');
  }, []);

  // Render loading state
  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <LoadingSpinner />
        <Text>Loading analytics...</Text>
      </View>
    );
  }

  // Render error state
  if (error) {
    return (
      <View style={styles.centerContainer}>
        <ErrorMessage message={error} onRetry={onRefresh} />
      </View>
    );
  }

  // Main render
  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        <Animated.View style={[styles.content, { opacity: contentOpacity }]}>
          <Header />
          <Animated.View style={[
            styles.timeFrameContainer,
            { transform: [{ scale: timeFrameScale }] }
          ]}>
            <TimeFrameSelector
              timeFrame={timeFrame}
              onTimeFrameChange={handleTimeFrameChange}
            />
          </Animated.View>
          {statsData && userData && (
            <>
              {/* <OverallProgressChart
                timeFrame={timeFrame}
                chartData={statsData?.chartData}
                loading={loading}
                userData={userData}
              /> */}
              <OverallProgressChart
                timeFrame={timeFrame}
                chartData={statsData.chartData || { type: 'daily', data: { calories: 0, protein: 0, carbs: 0, fat: 0 } }}
                loading={loading}
                userData={userData}
              />
              {/* <ProgressSummary 
                goals={statsData.goals} 
                userData={userData}
              /> */}
            </>
          )}
        </Animated.View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: 'white',
  },
  scrollContent: {
    padding: theme.spacing.m,
  },
  content: {
    flex: 1,
    width: getResponsiveWidth(100) - (theme.spacing.m * 2),
  },
  header: {
    marginBottom: getResponsiveHeight(1),
    marginTop: getResponsiveHeight(-1),
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  title: {
    ...theme.typography.title1,
    color: theme.colors.text.primary.light,
  },
  timeFrameContainer: {
    marginBottom: theme.spacing.s,
    padding: 1,
    width: '100%',
    alignItems: 'center',
  },
  timeFrameSelector: {
    flexDirection: 'row',
    justifyContent: 'center',
    position: 'relative',
    backgroundColor: theme.colors.background.primary.light,
    borderRadius: theme.layout.borderRadius.medium,
    padding: '0.1%',
    width: '92%',
    maxWidth: 350,
    alignSelf: 'center',
  },
  timeFrameButton: {
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1,
    height: '100%',
  },
  slider: {
    position: 'absolute',
    height: '92%',
    backgroundColor: theme.colors.primary.light,
    borderRadius: theme.layout.borderRadius.medium - 2,
    top: '4%',
    left: '2%',
  },
  timeFrameText: {
    ...theme.typography.subhead,
    color: theme.colors.text.primary.light,
    fontSize: Math.min(theme.typography.subhead.fontSize, getResponsiveWidth(3.5)),
  },
  activeTimeFrameText: {
    color: theme.colors.text.primary.light,
    fontWeight: '600',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: getResponsiveHeight(40),
  },
});

export default React.memo(AnalyticsScreen);




//this version does not work. don't use it.
// import React, { useEffect, useState, useCallback, useMemo } from 'react';
// import { 
//   View, Text, StyleSheet, Dimensions, TouchableOpacity, Vibration, 
//   SafeAreaView, ScrollView, RefreshControl, Animated
// } from 'react-native';
// import { useFocusEffect } from '@react-navigation/native';
// import { auth, db } from '../utils/firebase';
// import { 
//   collection, query, where, getDocs, Timestamp,
//   doc, getDoc, orderBy, limit
// } from 'firebase/firestore';
// import LinearGradient from 'react-native-linear-gradient';
// import { useSafeAreaInsets } from 'react-native-safe-area-context';

// import theme from '../styles/theme';
// import LoadingSpinner from '../Components/LoadingSpinner';
// import ErrorMessage from '../Components/ErrorMessage';
// import OverallProgressChart from '../analyticscomponents/OverallProgressChart';
// import ProgressSummary from '../analyticscomponents/ProgressSummary';

// const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

// // Responsive sizing helpers
// const getResponsiveWidth = (percentage) => SCREEN_WIDTH * (percentage / 100);
// const getResponsiveHeight = (percentage) => SCREEN_HEIGHT * (percentage / 100);
// const getResponsiveButtonWidth = () => {
//   const baseWidth = 100;
//   const scaleFactor = Math.min(SCREEN_WIDTH / 375, 1.3);
//   return Math.round(baseWidth * scaleFactor);
// };

// // Memoized helper functions
// const getStartDate = (now, timeFrame) => {
//   const startDate = new Date(now);
//   switch (timeFrame) {
//     case 'week':
//       startDate.setDate(now.getDate() - 7);
//       break;
//     case 'month':
//       startDate.setMonth(now.getMonth() - 1);
//       break;
//     default:
//       startDate.setHours(0, 0, 0, 0);
//   }
//   return startDate;
// };

// const processChartData = (goals, startDate, endDate) => {
//   const dataMap = new Map();
  
//   goals.forEach(goal => {
//     goal.progress.forEach(entry => {
//       const dateString = entry.date.toISOString().split('T')[0];
//       if (!dataMap.has(dateString)) {
//         dataMap.set(dateString, {
//           total: 0,
//           count: 0
//         });
//       }
//       const current = dataMap.get(dateString);
//       current.total += (entry.value / goal.target) * 100;
//       current.count += 1;
//     });
//   });

//   const sortedEntries = Array.from(dataMap.entries())
//     .sort(([dateA], [dateB]) => new Date(dateA) - new Date(dateB));

//   return {
//     labels: sortedEntries.map(([date]) => date),
//     datasets: [{
//       data: sortedEntries.map(([, value]) => 
//         value.count > 0 ? Math.round(value.total / value.count) : 0
//       )
//     }]
//   };
// };

// // Memoized components with responsive styles
// const Header = React.memo(() => (
//   <View style={styles.header}>
//     <Text style={[styles.title, { fontSize: theme.typography.title1.fontSize }]}>
//       Analytics
//     </Text>
//   </View>
// ));

// const TimeFrameSelector = React.memo(({ timeFrame, onTimeFrameChange }) => {
//   const slideAnim = useMemo(() => new Animated.Value(0), []);
//   const frames = ['day', 'week', 'month'];
//   const buttonWidth = getResponsiveButtonWidth();
  
//   useEffect(() => {
//     const toValue = frames.indexOf(timeFrame);
//     Animated.spring(slideAnim, {
//       toValue,
//       speed: 12,
//       bounciness: 0,
//       useNativeDriver: true,
//     }).start();
//   }, [timeFrame, slideAnim]);

//   return (
//     <View style={[styles.timeFrameSelector, { height: getResponsiveHeight(5) }]}>
//       <Animated.View
//         style={[
//           styles.slider,
//           {
//             width: buttonWidth,
//             transform: [{
//               translateX: slideAnim.interpolate({
//                 inputRange: [0, 1, 2],
//                 outputRange: [0, buttonWidth, buttonWidth * 2]
//               })
//             }]
//           }
//         ]}
//       />
//       {frames.map((frame) => (
//         <TouchableOpacity
//           key={frame}
//           style={[styles.timeFrameButton, { width: buttonWidth }]}
//           onPress={() => onTimeFrameChange(frame)}
//         >
//           <Text style={[
//             styles.timeFrameText,
//             timeFrame === frame && styles.activeTimeFrameText
//           ]}>
//             {frame.charAt(0).toUpperCase() + frame.slice(1)}
//           </Text>
//         </TouchableOpacity>
//       ))}
//     </View>
//   );
// });

// const ErrorContent = React.memo(({ message, onRetry }) => (
//   <View style={styles.centerContainer}>
//     <ErrorMessage message={message} onRetry={onRetry} />
//   </View>
// ));

// const LoadingContent = React.memo(() => (
//   <View style={styles.centerContainer}>
//     <LoadingSpinner />
//   </View>
// ));

// const MainContent = React.memo(({ 
//   userData, 
//   timeFrame, 
//   contentOpacity, 
//   timeFrameScale, 
//   onTimeFrameChange 
// }) => (
//   <Animated.View style={[
//     styles.content, 
//     { opacity: contentOpacity }
//   ]}>
//     <Header />
//     <Animated.View style={[
//       styles.timeFrameContainer, 
//       { 
//         transform: [{ scale: timeFrameScale }],
//         marginBottom: getResponsiveHeight(2)
//       }
//     ]}>
//       <TimeFrameSelector
//         timeFrame={timeFrame}
//         onTimeFrameChange={onTimeFrameChange}
//       />
//     </Animated.View>
//     {/* <OverallProgressChart 
//       chartData={userData.chartData}
//       timeFrame={timeFrame}
//     />
//     <ProgressSummary goals={userData.goals} /> */}
//   </Animated.View>
// ));

// const AnalyticsScreen = () => {
//   const [userData, setUserData] = useState({ goals: [], chartData: {} });
//   const [timeFrame, setTimeFrame] = useState('week');
//   const [refreshing, setRefreshing] = useState(false);
//   const [loading, setLoading] = useState(true);
//   const [error, setError] = useState(null);
//   const contentOpacity = useMemo(() => new Animated.Value(0), []);
//   const timeFrameScale = useMemo(() => new Animated.Value(1), []);
//   const [lastFetch, setLastFetch] = useState(null);
//   const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

//   const fetchData = useCallback(async (force = false) => {
//     try {
//       setLoading(true);
//       setError(null);

//       const userId = auth.currentUser?.uid;
//       if (!userId) {
//         throw new Error('No authenticated user found');
//       }

//       const currentDate = new Date();
//       let collectionName;
//       let queryStartDate;
//       let dateKey;

//       // Determine collection and date range based on timeFrame
//       switch (timeFrame) {
//         case 'day':
//           collectionName = 'dailyStats';
//           dateKey = currentDate.toISOString().split('T')[0];
//           queryStartDate = new Date(currentDate.setHours(0, 0, 0, 0));
//           break;
//         case 'week':
//           collectionName = 'weeklyStats';
//           const weekStart = new Date(currentDate);
//           weekStart.setDate(currentDate.getDate() - 7);
//           dateKey = weekStart.toISOString().split('T')[0];
//           queryStartDate = weekStart;
//           break;
//         case 'month':
//           collectionName = 'monthlyStats';
//           const monthStart = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
//           dateKey = monthStart.toISOString().slice(0, 7);
//           queryStartDate = monthStart;
//           break;
//         default:
//           throw new Error('Invalid time frame');
//       }

//       // Query the appropriate stats collection
//       const statsQuery = query(
//         collection(db, collectionName),
//         where('userId', '==', userId),
//         where('date', '>=', Timestamp.fromDate(queryStartDate)),
//         where('date', '<=', Timestamp.fromDate(currentDate)),
//         orderBy('date', 'desc')
//       );

//       const statsSnapshot = await getDocs(statsQuery);
      
//       if (statsSnapshot.empty) {
//         throw new Error('No data available for the selected time frame');
//       }

//       // Process the stats data
//       const processedData = statsSnapshot.docs.map(doc => {
//         const data = doc.data();
//         return {
//           id: doc.id,
//           nutrients: data.nutrients || {},
//           progress: data.progress || {
//             nutrients: { protein: 0, calories: 0, carbs: 0, fat: 0 },
//             goals: { weight: 0, overall: 0 }
//           },
//           metadata: data.metadata || {},
//           date: data.date?.toDate() || new Date()
//         };
//       });

//       // Create goals array from the nutrients data
//       const goals = [
//         {
//           id: 'calories',
//           name: 'Calories',
//           target: processedData[0].nutrients.targetCalories || 2000,
//           unit: 'kcal',
//           progress: processedData.map(entry => ({
//             date: entry.date,
//             value: entry.nutrients.calories || 0
//           }))
//         },
//         {
//           id: 'protein',
//           name: 'Protein',
//           target: processedData[0].nutrients.targetProtein || 150,
//           unit: 'g',
//           progress: processedData.map(entry => ({
//             date: entry.date,
//             value: entry.nutrients.protein || 0
//           }))
//         },
//         {
//           id: 'carbs',
//           name: 'Carbs',
//           target: processedData[0].nutrients.targetCarbs || 250,
//           unit: 'g',
//           progress: processedData.map(entry => ({
//             date: entry.date,
//             value: entry.nutrients.carbs || 0
//           }))
//         },
//         {
//           id: 'fat',
//           name: 'Fat',
//           target: processedData[0].nutrients.targetFat || 70,
//           unit: 'g',
//           progress: processedData.map(entry => ({
//             date: entry.date,
//             value: entry.nutrients.fat || 0
//           }))
//         }
//       ];

//       // Process chart data
//       const chartData = processChartData(goals, queryStartDate, currentDate);

//       setUserData({
//         goals,
//         chartData,
//         metadata: processedData[0].metadata,
//         progress: processedData[0].progress
//       });

//       setLastFetch(Date.now());

//       // Animate content appearance
//       Animated.parallel([
//         Animated.timing(contentOpacity, {
//           toValue: 1,
//           duration: 300,
//           useNativeDriver: true,
//         }),
//         Animated.spring(timeFrameScale, {
//           toValue: 1,
//           speed: 12,
//           bounciness: 6,
//           useNativeDriver: true,
//         }),
//       ]).start();

//     } catch (error) {
//       console.error('Error in fetchData:', error);
//       setError(error.message || 'Failed to load data. Please try again.');
//     } finally {
//       setLoading(false);
//     }
//   }, [timeFrame, contentOpacity, timeFrameScale]);

//   const fetchTimeFrameData = async (timeFrame) => {
//     const userId = auth.currentUser?.uid;
//     if (!userId) throw new Error('No authenticated user found');
  
//     const currentDate = new Date();
    
//     try {
//       switch(timeFrame) {
//         case 'day':
//           const todayKey = currentDate.toISOString().split('T')[0];
//           return await getDoc(doc(db, 'users', userId, 'daily_stats', todayKey));
          
//         case 'week':
//           const weekStart = new Date(currentDate);
//           weekStart.setDate(weekStart.getDate() - 7);
//           const weekId = weekStart.toISOString().split('T')[0];
//           return await getDoc(doc(db, 'users', userId, 'aggregated_stats', `weekly_${weekId}`));
          
//         case 'month':
//           const monthStart = new Date(currentDate);
//           monthStart.setMonth(monthStart.getMonth() - 1);
//           const monthId = monthStart.toISOString().slice(0, 7);
//           return await getDoc(doc(db, 'users', userId, 'aggregated_stats', `monthly_${monthId}`));
          
//         default:
//           throw new Error('Invalid time frame');
//       }
//     } catch (error) {
//       console.error('Error fetching time frame data:', error);
//       throw error;
//     }
//   };
  
//   useEffect(() => {
//     console.log('Initial load useEffect triggered');
//     fetchData(true);
//     return () => {
//       console.log('Cleaning up Analytics screen');
//     };
//   }, []);

//   useFocusEffect(
//     useCallback(() => {
//       console.log('Screen focused');
//       if (lastFetch === null) {
//         fetchData(true);
//       } else {
//         fetchData(false);
//       }
//     }, [fetchData, lastFetch])
//   );

//   const onRefresh = useCallback(async () => {
//     console.log('Manual refresh triggered');
//     setRefreshing(true);
//     await fetchData(true);
//     setRefreshing(false);
//   }, [fetchData]);

//   const handleTimeFrameChange = useCallback((frame) => {
//     setTimeFrame(frame);
//     // Vibration.vibrate(1);
//     Animated.sequence([
//       Animated.timing(timeFrameScale, {
//         toValue: 1,
//         duration: 100,
//         useNativeDriver: true,
//       }),
//       Animated.timing(timeFrameScale, {
//         toValue: 1,
//         duration: 100,
//         useNativeDriver: true,
//       })
//     ]).start();
//   }, [timeFrameScale]);

//   return (
//     <SafeAreaView style={styles.container}>
//       <ScrollView
//         contentContainerStyle={styles.scrollContent}
//         refreshControl={
//           <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
//         }
//       >
//         {loading ? (
//           <LoadingContent />
//         ) : error ? (
//           <ErrorContent message={error} onRetry={() => fetchData(true)} />
//         ) : (
//           <MainContent
//             userData={userData}
//             timeFrame={timeFrame}
//             contentOpacity={contentOpacity}
//             timeFrameScale={timeFrameScale}
//             onTimeFrameChange={handleTimeFrameChange}
//           />
//         )}
//       </ScrollView>
//     </SafeAreaView>
//   );
// };

// const styles = StyleSheet.create({
//   container: {
//     flex: 1,
//     backgroundColor: theme.colors.background.primary.light,
//   },
//   scrollContent: {
//     padding: theme.spacing.m,
//   },
//   content: {
//     flex: 1,
//     width: getResponsiveWidth(100) - (theme.spacing.m * 2),
//   },
//   header: {
//     marginBottom: getResponsiveHeight(1),
//     marginTop: getResponsiveHeight(-1),
//     flexDirection: 'row',
//     justifyContent: 'space-between',
//     alignItems: 'center',
//   },
//   title: {
//     ...theme.typography.title1,
//     color: theme.colors.text.primary.light,
//   },
//   timeFrameContainer: {
//     marginBottom: theme.spacing.s,
//     padding: 1,
//     width: '100%',
//     alignItems: 'center',
//   },
//   // timeFrameSelector: {
//   //   flexDirection: 'row',
//   //   justifyContent: 'center',
//   //   position: 'relative',
//   //   backgroundColor: theme.colors.background.tertiary.light,
//   //   borderRadius: theme.layout.borderRadius.medium,
//   //   padding: 1,
//   //   width: getResponsiveWidth(90),
//   //   maxWidth: 350,
//   //   marginBottom: getResponsiveHeight(-1),
//   // },
//   timeFrameSelector: {
//     flexDirection: 'row',
//     justifyContent: 'center',
//     position: 'relative',
//     backgroundColor: theme.colors.background.tertiary.light,
//     borderRadius: theme.layout.borderRadius.medium,
//     padding: '0.1%',
//     width: '92%',
//     maxWidth: 350,
//     alignSelf: 'center',
//   },
//   timeFrameButton: {
//     justifyContent: 'center',
//     alignItems: 'center',
//     zIndex: 1,
//     height: '100%',
//   },
//   slider: {
//     position: 'absolute',
//     // height: '100%',
//     height: '92%',
//     backgroundColor: theme.colors.primary.light,
//     borderRadius: theme.layout.borderRadius.medium - 2,
//     top: '4%',
//     left: '2%',
//     // top: 2,
//     // left: 18,
//   },
//   timeFrameText: {
//     ...theme.typography.subhead,
//     color: theme.colors.text.primary.light,
//     fontSize: Math.min(theme.typography.subhead.fontSize, getResponsiveWidth(3.5)),
//   },
//   activeTimeFrameText: {
//     color: theme.colors.text.primary.light,
//     fontWeight: '600',
//   },
//   centerContainer: {
//     flex: 1,
//     justifyContent: 'center',
//     alignItems: 'center',
//     minHeight: getResponsiveHeight(40),
//   },
// });

// export default React.memo(AnalyticsScreen);






// this works

// import React, { useEffect, useState, useCallback } from 'react';
// import { 
//   View, Text, StyleSheet, Dimensions, TouchableOpacity, Vibration, 
//   SafeAreaView, ScrollView, RefreshControl, Animated
// } from 'react-native';
// import { useFocusEffect } from '@react-navigation/native';
// import { auth, db } from '../utils/firebase';
// import { 
//   collection, query, where, getDocs, Timestamp,
//   doc, getDoc
// } from 'firebase/firestore';
// import theme from '../styles/theme';
// import LoadingSpinner from '../Components/LoadingSpinner';
// import ErrorMessage from '../Components/ErrorMessage';
// import { ArrowUpIcon, ArrowDownIcon } from 'react-native-heroicons/outline';
// import OverallProgressChart from '../analyticscomponents/OverallProgressChart';
// import ProgressSummary from '../analyticscomponents/ProgressSummary';

// const { width } = Dimensions.get('window');

// const AnalyticsScreen = () => {
//   const [userData, setUserData] = useState({
//     goals: [],
//     chartData: {},
//   });
//   const [timeFrame, setTimeFrame] = useState('week');
//   const [refreshing, setRefreshing] = useState(false);
//   const [loading, setLoading] = useState(true);
//   const [error, setError] = useState(null);
//   const [contentOpacity] = useState(new Animated.Value(0));
//   const [timeFrameScale] = useState(new Animated.Value(1));

//   const fetchData = useCallback(async () => {
//     console.log('Fetching data...');
//     setLoading(true);
//     setError(null);
    
//     try {
//       const userId = auth.currentUser?.uid;
//       if (!userId) {
//         throw new Error('No authenticated user found');
//       }

//       const userDocRef = doc(db, 'users', userId);
//       const userDocSnap = await getDoc(userDocRef);
      
//       if (!userDocSnap.exists()) {
//         throw new Error('User document not found');
//       }
      
//       const userData = userDocSnap.data();
//       const userGoals = Object.entries(userData.goals || {}).map(([key, value]) => ({
//         id: key,
//         name: key,
//         target: value,
//         unit: key === 'healthScore' ? 'points' : 'g',
//         progress: []
//       }));

//       const now = new Date();
//       const startDate = getStartDate(now, timeFrame);
//       const progressQuery = query(
//         collection(db, 'progress'),
//         where('userId', '==', userId),
//         where('date', '>=', Timestamp.fromDate(startDate)),
//         where('date', '<=', Timestamp.fromDate(now))
//       );
      
//       const progressSnapshot = await getDocs(progressQuery);
//       const progressData = progressSnapshot.docs.map(doc => ({
//         ...doc.data(),
//         date: doc.data().date.toDate()
//       }));

//       const progressByGoal = progressData.reduce((acc, progress) => {
//         if (!acc[progress.goalId]) {
//           acc[progress.goalId] = [];
//         }
//         acc[progress.goalId].push(progress);
//         return acc;
//       }, {});

//       const goalsWithProgress = userGoals.map(goal => ({
//         ...goal,
//         progress: progressByGoal[goal.id] || []
//       }));

//       const chartData = processChartData(goalsWithProgress, startDate, now);

//       setUserData({
//         goals: goalsWithProgress,
//         chartData,
//       });

//       Animated.parallel([
//         Animated.timing(contentOpacity, {
//           toValue: 1,
//           duration: 500,
//           useNativeDriver: true,
//         }),
//         Animated.spring(timeFrameScale, {
//           toValue: 1,
//           speed: 10,
//           bounciness: 8,
//           useNativeDriver: true,
//         }),
//       ]).start();
//     } catch (error) {
//       console.error('Error fetching data:', error);
//       setError(error.message || 'Failed to load data. Please try again.');
//     } finally {
//       setLoading(false);
//     }
//   }, [timeFrame, contentOpacity, timeFrameScale]);

//   useEffect(() => {
//     fetchData();
//   }, [fetchData]);

//   useFocusEffect(
//     useCallback(() => {
//       fetchData();
//     }, [fetchData])
//   );

//   const onRefresh = useCallback(async () => {
//     setRefreshing(true);
//     await fetchData();
//     setRefreshing(false);
//   }, [fetchData]);

//   const handleTimeFrameChange = (frame) => {
//     setTimeFrame(frame);
//     Vibration.vibrate(50);
//     Animated.timing(timeFrameScale, {
//       toValue: 1.2,
//       duration: 100,
//       useNativeDriver: true,
//     }).start(() => {
//       Animated.timing(timeFrameScale, {
//         toValue: 1,
//         duration: 100,
//         useNativeDriver: true,
//       }).start();
//     });
//   };

//   return (
//     <SafeAreaView style={styles.container}>
//       <ScrollView
//         contentContainerStyle={styles.scrollContent}
//         refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
//       >
//         {loading ? (
//           <View style={styles.centerContainer}>
//             <LoadingSpinner />
//           </View>
//         ) : error ? (
//           <View style={styles.centerContainer}>
//             <ErrorMessage message={error} onRetry={fetchData} />
//           </View>
//         ) : (
//           <Animated.View
//             style={[styles.content, { opacity: contentOpacity }]}
//           >
//             <Header />
            
//             <Animated.View style={[styles.timeFrameContainer, { transform: [{ scale: timeFrameScale }] }]}>
//               <TimeFrameSelector
//                 timeFrame={timeFrame}
//                 setTimeFrame={handleTimeFrameChange}
//               />
//             </Animated.View>

//             <OverallProgressChart 
//               chartData={userData.chartData}
//               timeFrame={timeFrame}
//             />

//             <ProgressSummary goals={userData.goals} />
//           </Animated.View>
//         )}
//       </ScrollView>
//     </SafeAreaView>
//   );
// };

// const Header = () => (
//   <View style={styles.header}>
//     <Text style={styles.title}>Analytics</Text>
//     {/* <TouchableOpacity style={styles.helpButton}>
//       <ArrowUpIcon size={24} color={theme.colors.text.primary.light} />
//     </TouchableOpacity> */}
//   </View>
// );

// const TimeFrameSelector = ({ timeFrame, setTimeFrame }) => (
//   <View style={styles.timeFrameSelector}>
//     {['day', 'week', 'month'].map((frame) => (
//       <TouchableOpacity
//         key={frame}
//         style={[
//           styles.timeFrameButton,
//           timeFrame === frame && styles.activeTimeFrame
//         ]}
//         onPress={() => setTimeFrame(frame)}
//         onPressIn={() => Vibration.vibrate(50)}
//       >
//         <Text 
//           style={[
//             styles.timeFrameText,
//             timeFrame === frame && styles.activeTimeFrameText
//           ]}
//         >
//           {frame.charAt(0).toUpperCase() + frame.slice(1)}
//         </Text>
//       </TouchableOpacity>
//     ))}
//   </View>
// );

// const getStartDate = (now, timeFrame) => {
//   const startDate = new Date(now);
//   switch (timeFrame) {
//     case 'week':
//       startDate.setDate(now.getDate() - 7);
//       break;
//     case 'month':
//       startDate.setMonth(now.getMonth() - 1);
//       break;
//     default: // day
//       startDate.setHours(0, 0, 0, 0);
//   }
//   return startDate;
// };

// const processChartData = (goals, startDate, endDate) => {
//   const data = {};
//   goals.forEach(goal => {
//     goal.progress.forEach(entry => {
//       const dateString = entry.date.toISOString().split('T')[0];
//       if (!data[dateString]) {
//         data[dateString] = 0;
//       }
//       data[dateString] += (entry.value / goal.target) * 100;
//     });
//   });

//   const sortedDates = Object.keys(data).sort();
//   const validData = sortedDates.map(date => {
//     const value = data[date] / goals.length;
//     return isFinite(value) ? value : 0;
//   });

//   return {
//     labels: sortedDates,
//     datasets: [{ data: validData }],
//   };
// };

// const styles = StyleSheet.create({
//   container: {
//     flex: 1,
//     backgroundColor: theme.colors.background.primary.light,
//   },
//   scrollContent: {
//     padding: theme.spacing.m,
//   },
//   content: {
//     flex: 1,
//   },
//   header: {
//     marginBottom: theme.spacing.m,
//     flexDirection: 'row',
//     justifyContent: 'space-between',
//     alignItems: 'center',
//   },
//   title: {
//     ...theme.typography.title1,
//     color: theme.colors.text.primary.light,
//   },
//   helpButton: {
//     padding: theme.spacing.s,
//     borderRadius: theme.layout.borderRadius.medium,
//     backgroundColor: theme.colors.background.tertiary.light,
//   },
//   timeFrameContainer: {
//     marginBottom: theme.spacing.m,
//   },
//   timeFrameSelector: {
//     flexDirection: 'row',
//     justifyContent: 'center',
//   },
//   timeFrameButton: {
//     paddingVertical: theme.spacing.s,
//     paddingHorizontal: theme.spacing.m,
//     borderRadius: theme.layout.borderRadius.medium,
//     backgroundColor: theme.colors.background.tertiary.light,
//   },
//   activeTimeFrame: {
//     backgroundColor: theme.colors.primary.light,
//   },
//   timeFrameText: {
//     ...theme.typography.subhead,
//     color: theme.colors.text.primary.light,
//   },
//   activeTimeFrameText: {
//     color: theme.colors.text.primary.light,
//   },
//   centerContainer: {
//     flex: 1,
//     justifyContent: 'center',
//     alignItems: 'center',
//     minHeight: 300,
//   },
// });

// export default AnalyticsScreen;




