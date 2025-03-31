import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import { BackHandler, Platform } from 'react-native';
import Purchases from 'react-native-purchases';

// Screens
import MainTabNavigator from './MainTabNavigator';
import CameraScreen from '../screens/CameraScreen';
import LoginScreen from '../screens/LoginScreen';
import OnboardingScreen from '../screens/OnboardingScreen';
import PaywallScreen from '../screens/PaywallScreen';
import ResultsScreen from '../screens/ResultsScreen';
// import SplashScreen from '../screens/SplashScreen';

// Utilities
import { 
  getStoredOnboardingData,
  checkSubscriptionStatus 
} from '../utils/UserDataStorage';

const Stack = createStackNavigator();

const AppNavigator = ({ user, isNewUser }) => {
  const [subscriptionStatus, setSubscriptionStatus] = useState(null);
  const [isOnboarded, setIsOnboarded] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Memoized screen listeners to prevent unnecessary re-creation
  const createScreenListeners = useCallback((screenName) => ({
    focus: () => {
      if (Platform.OS === 'android' && ['Onboarding', 'Paywall', 'Login'].includes(screenName)) {
        const backHandler = BackHandler.addEventListener(
          'hardwareBackPress',
          () => {
            console.log(`Prevented back navigation on ${screenName}`);
            return true;
          }
        );
        return () => backHandler.remove();
      }
    }
  }), []);

  // Optimized initialization with reduced complexity
  useEffect(() => {
    let isMounted = true;
    let purchaseListener = null;

    const initializeNavigationState = async () => {
      try {
        // Concurrent initialization with timeout
        const initPromise = Promise.all([
          checkSubscriptionStatus(),
          getStoredOnboardingData()
        ]);

        // Add a timeout to prevent indefinite loading
        const timeoutPromise = new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Initialization timeout')), 5000)
        );

        const [isSubscribed, onboardingData] = await Promise.race([
          initPromise, 
          timeoutPromise
        ]);

        if (isMounted) {
          setSubscriptionStatus(isSubscribed);
          setIsOnboarded(!!onboardingData);
        }
      } catch (error) {
        console.error('Navigation initialization error:', error);
        
        if (isMounted) {
          setSubscriptionStatus(false);
          setIsOnboarded(false);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    initializeNavigationState();

    // Purchase status listener with improved error handling
    purchaseListener = Purchases.addCustomerInfoUpdateListener(async (info) => {
      try {
        const isSubscribed = await checkSubscriptionStatus();
        if (isMounted) {
          setSubscriptionStatus(isSubscribed);
        }
      } catch (error) {
        console.error('Purchase status update failed:', error);
      }
    });

    // Cleanup function with null check
    return () => {
      isMounted = false;
      
      // Safely remove listener if it exists
      if (purchaseListener && typeof purchaseListener.remove === 'function') {
        purchaseListener.remove();
      }
    };
  }, [user, isNewUser]);

  // Determine initial route with memoization
  const initialRouteName = useMemo(() => {
    if (!user) {
      if (subscriptionStatus) return 'Login';
      return !isOnboarded ? 'Onboarding' : 'Paywall';
    }
    return 'MainTabs';
  }, [user, subscriptionStatus, isOnboarded]);

  // Show loading screen during initialization
  if (isLoading) {
    // return <SplashScreen />;
    return null; // Temporary fallback to prevent blank screen
  }

  return (
    <Stack.Navigator 
      initialRouteName={initialRouteName}
      screenOptions={{
        headerShown: false,
        gestureEnabled: false
      }}
    >
      {!user ? (
        // Not authenticated flow
        subscriptionStatus ? (
          <Stack.Screen
            name="Login"
            component={LoginScreen}
            listeners={createScreenListeners('Login')}
          />
        ) : (
          // Not subscribed flow
          <>
            <Stack.Screen
              name="Onboarding"
              component={OnboardingScreen}
              listeners={createScreenListeners('Onboarding')}
            />
            <Stack.Screen
              name="Paywall"
              component={PaywallScreen}
              listeners={createScreenListeners('Paywall')}
            />
            <Stack.Screen
              name="Login"
              component={LoginScreen}
              listeners={createScreenListeners('Login')}
            />
          </>
        )
      ) : (
        // Authenticated flow
        <>
          <Stack.Screen
            name="MainTabs"
            component={MainTabNavigator}
            listeners={createScreenListeners('MainTabs')}
          />
          <Stack.Screen
            name="Camera"
            component={CameraScreen}
            listeners={createScreenListeners('Camera')}
          />
          <Stack.Screen
            name="Results"
            component={ResultsScreen}
            listeners={createScreenListeners('Results')}
          />
        </>
      )}
    </Stack.Navigator>
  );
};

export default React.memo(AppNavigator);

/* this work exactly correctly but only problem is performance is

import React, { useState, useEffect } from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import { BackHandler, Platform } from 'react-native';
import Purchases from 'react-native-purchases';

import MainTabNavigator from './MainTabNavigator';
import CameraScreen from '../screens/CameraScreen';
import LoginScreen from '../screens/LoginScreen';
import OnboardingScreen from '../screens/OnboardingScreen';
import PaywallScreen from '../screens/PaywallScreen';
import ResultsScreen from '../screens/ResultsScreen';
import { 
  getStoredPurchaseData, 
  getStoredOnboardingData,
  checkSubscriptionStatus 
} from '../utils/UserDataStorage';

const Stack = createStackNavigator();

const AppNavigator = ({ user, isNewUser }) => {
  const [subscriptionStatus, setSubscriptionStatus] = useState(null);
  const [isOnboarded, setIsOnboarded] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const initializeNavigationState = async () => {
      try {
        setIsLoading(true);
        console.log('Initializing navigation state...', { user, isNewUser });

        // Check subscription status
        const isSubscribed = await checkSubscriptionStatus();
        console.log('Subscription check result:', isSubscribed);
        setSubscriptionStatus(isSubscribed);

        // Check if user has completed onboarding
        const onboardingData = await getStoredOnboardingData();
        console.log('Onboarding data check:', { hasData: !!onboardingData });
        setIsOnboarded(!!onboardingData);

      } catch (error) {
        console.error('Error initializing navigation:', error);
        setSubscriptionStatus(false);
        setIsOnboarded(false);
      } finally {
        setIsLoading(false);
      }
    };

    initializeNavigationState();

    // Set up subscription status listener
    const purchaseUpdatedListener = Purchases.addCustomerInfoUpdateListener(async (info) => {
      console.log('Purchase update received:', info);
      const isSubscribed = await checkSubscriptionStatus();
      setSubscriptionStatus(isSubscribed);
    });

    return () => {
      if (purchaseUpdatedListener) {
        purchaseUpdatedListener.remove();
      }
    };
  }, [user, isNewUser]);

  const createScreenListeners = (screenName) => ({
    focus: () => {
      console.log(`Screen focused: ${screenName}`);
      
      if (Platform.OS === 'android' && ['Onboarding', 'Paywall', 'Login'].includes(screenName)) {
        const backHandler = BackHandler.addEventListener(
          'hardwareBackPress',
          () => {
            console.log(`Prevented back navigation on ${screenName}`);
            return true;
          }
        );
        return () => backHandler.remove();
      }
    }
  });

  if (isLoading) {
    console.log('Navigation still loading...');
    return null;
  }

  // Determine initial route based on user state
  let initialRouteName = 'Onboarding';
  if (user) {
    initialRouteName = 'MainTabs';
  } else if (subscriptionStatus) {
    initialRouteName = 'Login';
  } else if (!isOnboarded) {
    initialRouteName = 'Onboarding';
  }

  console.log('Rendering navigation with states:', {
    user,
    subscriptionStatus,
    isOnboarded,
    initialRouteName
  });

  return (
    <Stack.Navigator 
      initialRouteName={initialRouteName}
      screenOptions={{
        headerShown: false,
        gestureEnabled: false
      }}
    >
      {!user ? (
        // Not authenticated flow
        subscriptionStatus ? (
          // Subscribed but not logged in
          <Stack.Screen
            name="Login"
            component={LoginScreen}
            listeners={createScreenListeners('Login')}
          />
        ) : (
          // Not subscribed flow
          <>
            <Stack.Screen
              name="Onboarding"
              component={OnboardingScreen}
              listeners={createScreenListeners('Onboarding')}
            />
            <Stack.Screen
              name="Paywall"
              component={PaywallScreen}
              listeners={createScreenListeners('Paywall')}
            />
            <Stack.Screen
              name="Login"
              component={LoginScreen}
              listeners={createScreenListeners('Login')}
            />
          </>
        )
      ) : (
        // Authenticated flow
        <>
          <Stack.Screen
            name="MainTabs"
            component={MainTabNavigator}
            listeners={createScreenListeners('MainTabs')}
          />
          <Stack.Screen
            name="Camera"
            component={CameraScreen}
            listeners={createScreenListeners('Camera')}
          />
          <Stack.Screen
            name="Results"
            component={ResultsScreen}
            listeners={createScreenListeners('Results')}
          />
        </>
      )}
    </Stack.Navigator>
  );
};

export default AppNavigator;
*/














/*
this was getting the onboardingscreen to rerender

import React, { useState, useEffect } from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import { BackHandler, Platform, Alert } from 'react-native';
import Purchases from 'react-native-purchases';

import MainTabNavigator from './MainTabNavigator';
import CameraScreen from '../screens/CameraScreen';
import LoginScreen from '../screens/LoginScreen';
import OnboardingScreen from '../screens/OnboardingScreen';
import PaywallScreen from '../screens/PaywallScreen';
import ResultsScreen from '../screens/ResultsScreen';
import { getStoredPurchaseData } from '../utils/UserDataStorage';

const Stack = createStackNavigator();

const AppNavigator = ({ user, isSubscribed }) => {
  const [subscriptionStatus, setSubscriptionStatus] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const checkSubscription = async () => {
      try {
        setIsLoading(true);
        console.log('Checking subscription status...');

        // Check stored purchase data first
        const storedPurchase = await getStoredPurchaseData();
        const storedActive = storedPurchase && storedPurchase.subscriptionStatus === 'active';
        console.log('Stored purchase data:', 
          { active: storedActive, data: storedPurchase });

        // If we have a valid stored subscription, use that
        if (storedActive) {
          console.log('Using stored subscription status:', { isActive: true });
          setSubscriptionStatus(true);
          setIsLoading(false);
          return;
        }

        // Only check RevenueCat if no valid stored subscription
        try {
          const customerInfo = await Purchases.getCustomerInfo();
          const revenueCatActive = customerInfo?.entitlements?.active?.Pro;
          console.log('RevenueCat subscription status:', 
            { active: revenueCatActive, customerInfo: customerInfo });

          setSubscriptionStatus(revenueCatActive || false);
        } catch (rcError) {
          console.error('RevenueCat error:', rcError);
          // If RevenueCat fails but we have stored data, use stored status
          setSubscriptionStatus(storedActive || false);
        }

      } catch (error) {
        console.error('Error checking subscription status:', error);
        // If all checks fail, default to stored status or false
        const storedPurchase = await getStoredPurchaseData();
        const storedActive = storedPurchase && storedPurchase.subscriptionStatus === 'active';
        setSubscriptionStatus(storedActive || false);
      } finally {
        setIsLoading(false);
      }
    };

    // Set up subscription status listener
    let purchaseUpdatedListener;
    try {
      purchaseUpdatedListener = Purchases.addCustomerInfoUpdateListener(async (info) => {
        console.log('Purchase update received:', info);
        checkSubscription();
      });
    } catch (error) {
      console.error('Error setting up RevenueCat listener:', error);
    }

    // Initial check
    checkSubscription();

    // Cleanup listener
    return () => {
      if (purchaseUpdatedListener) {
        purchaseUpdatedListener.remove();
      }
    };
  }, []);

  useEffect(() => {
    console.log('App state updated:', {
      user: user ? 'Logged in' : 'Not logged in',
      subscriptionStatus: subscriptionStatus ? 'Active' : 'Inactive',
      isLoading
    });
  }, [user, subscriptionStatus, isLoading]);

  const createScreenListeners = (screenName) => ({
    focus: () => {
      console.log(`Screen focused: ${screenName}`);
      
      if (Platform.OS === 'android' && ['Onboarding', 'Paywall', 'Login'].includes(screenName)) {
        const backHandler = BackHandler.addEventListener(
          'hardwareBackPress',
          () => {
            console.log(`Prevented back navigation on ${screenName}`);
            return true;
          }
        );
        return () => {
          console.log(`Removing back handler for ${screenName}`);
          backHandler.remove();
        };
      }
    },
    blur: () => {
      console.log(`Screen blurred: ${screenName}`);
    },
    state: (e) => {
      console.log(`Navigation state updated for ${screenName}:`, e.data);
    },
    beforeRemove: (e) => {
      console.log(`Screen about to be removed: ${screenName}`);
    }
  });

  if (isLoading || subscriptionStatus === null) {
    console.log('AppNavigator still loading...');
    return null;
  }

  return (
    <Stack.Navigator 
      screenOptions={{
        headerShown: false,
        gestureEnabled: false
      }}
    >
      {!user ? (
        !subscriptionStatus ? (
          <>
            <Stack.Screen
              name="Onboarding"
              component={OnboardingScreen}
              listeners={createScreenListeners('Onboarding')}
            />
            <Stack.Screen
              name="Paywall"
              component={PaywallScreen}
              listeners={createScreenListeners('Paywall')}
            />
            <Stack.Screen
              name="Login"
              component={LoginScreen}
              listeners={createScreenListeners('Login')}
            />
          </>
        ) : (
          <Stack.Screen
            name="Login"
            component={LoginScreen}
            listeners={createScreenListeners('Login')}
          />
        )
      ) : (
        <>
          <Stack.Screen
            name="MainTabs"
            component={MainTabNavigator}
            listeners={createScreenListeners('MainTabs')}
          />
          <Stack.Screen
            name="Camera"
            component={CameraScreen}
            listeners={createScreenListeners('Camera')}
          />
          <Stack.Screen
            name="Results"
            component={ResultsScreen}
            listeners={createScreenListeners('Results')}
          />
        </>
      )}
    </Stack.Navigator>
  );
};

export default AppNavigator;
*/


// import React from 'react';
// import { createStackNavigator } from '@react-navigation/stack';
// import MainTabNavigator from './MainTabNavigator'; // Main app tabs
// import CameraScreen from '../screens/CameraScreen';
// import LoginScreen from '../screens/LoginScreen';
// import OnboardingScreen from '../screens/OnboardingScreen';
// import PaywallScreen from '../screens/PaywallScreen';
// import ResultsScreen from '../screens/ResultsScreen';

// const Stack = createStackNavigator();

// const AppNavigator = ({ user, isSubscribed }) => {
//   console.log(
//     'AppNavigator rendering. User:',
//     user ? 'Logged in' : 'Not logged in',
//     'isSubscribed:',
//     isSubscribed ? 'Subscribed' : 'Not subscribed'
//   );

//   return (
//     <Stack.Navigator screenOptions={{ headerShown: false }}>
//       {/* If user is not logged in, show onboarding, paywall, and login flow */}
//       {!user ? (
//         <>
//           <Stack.Screen
//             name="Onboarding"
//             component={OnboardingScreen}
//             listeners={{
//               focus: () => console.log('Onboarding screen focused'),
//               blur: () => console.log('Onboarding screen blurred'),
//             }}
//           />
//           <Stack.Screen
//             name="Paywall"
//             component={PaywallScreen}
//             options={{
//               gestureEnabled: false, // Prevent back navigation from Paywall
//             }}
//             listeners={{
//               focus: () => console.log('Paywall screen focused'),
//               blur: () => console.log('Paywall screen blurred'),
//             }}
//           />
//           <Stack.Screen
//             name="Login"
//             component={LoginScreen}
//             listeners={{
//               focus: () => console.log('Login screen focused'),
//               blur: () => console.log('Login screen blurred'),
//             }}
//           />
//         </>
//       ) : isSubscribed ? (
//         // Main app flow for logged-in and subscribed users
//         <>
//           <Stack.Screen
//             name="MainTabs"
//             component={MainTabNavigator}
//             listeners={{
//               focus: () => console.log('Main app focused'),
//               blur: () => console.log('Main app blurred'),
//             }}
//           />
//           <Stack.Screen
//             name="Results"
//             component={ResultsScreen}
//             listeners={{
//               focus: () => console.log('Results screen focused'),
//               blur: () => console.log('Results screen blurred'),
//             }}
//           />
//           <Stack.Screen
//             name="Camera"
//             component={CameraScreen}
//             listeners={{
//               focus: () => console.log('Camera screen focused'),
//               blur: () => console.log('Camera screen blurred'),
//             }}
//           />
//         </>
//       ) : (
//         // Flow for logged-in but unsubscribed users: Onboarding -> Paywall
//         <>
//           <Stack.Screen
//             name="Onboarding"
//             component={OnboardingScreen}
//             listeners={{
//               focus: () => console.log('Onboarding for unsubscribed users focused'),
//               blur: () => console.log('Onboarding for unsubscribed users blurred'),
//             }}
//           />
//           <Stack.Screen
//             name="Paywall"
//             component={PaywallScreen}
//             options={{
//               gestureEnabled: false,
//             }}
//             listeners={{
//               focus: () => console.log('Paywall for unsubscribed users focused'),
//               blur: () => console.log('Paywall for unsubscribed users blurred'),
//             }}
//           />
//         </>
//       )}
//     </Stack.Navigator>
//   );
// };

// export default AppNavigator;










/*
import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import { View, Text } from 'react-native';
import { GestureHandlerRootView } from 'react-native-gesture-handler';

import MainTabNavigator from './MainTabNavigator'; // Import MainTabNavigator
import CameraScreen from '../screens/CameraScreen';
import LoginScreen from '../screens/LoginScreen';
import OnboardingScreen from '../screens/OnboardingScreen';
import HomeScreen from '../screens/HomeScreen';
import AnalyticsScreen from '../screens/AnalyticsScreen';
import ErrorBoundary from '../Components/ErrorBoundary';
import SettingsScreen from '../screens/SettingsScreen';
import ProfileScreen from '../screens/ProfileScreen';
import ResultsScreen from '../screens/ResultsScreen';
import PhotoPreviewScreen from '../screens/PhotoPreviewScreen';
import HistoryScreen from '../screens/HistoryScreen';
import PaywallScreen from '../screens/PaywallScreen';
const Stack = createStackNavigator();

// Create a separate stack for the main app flow
const MainStack = () => (
  <Stack.Navigator screenOptions={{ headerShown: false }}>
    <Stack.Screen 
      name="MainTabs" 
      component={MainTabNavigator}
      listeners={{
        focus: () => console.log('Main tabs focused'),
        blur: () => console.log('Main tabs blurred'),
      }}
    />
    <Stack.Screen 
      name="Results" 
      component={ResultsScreen}
      listeners={{
        focus: () => console.log('Results screen focused'),
        blur: () => console.log('Results screen blurred'),
      }}
    />
    <Stack.Screen 
      name="Camera" 
      component={CameraScreen}
    />
    <Stack.Screen 
      name="PhotoPreview" 
      component={PhotoPreviewScreen}
    />
    <Stack.Screen 
      name="History" 
      component={HistoryScreen}
    />
    <Stack.Screen 
      name="Paywall" 
      component={PaywallScreen}
    />
  </Stack.Navigator>
);

const AppNavigator = ({ user, isNewUser }) => {
  console.log('AppNavigator rendering. User:', user ? 'Logged in' : 'Not logged in', 'isNewUser:', isNewUser);
  
  return (
    // <ErrorBoundary>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        {user ? (
          isNewUser ? (
            <Stack.Screen 
              name="Onboarding" 
              component={OnboardingScreen} 
              listeners={{
                focus: () => console.log('Onboarding screen focused'),
                blur: () => console.log('Onboarding screen blurred'),
              }}
            />
          ) : (
            <>
            <Stack.Screen 
              name="MainTabNavigator" 
              component={OnboardingScreen}
              listeners={{
                focus: () => console.log('Main app focused'),
                blur: () => console.log('Main app blurred'),
              }}
            />
            <Stack.Screen
              name="Results"
              component={ResultsScreen}
              listeners={{
                focus: () => console.log('Results screen focused'),
                blur: () => console.log('Results screen blurred'),
              }}
            />
           </>
          )
        ) : (
          <Stack.Screen 
            name="Login" 
            component={LoginScreen}
            listeners={{
              focus: () => console.log('Login screen focused'),
              blur: () => console.log('Login screen blurred'),
            }}
          />
        )}
      </Stack.Navigator>
    // </ErrorBoundary>
  );
};

export default AppNavigator;

*/