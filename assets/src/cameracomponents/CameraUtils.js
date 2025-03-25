// // /Users/vanshshah/Desktop/New_app/5th_WellAI/WellAI/src/cameracomponents/CameraUtils.js
import Logger from '../utils/logger';
import ImageManipulator from 'react-native-image-manipulator';

const logger = new Logger('CameraUtils');

export const ERROR_MESSAGES = {
  CAMERA_PERMISSION: 'Camera permission is required to use this feature',
  IMAGE_CAPTURE: 'Failed to capture image. Please try again',
  IMAGE_ANALYSIS: 'Failed to analyze image. Please try again',
  NO_FOOD_DETECTED: 'No food items detected. Please try again with a clearer photo',
  FOOD_SEARCH: 'Unable to find matching foods. Please try again',
  UPLOAD_FAILED: 'Failed to upload image. Please check your connection',
  AUTH_REQUIRED: 'Please sign in to log food',
  SAVE_FAILED: 'Failed to save food log. Please try again',
  NETWORK_ERROR: 'Network connection error. Please check your connection',
  UNKNOWN_ERROR: 'An unexpected error occurred. Please try again'
};

export const IMAGE_VALIDATION = {
  MAX_SIZE: 10 * 1024 * 1024, // 10MB
  ALLOWED_MIME_TYPES: ['image/jpeg', 'image/png', 'image/jpg', 'application/octet-stream'], // Added octet-stream for file URIs
  BASE64_PATTERN: /^data:image\/(jpeg|png|jpg);base64,/,
  FILE_URI_PATTERN: /^file:\/\//
};


// Image processing constants optimized for food recognition
const IMAGE_PROCESSING = {
  BRIGHTNESS_INCREASE: 0.25,  // 15% brightness increase - optimal for food details
  CONTRAST_INCREASE: 0.15,    // 8% contrast increase - maintains natural look while enhancing edges
  FRAME_PADDING: 20,         // this is 20 before Padding around the frame in pixels
  SATURATION_INCREASE: 0.10  // 5% saturation increase - subtle enhancement for food colors
};

export const processAndOptimizeImage = async (imageUri, frameBounds) => {
  try {
    logger.info('Starting image optimization', { originalUri: imageUri });
    
    // First crop to frame bounds if provided
    let processedResult = imageUri;
    if (frameBounds) {
      const croppedResult = await ImageManipulator.manipulate(
        imageUri,
        [{
          crop: {
            originX: Math.max(0, frameBounds.x),
            originY: Math.max(0, frameBounds.y),
            width: frameBounds.width,
            height: frameBounds.height
          }
        }],
        {
          format: 'jpeg',
          quality: 1
        }
      );
      processedResult = croppedResult.uri;
    }

    // Then enhance image quality
    const enhancedResult = await ImageManipulator.manipulate(
      processedResult,
      [
        {
          brightness: IMAGE_PROCESSING.BRIGHTNESS_INCREASE
        },
        {
          contrast: IMAGE_PROCESSING.CONTRAST_INCREASE
        },
        {
          saturation: IMAGE_PROCESSING.SATURATION_INCREASE
        }
      ],
      {
        format: 'JPEG',
        quality: 0.9  // Maintain high quality for API processing
      }
    );

    logger.info('Image optimization complete', {
      finalUri: enhancedResult.uri,
      optimizationApplied: {
        brightness: IMAGE_PROCESSING.BRIGHTNESS_INCREASE,
        contrast: IMAGE_PROCESSING.CONTRAST_INCREASE,
        saturation: IMAGE_PROCESSING.SATURATION_INCREASE
      }
    });

    return enhancedResult;

  } catch (error) {
    logger.error('Image processing failed', { error });
    throw new Error('Failed to process image: ' + error.message);
  }
};

export const processImageData = async (blob, cropRegion = null) => {
  try {
    // Handle string URIs (both file:// and base64)
    if (typeof blob === 'string') {
      // If it's a file URI, return it directly
      if (blob.startsWith('file://')) {
        return blob;
      }
      // If it's a base64 string, validate it
      if (blob.includes('base64,')) {
        validateBase64Image(blob);
        return blob;
      }
    }

    // Handle blob object with uri property
    if (blob?.uri) {
      return blob.uri;
    }

    // If we reach here, the image format is invalid
    throw new Error('Invalid image format');
  } catch (error) {
    logger.error('Image processing failed', { error, cropRegion });
    throw error;
  }
};

export const validateBase64Image = (base64String) => {
  if (!base64String) {
    throw new Error('Image data is required');
  }

  if (typeof base64String === 'string' && base64String.startsWith('file://')) {
    return true; // Allow file URIs to pass validation
  }

  if (!base64String.includes('base64,')) {
    throw new Error('Invalid image format');
  }

  return true;
};

export const validateImageData = (data) => {
  // Handle string input (file URI or base64)
  if (typeof data === 'string') {
    if (data.startsWith('file://')) {
      return { uri: data };
    }
    if (data.includes('base64,')) {
      return { uri: data };
    }
  }

  // Handle object input
  if (!data) {
    throw new Error('Invalid image data: missing data');
  }

  // If it's an object with uri property
  if (data.uri) {
    return data;
  }

  // If dimensions are provided, validate them
  if (data.width && data.height) {
    if (data.cropRegion) {
      const { x, y, width, height } = data.cropRegion;
      if (x < 0 || y < 0 || width <= 0 || height <= 0) {
        throw new Error('Invalid crop region dimensions');
      }

      // Ensure the crop region doesn't exceed image bounds
      if (x + width > data.width || y + height > data.height) {
        // Automatically adjust dimensions to fit within bounds
        data.cropRegion.width = Math.min(width, data.width - x);
        data.cropRegion.height = Math.min(height, data.height - y);
      }

      // Store original dimensions for reference
      data.originalDimensions = {
        width: data.width,
        height: data.height
      };
    }
    return data;
  }

  throw new Error('Invalid image data: missing URI');
};

export const validateAnalysisResults = (results) => {
  if (!results) {
    throw new Error(ERROR_MESSAGES.IMAGE_ANALYSIS);
  }
  
  if (!results.labelAnnotations || !Array.isArray(results.labelAnnotations)) {
    logger.error('Invalid API response structure', { results });
    throw new Error('Invalid API response format');
  }
  
  if (results.error) {
    logger.error('API returned error', { error: results.error });
    throw new Error(`API Error: ${results.error.message}`);
  }
  
  const hasConfidentResults = results.labelAnnotations
    .some(label => label.score >= 0.8);
  
  if (!hasConfidentResults) {
    logger.warn('No high-confidence detections', { 
      highestScore: Math.max(...results.labelAnnotations.map(label => label.score || 0)) 
    });
    throw new Error('No high-confidence detections found');
  }

  logger.info('Vision API results validated', {
    totalLabels: results.labelAnnotations.length,
    confidenceScores: results.labelAnnotations.map(label => ({
      label: label.description,
      score: label.score
    }))
  });

  return results;
};

export const validateDetectedItems = (items) => {
  if (!items?.length) {
    throw new Error(ERROR_MESSAGES.NO_FOOD_DETECTED);
  }
  return items;
};

export const validateSearchResults = (results) => {
    if (!results || typeof results !== 'object') {
        throw new Error('Invalid search results format');
    }
      
    if (!Array.isArray(results.results)) {
        throw new Error('Invalid search results structure');
    }
      
    if (results.results.length === 0) {
        throw new Error(ERROR_MESSAGES.FOOD_SEARCH);
    }

    results.results.forEach(result => {
        if (!result.name || typeof result.name !== 'string') {
            throw new Error('Invalid food item name');
        }
        if (typeof result.calories !== 'number') {
            throw new Error('Invalid calorie information');
        }
    });
    return results;
};

export const validatePortionDetection = (portions) => {
    if (!portions || !Array.isArray(portions)) {
      throw new Error('Invalid portion detection results');
    }
    
    // if (portions.length === 0) {
    //   logger.warn('No portions detected');
    //   return [];
    // }
    
    return portions.filter(portion => 
      portion && 
      typeof portion.confidence === 'number' &&
      portion.confidence > 0.6
    );
};

export const validateNutritionData = (data) => {
  const required = [
    'name',
    'calories',
    'nutrients.protein',
    'nutrients.carbs',
    'nutrients.fat',
    'nutrients.fiber',
    'portionInfo.grams'
  ];

  const missing = required.filter(path => {
    const parts = path.split('.');
    let value = data;
    for (const part of parts) {
      value = value?.[part];
      if (value === undefined || value === null) return true;
    }
    return false;
  });

  if (missing.length > 0) {
    throw new Error(`Missing required fields: ${missing.join(', ')}`);
  }

  return true;
};

export const getImageDataType = (imageData) => {
  if (typeof imageData === 'string') {
    if (imageData.startsWith('file://')) {
      return 'file_uri';
    }
    if (imageData.includes('base64,')) {
      return 'base64';
    }
    return 'unknown';
  }
  
  if (imageData?.uri) {
    return 'object_uri';
  }
  
  return 'unknown';
};