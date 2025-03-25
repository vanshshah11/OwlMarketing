// /Users/vanshshah/Desktop/New_app/5th_WellAI/WellAI/src/analyticscomponents/OverallProgressChart.js
import React, { useMemo, memo, useEffect, useState, useRef } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  Dimensions, 
  Animated, 
  Easing,
  ActivityIndicator 
} from 'react-native';
import { LineChart } from 'react-native-chart-kit';
import { SFSymbol } from 'react-native-sfsymbols';
import PropTypes from 'prop-types';
import { 
  collection,
  query,
  where,
  getDocs,
  Timestamp,
  orderBy,
  limit 
} from 'firebase/firestore';
import { db, auth } from '../utils/firebase';
import theme from '../styles/theme';

const { width } = Dimensions.get('window');
const CHART_HEIGHT = 180;
const MIN_DATA_POINTS = 2;
const TREND_THRESHOLD = 5;
const ANIMATION_DURATION = 600;

const TimeFrames = {
  DAY: 'day',
  WEEK: 'week',
  MONTH: 'month'
};

const TimeFrameLabels = {
  [TimeFrames.DAY]: 'Last 24 Hours',
  [TimeFrames.WEEK]: 'Past 7 Days',
  [TimeFrames.MONTH]: 'Past 30 Days'
};

const ChartLegendLabels = {
  [TimeFrames.DAY]: 'Showing hourly progress',
  [TimeFrames.WEEK]: 'Showing daily progress',
  [TimeFrames.MONTH]: 'Showing weekly progress'
};

const fetchTimeFrameData = async (timeFrame) => {
  const userId = auth.currentUser?.uid;
  if (!userId) {
    throw new Error('No authenticated user found');
  }

  const { startDate, endDate, interval } = getTimeFrameDates(timeFrame);
  
  const collectionName = `${timeFrame}lyStats`;
  const statsQuery = query(
    collection(db, collectionName),
    where('userId', '==', userId),
    where('date', '>=', startDate),
    where('date', '<=', endDate),
    orderBy('date', 'desc')
  );

  const querySnapshot = await getDocs(statsQuery);
  
  if (querySnapshot.empty) {
    return [];
  }

  return querySnapshot.docs.map(doc => ({
    timestamp: doc.data().date,
    value: calculateProgressValue(doc.data())
  }));
};

// Add this helper function
const calculateProgressValue = (data) => {
  const nutrients = data.nutrients || {};
  const targetCalories = nutrients.targetCalories || 2000;
  const calories = nutrients.calories || 0;
  return (calories / targetCalories) * 100;
};

// Update chartConfig constant that was missing
const chartConfig = {
  backgroundColor: theme.colors.background.secondary.light,
  backgroundGradientFrom: theme.colors.background.secondary.light,
  backgroundGradientTo: theme.colors.background.secondary.light,
  decimalPlaces: 0,
  color: (opacity = 1) => `rgba(0, 122, 255, ${opacity})`,
  labelColor: () => theme.colors.text.secondary.light,
  style: {
    borderRadius: 16,
  },
  propsForDots: {
    r: '4',
    strokeWidth: '2',
    stroke: theme.colors.primary.light
  },
  propsForLabels: {
    ...theme.typography.caption
  }
};

// Add this code right after the ChartLegendLabels constant and before the getTimeFrameDates function
const ChartUtils = {
  formatLabels: (labels, timeFrame) => {
    if (!labels?.length) return [];
    
    const formatOptions = {
      [TimeFrames.DAY]: { hour: '2-digit' },
      [TimeFrames.WEEK]: { weekday: 'short' },
      [TimeFrames.MONTH]: { day: 'numeric', month: 'short' }
    };
    
    return labels.map(label => {
      const date = new Date(label);
      return date.toLocaleDateString(undefined, formatOptions[timeFrame] || {});
    });
  },

  calculateMetrics: (data) => {
    if (!data?.length) return ChartUtils.getDefaultMetrics();

    const average = Math.round(data.reduce((a, b) => a + b, 0) / data.length);
    const highest = Math.round(Math.max(...data));
    const trend = ChartUtils.calculateTrend(data);

    return { average, highest, ...trend };
  },

  calculateTrend: (data) => {
    if (data.length < 2) return ChartUtils.getDefaultTrend();

    const midPoint = Math.floor(data.length / 2);
    const firstHalf = data.slice(0, midPoint);
    const secondHalf = data.slice(midPoint);
    
    const firstAvg = firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length;
    const secondAvg = secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length;
    const difference = secondAvg - firstAvg;
    
    if (difference > TREND_THRESHOLD) {
      return {
        trend: 'Improving',
        trendIcon: 'arrow.up.circle.fill',
        trendColor: theme.colors.success.light
      };
    } 
    
    if (difference < -TREND_THRESHOLD) {
      return {
        trend: 'Declining',
        trendIcon: 'arrow.down.circle.fill',
        trendColor: theme.colors.error.light
      };
    }
    
    return ChartUtils.getDefaultTrend();
  },

  getDefaultTrend: () => ({
    trend: 'Stable',
    trendIcon: 'minus.circle.fill',
    trendColor: theme.colors.warning.light
  }),

  getDefaultMetrics: () => ({
    average: 0,
    highest: 0,
    ...ChartUtils.getDefaultTrend()
  })
};

// Enhanced utility functions with error handling and caching
const getTimeFrameDates = (timeFrame) => {
  const now = new Date();
  const endDate = Timestamp.fromDate(now);
  let startDate;
  let interval;

  switch (timeFrame) {
    case TimeFrames.DAY:
      startDate = Timestamp.fromDate(new Date(now - 24 * 60 * 60 * 1000));
      interval = 'hour';
      break;
    case TimeFrames.WEEK:
      startDate = Timestamp.fromDate(new Date(now - 7 * 24 * 60 * 60 * 1000));
      interval = 'day';
      break;
    case TimeFrames.MONTH:
      startDate = Timestamp.fromDate(new Date(now - 30 * 24 * 60 * 60 * 1000));
      interval = 'week';
      break;
    default:
      startDate = Timestamp.fromDate(new Date(now - 24 * 60 * 60 * 1000));
      interval = 'hour';
  }

  return { startDate, endDate, interval };
};

// Add logger utility after imports
const logger = {
  info: (message, data) => {
    if (__DEV__) {
      console.log(`[OverallProgressChart] ${message}`, data || '');
    }
  },
  error: (message, error) => {
    console.error(`[OverallProgressChart] ${message}`, error);
  },
  warn: (message, data) => {
    console.warn(`[OverallProgressChart] ${message}`, data || '');
  }
};

const fetchProgressData = async (timeFrame) => {
  const userId = auth.currentUser?.uid;
  if (!userId) {
    logger.warn('No user ID found when fetching progress data');
    return null;
  }

  try {
    logger.info(`Fetching progress data for timeframe: ${timeFrame}`);
    const data = await fetchTimeFrameData(timeFrame);
    if (!data.exists()) {
      logger.info(`No data found for timeframe: ${timeFrame}`);
      return null;
    }

    const stats = data.data();
    logger.info('Successfully fetched progress data', { timeFrame });
    
    // Format data based on time frame
    let progressData;
    switch(timeFrame) {
      case 'day':
        progressData = {
          timestamp: stats.date,
          value: (stats.nutrients.calories / stats.nutrients.targetCalories) * 100
        };
        break;
      case 'week':
      case 'month':
        progressData = {
          timestamp: stats.startDate,
          value: (stats.nutrients.avgCalories / stats.nutrients.targetCalories) * 100
        };
        break;
    }

    return [progressData];
  } catch (error) {
    logger.error('Error fetching progress data:', error);
    return null;
  }
};

// Animated Components
const AnimatedHeader = memo(({ timeFrame, fadeAnim }) => (
  <Animated.View style={[styles.headerContainer, { opacity: fadeAnim }]}>
    <View style={styles.titleContainer}>
      <Text style={styles.chartTitle}>Overall Progress</Text>
    </View>
    <Text style={styles.timeFrameLabel}>
      {TimeFrameLabels[timeFrame]}
    </Text>
  </Animated.View>
));

const AnimatedMetricItem = memo(({ 
  label, 
  value, 
  icon, 
  color, 
  fadeAnim, 
  slideAnim 
}) => (
  <Animated.View 
    style={[
      styles.metricItem,
      {
        opacity: fadeAnim,
        transform: [{ translateY: slideAnim }]
      }
    ]}
  >
    <SFSymbol 
      name={icon} 
      size={20} 
      color={color || theme.colors.primary.light} 
    />
    <Text style={styles.metricLabel}>{label}</Text>
    <Text style={styles.metricValue}>{value}</Text>
  </Animated.View>
));

const EmptyChartState = memo(({ fadeAnim }) => (
  <Animated.View style={[styles.emptyStateContainer, { opacity: fadeAnim }]}>
    <SFSymbol 
      name="chart.pie" 
      size={40} 
      color={theme.colors.text.secondary.light} 
    />
    <Text style={styles.emptyStateText}>
      Not enough data for the selected time frame
    </Text>
    <Text style={styles.emptyStateSubtext}>
      Continue tracking your progress to see your trends
    </Text>
  </Animated.View>
));

// Enhanced Chart Component
const OverallProgressChart = ({ timeFrame }) => {
  const [progressData, setProgressData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Animation values
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;
  const chartOpacity = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const loadProgressData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Reset animations
        fadeAnim.setValue(0);
        slideAnim.setValue(50);
        chartOpacity.setValue(0);

        const data = await fetchTimeFrameData(timeFrame);
        
        if (data && data.length > 0) {
          const chartData = {
            labels: data.map(item => item.timestamp instanceof Timestamp ? 
              item.timestamp.toDate().toISOString() : 
              new Date(item.timestamp).toISOString()
            ),
            datasets: [{
              data: data.map(item => Math.min(Math.max(item.value, 0), 100))
            }]
          };
          setProgressData(chartData);
        } else {
          setProgressData(null);
        }
      } catch (err) {
        logger.error('Failed to load progress data:', err);
        setError(err.message);
      } finally {
        setLoading(false);
        
        Animated.parallel([
          Animated.timing(fadeAnim, {
            toValue: 1,
            duration: ANIMATION_DURATION,
            easing: Easing.out(Easing.cubic),
            useNativeDriver: true,
          }),
          Animated.timing(slideAnim, {
            toValue: 0,
            duration: ANIMATION_DURATION,
            easing: Easing.out(Easing.cubic),
            useNativeDriver: true,
          }),
          Animated.timing(chartOpacity, {
            toValue: 1,
            duration: ANIMATION_DURATION,
            delay: ANIMATION_DURATION / 2,
            easing: Easing.out(Easing.cubic),
            useNativeDriver: true,
          })
        ]).start();
      }
    };

    loadProgressData();
  }, [timeFrame]);

  const { processedData, isValidData } = useMemo(() => {
    if (!progressData?.datasets?.[0]?.data || !progressData?.labels) {
      logger.warn('Invalid or missing progress data for chart');
      return { processedData: null, isValidData: false };
    }

    logger.info('Processing chart data');
    const data = {
      labels: ChartUtils.formatLabels(progressData.labels, timeFrame),
      datasets: [{
        data: progressData.datasets[0].data.map(value => 
          Math.min(Math.max(value, 0), 100)
        ),
        color: (opacity = 1) => `rgba(0, 122, 255, ${opacity})`,
        strokeWidth: 2
      }]
    };

    const isValid = data.labels.length >= MIN_DATA_POINTS;
    logger.info('Chart data processed', { 
      dataPoints: data.labels.length,
      isValid 
    });

    return { 
      processedData: data, 
      isValidData: isValid 
    };
  }, [progressData, timeFrame]);

  if (loading) {
    return (
      <View style={styles.chartCard}>
        <AnimatedHeader timeFrame={timeFrame} fadeAnim={fadeAnim} />
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.colors.primary.light} />
        </View>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.chartCard}>
        <AnimatedHeader timeFrame={timeFrame} fadeAnim={fadeAnim} />
        <View style={styles.errorContainer}>
          <SFSymbol 
            name="exclamationmark.triangle.fill" 
            size={40} 
            color={theme.colors.error.light} 
          />
          <Text style={styles.errorText}>
            Unable to load progress data
          </Text>
          <Text style={styles.errorSubtext}>
            {error}
          </Text>
        </View>
      </View>
    );
  }

  if (!isValidData) {
    return (
      <View style={styles.chartCard}>
        <AnimatedHeader timeFrame={timeFrame} fadeAnim={fadeAnim} />
        <EmptyChartState fadeAnim={fadeAnim} />
      </View>
    );
  }

  const metrics = ChartUtils.calculateMetrics(processedData.datasets[0].data);

  return (
    <View style={styles.chartCard}>
      <AnimatedHeader timeFrame={timeFrame} fadeAnim={fadeAnim} />
      
      <Animated.View style={{ opacity: chartOpacity }}>
        <LineChart
          data={processedData}
          width={width - 40}
          height={CHART_HEIGHT}
          yAxisSuffix="%"
          chartConfig={chartConfig}
          bezier
          style={styles.chart}
          withDots
          withInnerLines
          withOuterLines
          withHorizontalLines
          withVerticalLabels
          withHorizontalLabels
          fromZero
          segments={5}
          formatYLabel={(value) => Math.round(value)}
          renderDotContent={({ x, y, index, indexData }) => (
            <Animated.View
              key={index}
              style={[
                styles.dotLabel,
                { 
                  top: y - 24, 
                  left: x - 20,
                  opacity: chartOpacity,
                  transform: [{ scale: chartOpacity }]
                }
              ]}
            >
              <Text style={styles.dotLabelText}>
                {Math.round(indexData)}%
              </Text>
            </Animated.View>
          )}
        />
      </Animated.View>
      
      {/* <View style={styles.metricsContainer}>
        <AnimatedMetricItem 
          label="Average"
          value={`${metrics.average}%`}
          icon="number.circle.fill"
          fadeAnim={fadeAnim}
          slideAnim={slideAnim}
        />
        <AnimatedMetricItem 
          label="Highest"
          value={`${metrics.highest}%`}
          icon="arrow.up.circle.fill"
          color={theme.colors.success.light}
          fadeAnim={fadeAnim}
          slideAnim={slideAnim}
        />
        <AnimatedMetricItem 
          label="Trend"
          value={metrics.trend}
          icon={metrics.trendIcon}
          color={metrics.trendColor}
          fadeAnim={fadeAnim}
          slideAnim={slideAnim}
        />
      </View> */}
    </View>
  );
}; 

// Enhanced styles with new containers for loading and error states
const styles = StyleSheet.create({
  chartCard: {
    backgroundColor: theme.colors.background.secondary.light,
    borderRadius: theme.layout.borderRadius.large,
    padding: theme.spacing.m,
    marginBottom: theme.spacing.m,
    ...theme.shadows.medium,
  },
  headerContainer: {
    marginBottom: theme.spacing.m,
  },
  titleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  chartTitle: {
    ...theme.typography.headline,
    color: theme.colors.text.primary.light,
  },
  timeFrameLabel: {
    ...theme.typography.caption,
    color: theme.colors.text.secondary.light,
  },
  chart: {
    marginVertical: theme.spacing.m,
    borderRadius: theme.layout.borderRadius.large,
  },
  legendContainer: {
    alignItems: 'center',
    marginTop: theme.spacing.s,
  },
  legendText: {
    ...theme.typography.caption,
    color: theme.colors.text.secondary.light,
  },
  metricsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: theme.spacing.m,
    paddingTop: theme.spacing.m,
    borderTopWidth: 1,
    borderTopColor: theme.colors.background.tertiary.light,
  },
  metricItem: {
    alignItems: 'center',
  },
  metricLabel: {
    ...theme.typography.caption,
    color: theme.colors.text.secondary.light,
    marginTop: theme.spacing.xs,
  },
  metricValue: {
    ...theme.typography.subhead,
    color: theme.colors.text.primary.light,
  },
  emptyStateContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    height: CHART_HEIGHT,
    marginVertical: theme.spacing.m,
  },
  emptyStateText: {
    ...theme.typography.body,
    color: theme.colors.text.secondary.light,
    marginTop: theme.spacing.xxl,
    textAlign: 'center',
  },
  emptyStateSubtext: {
    ...theme.typography.caption,
    color: theme.colors.text.secondary.light,
    marginTop: theme.spacing.s,
    textAlign: 'center',
  },
  dotLabel: {
    position: 'absolute',
    backgroundColor: theme.colors.background.primary.light,
    borderRadius: theme.layout.borderRadius.small,
    padding: theme.spacing.xs,
    ...theme.shadows.small,
  },
  dotLabelText: {
    ...theme.typography.caption,
    color: theme.colors.text.primary.light,
  },
  loadingContainer: {
    height: CHART_HEIGHT,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorContainer: {
    height: CHART_HEIGHT,
    justifyContent: 'center',
    alignItems: 'center',
    padding: theme.spacing.m,
  },
  errorText: {
    ...theme.typography.body,
    color: theme.colors.error.light,
    marginTop: theme.spacing.m,
    textAlign: 'center',
  },
  errorSubtext: {
    ...theme.typography.caption,
    color: theme.colors.text.secondary.light,
    marginTop: theme.spacing.s,
    textAlign: 'center',
  },
});

OverallProgressChart.propTypes = {
  timeFrame: PropTypes.oneOf(Object.values(TimeFrames)).isRequired
};

export default memo(OverallProgressChart);
