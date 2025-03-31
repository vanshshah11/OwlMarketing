import React, { useMemo } from 'react';
import { View, Text, ScrollView, Dimensions, StyleSheet, ActivityIndicator } from 'react-native';
import { BarChart } from 'react-native-chart-kit';
import { format } from 'date-fns';
import Animated, { 
  FadeIn,
  FadeInDown,
  FadeInUp,
  Layout,
  useAnimatedStyle,
  withSpring,
  SlideInRight
} from 'react-native-reanimated';
import theme from '../styles/theme';

const { width: screenWidth } = Dimensions.get('window');
const BAR_SPACING = theme.spacing.m;
const BAR_WIDTH = {
  day: 32,
  week: 24,
  month: 16
};

const AnimatedBarChart = Animated.createAnimatedComponent(BarChart);
const AnimatedActivityIndicator = Animated.createAnimatedComponent(ActivityIndicator);

const CustomBarComponent = ({ value, index, width, ...props }) => {
  const animatedStyle = useAnimatedStyle(() => ({
    height: withSpring(value === 0 ? 2 : `${value}%`, {
      damping: 10,
      stiffness: 100,
    }),
  }));

  return (
    <Animated.View
      style={[
        {
          width,
          backgroundColor: props.color,
          borderRadius: theme.layout.borderRadius.small,
          marginRight: BAR_SPACING,
        },
        animatedStyle,
      ]}
      entering={FadeInDown.duration(500).delay(index * 50)}
      layout={Layout.springify()}
    />
  );
};

const OverallProgressChart = ({ timeFrame = 'day', chartData = null, loading = false, userData = null }) => {
  const safeDivide = (value = 0, goal = 0) => 
    goal > 0 ? Math.min((value / goal) * 100, 100) : 0;

  const getBarColor = (opacity = 1) => `rgba(66, 153, 225, ${opacity})`;
  
  const processedData = useMemo(() => {
    if (!chartData || loading || !userData) {
      return {
        labels: [],
        datasets: [{ data: [] }]
      };
    }

    const goals = {
      calories: userData?.dailyCalorieGoal || 2000,
      protein: userData?.dailyProteinGoal || 50,
      carbs: userData?.dailyCarbsGoal || 300,
      fat: userData?.dailyFatGoal || 65
    };

    // Normalize the data structure based on timeFrame
    if (timeFrame === 'day') {
      // Ensure we're handling both possible data structures
      const dailyData = chartData.type === 'daily' ? chartData.data : 
        (chartData.entries?.[chartData.entries.length - 1] || {});
      
      const colors = [
        theme.colors.macro.protein,
        theme.colors.macro.carbs,
        theme.colors.macro.fat,
        theme.colors.primary.light
      ];

      // Extract values safely
      const calories = dailyData.calories || 0;
      const protein = dailyData.nutrients?.protein || dailyData.protein || 0;
      const carbs = dailyData.nutrients?.carbs || dailyData.carbs || 0;
      const fat = dailyData.nutrients?.fat || dailyData.fat || 0;
    
      return {
        labels: ['Calories', 'Protein', 'Carbs', 'Fat'],
        datasets: [{
          data: [
            safeDivide(calories, goals.calories),
            safeDivide(protein, goals.protein),
            safeDivide(carbs, goals.carbs),
            safeDivide(fat, goals.fat)
          ],
          color: (opacity = 1, index) => colors[index] ? 
            `${colors[index]}${Math.round(opacity * 255).toString(16).padStart(2, '0')}` : 
            colors[0]
        }],
        rawValues: [calories, protein, carbs, fat],
        colors
      };
    } else {
      // Handle week/month view
      const entries = chartData.entries || [];
      const daysToShow = timeFrame === 'week' ? 7 : 30;
      
      // Ensure dates are in UTC
      const today = new Date();
      today.setUTCHours(0, 0, 0, 0);

      const dates = Array.from({ length: daysToShow }, (_, i) => {
        const date = new Date(today);
        date.setUTCDate(today.getUTCDate() - (daysToShow - 1 - i));
        return date.toISOString().split('T')[0];
      });

      const progressData = dates.map(date => {
        const entry = entries.find(e => e.date === date) || {
          calories: 0,
          nutrients: { protein: 0, carbs: 0, fat: 0 }
        };

        const calorieProgress = safeDivide(entry.calories, goals.calories);
        const proteinProgress = safeDivide(
          entry.nutrients?.protein || entry.protein || 0, 
          goals.protein
        );
        const carbsProgress = safeDivide(
          entry.nutrients?.carbs || entry.carbs || 0, 
          goals.carbs
        );
        const fatProgress = safeDivide(
          entry.nutrients?.fat || entry.fat || 0, 
          goals.fat
        );

        const overallProgress = (calorieProgress + proteinProgress + carbsProgress + fatProgress) / 4;

        return {
          label: format(new Date(date), timeFrame === 'week' ? 'EEE' : 'dd'),
          progress: Math.round(overallProgress)
        };
      });

      return {
        labels: progressData.map(d => d.label),
        datasets: [{
          data: progressData.map(d => d.progress),
          color: (opacity = 1) => getBarColor(opacity)
        }]
      };
    }
  }, [chartData, loading, userData, timeFrame]);

  const chartConfig = {
    backgroundGradientFrom: theme.colors.background.stuffimadeup,
    backgroundGradientTo: theme.colors.background.stuffimadeup,
    decimalPlaces: 0,
    color: (opacity = 1) => getBarColor(opacity),
    labelColor: (opacity = 1) => theme.colors.text.primary.light,
    propsForBackgroundLines: { strokeWidth: 0 },
    barPercentage: 0.8,
    barRadius: theme.layout.borderRadius.small,
    yAxisMax: 100,
    style: { borderRadius: theme.layout.borderRadius.medium },
    formatXLabel: (label) => label
  };

  if (loading) {
    return (
      <Animated.View 
        style={[styles.chartContainer, styles.loadingContainer]}
        entering={FadeIn.duration(300)}
      >
        <AnimatedActivityIndicator 
          size="large" 
          color={theme.colors.primary.light}
          style={styles.pulseAnimation}
        />
      </Animated.View>
    );
  }

  if (!processedData.labels.length || !processedData.datasets[0]?.data.length) {
    return (
      <Animated.View 
        style={styles.chartContainer}
        entering={FadeIn.delay(200)}
      >
        <Text style={styles.noDataText}>No progress data available</Text>
      </Animated.View>
    );
  }

  return (
    <Animated.View 
      style={styles.chartContainer}
      entering={FadeInUp.duration(500)}
      layout={Layout.springify()}
    >
      <ScrollView
        horizontal={timeFrame !== 'day'}
        showsHorizontalScrollIndicator={timeFrame === 'month'}
        contentContainerStyle={styles.scrollContainer}
        scrollIndicatorInsets={{ right: 1 }}
      >
        <View style={styles.chartWrapper}>
          <AnimatedBarChart
            data={processedData}
            width={Math.max(
              (BAR_WIDTH[timeFrame] + BAR_SPACING) * processedData.labels.length + 40,
              screenWidth - 40
            )}
            height={240}
            chartConfig={chartConfig}
            style={styles.chart}
            showBarTops={false}
            fromZero
            yAxisLabel=""
            yAxisSuffix="%"
            withInnerLines={false}
            segments={4}
            verticalLabelRotation={timeFrame === 'month' ? 0 : 0}
            withVerticalLabels={true}
            withHorizontalLabels={true}
            customBar={CustomBarComponent}
          />
        </View>
      </ScrollView>

      {timeFrame === 'day' && (
        <Animated.View 
          style={styles.macroValues}
          entering={FadeIn.delay(300)}
        >
          {processedData.labels.map((label, index) => (
            <Animated.View 
              key={label} 
              style={styles.macroItem}
              entering={SlideInRight.duration(300).delay(200 + index * 50)}
            >
              <View style={[styles.legendDot, { backgroundColor: processedData.colors[index] }]} />
              <Text style={styles.macroLabel}>{label}</Text>
              <Text style={styles.macroValue}>
                {processedData.rawValues[index].toFixed(1)}
                {label === 'Calories' ? ' kcal' : 'g'}
              </Text>
            </Animated.View>
          ))}
        </Animated.View>
      )}

      {timeFrame !== 'day' && (
        <Animated.View 
          style={styles.legendContainer}
          entering={FadeIn.delay(400)}
        >
          <View style={styles.legendItem}>
            <View style={[styles.legendDot, { backgroundColor: theme.colors.primary.light }]} />
            <Text style={styles.legendText}>Daily Goal Progress</Text>
          </View>
        </Animated.View>
      )}
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  chartContainer: {
    backgroundColor: theme.colors.background.stuffimadeup,
    borderRadius: theme.layout.borderRadius.medium,
    marginVertical: theme.spacing.m,
    padding: theme.spacing.m,
    elevation: theme.shadows.medium.elevation,
    // shadowColor: theme.colors.primary.dark,
    // shadowOffset: { width: 0, height: 8 },
    // shadowOpacity: 0.1,
    // shadowRadius: 16,
  },
  loadingContainer: {
    height: 240,
    justifyContent: 'center',
    alignItems: 'center'
  },
  chartWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  chart: {
    marginVertical: theme.spacing.s,
    marginLeft: -theme.spacing.xl,
    // marginRight: theme.spacing.l,
    borderRadius: theme.layout.borderRadius.medium,
  },
  scrollContainer: {
    paddingRight: theme.spacing.m
  },
  legendContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: theme.spacing.m
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: theme.spacing.s
  },
  legendDot: {
    width: theme.spacing.s,
    height: theme.spacing.s,
    borderRadius: theme.layout.borderRadius.circular,
    marginRight: theme.spacing.xs
  },
  legendText: {
    fontSize: theme.typography.caption.fontSize,
    color: theme.colors.text.secondary.light,
    fontWeight: '500'
  },
  noDataText: {
    textAlign: 'center',
    padding: theme.spacing.m,
    color: theme.colors.text.secondary.light
  },
  macroValues: {
    marginTop: theme.spacing.m,
    gap: theme.spacing.s
  },
  macroItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: theme.spacing.xs
  },
  macroLabel: {
    flex: 1,
    marginLeft: theme.spacing.s,
    fontSize: theme.typography.caption.fontSize,
    color: theme.colors.text.primary.light
  },
  macroValue: {
    fontSize: theme.typography.caption.fontSize,
    fontWeight: '500',
    color: theme.colors.text.primary.light
  },
  pulseAnimation: {
    transform: [{ scale: 1.2 }],
  },
});

export default OverallProgressChart;



//the y axis in day is incorrect. can you please help me solve this? the values that I can see here are 0%, 0%, 1%, 1%, 1% in day. the bars are still not correctly showing. f
// import React, { useMemo } from 'react';
// import { View, Text, ScrollView, Dimensions, StyleSheet, ActivityIndicator } from 'react-native';
// import { BarChart } from 'react-native-chart-kit';
// import { format } from 'date-fns';
// import theme from '../styles/theme';

// const { width: screenWidth } = Dimensions.get('window');
// const BAR_SPACING = 16;
// const BAR_WIDTH = {
//   day: 32,
//   week: 24,
//   month: 16
// };

// const OverallProgressChart = ({ timeFrame = 'day', chartData = null, loading = false, userData = null }) => {
//   const safeDivide = (value = 0, goal = 0) => 
//     goal > 0 ? Math.min((value / goal) * 100, 100) : 0;

//   const getBarColor = (opacity = 1) => `rgba(66, 153, 225, ${opacity})`;
  
//   const processedData = useMemo(() => {
//     if (!chartData || loading || !userData) {
//       return {
//         labels: [],
//         datasets: [{ data: [] }]
//       };
//     }

//     const goals = userData?.goals || {
//       calories: 2000,
//       protein: 50,
//       carbs: 300,
//       fat: 65
//     };

//     if (timeFrame === 'day') {
//       // For day view: Show four bars for today's macros
//       const { calories = 0, nutrients = {} } = chartData.current || {};
//       return {
//         labels: ['Calories', 'Protein', 'Carbs', 'Fat'],
//         datasets: [{
//           data: [
//             safeDivide(calories, goals.calories),
//             safeDivide(nutrients.protein || 0, goals.protein),
//             safeDivide(nutrients.carbs || 0, goals.carbs),
//             safeDivide(nutrients.fat || 0, goals.fat)
//           ],
//           colors: [
//             '#4299E1', // Calories - Blue
//             '#48BB78', // Protein - Green
//             '#ECC94B', // Carbs - Yellow
//             '#F56565'  // Fat - Red
//           ]
//         }],
//         rawValues: [
//           calories,
//           nutrients.protein || 0,
//           nutrients.carbs || 0,
//           nutrients.fat || 0
//         ]
//       };
//     } else {
//       // For week/month view: Show daily progress bars
//       const entries = chartData.dailyEntries || [];
//       const daysToShow = timeFrame === 'week' ? 7 : 30;
      
//       // Create array of last n days
//       const today = new Date();
//       const dates = Array.from({ length: daysToShow }, (_, i) => {
//         const date = new Date(today);
//         date.setDate(today.getDate() - i);
//         return date.toISOString().split('T')[0];
//       }).reverse();

//       // Map dates to data, calculating overall progress for each day
//       const progressData = dates.map(date => {
//         const entry = entries.find(e => e.dateKey === date);
        
//         if (!entry) {
//           return {
//             label: format(new Date(date), timeFrame === 'week' ? 'EEE' : 'MM/dd'),
//             progress: null
//           };
//         }

//         // Calculate overall progress as average of all goals met
//         const calorieProgress = safeDivide(entry.calories, goals.calories);
//         const proteinProgress = safeDivide(entry.nutrients?.protein, goals.protein);
//         const carbsProgress = safeDivide(entry.nutrients?.carbs, goals.carbs);
//         const fatProgress = safeDivide(entry.nutrients?.fat, goals.fat);
        
//         const overallProgress = (calorieProgress + proteinProgress + carbsProgress + fatProgress) / 4;

//         return {
//           label: format(new Date(date), timeFrame === 'week' ? 'EEE' : 'MM/dd'),
//           progress: Math.round(overallProgress)
//         };
//       });

//       return {
//         labels: progressData.map(d => d.label),
//         datasets: [{
//           data: progressData.map(d => d.progress),
//           color: (opacity = 1) => getBarColor(opacity)
//         }]
//       };
//     }
//   }, [chartData, loading, userData, timeFrame]);

//   const chartConfig = {
//     backgroundGradientFrom: theme.colors?.background?.primary?.light || '#FFFFFF',
//     backgroundGradientTo: theme.colors?.background?.primary?.light || '#FFFFFF',
//     decimalPlaces: 0,
//     color: (opacity = 1, index) => {
//       if (timeFrame === 'day' && processedData.datasets[0]?.colors) {
//         return `${processedData.datasets[0].colors[index]}${opacity}`;
//       }
//       return getBarColor(opacity);
//     },
//     labelColor: (opacity = 1) => theme.colors?.text?.primary?.light || `rgba(0, 0, 0, ${opacity})`,
//     propsForBackgroundLines: { strokeWidth: 0 },
//     barPercentage: 0.8,
//     barRadius: 4,
//     yAxisMax: 100,
//     style: { borderRadius: 16 }
//   };

//   if (loading) {
//     return (
//       <View style={[styles.chartContainer, styles.loadingContainer]}>
//         <ActivityIndicator size="large" color={theme.colors?.primary?.light || '#4299E1'} />
//       </View>
//     );
//   }

//   if (!processedData.labels.length || !processedData.datasets[0]?.data.length) {
//     return (
//       <View style={styles.chartContainer}>
//         <Text style={styles.noDataText}>No progress data available</Text>
//       </View>
//     );
//   }

//   return (
//     <View style={styles.chartContainer}>
//       <ScrollView
//         horizontal={timeFrame !== 'day'}
//         showsHorizontalScrollIndicator={false}
//         contentContainerStyle={styles.scrollContainer}
//       >
//         <BarChart
//           data={processedData}
//           width={Math.max(
//             (BAR_WIDTH[timeFrame] + BAR_SPACING) * processedData.labels.length + 40,
//             screenWidth - 40
//           )}
//           height={240}
//           chartConfig={chartConfig}
//           style={styles.chart}
//           showBarTops={false}
//           fromZero
//           yAxisLabel=""
//           yAxisSuffix="%"
//           withInnerLines={false}
//           segments={4}
//           verticalLabelRotation={timeFrame === 'month' ? 45 : 0}
//         />
//       </ScrollView>

//       {timeFrame === 'day' && (
//         <View style={styles.macroValues}>
//           {processedData.labels.map((label, index) => (
//             <View key={label} style={styles.macroItem}>
//               <View style={[styles.legendDot, { backgroundColor: processedData.datasets[0].colors[index] }]} />
//               <Text style={styles.macroLabel}>{label}</Text>
//               <Text style={styles.macroValue}>
//                 {processedData.rawValues[index].toFixed(1)}
//                 {label === 'Calories' ? ' kcal' : 'g'}
//               </Text>
//             </View>
//           ))}
//         </View>
//       )}

//       {timeFrame !== 'day' && (
//         <View style={styles.legendContainer}>
//           <View style={styles.legendItem}>
//             <View style={[styles.legendDot, { backgroundColor: '#4299E1' }]} />
//             <Text style={styles.legendText}>Daily Goal Progress</Text>
//           </View>
//         </View>
//       )}
//     </View>
//   );
// };

// const styles = StyleSheet.create({
//   chartContainer: {
//     backgroundColor: theme.colors?.background?.primary?.light || '#FFFFFF',
//     borderRadius: 16,
//     marginVertical: 12,
//     padding: 16,
//     marginLeft:-26,
//     elevation: 2,
//   },
//   loadingContainer: {
//     height: 240,
//     justifyContent: 'center',
//     alignItems: 'center'
//   },
//   chart: {
//     marginVertical: 8,
//     borderRadius: 16,
//   },
//   scrollContainer: {
//     // paddingRight: 16
//   },
//   legendContainer: {
//     flexDirection: 'row',
//     justifyContent: 'center',
//     marginTop: 16
//   },
//   legendItem: {
//     flexDirection: 'row',
//     alignItems: 'center',
//     paddingHorizontal: 8
//   },
//   legendDot: {
//     width: 12,
//     height: 12,
//     borderRadius: 6,
//     marginRight: 6
//   },
//   legendText: {
//     fontSize: 14,
//     color: theme.colors?.text?.secondary?.light || '#666666',
//     fontWeight: '500'
//   },
//   noDataText: {
//     textAlign: 'center',
//     padding: 20,
//     color: theme.colors?.text?.secondary?.light || '#666666'
//   },
//   macroValues: {
//     marginTop: 16,
//     gap: 8
//   },
//   macroItem: {
//     flexDirection: 'row',
//     alignItems: 'center',
//     paddingVertical: 4
//   },
//   macroLabel: {
//     flex: 1,
//     marginLeft: 8,
//     fontSize: 14,
//     color: theme.colors?.text?.primary?.light || '#000000'
//   },
//   macroValue: {
//     fontSize: 14,
//     fontWeight: '500',
//     color: theme.colors?.text?.primary?.light || '#000000'
//   }
// });

// export default OverallProgressChart;









// const ProgressSummary = ({ userData }) => {
//   const calculateProgress = () => {
//     const { onboarding, weight, targetWeight, goal, createdAt } = userData;
//     const initialWeight = onboarding.weight;
//     const currentWeight = weight;
//     const startDate = new Date(createdAt);

//     const totalWeightGoal = Math.abs(targetWeight - initialWeight);
//     const weightProgress = Math.abs(currentWeight - initialWeight);
//     const progressPercentage = (weightProgress / totalWeightGoal) * 100;

//     const totalDays = Math.ceil((new Date() - startDate) / (1000 * 60 * 60 * 24));
//     const estimatedTotalDays = 90;
//     const timeProgress = (totalDays / estimatedTotalDays) * 100;

//     return {
//       progressPercentage: Math.min(progressPercentage, 100),
//       timeProgress: Math.min(timeProgress, 100),
//       weightDifference: currentWeight - initialWeight,
//       remainingWeight: Math.abs(targetWeight - currentWeight),
//       isGaining: goal === 'Gain Weight'
//     };
//   };

//   const progress = calculateProgress();

//   return (
//     <View style={styles.summaryContainer}>
//       <Text style={styles.summaryTitle}>Progress Overview</Text>
      
//       <View style={styles.statsContainer}>
//         <View style={styles.statCard}>
//           <Text style={[styles.statValue, { 
//             color: progress.isGaining ? theme.colors.success : theme.colors.error 
//           }]}>
//             {Math.abs(progress.weightDifference).toFixed(1)} kg
//           </Text>
//           <Text style={styles.statLabel}>
//             {progress.weightDifference > 0 ? 'Weight Gained' : 'Weight Lost'}
//           </Text>
//         </View>

//         <View style={styles.statCard}>
//           <Text style={styles.statValue}>
//             {progress.remainingWeight.toFixed(1)} kg
//           </Text>
//           <Text style={styles.statLabel}>
//             Remaining to Goal
//           </Text>
//         </View>

//         <View style={styles.statCard}>
//           <Text style={styles.statValue}>
//             {progress.progressPercentage.toFixed(0)}%
//           </Text>
//           <Text style={styles.statLabel}>
//             Of Goal Achieved
//           </Text>
//         </View>

//         <View style={styles.statCard}>
//           <Text style={styles.statValue}>
//             {userData.currentStreak || 0}
//           </Text>
//           <Text style={styles.statLabel}>
//             Day Streak
//           </Text>
//         </View>
//       </View>

//       <View style={styles.insightCard}>
//         <Text style={styles.insightTitle}>Smart Insights</Text>
//         <Text style={styles.insightText}>
//           {progress.progressPercentage > progress.timeProgress 
//             ? "You're ahead of schedule! Keep up the great work!"
//             : "Slightly behind schedule. Consider adjusting your routine to reach your goal in time."}
//         </Text>
//         <Text style={styles.insightDetails}>
//           Current BMR: {userData.bmr.toFixed(1)} calories
//           {'\n'}
//           Daily Calorie Goal: {userData.dailyCalorieGoal} calories
//         </Text>
//       </View>
//     </View>
//   );
// };

// const styles = StyleSheet.create({
//   chartContainer: {
//     backgroundColor: theme.colors.background.primary.light,
//     borderRadius: theme.layout.borderRadius.large,
//     padding: theme.spacing.m,
//     marginVertical: theme.spacing.s,
//     shadowColor: '#000',
//     shadowOffset: { width: 0, height: 2 },
//     shadowOpacity: 0.1,
//     shadowRadius: 4,
//     elevation: 3,
//   },
//   chartWrapper: {
//     position: 'relative',
//   },
//   chart: {
//     marginVertical: theme.spacing.s,
//     borderRadius: theme.layout.borderRadius.medium,
//   },
//   tooltip: {
//     position: 'absolute',
//     backgroundColor: theme.colors.background.secondary.light,
//     padding: theme.spacing.s,
//     borderRadius: theme.layout.borderRadius.small,
//     shadowColor: '#000',
//     shadowOffset: { width: 0, height: 2 },
//     shadowOpacity: 0.25,
//     shadowRadius: 3.84,
//     elevation: 5,
//   },
//   tooltipTitle: {
//     ...theme.typography.caption1,
//     fontWeight: '600',
//     marginBottom: 2,
//   },
//   tooltipText: {
//     ...theme.typography.caption2,
//   },
//   legendContainer: {
//     flexDirection: 'row',
//     justifyContent: 'center',
//     marginTop: theme.spacing.s,
//   },
//   legendItem: {
//     flexDirection: 'row',
//     alignItems: 'center',
//     marginHorizontal: theme.spacing.s,
//   },
//   legendDot: {
//     width: 8,
//     height: 8,
//     borderRadius: 4,
//     marginRight: theme.spacing.xs,
//   },
//   legendText: {
//     ...theme.typography.caption1,
//     color: theme.colors.text.secondary.light,
//   },
//   summaryContainer: {
//     marginTop: theme.spacing.m,
//   },
//   summaryTitle: {
//     ...theme.typography.title3,
//     marginBottom: theme.spacing.m,
//   },
//   statsContainer: {
//     flexDirection: 'row',
//     flexWrap: 'wrap',
//     justifyContent: 'space-between',
//     marginBottom: theme.spacing.m,
//   },
//   statCard: {
//     width: '48%',
//     backgroundColor: theme.colors.background.primary.light,
//     borderRadius: theme.layout.borderRadius.medium,
//     padding: theme.spacing.m,
//     marginBottom: theme.spacing.s,
//     alignItems: 'center',
//     shadowColor: '#000',
//     shadowOffset: { width: 0, height: 1 },
//     shadowOpacity: 0.1,
//     shadowRadius: 2,
//     elevation: 2,
//   },
//   statValue: {
//     ...theme.typography.title2,
//     color: theme.colors.primary.light,
//     marginBottom: theme.spacing.xs,
//   },
//   statLabel: {
//     ...theme.typography.caption1,
//     color: theme.colors.text.secondary.light,
//     textAlign: 'center',
//   },
//   insightCard: {
//     backgroundColor: theme.colors.background.secondary.light,
//     borderRadius: theme.layout.borderRadius.medium,
//     padding: theme.spacing.m,
//     marginTop: theme.spacing.s,
//   },
//   insightTitle: {
//     ...theme.typography.title4,
//     marginBottom: theme.spacing.xs,
//   },
//   insightText: {
//     ...theme.typography.body,
//     color: theme.colors.text.primary.light,
//     marginBottom: theme.spacing.xs,
//   },
//   insightDetails: {
//     ...theme.typography.caption1,
//     color: theme.colors.text.secondary.light,
//   },
// });

// export { OverallProgressChart, ProgressSummary };










// import React, { useState, useCallback, useMemo, useEffect } from 'react';
// import { View, Text, Animated, Dimensions, StyleSheet, TouchableOpacity } from 'react-native';
// import { BarChart } from 'react-native-chart-kit';
// import theme from '../styles/theme';
// import { fetchCalorieEntries } from '../utils/firebase'; // Import from your firebase.js
// import { Timestamp } from 'firebase/firestore';

// const screenWidth = Dimensions.get('window').width;

// const OverallProgressChart = ({ userId, userData }) => {
//   const [activeIndex, setActiveIndex] = useState(null);
//   const [scaleAnim] = useState(new Animated.Value(1));
//   const [timeFrame, setTimeFrame] = useState('Week');
//   const [calorieData, setCalorieData] = useState([]);

//   const segments = ['Day', 'Week', 'Month'];

//   // Fetch calorie entries based on selected time frame
//   const fetchCalorieEntriesForTimeFrame = useCallback(async () => {
//     try {
//       let startDate, endDate;
//       const now = new Date();

//       switch (timeFrame) {
//         case 'Day':
//           // Last 7 days
//           startDate = Timestamp.fromDate(new Date(now.getFullYear(), now.getMonth(), now.getDate() - 6));
//           endDate = Timestamp.fromDate(now);
//           break;
//         case 'Week':
//           // Last 4 weeks
//           startDate = Timestamp.fromDate(new Date(now.getFullYear(), now.getMonth(), now.getDate() - 28));
//           endDate = Timestamp.fromDate(now);
//           break;
//         case 'Month':
//           // Last 6 months
//           startDate = Timestamp.fromDate(new Date(now.getFullYear(), now.getMonth() - 5, 1));
//           endDate = Timestamp.fromDate(now);
//           break;
//       }

//       const entries = await fetchCalorieEntries(userId, startDate, endDate);
//       setCalorieData(entries);
//     } catch (error) {
//       console.error('Error fetching calorie entries:', error);
//     }
//   }, [userId, timeFrame]);

//   useEffect(() => {
//     fetchCalorieEntriesForTimeFrame();
//   }, [fetchCalorieEntriesForTimeFrame]);

//   // Process calorie data for chart
//   const chartData = useMemo(() => {
//     const { dailyCalorieGoal, macroPercentages } = userData;

//     // Generate labels based on time frame
//     const generateLabels = () => {
//       const now = new Date();
//       switch (timeFrame) {
//         case 'Day':
//           return Array.from({ length: 7 }, (_, i) => {
//             const date = new Date(now);
//             date.setDate(date.getDate() - (6 - i));
//             return date.getDate().toString();
//           });
//         case 'Week':
//           return Array.from({ length: 4 }, (_, i) => `W${i + 1}`);
//         case 'Month':
//           return Array.from({ length: 6 }, (_, i) => {
//             const date = new Date(now);
//             date.setMonth(date.getMonth() - (5 - i));
//             return date.toLocaleString('default', { month: 'short' });
//           });
//       }
//     };

//     const labels = generateLabels();

//     // Aggregate data for each label
//     const aggregateData = (dataType) => {
//       return labels.map((label, index) => {
//         const filteredEntries = calorieData.filter(entry => {
//           const entryDate = entry.timestamp.toDate();
          
//           switch (timeFrame) {
//             case 'Day':
//               return entryDate.getDate() === parseInt(label);
//             case 'Week':
//               const weekNumber = Math.floor(index);
//               return Math.floor((entryDate - new Date()) / (7 * 24 * 60 * 60 * 1000)) === -weekNumber;
//             case 'Month':
//               return entryDate.toLocaleString('default', { month: 'short' }) === label;
//           }
//         });

//         const total = filteredEntries.reduce((sum, entry) => sum + entry[dataType], 0);
//         const percentage = (total / dailyCalorieGoal) * 100;
        
//         return Math.min(percentage, 100);
//       });
//     };

//     return {
//       labels,
//       datasets: [
//         {
//           data: aggregateData('calories'),
//           color: (opacity = 1) => `rgba(66, 153, 225, ${opacity})`, // Blue - Calories
//           strokeWidth: 2
//         },
//         {
//           data: aggregateData('protein'),
//           color: (opacity = 1) => `rgba(72, 187, 120, ${opacity})`, // Green - Protein
//           strokeWidth: 2
//         },
//         {
//           data: aggregateData('carbs'),
//           color: (opacity = 1) => `rgba(236, 201, 75, ${opacity})`, // Yellow - Carbs
//           strokeWidth: 2
//         },
//         {
//           data: aggregateData('fat'),
//           color: (opacity = 1) => `rgba(245, 101, 101, ${opacity})`, // Red - Fat
//           strokeWidth: 2
//         }
//       ]
//     };
//   }, [calorieData, timeFrame, userData]);


//   const handleDataPointClick = useCallback((data) => {
//     const index = data.index;
//     setActiveIndex(index === activeIndex ? null : index);
//     Animated.sequence([
//       Animated.timing(scaleAnim, {
//         toValue: 0.95,
//         duration: 100,
//         useNativeDriver: true
//       }),
//       Animated.spring(scaleAnim, {
//         toValue: 1,
//         speed: 12,
//         bounciness: 6,
//         useNativeDriver: true
//       })
//     ]).start();
//   }, [activeIndex, scaleAnim]);

//   const chartConfig = {
//     backgroundColor: theme.colors.background.primary.light,
//     backgroundGradientFrom: theme.colors.background.primary.light,
//     backgroundGradientTo: theme.colors.background.primary.light,
//     decimalPlaces: 0,
//     color: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
//     labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
//     style: {
//       borderRadius: 16,
//     },
//     propsForBackgroundLines: {
//       strokeDasharray: '',
//       strokeWidth: 1,
//       stroke: "rgba(0,0,0,0.1)",
//     },
//     propsForLabels: {
//       fontSize: 12,
//       fontWeight: '500',
//     }
//   };

//   if (!chartData) return null;

//   return (
//     <Animated.View style={[styles.chartContainer, { transform: [{ scale: scaleAnim }] }]}>
//       <View style={styles.chartWrapper}>
//         <BarChart
//           data={chartData}
//           width={screenWidth - 40}
//           height={220}
//           chartConfig={chartConfig}
//           style={styles.chart}
//           showBarTops={false}
//           fromZero={true}
//           onDataPointClick={handleDataPointClick}
//           yAxisLabel="%"
//           yAxisSuffix=""
//           withInnerLines={true}
//           segments={5}
//         />
//       </View>

//       {activeIndex !== null && chartData.datasets[0].data[activeIndex] && (
//         <View style={[styles.tooltip, {
//           top: 100,
//           left: (screenWidth - 40) * (activeIndex / (chartData.labels.length - 1)) - 45
//         }]}>
//           <Text style={styles.tooltipTitle}>{chartData.labels[activeIndex]}</Text>
//           <Text style={styles.tooltipText}>
//             Calories: {chartData.datasets[0].data[activeIndex].toFixed(1)}%
//           </Text>
//           <Text style={styles.tooltipText}>
//             Protein: {chartData.datasets[1].data[activeIndex].toFixed(1)}%
//           </Text>
//           <Text style={styles.tooltipText}>
//             Carbs: {chartData.datasets[2].data[activeIndex].toFixed(1)}%
//           </Text>
//           <Text style={styles.tooltipText}>
//             Fat: {chartData.datasets[3].data[activeIndex].toFixed(1)}%
//           </Text>
//         </View>
//       )}

//       <View style={styles.legendContainer}>
//         <View style={styles.legendItem}>
//           <View style={[styles.legendDot, { backgroundColor: '#EEEEEE' }]} />
//           <Text style={styles.legendText}>Calories</Text>
//         </View>
//         <View style={styles.legendItem}>
//           <View style={[styles.legendDot, { backgroundColor: '#48BB78' }]} />
//           <Text style={styles.legendText}>Protein</Text>
//         </View>
//         <View style={styles.legendItem}>
//           <View style={[styles.legendDot, { backgroundColor: '#ECC94B' }]} />
//           <Text style={styles.legendText}>Carbs</Text>
//         </View>
//         <View style={styles.legendItem}>
//           <View style={[styles.legendDot, { backgroundColor: '#F56565' }]} />
//           <Text style={styles.legendText}>Fat</Text>
//         </View>
//       </View>
//     </Animated.View>
//   );
// };

// const ProgressSummary = ({ userData }) => {
//   const calculateProgress = () => {
//     const {
//       onboarding: { weight: initialWeight },
//       weight: currentWeight,
//       targetWeight,
//       goal,
//       createdAt
//     } = userData;

//     const totalWeightGoal = Math.abs(targetWeight - initialWeight);
//     const weightProgress = Math.abs(currentWeight - initialWeight);
//     const progressPercentage = (weightProgress / totalWeightGoal) * 100;

//     const startDate = new Date(createdAt);
//     const totalDays = Math.ceil((new Date() - startDate) / (1000 * 60 * 60 * 24));
//     const estimatedTotalDays = 90; // Assuming 90 days for goal achievement
//     const timeProgress = (totalDays / estimatedTotalDays) * 100;

//     const weightDifference = currentWeight - initialWeight;
//     const remainingWeight = Math.abs(targetWeight - currentWeight);
    
//     return {
//       progressPercentage: Math.min(progressPercentage, 100),
//       timeProgress: Math.min(timeProgress, 100),
//       weightDifference,
//       remainingWeight,
//       isGaining: goal === 'Gain Weight'
//     };
//   };

//   const progress = calculateProgress();

//   return (
//     <View style={styles.summaryContainer}>
//       <Text style={styles.summaryTitle}>Progress Overview</Text>
      
//       <View style={styles.statsContainer}>
//         <View style={styles.statCard}>
//           <Text style={[styles.statValue, { 
//             color: progress.isGaining ? theme.colors.success : theme.colors.error 
//           }]}>
//             {Math.abs(progress.weightDifference).toFixed(1)} kg
//           </Text>
//           <Text style={styles.statLabel}>
//             {progress.weightDifference > 0 ? 'Weight Gained' : 'Weight Lost'}
//           </Text>
//         </View>

//         <View style={styles.statCard}>
//           <Text style={styles.statValue}>
//             {progress.remainingWeight.toFixed(1)} kg
//           </Text>
//           <Text style={styles.statLabel}>
//             Remaining to Goal
//           </Text>
//         </View>

//         <View style={styles.statCard}>
//           <Text style={styles.statValue}>
//             {progress.progressPercentage.toFixed(0)}%
//           </Text>
//           <Text style={styles.statLabel}>
//             Of Goal Achieved
//           </Text>
//         </View>

//         <View style={styles.statCard}>
//           <Text style={styles.statValue}>
//             {userData.currentStreak || 0}
//           </Text>
//           <Text style={styles.statLabel}>
//             Day Streak
//           </Text>
//         </View>
//       </View>

//       <View style={styles.insightCard}>
//         <Text style={styles.insightTitle}>Smart Insights</Text>
//         <Text style={styles.insightText}>
//           {progress.progressPercentage > progress.timeProgress 
//             ? "You're ahead of schedule! Keep up the great work!"
//             : "Slightly behind schedule. Consider adjusting your routine to reach your goal in time."}
//         </Text>
//         <Text style={styles.insightDetails}>
//           Current BMR: {userData.bmr.toFixed(1)} calories
//           {'\n'}
//           Daily Calorie Goal: {userData.dailyCalorieGoal} calories
//         </Text>
//       </View>
//     </View>
//   );
// };

// const styles = StyleSheet.create({
//   chartContainer: {
//     backgroundColor: theme.colors.background.primary.light,
//     borderRadius: theme.layout.borderRadius.large,
//     padding: theme.spacing.m,
//     marginVertical: theme.spacing.s,
//     shadowColor: '#000',
//     shadowOffset: { width: 0, height: 2 },
//     shadowOpacity: 0.1,
//     shadowRadius: 4,
//     elevation: 3,
//   },
//   chartTitle: {
//     ...theme.typography.title3,
//     marginBottom: theme.spacing.s,
//   },
//   chart: {
//     marginVertical: theme.spacing.s,
//     borderRadius: theme.layout.borderRadius.medium,
//   },
//   tooltip: {
//     position: 'absolute',
//     backgroundColor: theme.colors.background.secondary.light,
//     padding: theme.spacing.s,
//     borderRadius: theme.layout.borderRadius.small,
//     shadowColor: '#000',
//     shadowOffset: { width: 0, height: 2 },
//     shadowOpacity: 0.25,
//     shadowRadius: 3.84,
//     elevation: 5,
//   },
//   tooltipTitle: {
//     ...theme.typography.caption1,
//     fontWeight: '600',
//     marginBottom: 2,
//   },
//   tooltipText: {
//     ...theme.typography.caption2,
//     color: theme.colors.text.secondary.light,
//   },
//   legendContainer: {
//     flexDirection: 'row',
//     justifyContent: 'center',
//     marginTop: theme.spacing.s,
//   },
//   legendItem: {
//     flexDirection: 'row',
//     alignItems: 'center',
//     marginHorizontal: theme.spacing.s,
//   },
//   legendDot: {
//     width: 8,
//     height: 8,
//     borderRadius: 4,
//     marginRight: theme.spacing.xs,
//   },
//   legendText: {
//     ...theme.typography.caption1,
//     color: theme.colors.text.secondary.light,
//   },
//   summaryContainer: {
//     marginTop: theme.spacing.m,
//   },
//   summaryTitle: {
//     ...theme.typography.title3,
//     marginBottom: theme.spacing.m,
//   },
//   statsContainer: {
//     flexDirection: 'row',
//     flexWrap: 'wrap',
//     justifyContent: 'space-between',
//     marginBottom: theme.spacing.m,
//   },
//   statCard: {
//     width: '48%',
//     backgroundColor: theme.colors.background.primary.light,
//     borderRadius: theme.layout.borderRadius.medium,
//     padding: theme.spacing.m,
//     marginBottom: theme.spacing.s,
//     alignItems: 'center',
//     shadowColor: '#000',
//     shadowOffset: { width: 0, height: 1 },
//     shadowOpacity: 0.1,
//     shadowRadius: 2,
//     elevation: 2,
//   },
//   statValue: {
//     ...theme.typography.title2,
//     color: theme.colors.primary.light,
//     marginBottom: theme.spacing.xs,
//   },
//   statLabel: {
//     ...theme.typography.caption1,
//     color: theme.colors.text.secondary.light,
//     textAlign: 'center',
//   },
//   insightCard: {
//     backgroundColor: theme.colors.background.secondary.light,
//     borderRadius: theme.layout.borderRadius.medium,
//     padding: theme.spacing.m,
//     marginTop: theme.spacing.s,
//   },
//   insightTitle: {
//     ...theme.typography.title4,
//     marginBottom: theme.spacing.xs,
//   },
//   insightText: {
//     ...theme.typography.body,
//     color: theme.colors.text.primary.light,
//     marginBottom: theme.spacing.xs,
//   },
//   insightDetails: {
//     ...theme.typography.caption1,
//     color: theme.colors.text.secondary.light,
//   },
//   emptyContainer: {
//     padding: theme.spacing.m,
//     alignItems: 'center',
//     justifyContent: 'center',
//   },
//   emptyText: {
//     ...theme.typography.body,
//     color: theme.colors.text.secondary.light,
//   },
//   chartWrapper: {
//     position: 'relative',
//   },
//   lineChartOverlay: {
//     position: 'absolute',
//     top: 0,
//     left: 0,
//     right: 0,
//     bottom: 0,
//     backgroundColor: 'transparent'
//   },
//   chartContainer: {
//     backgroundColor: theme.colors.background.primary.light,
//     borderRadius: theme.layout.borderRadius.large,
//     padding: theme.spacing.m,
//     marginVertical: theme.spacing.s,
//     shadowColor: '#000',
//     shadowOffset: { width: 0, height: 2 },
//     shadowOpacity: 0.1,
//     shadowRadius: 4,
//     elevation: 3,
//   },
//   chartTitle: {
//     ...theme.typography.title3,
//     marginBottom: theme.spacing.s,
//   },
//   chart: {
//     marginVertical: theme.spacing.s,
//     borderRadius: theme.layout.borderRadius.medium,
//   },
//   chartWrapper: {
//     position: 'relative',
//   },
//   lineChartOverlay: {
//     position: 'absolute',
//     top: 0,
//     left: 0,
//     right: 0,
//     bottom: 0,
//     backgroundColor: 'transparent'
//   },
//   tooltip: {
//     position: 'absolute',
//     backgroundColor: theme.colors.background.secondary.light,
//     padding: theme.spacing.s,
//     borderRadius: theme.layout.borderRadius.small,
//     shadowColor: '#000',
//     shadowOffset: { width: 0, height: 2 },
//     shadowOpacity: 0.25,
//     shadowRadius: 3.84,
//     elevation: 5,
//   },
//   tooltipTitle: {
//     ...theme.typography.caption1,
//     fontWeight: '600',
//     marginBottom: 2,
//   },
//   tooltipText: {
//     ...theme.typography.caption2,
//     color: theme.colors.text.secondary.light,
//   },
//   legendContainer: {
//     flexDirection: 'row',
//     justifyContent: 'center',
//     marginTop: theme.spacing.s,
//   },
//   legendItem: {
//     flexDirection: 'row',
//     alignItems: 'center',
//     marginHorizontal: theme.spacing.s,
//   },
//   legendDot: {
//     width: 8,
//     height: 8,
//     borderRadius: 4,
//     marginRight: theme.spacing.xs,
//   },
//   legendText: {
//     ...theme.typography.caption1,
//     color: theme.colors.text.secondary.light,
//   },
//   emptyContainer: {
//     padding: theme.spacing.m,
//     alignItems: 'center',
//     justifyContent: 'center',
//   },
//   emptyText: {
//     ...theme.typography.body,
//     color: theme.colors.text.secondary.light,
//   },

//   segmentedControl: {
//     flexDirection: 'row',
//     backgroundColor: theme.colors.background.secondary.light,
//     borderRadius: theme.layout.borderRadius.large,
//     padding: 2,
//     marginBottom: theme.spacing.m,
//   },
//   segment: {
//     flex: 1,
//     paddingVertical: 8,
//     alignItems: 'center',
//   },
//   activeSegment: {
//     backgroundColor: 'white',
//     borderRadius: theme.layout.borderRadius.large,
//     shadowColor: '#000',
//     shadowOffset: { width: 0, height: 1 },
//     shadowOpacity: 0.1,
//     shadowRadius: 2,
//     elevation: 1,
//   },
//   firstSegment: {
//     borderTopLeftRadius: theme.layout.borderRadius.large,
//     borderBottomLeftRadius: theme.layout.borderRadius.large,
//   },
//   lastSegment: {
//     borderTopRightRadius: theme.layout.borderRadius.large,
//     borderBottomRightRadius: theme.layout.borderRadius.large,
//   },
//   segmentText: {
//     ...theme.typography.body,
//     color: theme.colors.text.secondary.light,
//   },
//   activeSegmentText: {
//     color: theme.colors.text.primary.light,
//     fontWeight: '600',
//   },
// });

// export { OverallProgressChart, ProgressSummary };
