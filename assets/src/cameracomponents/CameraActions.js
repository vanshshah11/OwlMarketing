// // /Users/vanshshah/Desktop/New_app/5th_WellAI/WellAI/src/cameracomponents/CameraActions.js

import { Alert } from 'react-native';
import axios from 'axios';
import { uploadImage } from '../utils/firebase';
import { 
  analyzeImage, 
  searchFood, 
  detectPortionSize, 
  calculateNutritionWithPortion,
  processVisionResults,
} from '../utils/api';
import { logger } from '../utils/api/logging';
import FoodLogger from '../utils/api/foodlogging';
import { NativeEventEmitter, NativeModules } from 'react-native';
import { 
  validateImageData, 
  validateAnalysisResults, 
  validateDetectedItems, 
  validateSearchResults,
  ERROR_MESSAGES,
  validatePortionDetection,
  processImageData,
  compressImage 
} from './CameraUtils';
import useFoodLoggingStore from '../stores/foodLoggingStore'; // Add this line with existing imports

// Initialize event emitter only if the native module exists
export const createEventEmitter = () => {
  try {
    const { RNCameraManager } = NativeModules;
    return RNCameraManager ? new NativeEventEmitter(RNCameraManager) : null;
  } catch (error) {
    logger.warn('Failed to initialize camera event emitter', error);
    return null;
  }
};

export const handleImageCapture = async (
  cameraRef,
  setCapturedImage,
  setAnalysisResult,
  setDetectedPortions,
  setFoodOptions,
  setShowModal,
  setError,
  setProcessing,
  framingGuideRef,
  user,        // Added user parameter
  navigation   // Added navigation parameter
) => {
  if (!cameraRef.current || cameraRef.current.processing) {
    logger.warn('Camera not ready or already processing');
    return;
  }

  // Check if user is authenticated
  if (!user || !user.uid) {
    setError(ERROR_MESSAGES.UNAUTHORIZED);
    setProcessing(false);
    return;
  }

  setProcessing(true);
  setError(null);

  try {
    logger.info('Starting image capture');

    const options = {
      quality: 1.0,
      base64: false,
      fixOrientation: true,
      width: 1920,
      height: 1080,
      imageType: 'jpg',
      forceUpOrientation: true
    };
    
    const imageData = await cameraRef.current.takePictureAsync(options);

    const frameBounds = framingGuideRef?.current?.getBounds();
    if (!frameBounds) {
      throw new Error('Framing guide bounds not available');
    }

    const cropRegion = {
      x: (frameBounds.x / frameBounds.screenWidth) * imageData.width,
      y: (frameBounds.y / frameBounds.screenHeight) * imageData.height,
      width: (frameBounds.width / frameBounds.screenWidth) * imageData.width,
      height: (frameBounds.height / frameBounds.screenHeight) * imageData.height
    };

    if (!imageData.width || !imageData.height) {
      throw new Error('Image dimensions are required');
    }

    const validatedData = {
      uri: imageData.uri,
      width: cropRegion.width,
      height: cropRegion.height,
      cropRegion,
      originalWidth: imageData.width,
      originalHeight: imageData.height
    };

    setCapturedImage(validatedData);
    
    const visionResults = await analyzeImage(validatedData.uri, cropRegion);
    const validatedResults = validateAnalysisResults(visionResults);
    setAnalysisResult(validatedResults);
    
    const processedFoodItems = processVisionResults(validatedResults);
    logger.info('Vision results processed', { 
      processedItems: processedFoodItems.length 
    });

    // Early return if no food items detected
    if (processedFoodItems.length === 0) {
      setError(ERROR_MESSAGES.NO_FOOD_DETECTED);
      setProcessing(false);
      return;
    }

    const portions = await detectPortionSize(validatedResults);
    const validatedPortions = validatePortionDetection(portions);
    setDetectedPortions(validatedPortions);
    
    let finalFoodOptions = [];
    const confidenceThreshold = 0.7; // Adjust as needed

    if (processedFoodItems.length > 0) {
      const searchResults = await searchFood(processedFoodItems[0].name);
      const validatedSearchResults = validateSearchResults(searchResults);
      
      const bestPortion = validatedPortions.length > 0 
        ? validatedPortions.reduce((a, b) => a.confidence > b.confidence ? a : b)
        : null;

      finalFoodOptions = validatedSearchResults.results
        .map(result => calculateNutritionWithPortion(result, bestPortion))
        .filter(food => food.confidence >= confidenceThreshold);

      // Attempt auto-selection if high confidence result exists
      if (finalFoodOptions.length > 0) {
        try {
          await handleFoodSelection(
            finalFoodOptions[0],
            user,
            validatedData,
            () => {}, // No-op for setSelectedFood
            () => {}, // No-op for setShowModal
            navigation
          );
          
          setProcessing(false);
          return;
        } catch (autoSelectError) {
          logger.error('Auto-selection failed', autoSelectError);
          // Fall back to manual selection
        }
      }
    }

    // Fallback to manual selection
    setFoodOptions(finalFoodOptions);
    setShowModal(true);

  } catch (error) {
    logger.error('Error in handleImageCapture', error, { 
      component: 'CameraActions'
    });
    
    // Specific error handling
    const errorMessage = error.message || ERROR_MESSAGES.UNKNOWN_ERROR;
    setError(errorMessage);
    
    // Show user-friendly alert
    Alert.alert(
      'Image Capture Error',
      'Unable to process the image. Please try again.',
      [{ text: 'OK' }]
    );
  } finally {
    setProcessing(false);
  }
};

// export const handleFoodSelection = async (
//   food,
//   user,
//   capturedImage,
//   setSelectedFood,
//   setShowModal,
//   navigation
// ) => {
//   // Validate input parameters
//   if (!food || !user) {
//     logger.error('Invalid input: Food or User data missing');
//     throw new Error('Food and user data are required');
//   }

//   try {
//     const logFoodEntry = useFoodLoggingStore.getState().logFoodEntry;
//     const setUserId = useFoodLoggingStore.getState().setUserId;

//     // Sanitize and validate food data
//     const sanitizedFood = {
//       name: food?.name || 'Unknown Food',
//       calories: Math.round(food?.calories || 0),
//       nutrients: {
//         protein: (parseFloat(food?.nutrients?.protein || 0)).toFixed(1),
//         carbs: (parseFloat(food?.nutrients?.carbs || 0)).toFixed(1),
//         fat: (parseFloat(food?.nutrients?.fat || 0)).toFixed(1),
//         fiber: (parseFloat(food?.nutrients?.fiber || 0)).toFixed(1)
//       },
//       portionInfo: {
//         type: food?.portionInfo?.type || 'serving',
//         grams: (parseFloat(food?.portionInfo?.grams || 100)).toFixed(1),
//         confidence: (parseFloat(food?.portionInfo?.confidence || 1.0)).toFixed(2)
//       },
//       source: food?.source || '',
//       servingSize: (food?.servingSize || '100').toString(),
//       servingUnit: food?.servingUnit || 'g'
//     };

//     const sanitizedImage = capturedImage ? {
//       uri: capturedImage.uri,
//       width: Number(capturedImage.width) || 800,
//       height: Number(capturedImage.height) || 600,
//     } : null;

//     // Validate food data
//     const isValidData = validateFoodData(sanitizedFood);
//     if (!isValidData.valid) {
//       throw new Error(`Invalid food data: ${isValidData.reason}`);
//     }

//     // Set UI state and navigate immediately
//     setSelectedFood(food);
//     setShowModal(false);
//     navigation.goBack();

//     // Set user ID in the store
//     setUserId(user.uid);

//     // Log food entry in the background
//     const loggingPromise = logFoodEntry(
//       sanitizedFood,
//       sanitizedImage?.uri
//     ).catch(error => {
//       // Silent background error logging
//       logger.error('Background food logging failed', error, { 
//         foodName: food?.name || 'Unknown',
//         userId: user?.uid || 'Unknown'
//       });
      
//       // Optional: Implement retry or offline queue mechanism
//       Alert.alert(
//         'Logging Issue',
//         'Unable to save food entry. It will be saved when connection is restored.',
//         [{ text: 'OK' }]
//       );
//     });

//     // Optionally wait for logging to complete (uncomment if needed)
//     // await loggingPromise;

//   } catch (error) {
//     // More comprehensive error handling
//     logger.error('Error in handleFoodSelection', error, { 
//       foodName: food?.name || 'Unknown',
//       userId: user?.uid || 'Unknown'
//     });
    
//     // Show error alert
//     Alert.alert(
//       'Food Entry Error',
//       getErrorMessage(error),
//       [{ text: 'OK' }]
//     );

//     // Rethrow to allow caller to handle
//     throw error;
//   }
// };

export const handleFoodSelection = async (
  food,
  user,
  capturedImage,
  setSelectedFood,
  setShowModal,
  navigation
) => {
  if (!food || !user) {
    logger.error('Invalid input: Food or User data missing');
    throw new Error('Food and user data are required');
  }

  try {
    const logFoodEntry = useFoodLoggingStore.getState().logFoodEntry;
    const setUserId = useFoodLoggingStore.getState().setUserId;

    // Sanitize and validate food data (keep existing validation)
    const sanitizedFood = {
      name: food?.name || 'Unknown Food',
      calories: Math.round(food?.calories || 0),
      nutrients: {
        protein: (parseFloat(food?.nutrients?.protein || 0)).toFixed(1),
        carbs: (parseFloat(food?.nutrients?.carbs || 0)).toFixed(1),
        fat: (parseFloat(food?.nutrients?.fat || 0)).toFixed(1),
        fiber: (parseFloat(food?.nutrients?.fiber || 0)).toFixed(1)
      },
      portionInfo: {
        type: food?.portionInfo?.type || 'serving',
        grams: (parseFloat(food?.portionInfo?.grams || 100)).toFixed(1),
        confidence: (parseFloat(food?.portionInfo?.confidence || 1.0)).toFixed(2)
      },
      source: food?.source || '',
      servingSize: (food?.servingSize || '100').toString(),
      servingUnit: food?.servingUnit || 'g'
    };

    const sanitizedImage = capturedImage ? {
      uri: capturedImage.uri,
      width: Number(capturedImage.width) || 800,
      height: Number(capturedImage.height) || 600,
    } : null;

    // Set UI state immediately
    setSelectedFood(food);
    setShowModal(false);
    navigation.goBack();

    // Set user ID in the store
    setUserId(user.uid);

    // Log food entry (now with optimistic update)
    logFoodEntry(sanitizedFood, sanitizedImage?.uri)
      .catch(error => {
        logger.error('Background food logging failed', error, { 
          foodName: food?.name || 'Unknown',
          userId: user?.uid || 'Unknown'
        });
        
        // Optional: Show non-blocking notification
        Alert.alert(
          'Logging Issue',
          'Unable to save food entry. It will be saved when connection is restored.',
          [{ text: 'OK' }]
        );
      });

  } catch (error) {
    logger.error('Error in handleFoodSelection', error);
    
    Alert.alert(
      'Food Entry Error',
      getErrorMessage(error),
      [{ text: 'OK' }]
    );

    throw error;
  }
};

export const validateFoodData = (foodData) => {
  if (!foodData.name) {
    return { valid: false, reason: 'Food name is required' };
  }
  
  if (foodData.calories < 0) {
    return { valid: false, reason: 'Calories cannot be negative' };
  }

  if (!foodData.portionInfo?.grams) {
    return { valid: false, reason: 'Portion size is required' };
  }

  // Add nutrient validation
  const nutrients = foodData.nutrients || {};
  const hasValidNutrients = Object.values(nutrients).some(value => 
    parseFloat(value) > 0
  );
  
  if (!hasValidNutrients) {
    return { valid: false, reason: 'At least one nutrient value is required' };
  }

  return { valid: true };
};

export const getErrorMessage = (error) => {
  switch(error.code) {
    case 'INVALID_FOOD_DATA':
      return 'The food information appears to be invalid. Please try again with complete information.';
    case 'FOOD_LOGGING_FAILED':
      return 'Unable to save your food entry. Please check your connection and try again.';
    default:
      return 'Unable to log food entry. Please try again.';
  }
};

export const handleFlashToggle = (setFlashMode, RNCameraConstants) => {
  setFlashMode(prevMode => 
    prevMode === RNCameraConstants.FlashMode.off
      ? RNCameraConstants.FlashMode.torch
      : RNCameraConstants.FlashMode.off
  );
};

export const handleBackPress = (navigation) => {
  navigation.goBack();
};




// export const handleImageCapture = async (
//   cameraRef,
//   setCapturedImage,
//   setAnalysisResult,
//   setDetectedPortions,
//   setFoodOptions,
//   setShowModal,
//   setError,
//   setProcessing,
//   framingGuideRef
// ) => {
//   if (!cameraRef.current || cameraRef.current.processing) {
//     logger.warn('Camera not ready or already processing');
//     return;
//   }

//   setProcessing(true);
//   setError(null);

//   try {
//     logger.info('Starting image capture');

//     const options = {
//       quality: 1.0,
//       base64: false,
//       fixOrientation: true,
//       width: 1920,
//       height: 1080,
//       imageType: 'jpg',
//       forceUpOrientation: true
//     };
    
//     // In handleImageCapture function, modify the image processing section:
//     const imageData = await cameraRef.current.takePictureAsync(options);

//     // Get framing guide bounds - this part is already correct
//     const frameBounds = framingGuideRef?.current?.getBounds();
//     if (!frameBounds) {
//       throw new Error('Framing guide bounds not available');
//     }

//     // Calculate crop dimensions based on the framing guide - this is already correct
//     const cropRegion = {
//       x: (frameBounds.x / frameBounds.screenWidth) * imageData.width,
//       y: (frameBounds.y / frameBounds.screenHeight) * imageData.height,
//       width: (frameBounds.width / frameBounds.screenWidth) * imageData.width,
//       height: (frameBounds.height / frameBounds.screenHeight) * imageData.height
//     };

//     // Add this new validation check before proceeding
//     if (!imageData.width || !imageData.height) {
//       throw new Error('Image dimensions are required');
//     }
//     // Create validated data with all required dimensions - modify this part
//     const validatedData = {
//       uri: imageData.uri,
//       width: cropRegion.width,  // Use crop width instead of full image width
//       height: cropRegion.height, // Use crop height instead of full image height
//       cropRegion,
//       originalWidth: imageData.width,
//       originalHeight: imageData.height
//     };

//     setCapturedImage(validatedData);
    
//     // Pass the crop region to the API
//     const visionResults = await analyzeImage(validatedData.uri, cropRegion);
//     const validatedResults = validateAnalysisResults(visionResults);
//     setAnalysisResult(validatedResults);
    
//     // Process vision results to get refined food items
//     const processedFoodItems = processVisionResults(validatedResults);
//     logger.info('Vision results processed', { 
//       processedItems: processedFoodItems.length 
//     });

//     // Detect portions
//     const portions = await detectPortionSize(validatedResults);
//     const validatedPortions = validatePortionDetection(portions);
//     setDetectedPortions(validatedPortions);
    
//     // Search food database using the most confident processed result
//     let finalFoodOptions = [];
//     if (processedFoodItems.length > 0) {
//       const searchResults = await searchFood(processedFoodItems[0].name);
//       const validatedSearchResults = validateSearchResults(searchResults);
      
//       // Calculate nutrition with portions
//       const bestPortion = validatedPortions.length > 0 
//         ? validatedPortions.reduce((a, b) => a.confidence > b.confidence ? a : b)
//         : null;

//       finalFoodOptions = validatedSearchResults.results.map(result => 
//         calculateNutritionWithPortion(result, bestPortion)
//       );
//     }

//     setFoodOptions(finalFoodOptions);
//     setShowModal(true);

//   } catch (error) {
//     logger.error('Error in handleImageCapture', error, { 
//       component: 'CameraActions'
//     });
//     setError(error.message || ERROR_MESSAGES.UNKNOWN_ERROR);
//   } finally {
//     setProcessing(false);
//   }
// };

// export const handleFoodSelection = async (
//   food,
//   user,
//   capturedImage,
//   setSelectedFood,
//   setShowModal,
//   navigation
// ) => {
//   try {
//     // Get store methods
//     const logFoodEntry = useFoodLoggingStore.getState().logFoodEntry;
//     const setUserId = useFoodLoggingStore.getState().setUserId;

//     if (!food || !user) {
//       throw new Error('Food and user data are required');
//     }

//     // Set UI state and navigate immediately
//     setSelectedFood(food);
//     setShowModal(false);
//     navigation.goBack();

//     // Set user ID in the store
//     setUserId(user.uid);

//     // Continue with food logging in the background
//     const sanitizedFood = {
//       name: food?.name || 'Unknown Food',
//       calories: Math.round(food?.calories || 0),
//       nutrients: {
//         protein: (parseFloat(food?.nutrients?.protein || 0)).toFixed(1),
//         carbs: (parseFloat(food?.nutrients?.carbs || 0)).toFixed(1),
//         fat: (parseFloat(food?.nutrients?.fat || 0)).toFixed(1),
//         fiber: (parseFloat(food?.nutrients?.fiber || 0)).toFixed(1)
//       },
//       portionInfo: {
//         type: food?.portionInfo?.type || 'serving',
//         grams: (parseFloat(food?.portionInfo?.grams || 100)).toFixed(1),
//         confidence: (parseFloat(food?.portionInfo?.confidence || 1.0)).toFixed(2)
//       },
//       source: food?.source || '',
//       servingSize: (food?.servingSize || '100').toString(),
//       servingUnit: food?.servingUnit || 'g'
//     };

//     const sanitizedImage = capturedImage ? {
//       uri: capturedImage.uri,
//       width: Number(capturedImage.width) || 800,
//       height: Number(capturedImage.height) || 600,
//     } : null;

//     const sanitizedUser = {
//       uid: user.uid || null,
//       settings: user.settings || {}
//     };

//     if (!sanitizedUser.uid) {
//       throw new Error('Valid user ID is required');
//     }

//     const isValidData = validateFoodData(sanitizedFood);
    
//     if (!isValidData.valid) {
//       throw new Error(`Invalid food data: ${isValidData.reason}`);
//     }

//     // Use store's logFoodEntry method
//     await logFoodEntry(
//       sanitizedFood,
//       sanitizedImage?.uri
//     );

//   } catch (error) {
//     // Log errors silently in the background
//     logger.error('Error in handleFoodSelection', error, { 
//       foodName: food?.name || 'Unknown',
//       userId: user?.uid || 'Unknown'
//     });
//     // Only show error if we haven't navigated yet
//     if (!navigation.isFocused()) {
//       Alert.alert(
//         'Error',
//         getErrorMessage(error),
//         [{ text: 'OK' }]
//       );
//     }
//   }
// };

// Helper functions remain unchanged





// export const handleFoodSelection = async (
//   food,
//   user,
//   capturedImage,
//   setSelectedFood,
//   setShowModal,
//   navigation
// ) => {
//   try {
//     if (!food || !user) {
//       throw new Error('Food and user data are required');
//     }

//     // Set UI state and navigate immediately
//     setSelectedFood(food);
//     setShowModal(false);
//     navigation.goBack();

//     // Continue with food logging in the background
//     const sanitizedFood = {
//       name: food?.name || 'Unknown Food',
//       calories: Math.round(food?.calories || 0),
//       nutrients: {
//         protein: (parseFloat(food?.nutrients?.protein || 0)).toFixed(1),
//         carbs: (parseFloat(food?.nutrients?.carbs || 0)).toFixed(1),
//         fat: (parseFloat(food?.nutrients?.fat || 0)).toFixed(1),
//         fiber: (parseFloat(food?.nutrients?.fiber || 0)).toFixed(1)
//       },
//       portionInfo: {
//         type: food?.portionInfo?.type || 'serving',
//         grams: (parseFloat(food?.portionInfo?.grams || 100)).toFixed(1),
//         confidence: (parseFloat(food?.portionInfo?.confidence || 1.0)).toFixed(2)
//       },
//       source: food?.source || '',
//       servingSize: (food?.servingSize || '100').toString(),
//       servingUnit: food?.servingUnit || 'g'
//     };

//     const sanitizedImage = capturedImage ? {
//       uri: capturedImage.uri,
//       width: Number(capturedImage.width) || 800,
//       height: Number(capturedImage.height) || 600,
//     } : null;

//     const sanitizedUser = {
//       uid: user.uid || null,
//       settings: user.settings || {}
//     };

//     if (!sanitizedUser.uid) {
//       throw new Error('Valid user ID is required');
//     }

//     const foodLogger = new FoodLogger(sanitizedUser.uid);
//     const isValidData = validateFoodData(sanitizedFood);
    
//     if (!isValidData.valid) {
//       throw new Error(`Invalid food data: ${isValidData.reason}`);
//     }

//     await foodLogger.logFoodEntry(
//       sanitizedFood,
//       sanitizedImage?.uri
//     );

//   } catch (error) {
//     // Log errors silently in the background
//     logger.error('Error in handleFoodSelection', error, { 
//       foodName: food?.name || 'Unknown',
//       userId: user?.uid || 'Unknown'
//     });
//     // Only show error if we haven't navigated yet
//     if (!navigation.isFocused()) {
//       Alert.alert(
//         'Error',
//         getErrorMessage(error),
//         [{ text: 'OK' }]
//       );
//     }
//   }
// };
