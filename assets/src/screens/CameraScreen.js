//CameraScreen.js
///Users/vanshshah/Desktop/New_app/5th_WellAI/WellAI/src/screens/CameraScreen.js

import React, { useRef, useState, useEffect } from 'react';
import { 
  View, 
  TouchableOpacity, 
  Text, 
  StyleSheet, 
  Alert, 
  ActivityIndicator, 
  SafeAreaView,
  Modal,
  FlatList,
  Platform,
  StatusBar,
  Dimensions,
  PanResponder,
  Linking
} from 'react-native';
import { RNCamera } from 'react-native-camera';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { BlurView } from '@react-native-community/blur';
import { SFSymbol } from 'react-native-sfsymbols';
import { useNavigation, useIsFocused, useFocusEffect } from '@react-navigation/native';
import { check, PERMISSIONS, request, RESULTS } from 'react-native-permissions';

import { analyzeImage, searchFood, logFoodWithImageAndPortion, detectPortionSize, calculateNutritionWithPortion } from '../utils/api';
import { auth, uploadImage, addCalorieEntry } from '../utils/firebase';
import theme from '../styles/theme';
import Logger from '../utils/logger'; // Assume we have a logging utility
import { 
  validateImageData,
  validateAnalysisResults,
  validateDetectedItems,
  validateSearchResults,
  ERROR_MESSAGES,
  validatePortionDetection,  // Add this import 
} from '../cameracomponents/CameraUtils';
import {
  handleImageCapture,
  handleFoodSelection,
  handleFlashToggle,
  handleBackPress
} from '../cameracomponents/CameraActions';
import { styles } from '../styles/CameraScreen.styles';

const { width, height } = Dimensions.get('window');
const FRAME_SIZE = theme.layout.maxContentWidth;
const logger = new Logger('CameraScreen');

const CameraScreen = () => {
  const navigation = useNavigation();
  const isFocused = useIsFocused();
  const cameraRef = useRef(null);
  const framingGuideRef = useRef(null);
  const [processing, setProcessing] = useState(false);
  const [capturedImage, setCapturedImage] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [foodOptions, setFoodOptions] = useState([]);
  const [selectedFood, setSelectedFood] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [flashMode, setFlashMode] = useState(RNCamera.Constants.FlashMode.off);
  const [detectedPortions, setDetectedPortions] = useState([]);
  const [error, setError] = useState(null);
  const insets = useSafeAreaInsets();
  const [user, setUser] = useState(null);
  const [cameraPermission, setCameraPermission] = useState(null);
  const [showPermissionDeniedUI, setShowPermissionDeniedUI] = useState(false);
  const [permissionStatus, setPermissionStatus] = useState(null);
  const [permissionChecked, setPermissionChecked] = useState(false);

  useEffect(() => {
    const unsubscribe = auth.onAuthStateChanged(user => {
      try {
        setUser(user);
        logger.info('Auth state changed', { userId: user?.uid });
      } catch (error) {
        logger.error('Auth state change error', { error });
      }
    });
    return unsubscribe;
  }, []);

  useEffect(() => {
    if ((isFocused && !permissionChecked) || permissionStatus === null) {
      checkCameraPermission();
    }
  }, [isFocused, permissionStatus]);

  useEffect(() => {
    return () => {
      if (cameraRef.current) {
        cameraRef.current.stopPreview();
      }
      setCapturedImage(null);
      setAnalysisResult(null);
      setFoodOptions([]);
      setSelectedFood(null);
      setShowModal(false);
      setError(null);
      setProcessing(false);
    };
  }, []);

  // Add this after your existing useEffects
  useFocusEffect(
    React.useCallback(() => {
      if (permissionStatus === RESULTS.BLOCKED) {
        checkCameraPermission();
      }
    }, [permissionStatus])
  );

  const checkCameraPermission = async () => {
    try {
      const status = await check(
        Platform.OS === 'ios' 
          ? PERMISSIONS.IOS.CAMERA 
          : PERMISSIONS.ANDROID.CAMERA
      );
      
      setPermissionStatus(status);
      setPermissionChecked(true);
      
      switch (status) {
        case RESULTS.DENIED:
          requestCameraPermission();
          break;
          
        case RESULTS.GRANTED:
          setCameraPermission(true);
          setShowPermissionDeniedUI(false);
          break;
          
        case RESULTS.BLOCKED:
          setCameraPermission(false);
          setShowPermissionDeniedUI(true);
          showPermissionBlockedAlert();
          break;
          
        default:
          setCameraPermission(false);
          setShowPermissionDeniedUI(true);
      }
    } catch (error) {
      logger.error('Camera permission check failed', { error });
      setShowPermissionDeniedUI(true);
      Alert.alert(
        'Error',
        'Failed to check camera permissions. Please try again.',
        [{ text: 'OK' }]
      );
    }
  };

  const requestCameraPermission = async () => {
    try {
      const result = await request(
        Platform.OS === 'ios' 
          ? PERMISSIONS.IOS.CAMERA 
          : PERMISSIONS.ANDROID.CAMERA
      );
      
      setPermissionStatus(result);
      
      if (result === RESULTS.GRANTED || result === RESULTS.LIMITED) {
        setCameraPermission(true);
        setShowPermissionDeniedUI(false);
      } else {
        setCameraPermission(false);
        setShowPermissionDeniedUI(true);
        if (result === RESULTS.BLOCKED) {
          showPermissionBlockedAlert();
        }
      }
    } catch (error) {
      logger.error('Camera permission request failed', { error });
      setCameraPermission(false);
      setShowPermissionDeniedUI(true);
    }
  };
  
  const showPermissionBlockedAlert = () => {
    Alert.alert(
      'Camera Permission Required',
      'Please enable camera access in your device settings to use this feature.',
      [
        {
          text: 'Open Settings',
          onPress: handleOpenSettings
        },
        {
          text: 'Cancel',
          style: 'cancel'
        }
      ],
      { cancelable: false }
    );
  };

  const handleError = (error, customMessage) => {
    logger.error('Error occurred', { 
      error, 
      component: 'CameraScreen',
      customMessage 
    });
  
    const message = customMessage || 
      ERROR_MESSAGES[error.code] || 
      error.message || 
      ERROR_MESSAGES.UNKNOWN_ERROR;
    
    setError(message);
    Alert.alert('Error', message, [{ 
      text: 'OK',
      onPress: () => {
        setError(null);
        setProcessing(false);
      }
    }]);
  };

  // const onImageCapture = async () => {
  //   return handleImageCapture(
  //     cameraRef,
  //     setCapturedImage,
  //     setAnalysisResult,
  //     setDetectedPortions,
  //     setFoodOptions,
  //     setShowModal,
  //     setError,
  //     setProcessing,
  //     framingGuideRef  
  //   );
  // };

  const onImageCapture = async () => {
    return handleImageCapture(
      cameraRef,
      setCapturedImage,
      setAnalysisResult,
      setDetectedPortions,
      setFoodOptions,
      setShowModal,
      setError,
      setProcessing,
      framingGuideRef,
      user,         // Add user parameter
      navigation    // Add navigation parameter
    );
  };
  
  const onFoodSelection = async (food) => {
    return handleFoodSelection(
      food,
      user,
      capturedImage,
      setSelectedFood,
      setShowModal,
      navigation
    );
  };
  
  const onFlashToggle = () => {
    handleFlashToggle(setFlashMode, RNCamera.Constants);
  };
  
  const onBackPress = () => {
    return handleBackPress(navigation);
  };

  const handleOpenSettings = async () => {
    try {
      await Linking.openSettings();
    } catch (error) {
      logger.error('Failed to open settings', { error });
      Alert.alert(
        'Error',
        'Unable to open device settings. Please open settings manually.',
        [{ text: 'OK' }]
      );
    }
  };

  const renderPermissionDeniedView = () => (
    <SafeAreaView style={styles.permissionContainer}>
      <View style={styles.permissionContent}>
        <SFSymbol 
          name="camera.circle"
          weight="bold"
          scale="large"
          color={theme.colors.text.secondary.dark}
          size={60}
        />
        <Text style={[styles.permissionTitle, theme.typography.title2]}>
          {permissionStatus === RESULTS.BLOCKED 
            ? 'Camera Access Blocked'
            : 'Camera Permission Required'}
        </Text>
        <Text style={[styles.permissionText, theme.typography.body]}>
          {permissionStatus === RESULTS.BLOCKED 
            ? 'Please enable camera access in your device settings to continue.'
            : 'To capture and analyze your food, we need access to your camera.'}
        </Text>
        <View style={styles.permissionButtons}>
          <TouchableOpacity
            style={[styles.permissionButton, styles.permissionButtonPrimary]}
            onPress={permissionStatus === RESULTS.BLOCKED 
              ? handleOpenSettings 
              : requestCameraPermission}
          >
            <Text style={[styles.permissionButtonText, theme.typography.button]}>
              {permissionStatus === RESULTS.BLOCKED 
                ? 'Open Settings'
                : 'Grant Permission'}
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.permissionButton, styles.permissionButtonSecondary]}
            onPress={() => navigation.goBack()}
          >
            <Text style={[styles.permissionButtonText, theme.typography.button]}>
              Go Back
            </Text>
          </TouchableOpacity>
        </View>
      </View>
    </SafeAreaView>
  );

  if (!permissionChecked) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
      </View>
    );
  }

  if (showPermissionDeniedUI) {
    return renderPermissionDeniedView();
  }

  const FramingGuide = React.forwardRef(({ onFrameChange }, ref) => {
    const FRAME_SIZE = Math.min(theme.layout.maxContentWidth, theme.responsive.height(40));
    
    // Calculate frame position using theme spacing
    const frameX = (Dimensions.get('window').width - FRAME_SIZE) / 2;
    const frameY = (Dimensions.get('window').height - FRAME_SIZE) / 2.5;
  
    useEffect(() => {
      if (ref) {
        ref.current = {
          getBounds: () => ({
            x: frameX,
            y: frameY,
            width: FRAME_SIZE,
            height: FRAME_SIZE,
            screenWidth: Dimensions.get('window').width,
            screenHeight: Dimensions.get('window').height
          })
        };
      }
    }, []);
    
    return (
      <View 
        style={[
          styles.framingGuide,
          {
            width: FRAME_SIZE,
            height: FRAME_SIZE,
            left: frameX,
            top: frameY,
            // borderWidth: theme.layout.camera.frameGuideThickness,
            borderColor: theme.colors.background.camera.frameGuide
          }
        ]}
      >
        <View style={[styles.corner, styles.topLeft]} />
        <View style={[styles.corner, styles.topRight]} />
        <View style={[styles.corner, styles.bottomLeft]} />
        <View style={[styles.corner, styles.bottomRight]} />
      </View>
    );
  });

  return (
    <View style={styles.container}>
      <StatusBar translucent backgroundColor="transparent" barStyle="light-content" />
      
      {error && (
        <View style={[styles.errorContainer, { backgroundColor: theme.colors.error.dark }]}>
          <Text style={[styles.errorText, theme.typography.footnote]}>
            {error}
          </Text>
        </View>
      )}

      {isFocused && (
        <RNCamera
          ref={cameraRef}
          style={StyleSheet.absoluteFill}
          type={RNCamera.Constants.Type.back}
          flashMode={flashMode}
          captureAudio={false}
        >
          <SafeAreaView style={[styles.overlay, { paddingTop: insets.top }]}>
            <View style={styles.header}>
              <TouchableOpacity 
                onPress={onBackPress} 
                style={[styles.backButton, theme.mixins.camera.control]}
              >
                <SFSymbol 
                  name="chevron.left" 
                  weight="bold"
                  scale="large"
                  color={theme.colors.text.primary.dark}
                  size={theme.layout.iconSize.tiny}
                />
              </TouchableOpacity>
              <Text style={[styles.headerText, theme.typography.headline]}>
                Capture Food
              </Text>
            </View>
            
            <FramingGuide ref={framingGuideRef} />
            
            <View style={styles.controls}>
              <TouchableOpacity 
                onPress={onFlashToggle} 
                style={[styles.controlButton, theme.mixins.camera.control, { position: 'absolute', left: theme.spacing.m }]}
              >
                <SFSymbol 
                  name={flashMode === RNCamera.Constants.FlashMode.off ? "bolt.slash.fill" : "bolt.fill"}
                  weight="bold"
                  scale="large"
                  color={theme.colors.text.primary.dark}
                  size={theme.layout.iconSize.tiny}
                />
              </TouchableOpacity>
              
              <TouchableOpacity 
                onPress={onImageCapture} 
                style={[styles.captureButton, {
                  backgroundColor: theme.colors.background.camera.captureButton,
                }]}
              >
                {processing ? (
                  <ActivityIndicator size="large" color={theme.colors.text.primary.dark} />
                ) : (
                  <View style={styles.captureButtonInner} />
                )}
              </TouchableOpacity>
              
              {/* Empty view removed */}
            </View>
          </SafeAreaView>
        </RNCamera>
      )}
      
      <Modal
        animationType="slide"
        transparent={true}
        visible={showModal}
        onRequestClose={() => setShowModal(false)}
      >
        <BlurView 
          style={styles.modalContainer} 
          blurType="dark" 
          blurAmount={10}
        >
          <View style={[styles.modalContent, theme.shadows.medium]}>
            <FlatList
              data={foodOptions}
              renderItem={({ item }) => (
                <TouchableOpacity 
                  style={[styles.foodItem, { borderBottomColor: theme.colors.background.tertiary.light }]}
                  onPress={() => onFoodSelection(item)}
                >
                  <View>
                    <Text style={[styles.foodName, theme.typography.callout]}>
                      {item.name}
                    </Text>
                    <Text style={[styles.foodCalories, theme.typography.footnote]}>
                      {Math.round(item.calories)} cal
                    </Text>
                  </View>
                  {item.portionInfo && (
                    <Text style={[styles.portionInfo, theme.typography.caption]}>
                      {`${item.portionInfo.type} (${item.portionInfo.grams}g)`}
                    </Text>
                  )}
                </TouchableOpacity>
              )}
              keyExtractor={(item, index) => index.toString()}
              style={styles.foodList}
            />
            <TouchableOpacity 
              style={styles.closeButton}
              onPress={() => setShowModal(false)}
            >
              <Text style={[styles.closeButtonText, theme.typography.button2]}>
                Close
              </Text>
            </TouchableOpacity>
          </View>
        </BlurView>
      </Modal>
    </View>
  );
};

export default CameraScreen;