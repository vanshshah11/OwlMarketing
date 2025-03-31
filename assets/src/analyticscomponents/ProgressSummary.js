// /Users/vanshshah/Desktop/New_app/5th_WellAI/WellAI/src/analyticscomponents/ProgressSummary.js
// for ProgressSummary do something in the lines of this. this was my previous rendition but still not up to the mark. 

import React, { useMemo, useEffect, useState } from 'react';
import { View, Text, StyleSheet, Animated, useWindowDimensions } from 'react-native';
import { SFSymbol } from 'react-native-sfsymbols';
import theme from '../styles/theme';
import { auth, fetchUserData, fetchProgressData } from '../utils/firebase';
import { Timestamp } from 'firebase/firestore';
import * as Animatable from 'react-native-animatable';

const logEvent = (event, details = {}) => {
  console.log(`[ProgressSummary] ${event}`, details);
};

const ProgressSummary = ({ goals }) => {
  const [metrics, setMetrics] = useState({
    completed: 0,
    total: 0,
    completionRate: 0,
    trend: 'Neutral',
    trendColor: theme.colors.warning.light,
  });
  const [loading, setLoading] = useState(true);
  const { width: screenWidth } = useWindowDimensions();

  const fadeAnim = useMemo(() => new Animated.Value(0), []);

  useEffect(() => {
    if (goals.length > 0) {
      logEvent('Processing goals', { count: goals.length });
      const totalGoals = goals.length;
      const completed = goals.filter(goal => 
        goal.progress.length > 0 && 
        goal.progress.some(entry => entry.value >= goal.target)
      ).length;
  
      const completionRate = totalGoals > 0 ? (completed / totalGoals) * 100 : 0;
      
      logEvent('Goals processed', { 
        completed,
        total: totalGoals,
        completionRate 
      });
  
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: theme.animationDurations.medium,
        useNativeDriver: true,
      }).start();
  
      fetchUserProgress();
    }
  }, [goals]); // Dependency is now goals

  const fetchUserProgress = async () => {
    try {
      setLoading(true);
      logEvent('Fetching user progress');
      
      const userId = auth.currentUser?.uid;
      if (!userId) {
        logEvent('No authenticated user found');
        return;
      }
  
      const totalGoals = goals.length;
      const completed = goals.filter(goal => 
        goal.progress.length > 0 && 
        goal.progress.some(entry => entry.value >= goal.target)
      ).length;
  
      const completionRate = totalGoals > 0 ? (completed / totalGoals) * 100 : 0;
  
      // Create a map of goals for trend calculation
      const goalsMap = Object.fromEntries(
        goals.map(goal => [goal.id, goal.target])
      );
  
      // Flatten all progress entries
      const allProgressData = goals.flatMap(goal => 
        goal.progress.map(entry => ({
          ...entry,
          goalId: goal.id
        }))
      );
  
      const trend = calculateTrend(allProgressData, goalsMap);
  
      setMetrics({
        completed,
        total: totalGoals,
        completionRate,
        ...trend,
      });

      logEvent('Progress data fetched', { 
        completed: metrics.completed,
        total: metrics.total,
        trend: metrics.trend 
      });

    } catch (error) {
      logEvent('Error fetching progress', { error: error.message });
      console.error('Error fetching progress:', error);
    } finally {
      setLoading(false);
    }
  };

  const cardWidth = useMemo(() => {
    const padding = theme.spacing.m * 2;
    const gap = theme.spacing.s;
    return (screenWidth - padding - (gap * 2)) / 3;
  }, [screenWidth]);

  if (loading) {
    logEvent('Rendering loading state');
    return null;
  }

  logEvent('Rendering progress summary', {
    completionRate: metrics.completionRate,
    trend: metrics.trend
  });

  return (
    <Animated.View style={[styles.container, { opacity: fadeAnim }]}>
      <SummaryHeader metrics={metrics} />
      <View style={styles.metricsContainer}>
        <Animatable.View 
          animation="fadeInUp" 
          delay={300} 
          duration={theme.animationDurations.medium}
        >
          <MetricCard
            icon="chart.bar.fill"
            label="Completed"
            value={`${metrics.completed}/${metrics.total}`}
            subtitle="Goals"
            color={theme.colors.primary.light}
            width={cardWidth}
          />
        </Animatable.View>

        <Animatable.View 
          animation="fadeInUp" 
          delay={500} 
          duration={theme.animationDurations.medium}
        >
          <MetricCard
            icon="chart.pie.fill"
            label="Completion"
            value={`${Math.round(metrics.completionRate)}%`}
            subtitle="Rate"
            color={theme.colors.success.light}
            width={cardWidth}
          />
        </Animatable.View>

        <Animatable.View 
          animation="fadeInUp" 
          delay={700} 
          duration={theme.animationDurations.medium}
        >
          <MetricCard
            icon="arrow.up.right.circle.fill"
            label="Trend"
            value={metrics.trend}
            subtitle="This Week"
            color={metrics.trendColor}
            width={cardWidth}
          />
        </Animatable.View>
      </View>
    </Animated.View>
  );
};

const SummaryHeader = ({ metrics }) => (
  <Animatable.View 
    animation="fadeInDown" 
    duration={theme.animationDurations.medium} 
    style={styles.header}
  >
    <View style={styles.titleContainer}>
      <Text style={styles.title}>Progress Summary</Text>
    </View>
    <Text style={styles.subtitle}>
      {getMotivationalMessage(metrics.completionRate)}
    </Text>
  </Animatable.View>
);

const MetricCard = ({ icon, label, value, subtitle, color, width }) => (
  <View style={[styles.metricCard, { width }]}>
    <SFSymbol 
      name={icon} 
      weight="semibold"
      scale="medium"
      color={color} 
      size={theme.layout.iconSize.medium} 
      style={styles.icon}
    />
    <Text style={styles.metricLabel}>{label}</Text>
    <Text style={styles.metricValue}>{value}</Text>
    <Text style={styles.metricSubtitle}>{subtitle}</Text>
  </View>
);

const calculateTrend = (progressData, goals) => {
  if (progressData.length === 0) {
    logEvent('No progress data for trend calculation');
    return { 
      trend: 'Neutral', 
      trendColor: theme.colors.warning.light 
    };
  }

  // Sort progress data by date
  const sortedProgress = progressData.sort((a, b) => a.date - b.date);
  
  const recentProgress = sortedProgress.slice(-3);
  const olderProgress = sortedProgress.slice(0, Math.min(3, sortedProgress.length));
  
  const recentCompletion = recentProgress.reduce((acc, entry) => 
    acc + (entry.value >= (goals[entry.goalId] || 0) ? 1 : 0), 0);
  
  const olderCompletion = olderProgress.reduce((acc, entry) => 
    acc + (entry.value >= (goals[entry.goalId] || 0) ? 1 : 0), 0);

  if (recentCompletion > olderCompletion) {
    const result = { 
      trend: 'Rising', 
      trendColor: theme.colors.success.light 
    };
    logEvent('Trend calculated', { trend: result.trend });
    return result;
  } else if (recentCompletion < olderCompletion) {
    const result = { 
      trend: 'Falling', 
      trendColor: theme.colors.error.light 
    };
    logEvent('Trend calculated', { trend: result.trend });
    return result;
  }
  const result = { 
    trend: 'Stable', 
    trendColor: theme.colors.warning.light 
  };
  logEvent('Trend calculated', { trend: result.trend });
  return result;
};

const getMotivationalMessage = (completionRate) => {
  if (completionRate >= 100) return 'All goals achieved! Outstanding work!';
  if (completionRate >= 75) return 'Almost there! Keep pushing!';
  if (completionRate >= 50) return 'Halfway there! You\'re doing great!';
  if (completionRate >= 25) return 'Great start! Keep going!';
  return 'Every step counts! You\'ve got this!';
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: theme.colors.background.secondary.light,
    borderRadius: theme.layout.borderRadius.large,
    ...theme.mixins.padding.all(theme.spacing.m),
    ...theme.mixins.margin.vertical(theme.spacing.xxxs),
    ...theme.shadows.medium,
  },
  header: {
    ...theme.mixins.margin.bottom(theme.spacing.l),
  },
  titleContainer: {
    ...theme.mixins.row,
  },
  title: {
    ...theme.typography.headline,
    color: theme.colors.text.primary.light,
  },
  subtitle: {
    ...theme.typography.footnote,
    color: theme.colors.text.secondary.light,
    ...theme.mixins.margin.top(theme.spacing.xs),
  },
  metricsContainer: {
    ...theme.mixins.row,
    justifyContent: 'space-between',
    gap: theme.spacing.xxxs,
  },
  metricCard: {
    ...theme.mixins.center,
    ...theme.mixins.padding.vertical(theme.spacing.m),//xl
    borderRadius: theme.layout.borderRadius.medium,
  },
  icon: {
    ...theme.mixins.margin.bottom(theme.spacing.xs),
  },
  metricLabel: {
    ...theme.typography.caption,
    color: theme.colors.text.secondary.light,
    ...theme.mixins.margin.top(theme.spacing.xs),
  },
  metricValue: {
    ...theme.typography.headline,
    color: theme.colors.text.primary.light,
    ...theme.mixins.margin.vertical(theme.spacing.xxs),
  },
  metricSubtitle: {
    ...theme.typography.caption2,
    color: theme.colors.text.secondary.light,
  },
});

export default React.memo(
  ProgressSummary, 
  (prevProps, nextProps) => {
    // Only re-render if goals have meaningfully changed
    return prevProps.goals.length === nextProps.goals.length &&
           prevProps.goals.every((goal, index) => 
             goal.id === nextProps.goals[index].id && 
             goal.progress.length === nextProps.goals[index].progress.length
           );
  }
);

/* 
import React, { useMemo, useEffect, useState } from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';
import { SFSymbol } from 'react-native-sfsymbols';
import theme from '../styles/theme';
import { auth, db } from '../utils/firebase';
import { collection, query, where, getDocs, Timestamp } from 'firebase/firestore';
import * as Animatable from 'react-native-animatable';

const ProgressSummary = () => {
  const [metrics, setMetrics] = useState({
    completed: 0,
    total: 5,
    completionRate: 0,
    averageProgress: 0,
    trend: 'Neutral',
    trendColor: theme.colors.warning.light,
  });

  const fadeAnim = new Animated.Value(0);

  useEffect(() => {
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 1000,
      useNativeDriver: true,
    }).start();

    fetchUserProgress();
  }, []);

  const fetchUserProgress = async () => {
    try {
      const userId = auth.currentUser?.uid;
      if (!userId) return;

      const startDate = new Date();
      startDate.setDate(startDate.getDate() - 7); // Last 7 days

      const caloriesRef = collection(db, 'calories');
      const q = query(
        caloriesRef,
        where('userId', '==', userId),
        where('timestamp', '>=', Timestamp.fromDate(startDate))
      );

      const querySnapshot = await getDocs(q);
      const entries = querySnapshot.docs.map(doc => doc.data());

      // Calculate metrics based on entries
      const calculatedMetrics = calculateMetrics(entries);
      setMetrics(calculatedMetrics);
    } catch (error) {
      console.error('Error fetching progress:', error);
    }
  };

  return (
    <Animated.View style={[styles.container, { opacity: fadeAnim }]}>
      <SummaryHeader metrics={metrics} />
      <View style={styles.metricsContainer}>
        <Animatable.View 
          animation="fadeInUp" 
          delay={300} 
          duration={1000}
        >
          <MetricCard
            icon="chart.bar.fill"
            label="Completed"
            value={`${metrics.completed}/${metrics.total}`}
            subtitle="Goals"
            color={theme.colors.primary.light}
          />
        </Animatable.View>

        <Animatable.View 
          animation="fadeInUp" 
          delay={500} 
          duration={1000}
        >
          <MetricCard
            icon="chart.pie.fill"
            label="Completion"
            value={`${Math.round(metrics.completionRate)}%`}
            subtitle="Rate"
            color={theme.colors.success.light}
          />
        </Animatable.View>

        <Animatable.View 
          animation="fadeInUp" 
          delay={700} 
          duration={1000}
        >
          <MetricCard
            icon="arrow.up.right.circle.fill"
            label="Trend"
            value={metrics.trend}
            subtitle="This Week"
            color={metrics.trendColor}
          />
        </Animatable.View>
      </View>
    </Animated.View>
  );
};

const SummaryHeader = ({ metrics }) => (
  <Animatable.View 
    animation="fadeInDown" 
    duration={1000} 
    style={styles.header}
  >
    <View style={styles.titleContainer}>
      <Text style={styles.title}>Progress Summary</Text>
    </View>
    <Text style={styles.subtitle}>
      {getMotivationalMessage(metrics.completionRate)}
    </Text>
  </Animatable.View>
);

const MetricCard = ({ icon, label, value, subtitle, color }) => (
  <View style={styles.metricCard}>
    <SFSymbol 
      name={icon} 
      weight="bold" 
      scale="large" 
      color={color} 
      size={24} 
    />
    <Text style={styles.metricLabel}>{label}</Text>
    <Text style={styles.metricValue}>{value}</Text>
    <Text style={styles.metricSubtitle}>{subtitle}</Text>
  </View>
);

const calculateMetrics = (entries) => {
  const total = 5; // Total goals
  const completed = entries.filter(entry => entry.completed).length;
  const completionRate = (completed / total) * 100;
  
  // Calculate trend
  let trend = 'Neutral';
  let trendColor = theme.colors.warning.light;
  
  if (completionRate >= 75) {
    trend = 'Rising';
    trendColor = theme.colors.success.light;
  } else if (completionRate <= 25) {
    trend = 'Falling';
    trendColor = theme.colors.error.light;
  }

  return {
    completed,
    total,
    completionRate,
    averageProgress: completionRate,
    trend,
    trendColor,
  };
};

const getMotivationalMessage = (completionRate) => {
  if (completionRate >= 100) return 'All goals achieved! Outstanding work!';
  if (completionRate >= 75) return 'Almost there! Keep pushing!';
  if (completionRate >= 50) return 'Halfway there! You\'re doing great!';
  if (completionRate >= 25) return 'Great start! Keep going!';
  return 'Every step counts! You\'ve got this!';
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: theme.colors.background.secondary.light,
    borderRadius: theme.layout.borderRadius.large,
    padding: theme.spacing.m,
    marginBottom: theme.spacing.m,
    ...theme.shadows.medium,
  },
  header: {
    marginBottom: theme.spacing.l,
  },
  titleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  title: {
    ...theme.typography.headline,
    color: theme.colors.text.primary.light,
  },
  subtitle: {
    ...theme.typography.footnote,
    color: theme.colors.text.secondary.light,
  },
  metricsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  metricCard: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: theme.spacing.l,
  },
  metricLabel: {
    ...theme.typography.caption,
    color: theme.colors.text.secondary.light,
    paddingTop: theme.spacing.m,
  },
  metricValue: {
    ...theme.typography.title3,
    color: theme.colors.text.primary.light,
  },
  metricSubtitle: {
    ...theme.typography.caption,
    color: theme.colors.text.secondary.light,
  },
});

export default ProgressSummary;
*/






// import React, { useMemo } from 'react';
// import { View, Text, StyleSheet, Animated, TouchableOpacity } from 'react-native';
// import { SFSymbol } from 'react-native-sfsymbols';
// import theme from '../styles/theme';

// const ProgressSummary = ({ goals }) => {
//   const metrics = useMemo(() => calculateMetrics(goals), [goals]);

//   if (!goals || goals.length === 0) {
//     return <EmptyState />;
//   }

//   return (
//     <View style={styles.container}>
//       <SummaryHeader metrics={metrics} />
//       <OverallMetrics metrics={metrics} />
//       <GoalsList goals={goals} />
//     </View>
//   );
// };

// const SummaryHeader = ({ metrics }) => (
//   <View style={styles.header}>
//     <View style={styles.titleContainer}>
//       <Text style={styles.title}>Progress Summary</Text>
//     </View>
//     <Text style={styles.subtitle}>
//       {getMotivationalMessage(metrics.completionRate)}
//     </Text>
//   </View>
// );

// const OverallMetrics = ({ metrics }) => (
//   <View style={styles.metricsContainer}>
//     <MetricCard
//       icon="trophy.fill"
//       label="Completed"
//       value={`${metrics.completed}/${metrics.total}`}
//       subtitle="Goals"
//       color={theme.colors.success.light}
//     />
//     <MetricCard
//       icon="chart.bar.fill"
//       label="Average"
//       value={`${metrics.averageProgress}%`}
//       subtitle="Completion"
//       color={theme.colors.primary.light}
//     />
//     <MetricCard
//       icon="arrow.up.right.circle.fill"
//       label="Trending"
//       value={metrics.trend}
//       subtitle="Direction"
//       color={metrics.trendColor}
//     />
//   </View>
// );

// const MetricCard = ({ icon, label, value, subtitle, color }) => (
//   <View style={styles.metricCard}>
//     <SFSymbol name={icon} size={24} color={color} />
//     <Text style={styles.metricLabel}>{label}</Text>
//     <Text style={styles.metricValue}>{value}</Text>
//     <Text style={styles.metricSubtitle}>{subtitle}</Text>
//   </View>
// );

// const GoalsList = ({ goals }) => (
//     <View style={styles.goalsContainer}>
//       <Text style={styles.sectionTitle}>Individual Goals</Text>
//       {goals.map((goal, index) => (
//         <GoalProgressCard key={goal.id || index} goal={goal} />
//       ))}
//     </View>
//   );
  
//   const GoalProgressCard = ({ goal }) => {
//     const progress = useMemo(() => calculateGoalProgress(goal), [goal]);
//     const progressColor = getProgressColor(progress.percentage);
//     const [animation] = React.useState(new Animated.Value(0));
  
//     React.useEffect(() => {
//       Animated.timing(animation, {
//         toValue: progress.percentage,
//         duration: 1000,
//         useNativeDriver: false,
//       }).start();
//     }, [progress.percentage]);
  
//     return (
//       <View style={styles.goalCard}>
//         <View style={styles.goalHeader}>
//           <View style={styles.goalTitleContainer}>
//             <SFSymbol 
//               name={getGoalIcon(goal.name)} 
//               size={20} 
//               color={progressColor} 
//             />
//             <Text style={styles.goalTitle}>{goal.name}</Text>
//           </View>
//           <Text style={[styles.goalStatus, { color: progressColor }]}>
//             {progress.statusText}
//           </Text>
//         </View>
  
//         <View style={styles.progressContainer}>
//           <View style={styles.progressBarContainer}>
//             <Animated.View
//               style={[
//                 styles.progressBar,
//                 {
//                   width: animation.interpolate({
//                     inputRange: [0, 100],
//                     outputRange: ['0%', '100%'],
//                   }),
//                   backgroundColor: progressColor,
//                 },
//               ]}
//             />
//           </View>
//           <View style={styles.progressDetails}>
//             <Text style={styles.progressText}>
//               {progress.current.toFixed(1)} / {goal.target} {goal.unit}
//             </Text>
//             <Text style={styles.progressPercentage}>
//               {progress.percentage.toFixed(0)}%
//             </Text>
//           </View>
//         </View>
  
//         {progress.trend && (
//           <View style={styles.trendContainer}>
//             <SFSymbol 
//               name={progress.trend.icon} 
//               size={16} 
//               color={progress.trend.color} 
//             />
//             <Text style={[styles.trendText, { color: progress.trend.color }]}>
//               {progress.trend.text}
//             </Text>
//           </View>
//         )}
//       </View>
//     );
//   };
  
//   const EmptyState = () => (
//     <View style={styles.emptyContainer}>
//       <SFSymbol 
//         name="square.stack.3d.up.fill" 
//         size={40} 
//         color={theme.colors.text.secondary.light} 
//       />
//       <Text style={styles.emptyTitle}>No Goals Set</Text>
//       <Text style={styles.emptyText}>
//         Start by setting some goals to track your progress
//       </Text>
//       <TouchableOpacity style={styles.addButton}>
//         <Text style={styles.addButtonText}>Add Your First Goal</Text>
//       </TouchableOpacity>
//     </View>
//   );
  
//   // Helper functions
//   const calculateMetrics = (goals) => {
//     if (!goals || goals.length === 0) {
//       return {
//         completed: 0,
//         total: 0,
//         completionRate: 0,
//         averageProgress: 0,
//         trend: 'Neutral',
//         trendColor: theme.colors.warning.light,
//       };
//     }
  
//     const completed = goals.filter(goal => 
//       calculateGoalProgress(goal).percentage >= 100
//     ).length;
  
//     const averageProgress = goals.reduce((sum, goal) => 
//       sum + calculateGoalProgress(goal).percentage, 0
//     ) / goals.length;
  
//     const trend = calculateOverallTrend(goals);
  
//     return {
//       completed,
//       total: goals.length,
//       completionRate: (completed / goals.length) * 100,
//       averageProgress: Math.round(averageProgress),
//       trend: trend.text,
//       trendColor: trend.color,
//     };
//   };
  
//   const calculateGoalProgress = (goal) => {
//     if (!goal.progress || goal.progress.length === 0) {
//       return {
//         current: 0,
//         percentage: 0,
//         statusText: 'Not Started',
//         trend: null,
//       };
//     }
  
//     const current = goal.progress[goal.progress.length - 1].value;
//     const percentage = Math.min((current / goal.target) * 100, 100);
//     const trend = calculateProgressTrend(goal.progress);
  
//     return {
//       current,
//       percentage,
//       statusText: getStatusText(percentage),
//       trend,
//     };
//   };
  
//   const calculateProgressTrend = (progress) => {
//     if (progress.length < 2) return null;
  
//     const recentValues = progress.slice(-3);
//     const changes = recentValues.map((entry, i) => 
//       i > 0 ? entry.value - recentValues[i - 1].value : 0
//     ).slice(1);
  
//     const averageChange = changes.reduce((a, b) => a + b, 0) / changes.length;
  
//     if (Math.abs(averageChange) < 0.1) return {
//       text: 'Steady',
//       icon: 'minus.circle.fill',
//       color: theme.colors.warning.light,
//     };
  
//     if (averageChange > 0) return {
//       text: 'Improving',
//       icon: 'arrow.up.circle.fill',
//       color: theme.colors.success.light,
//     };
  
//     return {
//       text: 'Declining',
//       icon: 'arrow.down.circle.fill',
//       color: theme.colors.error.light,
//     };
//   };
  
//   const calculateOverallTrend = (goals) => {
//     const trends = goals
//       .map(goal => calculateGoalProgress(goal).trend)
//       .filter(Boolean);
  
//     if (trends.length === 0) return {
//       text: 'Neutral',
//       color: theme.colors.warning.light,
//     };
  
//     const improving = trends.filter(t => t.text === 'Improving').length;
//     const declining = trends.filter(t => t.text === 'Declining').length;
  
//     if (improving > declining) return {
//       text: 'Upward',
//       color: theme.colors.success.light,
//     };
//     if (declining > improving) return {
//       text: 'Downward',
//       color: theme.colors.error.light,
//     };
//     return {
//       text: 'Stable',
//       color: theme.colors.warning.light,
//     };
//   };
  
//   const getStatusText = (percentage) => {
//     if (percentage >= 100) return 'Completed';
//     if (percentage >= 75) return 'Almost There';
//     if (percentage >= 50) return 'Halfway';
//     if (percentage >= 25) return 'In Progress';
//     if (percentage > 0) return 'Just Started';
//     return 'Not Started';
//   };
  
//   const getProgressColor = (percentage) => {
//     if (percentage >= 100) return theme.colors.success.light;
//     if (percentage >= 50) return theme.colors.primary.light;
//     if (percentage >= 25) return theme.colors.warning.light;
//     return theme.colors.error.light;
//   };
  
//   const getGoalIcon = (goalName) => {
//     const icons = {
//       healthScore: 'heart.fill',
//       steps: 'figure.walk',
//       water: 'drop.fill',
//       sleep: 'moon.fill',
//       default: 'target',
//     };
//     return icons[goalName.toLowerCase()] || icons.default;
//   };
  
//   const getMotivationalMessage = (completionRate) => {
//     if (completionRate >= 100) return 'All goals achieved! Outstanding work! 🎯';
//     if (completionRate >= 75) return 'Almost there! Keep pushing! 💪';
//     if (completionRate >= 50) return 'Halfway there! You\'re doing great! 🌟';
//     if (completionRate >= 25) return 'Great start! Keep going! 🚀';
//     return 'Every step counts! You\'ve got this! 💫';
//   };
  
//   const styles = StyleSheet.create({
//     container: {
//       backgroundColor: theme.colors.background.secondary.light,
//       borderRadius: theme.layout.borderRadius.large,
//       padding: theme.spacing.m,
//       marginBottom: theme.spacing.m,
//       ...theme.shadows.medium,
//     },
//     header: {
//       marginBottom: theme.spacing.m,
//     },
//     titleContainer: {
//       flexDirection: 'row',
//       alignItems: 'center',
//       marginBottom: theme.spacing.xs,
//     },
//     title: {
//       ...theme.typography.headline,
//       color: theme.colors.text.primary.light,
//       marginLeft: theme.spacing.s,
//     },
//     subtitle: {
//       ...theme.typography.subhead,
//       color: theme.colors.text.secondary.light,
//     },
//     metricsContainer: {
//       flexDirection: 'row',
//       justifyContent: 'space-between',
//       marginBottom: theme.spacing.l,
//     },
//     metricCard: {
//       flex: 1,
//       alignItems: 'center',
//       padding: theme.spacing.s,
//     },
//     metricLabel: {
//       ...theme.typography.caption,
//       color: theme.colors.text.secondary.light,
//       marginTop: theme.spacing.xs,
//     },
//     metricValue: {
//       ...theme.typography.title3,
//       color: theme.colors.text.primary.light,
//     },
//     metricSubtitle: {
//       ...theme.typography.caption,
//       color: theme.colors.text.secondary.light,
//     },
//     goalsContainer: {
//       marginTop: theme.spacing.m,
//     },
//     sectionTitle: {
//       ...theme.typography.headline,
//       color: theme.colors.text.primary.light,
//       marginBottom: theme.spacing.m,
//     },
//     goalCard: {
//       backgroundColor: theme.colors.background.primary.light,
//       borderRadius: theme.layout.borderRadius.medium,
//       padding: theme.spacing.m,
//       marginBottom: theme.spacing.m,
//       ...theme.shadows.small,
//     },
//     goalHeader: {
//       flexDirection: 'row',
//       justifyContent: 'space-between',
//       alignItems: 'center',
//       marginBottom: theme.spacing.s,
//     },
//     goalTitleContainer: {
//       flexDirection: 'row',
//       alignItems: 'center',
//     },
//     goalTitle: {
//       ...theme.typography.subhead,
//       color: theme.colors.text.primary.light,
//       marginLeft: theme.spacing.s,
//     },
//     goalStatus: {
//       ...theme.typography.caption,
//       fontWeight: '500',
//     },
//     progressContainer: {
//       marginTop: theme.spacing.s,
//     },
//     progressBarContainer: {
//       height: 8,
//       backgroundColor: theme.colors.background.tertiary.light,
//       borderRadius: 4,
//       overflow: 'hidden',
//     },
//     progressBar: {
//       height: '100%',
//       borderRadius: 4,
//     },
//     progressDetails: {
//       flexDirection: 'row',
//       justifyContent: 'space-between',
//       marginTop: theme.spacing.xs,
//     },
//     progressText: {
//       ...theme.typography.caption,
//       color: theme.colors.text.secondary.light,
//     },
//     progressPercentage: {
//       ...theme.typography.caption,
//       color: theme.colors.text.secondary.light,
//     },
//     trendContainer: {
//       flexDirection: 'row',
//       alignItems: 'center',
//       marginTop: theme.spacing.s,
//     },
//     trendText: {
//       ...theme.typography.caption,
//       marginLeft: theme.spacing.xs,
//     },
//     emptyContainer: {
//       alignItems: 'center',
//       padding: theme.spacing.xl,
//     },
//     emptyTitle: {
//       ...theme.typography.title2,
//       color: theme.colors.text.primary.light,
//       marginTop: theme.spacing.m,
//     },
//     emptyText: {
//       ...theme.typography.body,
//       color: theme.colors.text.secondary.light,
//       textAlign: 'center',
//       marginTop: theme.spacing.s,
//     },
//     addButton: {
//       backgroundColor: theme.colors.primary.light,
//       paddingHorizontal: theme.spacing.l,
//       paddingVertical: theme.spacing.m,
//       borderRadius: theme.layout.borderRadius.medium,
//       marginTop: theme.spacing.l,
//     },
//     addButtonText: {
//       ...theme.typography.button,
//       color: theme.colors.text.primary.light,
//     },
//   });
  
//   export default ProgressSummary;