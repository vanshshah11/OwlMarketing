import React, { useEffect, useState, useRef } from 'react';
import { Animated, View, Text, Image, StyleSheet, ScrollView, TouchableOpacity, Platform, ActivityIndicator, TextInput, Modal } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'react-native-linear-gradient';
import { SFSymbol } from 'react-native-sfsymbols';
import { BlurView } from '@react-native-community/blur';
import theme from '../styles/theme';
import { auth, addCalorieEntry, uploadImage, updateCalorieEntry } from '../utils/firebase';
import { getFoodNutrition, analyzeImage } from '../utils/api';
import LazyImage from '../Components/LazyImage';
import FastImage from 'react-native-fast-image';
import ReactNativeHapticFeedback from 'react-native-haptic-feedback';

const hapticOptions = {
  enableVibrateFallback: true,
  ignoreAndroidSystemSettings: false
};

const ResultsScreen = ({ route, navigation }) => {
  const [scrollY] = useState(new Animated.Value(0));
  const [imageLoaded, setImageLoaded] = useState(false);
  const { image, barcode, existingData, originalItem, isPrefetched } = route.params || {};
  const [nutritionData, setNutritionData] = useState(existingData || {
    mealName: '',
    calories: 0,
    carbs: 0,
    protein: 0,
    fat: 0,
    fiber: 0,
    sugar: 0
  });
  const [loading, setLoading] = useState(!isPrefetched);
  const [error, setError] = useState(null);
  const [quantity, setQuantity] = useState(1);
  const [imageAspectRatio, setImageAspectRatio] = useState(1);
  const [saving, setSaving] = useState(false);
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;
  const scaleAnim = useRef(new Animated.Value(0.95)).current;
  const [isEditing, setIsEditing] = useState(false);
  const [editedData, setEditedData] = useState(nutritionData);
  const [scrollThresholdReached, setScrollThresholdReached] = useState(false);

  useEffect(() => {
    // Enable swipe back gesture
    navigation.setOptions({
      gestureEnabled: true,
      gestureResponseDistance: 50,
    });
  
    const scrollListener = scrollY.addListener(({ value }) => {
      // Optional: Add any additional scroll-related logic
    });
  
    return () => {
      scrollY.removeListener(scrollListener);
    };
  }, [navigation, scrollY]);

  useEffect(() => {
    const initializeData = async () => {
      // If we have existingData from a RecentlyEatenCard, use it immediately
      if (existingData) {
        setNutritionData(existingData);
        setLoading(false);
        return;
      }

      try {
        // For prefetched images, skip analysis and just get nutrition
        if (isPrefetched) {
          const foodData = await getFoodNutrition(image);
          setNutritionData({
            mealName: foodData.description || 'Unknown Food',
            calories: foodData.calories || 0,
            carbs: foodData.carbohydrates || 0,
            protein: foodData.protein || 0,
            fat: foodData.fat || 0,
            fiber: foodData.fiber || 0,
            sugar: foodData.sugar || 0
          });
        } else if (image) {
          const imageUrl = await uploadImage(auth.currentUser.uid, image);
          const analysisResult = await analyzeImage(imageUrl);
          const primaryLabel = analysisResult.labels[0];
          const foodData = await getFoodNutrition(primaryLabel);
          setNutritionData({
            mealName: foodData.description || 'Unknown Food',
            calories: foodData.calories || 0,
            carbs: foodData.carbohydrates || 0,
            protein: foodData.protein || 0,
            fat: foodData.fat || 0,
            fiber: foodData.fiber || 0,
            sugar: foodData.sugar || 0
          });
        } else if (barcode) {
          const foodData = await getFoodNutrition(barcode);
          setNutritionData({
            mealName: foodData.description || 'Unknown Food',
            calories: foodData.calories || 0,
            carbs: foodData.carbohydrates || 0,
            protein: foodData.protein || 0,
            fat: foodData.fat || 0,
            fiber: foodData.fiber || 0,
            sugar: foodData.sugar || 0
          });
        }
      } catch (err) {
        console.error('Error fetching nutrition data:', err);
        setError('Failed to analyze food. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    initializeData();
  }, [existingData, image, barcode, isPrefetched]);

  useEffect(() => {
    // Entrance animations
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 400,
        useNativeDriver: true,
      }),
      Animated.spring(slideAnim, {
        toValue: 0,
        tension: 35,
        friction: 6,
        useNativeDriver: true,
      }),
      Animated.spring(scaleAnim, {
        toValue: 1,
        tension: 45,
        friction: 7,
        useNativeDriver: true,
      })
    ]).start();
  }, []);

  const handleQuantityChange = (change) => {
    const newQuantity = quantity + change;
    if (newQuantity >= 1 && newQuantity <= 10) {
      const buttonScale = new Animated.Value(0.95);
      Animated.spring(buttonScale, {
        toValue: 1,
        friction: 3,
        tension: 40,
        useNativeDriver: true
      }).start();
      
      setQuantity(newQuantity);
      ReactNativeHapticFeedback.trigger('impactLight', hapticOptions);
    } else {
      ReactNativeHapticFeedback.trigger('notificationError', hapticOptions);
    }
  };

  const cleanDataForFirestore = (data) => {
    // Remove any undefined or null values
    const cleanData = {};
    Object.keys(data).forEach(key => {
      if (data[key] !== undefined && data[key] !== null) {
        cleanData[key] = data[key];
      }
    });
    return cleanData;
  };

  const handleEditToggle = async () => {
    if (isEditing) {
      try {
        setSaving(true);
        ReactNativeHapticFeedback.trigger('impactMedium', hapticOptions);
        
        // Only get the fields that were actually edited
        const updatedFields = {};
        Object.keys(editedData).forEach(key => {
          if (editedData[key] !== nutritionData[key]) {
            updatedFields[key] = editedData[key];
          }
        });

        if (Object.keys(updatedFields).length > 0) {
          // Update only the changed fields in Firebase
          await updateCalorieEntry(originalItem.id, updatedFields);
          ReactNativeHapticFeedback.trigger('notificationSuccess', hapticOptions);
          
          // Update local state with the changes
          setNutritionData(prev => ({
            ...prev,
            ...updatedFields
          }));
        }
      } catch (err) {
        console.error('Error updating entry:', err);
        ReactNativeHapticFeedback.trigger('notificationError', hapticOptions);
        setError('Failed to update values. Please try again.');
      } finally {
        setSaving(false);
      }
    }
    setIsEditing(!isEditing);
  };

  const handleValueChange = (field, value) => {
    const numericValue = parseFloat(value) || 0;
    const fieldLower = field.toLowerCase();
    
    // Only update editedData for the changed field
    setEditedData(prev => ({
      ...prev,
      [fieldLower]: numericValue
    }));
  };

  const handleSave = async () => {
    if (isEditing) {
      // If we're in editing mode, just toggle edit mode
      setIsEditing(false);
      return;
    }
  
    try {
      setSaving(true);
      // ReactNativeHapticFeedback.trigger('impactLight', hapticOptions);
      
      // Check if this is an existing entry being modified
      if (originalItem && originalItem.id) {
        // If it's an existing entry, update only the changes
        const updatedFields = {};
        Object.keys(editedData).forEach(key => {
          if (editedData[key] !== nutritionData[key]) {
            updatedFields[key] = editedData[key];
          }
        });
  
        if (Object.keys(updatedFields).length > 0) {
          await updateCalorieEntry(originalItem.id, updatedFields);
          ReactNativeHapticFeedback.trigger('notificationSuccess', hapticOptions);
          
          // Update local state with the changes
          setNutritionData(prev => ({
            ...prev,
            ...updatedFields
          }));
        }
  
        navigation.navigate('Home', { refresh: true });
      } else {
        // If it's a new entry, proceed with the original save logic
        const cleanedData = cleanDataForFirestore({
          userId: auth.currentUser.uid,
          imageUrl: image || originalItem?.imageUrl,
          barcode: barcode || originalItem?.barcode,
          quantity,
          mealName: nutritionData.mealName || 'Unknown Food',
          calories: nutritionData.calories || 0,
          carbs: nutritionData.carbs || 0,
          protein: nutritionData.protein || 0,
          fat: nutritionData.fat || 0,
          fiber: nutritionData.fiber || 0,
          sugar: nutritionData.sugar || 0,
          healthScore: calculateHealthScore(nutritionData),
          createdAt: originalItem?.createdAt || new Date(),
          dateKey: new Date().toISOString().split('T')[0]
        });
  
        await addCalorieEntry(auth.currentUser.uid, cleanedData);
        ReactNativeHapticFeedback.trigger('notificationSuccess', hapticOptions);
        navigation.navigate('Home', { refresh: true });
      }
    } catch (err) {
      console.error('Error saving/updating entry:', err);
      ReactNativeHapticFeedback.trigger('notificationError', hapticOptions);
      setError('Failed to save/update entry. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const calculateHealthScore = (data) => {
    // Base score starts at 5
    let score = 5;
    
    // Helper function to check if food appears to be a fruit/vegetable
    // based on typical macro ratios and nutrition content
    const isLikelyFruitOrVeg = (data) => {
      const hasHighWaterContent = data.calories < 100 //per serving;
      const hasNaturalSugars = (data.sugar / data.carbs) > 0.5;
      const hasLowFat = (data.fat * 9) / data.calories < 0.15;
      const hasFiber = data.fiber > 0;
      return hasHighWaterContent && hasNaturalSugars && hasLowFat && hasFiber;
    };
  
    // 1. Natural Food Bonus (0-3 points)
    if (isLikelyFruitOrVeg(data)) {
      score += 3;
    }
  
    // 2. Nutrient Density Score (0-3 points)
    const caloriesPerServing = data.calories;
    if (caloriesPerServing <= 100) {
      score += 2;
    } else if (caloriesPerServing <= 200) {
      score += 1;
    }
  
    // 3. Fiber Content (0-2 points)
    // For fruits/vegetables, we look at fiber-to-calorie ratio instead of fiber-to-carb
    const fiberToCalorieRatio = (data.fiber / data.calories) * 100;
    if (fiberToCalorieRatio >= 1.5) {
      score += 2;
    } else if (fiberToCalorieRatio >= 0.75) {
      score += 1;
    }
  
    // 4. Natural Sugar vs Added Sugar Context (0-1 points)
    // If it's likely a fruit/veg, don't penalize for natural sugars
    if (!isLikelyFruitOrVeg(data)) {
      const sugarToCalorieRatio = (data.sugar * 4 / data.calories);
      if (sugarToCalorieRatio > 0.3) {
        score -= 1;
      }
    }
  
    // 5. Protein Quality Score (0-1 point)
    const proteinToCalorieRatio = (data.protein * 4 / data.calories);
    if (proteinToCalorieRatio >= 0.15) {
      score += 1;
    }
  
    // 6. Balanced Macronutrient Bonus (0-1 point)
    const hasBalancedMacros = () => {
      const totalCals = data.calories || 1;
      const proteinRatio = (data.protein * 4 / totalCals);
      const carbRatio = (data.carbs * 4 / totalCals);
      const fatRatio = (data.fat * 9 / totalCals);
      
      // For fruits/veg, we expect different macro ratios
      if (isLikelyFruitOrVeg(data)) {
        return true; // Natural foods get this bonus
      }
      
      return proteinRatio >= 0.1 && carbRatio >= 0.2 && fatRatio >= 0.15;
    };
  
    if (hasBalancedMacros()) {
      score += 1;
    }
  
    // Ensure score stays within 0-10 range
    return Math.max(0, Math.min(10, Math.round(score)));
  };

  const renderMetricCard = (symbolName, label, value, unit = '') => (
    <View style={[styles.metricCard, { 
        flex: 1,
        minWidth: theme.responsive.width(35),
        backgroundColor: theme.colors.background.secondary.light,
        borderRadius: theme.layout.borderRadius.large,
        padding: theme.spacing.s,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.08,
        shadowRadius: 6,
        elevation: 5
    }]}>
      <View style={[styles.metricCardContent, theme.mixins.row]}>
        <View style={[styles.metricIconContainer, {
          width: theme.layout.iconSize.large,
          height: theme.layout.iconSize.large,
          borderRadius: theme.layout.iconSize.medium / 1.5,
          backgroundColor: `${getIconColor(label)}20`, // Add transparency to icon background
          ...theme.mixins.center
        }]}>
          <SFSymbol 
            name={symbolName} 
            size={theme.layout.iconSize.tiny}
            color={getIconColor(label)} 
            weight="semibold"
          />
        </View>
        <View style={styles.metricTextContainer}>
          <Text style={[styles.metricLabel, theme.typography.subhead, { 
            color: theme.colors.text.secondary.light,
            marginBottom: theme.spacing.xxxs
          }]}>
            {label}
          </Text>
          {isEditing ? (
            <TextInput
              style={[styles.metricInput, theme.typography.title3, {
                color: theme.colors.text.primary.light,
                borderBottomWidth: 1,
                borderBottomColor: theme.colors.primary.light,
                padding: 0,
              }]}
              value={String(editedData[label.toLowerCase()] || '')}
              onChangeText={(text) => handleValueChange(label.toLowerCase(), text)}
              keyboardType="numeric"
              placeholder={String(value || '0')}
            />
          ) : (
          <Text style={[styles.metricValue, theme.typography.title3, {
              color: theme.colors.text.primary.light,
              marginTop: theme.spacing.xxxs,
              fontWeight: '600'
          }]}>
            {value ? ((value * quantity).toFixed(1) + unit) : '0' + unit}
          </Text>
          )}
        </View>
      </View>
    </View>
  );

  const getIconColor = (label) => {
    switch (label) {
      case 'Calories': return theme.colors.warning.light;
      case 'Carbs': return theme.colors.warning.dark;
      case 'Protein': return theme.colors.error.light;
      case 'Fat': return theme.colors.macro.fat;
      default: return theme.colors.text.primary.light;
    }
  };

  const handleScroll = (event) => {
    const offsetY = event.nativeEvent.contentOffset.y;
    scrollY.setValue(offsetY);
    if (offsetY > 80 && !scrollThresholdReached) {
      ReactNativeHapticFeedback.trigger('impactLight', hapticOptions);
      setScrollThresholdReached(true);
    } else if (offsetY <= 80 && scrollThresholdReached) {
      setScrollThresholdReached(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color={theme.colors.primary.light} />
        <Text style={[styles.loadingText, theme.typography.body]}>
          Analyzing your food...
        </Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.centerContainer}>
        <Text style={[styles.errorText, theme.typography.body]}>{error}</Text>
        <TouchableOpacity 
          style={[styles.fixButton, { width: theme.layout.maxContentWidth }]}
          onPress={() => navigation.goBack()}>
          <Text style={[styles.fixButtonText, theme.typography.button2]}>
            Try Again
          </Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { 
      backgroundColor: theme.colors.background.stuffimadeup
    }]} edges={['bottom']}>
      <View style={[styles.headerContainer, {
        height: Platform.OS === 'ios' ? theme.layout.buttonHeight + theme.spacing.xl : theme.layout.buttonHeight,
        zIndex: theme.zIndex.header
      }]}>
        {image && (
          <>
            <FastImage 
              source={{ uri: image }} 
              style={[styles.headerBackground, { opacity: 0.9 }]}
              resizeMode={FastImage.resizeMode.cover}
            />
            <BlurView
              style={[styles.headerBlur, { 
                opacity: imageLoaded ? 1 : 0,
                backgroundColor: 'rgba(248, 247, 248, 0.45)'
              }]}
              blurType="light"
              blurAmount={25}
              reducedTransparencyFallbackColor="white"
            >
              <View style={[styles.header, { 
                backgroundColor: imageLoaded ? 'transparent' : 'rgba(255, 255, 255, 0.95)'
              }]}>
                <TouchableOpacity 
                  style={[styles.headerButton, { 
                    ...theme.shadows.small
                  }]} 
                  onPress={() => navigation.goBack()}>
                  <SFSymbol 
                    name="chevron.left" 
                    size={theme.layout.iconSize.medium}
                    color={theme.colors.text.primary.light}
                    weight="medium"
                  />
                </TouchableOpacity>
                <Text style={[styles.headerTitle, theme.typography.headline, {
                  textShadowColor: 'rgba(0, 0, 0, 0.1)',
                  textShadowOffset: { width: 0, height: 1 },
                  textShadowRadius: 2
                }]}>
                  Optimal AI
                </Text>
                <TouchableOpacity style={[styles.headerButton, { opacity: 0 }]}>
                  {/* <SFSymbol 
                    name="square.and.arrow.up" 
                    size={theme.layout.iconSize.medium}
                    color={theme.colors.text.primary.light}
                    weight="medium"
                  /> */}
                </TouchableOpacity>
              </View>
            </BlurView>
          </>
        )}
      </View>

      <Animated.View style={[
        styles.mainContainer,
        {
          opacity: fadeAnim,
          transform: [
            { translateY: slideAnim },
            { scale: scaleAnim }
          ],
          shadowColor: '#000',
          shadowOffset: { width: 0, height: 8 },
          shadowOpacity: 0.1,
          shadowRadius: 12
        }
      ]}>
        <ScrollView 
          style={styles.content}
          contentContainerStyle={[styles.contentContainer, {
            paddingTop: theme.spacing.m,
            paddingBottom: theme.spacing.xl
          }]}
          onScroll={Animated.event(
            [{ nativeEvent: { contentOffset: { y: scrollY } } }],
            { useNativeDriver: false, listener: handleScroll }
          )}
          scrollEventThrottle={16}
          bounces={true}
          showsVerticalScrollIndicator={false}
        >
          <Animated.View style={[styles.imageContainer, { 
            height: theme.responsive.height(30),
            overflow: 'hidden',
            backgroundColor: theme.colors.background.secondary.light,
            borderRadius: theme.layout.borderRadius.medium,
            transform: [{
              scale: scrollY.interpolate({
                inputRange: [-100, 0, 100],
                outputRange: [1.25, 1, 0.95],
                extrapolateLeft: 'extend',
                extrapolateRight: 'clamp'
              })
            }],
            ...theme.shadows.medium
          }]}>
            {image && (
              <Animated.View style={[styles.foodImage, {
                transform: [{
                  translateY: scrollY.interpolate({
                    inputRange: [-200, 0, 100],
                    outputRange: [-40, 0, 25],
                    extrapolate: 'clamp'
                  })
                }]
              }]}>
                <LazyImage 
                  source={{ uri: image }}
                  style={[StyleSheet.absoluteFill, { 
                    transform: [{ scale: 1.05 }], 
                    borderRadius: theme.layout.borderRadius.medium,
                  }]}
                  priority={FastImage.priority.high}
                  resizeMode={FastImage.resizeMode.cover}
                  onLoadEnd={() => setImageLoaded(true)}
                />
                <LinearGradient
                  colors={['rgba(0,0,0,0.2)', 'transparent', 'rgba(0,0,0,0.25)']}
                  style={StyleSheet.absoluteFill}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 0, y: 1 }}
                />
              </Animated.View>
            )}
          </Animated.View>

          <View style={[styles.detailsContainer, {
            backgroundColor: theme.colors.background.stuffimadeup,
            borderTopLeftRadius: theme.layout.borderRadius.xxl,
            borderTopRightRadius: theme.layout.borderRadius.xxl,
            marginTop: -theme.spacing.xl,
            padding: theme.spacing.l,
            paddingBottom: theme.spacing.xxxxxxl,
            flex: 1,
            ...theme.shadows.medium
          }]}>
            <View style={styles.headerRow}>
              <Text style={[styles.mealTitle, theme.typography.title2, {
                color: theme.colors.text.primary.light,
                letterSpacing: -0.5
              }]}>
                {nutritionData?.mealName || 'Unknown Food'}
              </Text>
              <Text style={[styles.timestamp, theme.typography.footnote, {
                color: theme.colors.text.secondary.light,
                backgroundColor: 'rgba(229, 229, 234, 0.5)',
                paddingHorizontal: theme.spacing.xs,
                paddingVertical: theme.spacing.xxxs,
                borderRadius: theme.layout.borderRadius.medium,
                overflow: 'hidden'
              }]}>
                {originalItem?.createdAt ? 
                  new Date(originalItem.createdAt).toLocaleTimeString([], { 
                    hour: '2-digit', 
                    minute: '2-digit',
                    hour12: true
                  }) 
                  : 
                  new Date().toLocaleTimeString([], { 
                    hour: '2-digit', 
                    minute: '2-digit',
                    hour12: true
                  })
                }
              </Text>
            </View>

            <View style={styles.quantityRow}>
              <View style={{ flex: 1 }} />
              <View style={[styles.quantityContainer, {
                backgroundColor: 'rgba(229, 229, 234, 0.5)',
                borderRadius: theme.layout.borderRadius.large,
                padding: theme.spacing.xxs
              }]}>
                <TouchableOpacity 
                  style={[styles.quantityButton, { 
                    width: theme.layout.iconSize.large,
                    height: theme.layout.iconSize.large,
                    borderRadius: theme.layout.iconSize.large / 2,
                    backgroundColor: quantity === 1 ? 'rgba(229, 229, 234, 0.7)' : theme.colors.background.tertiary.light,
                    ...theme.mixins.center,
                    ...theme.shadows.tiny
                  }]}
                  onPress={() => handleQuantityChange(-1)}>
                  <Text style={[styles.quantityButtonText, theme.typography.button, {
                    lineHeight: theme.layout.iconSize.large,
                    textAlign: 'center',
                    marginTop: Platform.OS === 'ios' ? -theme.spacing.xxxs : 0,
                    color: quantity === 1 ? theme.colors.text.secondary.light : theme.colors.text.primary.light
                  }]}>−</Text>
                </TouchableOpacity>
                <Text style={[styles.quantityText, theme.typography.headline, {
                  color: theme.colors.text.primary.light
                }]}>
                  {quantity}
                </Text>
                <TouchableOpacity 
                  style={[styles.quantityButton, { 
                    width: theme.layout.iconSize.large,
                    height: theme.layout.iconSize.large,
                    borderRadius: theme.layout.iconSize.large / 2,
                    backgroundColor: quantity === 10 ? 'rgba(229, 229, 234, 0.7)' : theme.colors.background.tertiary.light,
                    ...theme.mixins.center,
                    ...theme.shadows.tiny
                  }]}
                  onPress={() => handleQuantityChange(1)}>
                  <Text style={[styles.quantityButtonText, theme.typography.button, {
                    lineHeight: theme.layout.iconSize.large,
                    textAlign: 'center',
                    marginTop: Platform.OS === 'ios' ? -theme.spacing.xxxs : 0,
                    color: quantity === 10 ? theme.colors.text.secondary.light : theme.colors.text.primary.light
                  }]}>+</Text>
                </TouchableOpacity>
              </View>
            </View>

            <View style={[styles.metricsGrid, {
              flexDirection: 'row',
              flexWrap: 'wrap',
              gap: theme.spacing.s,
              marginBottom: theme.spacing.l
            }]}>
              {renderMetricCard('flame.fill', 'Calories', nutritionData?.calories || 0)}
              {renderMetricCard('leaf.fill', 'Carbs', nutritionData?.carbs || 0, 'g')}
              {renderMetricCard('figure.walk', 'Protein', nutritionData?.protein || 0, 'g')}
              {renderMetricCard('drop.fill', 'Fat', nutritionData?.fat || 0, 'g')}
            </View>

            <View style={[styles.healthScoreContainer, {
              marginBottom: theme.spacing.l,
              backgroundColor: theme.colors.background.secondary.light,
              borderRadius: theme.layout.borderRadius.large,
              padding: theme.spacing.s,
              width: '100%', // Add this line

              ...theme.shadows.small
            }]}>
              <View style={[styles.healthScoreContent, theme.mixins.row]}>
                <View style={[styles.healthScoreIconContainer, {
                  width: theme.layout.iconSize.large,
                  height: theme.layout.iconSize.large,
                  borderRadius: theme.layout.iconSize.medium / 1.5,
                  backgroundColor: 'rgba(255, 59, 48, 0.15)', // Red with transparency
                  ...theme.mixins.center
                }]}>
                <SFSymbol 
                  name="heart.fill" 
                  size={theme.layout.iconSize.tiny}
                  color={theme.colors.error.light}
                  weight="semibold"
                  />
                </View>
                <View style={[styles.healthScoreTextContainer, theme.mixins.row]}>
                  <Text style={[styles.healthScoreLabel, theme.typography.callout, { 
                    color: theme.colors.text.secondary.light,
                    flex: 1
                  }]}>
                  Health Score
                </Text>
                  <Text style={[styles.healthScoreValue, theme.typography.headline, {
                    color: theme.colors.text.primary.light,
                    marginTop: theme.spacing.xxxs,
                    fontWeight: '600'
                  }]}>
                  {calculateHealthScore(nutritionData)}/10
                </Text>
                </View>
              </View>
              <View style={[styles.healthScoreBar, {
                height: theme.layout.progressBar.small,
                // height: theme.layout.buttonHeight * 0.1,
                backgroundColor: 'rgba(229, 229, 234, 0.5)',
                borderRadius: theme.layout.borderRadius.medium,
                overflow: 'hidden',
                marginTop: theme.spacing.xs, // Change from xxs to xxxs
                position: 'relative',
                top: -6, // Add this line to move just the bar up by 4 pixels
              }]}>
                <LinearGradient
                  colors={[theme.colors.success.light, theme.colors.success.dark]}
                  style={[
                    styles.healthScoreFill, 
                    { 
                      width: `${calculateHealthScore(nutritionData) * 10}%`,
                      borderRadius: theme.layout.borderRadius.medium,
                      shadowColor: theme.colors.success.light,
                      shadowOffset: { width: 0, height: 0 },
                      shadowOpacity: 0.5,
                      shadowRadius: 4
                    }
                  ]}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                />
              </View>
            </View>
          </View>
        </ScrollView>

        <View style={[styles.bottomActions, {
          position: 'absolute',
          bottom: -40,
          left: 0,
          right: 0,
          height: Platform.OS === 'ios' ? 120 : 100,
          backgroundColor: theme.colors.background.stuffimadeup,
          paddingHorizontal: theme.spacing.m,
          paddingTop: theme.spacing.xl,
          paddingBottom: Platform.OS === 'ios' ? 34 : theme.spacing.l,
          borderTopWidth: 1,
          borderTopColor: 'rgba(0,0,0,0.03)',
          ...theme.shadows.medium
        }]}>
          <View style={[styles.actionButtons, {
            ...theme.mixins.row,
            gap: theme.spacing.s,
            width: '100%',
            justifyContent: 'center'
          }]}>
            {isEditing ? (
              <TouchableOpacity 
                style={[styles.editingButton, {
                  flex: 0.8,
                  flexDirection: 'row',
                  alignItems: 'center',
                  justifyContent: 'center',
                  backgroundColor: '#000000', // Changed from theme.colors.text.primary.dark to #000000
                  borderRadius: theme.layout.borderRadius.large,
                  padding: theme.spacing.s,
                  gap: theme.spacing.xs,
                  height: theme.layout.buttonHeight,
                  ...theme.shadows.small
                }]}
                onPress={handleEditToggle}
                activeOpacity={0.8}>
                <Text style={[styles.editingButtonText, theme.typography.button2, {
                  color: "#FFFFFF"
                }]}>
                  Done
                </Text>
              </TouchableOpacity>
            ) : (
              <>
            <TouchableOpacity 
              style={[styles.fixButton, {
                flex: 0.8,
                ...theme.mixins.row,
                ...theme.mixins.center,
                backgroundColor: 'rgba(229, 229, 234, 0.7)',
                borderRadius: theme.layout.borderRadius.large,
                padding: theme.spacing.s,
                gap: theme.spacing.xs,
                height: theme.layout.buttonHeight,
                ...theme.shadows.small
              }]}
              onPress={handleEditToggle}
              activeOpacity={0.7}>
              {/* <SFSymbol 
                name="square.and.pencil" 
                size={theme.layout.iconSize.tiny}
                color={theme.colors.text.primary.light}
                weight="semibold"
              /> */}
              <Text></Text>
              <Text style={[styles.fixButtonText, theme.typography.headline, {
                color: theme.colors.text.primary.light
              }]}>
                Edit
              </Text>
            </TouchableOpacity>
            <TouchableOpacity 
              style={[
                styles.saveButton, 
                saving && styles.savingButton,
                {
                  flex: 0.8,
                  backgroundColor: '#000000', // Changed from theme.colors.text.primary.dark to #000000
                  borderRadius: theme.layout.borderRadius.large,
                  padding: theme.spacing.s,
                  alignItems: 'center',
                  justifyContent: 'center',
                  height: theme.layout.buttonHeight,
                  ...theme.shadows.small
                }
              ]}
              onPress={handleSave}
              disabled={saving}>
              {saving ? (
                <ActivityIndicator color="#FFFFFF" size="small" />
              ) : (
                <Text style={[styles.saveButtonText, theme.typography.button2, {
                  color: '#FFFFFF'
                }]}>
                  Next
                </Text>
              )}
            </TouchableOpacity>
              </>
            )}
          </View>
        </View>
      </Animated.View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background.stuffimadeup,
  },
  headerContainer: {
    position: 'relative',
    width: '100%',
    overflow: 'hidden',
  },
  headerBackground: {
    ...StyleSheet.absoluteFillObject,
    width: '100%',
    height: '100%',
  },
  headerBlur: {
    ...StyleSheet.absoluteFillObject,
    paddingTop: Platform.OS === 'ios' ? 48 : 0,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: theme.spacing.m,
    height: theme.layout.buttonHeight,
    width: '100%',
    marginTop: Platform.OS === 'ios' ? -theme.spacing.m : 0,
  },
  headerButton: {
    padding: theme.spacing.xs,
    width: theme.layout.buttonHeight * 0.7,
    height: theme.layout.buttonHeight * 0.7,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: Platform.OS === 'ios' ? theme.spacing.xxxxs : 0,
  },
  headerTitle: {
    ...theme.typography.headline,
    color: theme.colors.text.primary.light,
    textAlign: 'center',
    marginTop: Platform.OS === 'ios' ? theme.spacing.xxxxs : 0,
  },
  content: {
    flex: 1,
  },
  imageContainer: {
    width: '100%',
    position: 'relative',
    overflow: 'hidden',
    marginTop: -theme.spacing.m,
  },
  foodImage: {
    width: '100%',
    height: '100%',
    borderRadius: theme.layout.borderRadius.medium,
  },
  shareButton: {
    position: 'absolute',
    bottom: theme.spacing.xxxl,
    right: theme.spacing.m,
    backgroundColor: theme.colors.background.frostedGlass,
    borderRadius: theme.layout.borderRadius.medium,
    padding: theme.spacing.s,
  },
  detailsContainer: {
    backgroundColor: theme.colors.background.secondary.light,
    borderTopLeftRadius: theme.layout.borderRadius.large,
    borderTopRightRadius: theme.layout.borderRadius.large,
    marginTop: -theme.spacing.xl,
    padding: theme.spacing.l,
    minHeight: '400%', // Add this to ensure minimum height

    ...theme.shadows.medium,
  },
  timestamp: {
    ...theme.typography.footnote,
    color: theme.colors.text.secondary.light,
    marginLeft: theme.spacing.m,
    marginTop: -theme.spacing.xl,

  },
  mealTitle: {
    ...theme.typography.title2,
    color: theme.colors.text.primary.light,
    flex: 1,
  },
  quantityContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  quantityButton: {
    borderRadius: theme.layout.borderRadius.medium,
    backgroundColor: theme.colors.background.tertiary.light,
  },
  quantityButtonText: {
    ...theme.typography.button,
    color: theme.colors.text.primary.light,
  },
  quantityText: {
    ...theme.typography.headline,
    marginHorizontal: theme.spacing.m,
    color: theme.colors.text.primary.light,
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: theme.spacing.s,
    marginBottom: theme.spacing.l,
  },
  metricCard: {
    flex: 1,
    minHeight: theme.layout.buttonHeight * 1.4,
  },
  metricCardContent: {
    flex: 1,
    gap: theme.spacing.s,
    alignItems: 'center',
  },
  metricIconContainer: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  metricTextContainer: {
    flex: 1,
    justifyContent: 'center',
  },
  metricLabel: {
    // Margins handled in component
  },
  metricValue: {
    // Margins handled in component
  },
  healthScoreContainer: {
    marginBottom: theme.spacing.l,
    backgroundColor: theme.colors.background.secondary.light,
    borderRadius: theme.layout.borderRadius.large,
    padding: theme.spacing.s,
    height: theme.layout.buttonHeight * 1.6, // Added this line,
    width: '100%', // Add this line

    ...theme.shadows.small
  },
  healthScoreContent: {
    flex: 1,
    gap: theme.spacing.s,
    marginBottom: theme.spacing.s,
  },
  healthScoreTextContainer: {
    flex: 1,
    justifyContent: 'center',
  },
  healthScoreBar: {
    // height: theme.layout.progressBar.medium,
    backgroundColor: 'rgba(229, 229, 234, 0.5)',
    borderRadius: theme.layout.borderRadius.medium,
    overflow: 'hidden',
    marginTop: theme.spacing.xxxs // Change from xxs to xxxs
  },
  healthScoreFill: {
    height: '100%',
    borderRadius: theme.layout.borderRadius.medium,
  },
  actionButtons: {
    ...theme.mixins.row,
    gap: theme.spacing.s,
    width: '100%',
  },
  fixButton: {
    flex: 0.8,
    ...theme.mixins.row,
    ...theme.mixins.center,
    backgroundColor: theme.colors.background.tertiary.light,
    borderRadius: theme.layout.borderRadius.large,
    padding: theme.spacing.s,
    gap: theme.spacing.xs,
    height: theme.layout.buttonHeight,
  },
  fixButtonText: {
    ...theme.typography.button2,
    color: theme.colors.text.primary.light,
  },
  saveButton: {
    flex: 0.8,
    backgroundColor: '#000000', // Changed from theme.colors.text.primary.dark to #000000
    borderRadius: theme.layout.borderRadius.large,
    padding: theme.spacing.s,
    alignItems: 'center',
    justifyContent: 'center',
    height: theme.layout.buttonHeight,
  },
  saveButtonText: {
    ...theme.typography.button2,
    color: '#FFFFFF',
  },
  centerContainer: {
    flex: 1,
    ...theme.mixins.center,
    backgroundColor: theme.colors.background.primary.light,
  },
  errorText: {
    ...theme.typography.body,
    color: theme.colors.error.light,
    textAlign: 'center',
    marginBottom: theme.spacing.m,
  },
  loadingText: {
    ...theme.typography.body,
    color: theme.colors.text.secondary.light,
    marginTop: theme.spacing.m,
  },
  savingButton: {
    // opacity: 0.7,
    transform: [{ scale: 0.98 }],
  },
  quantityRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: theme.spacing.l,
    marginTop: -theme.spacing.s,
  },
  mainContainer: {
    flex: 1,
    position: 'relative',
  },
  contentContainer: {
    flexGrow: 1,
    paddingBottom: Platform.OS === 'ios' ? 120 : 100,
  },
  bottomActions: {
    position: 'absolute',
    bottom: -40,
    left: 0,
    right: 0,
    height: Platform.OS === 'ios' ? 120 : 100,
    backgroundColor: theme.colors.background.stuffimadeup,
    paddingHorizontal: theme.spacing.m,
    paddingTop: theme.spacing.xl,
    paddingBottom: Platform.OS === 'ios' ? 34 : theme.spacing.l,
    ...theme.shadows.medium,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing.s,
  },
  metricInput: {
    padding: 0,
  },
  editingButton: {
    flex: 0.8,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#000000', // Changed from theme.colors.text.primary.dark to #000000
    borderRadius: theme.layout.borderRadius.large,
    padding: theme.spacing.s,
    gap: theme.spacing.xs,
    height: theme.layout.buttonHeight,
  },
  editingButtonText: {
    ...theme.typography.button2,
    color: "#FFFFFF",
  },
  healthScoreIconContainer: {
    justifyContent: 'center',
    alignItems: 'center',
  },
});

export default ResultsScreen;