// import React, { useRef, useState } from 'react';
// import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
// import { TouchableOpacity, View, StyleSheet, Platform, Image } from 'react-native';
// import { BlurView } from '@react-native-community/blur';
// import LottieView from 'lottie-react-native';
// import { useNavigation } from '@react-navigation/native';

// // Import your screen components here
// import HomeScreen from '../screens/HomeScreen';
// import AnalyticsScreen from '../screens/AnalyticsScreen';
// import ProfileScreen from '../screens/ProfileScreen';
// import AddScreen from '../screens/CameraScreen';

// const Tab = createBottomTabNavigator();

// const logError = (error, errorInfo) => {
//   console.error('Error:', error);
//   console.error('Error Info:', errorInfo);
// };

// const TabIcon = ({ source, size, onPress, routeName }) => {
//   return (
//     <TouchableOpacity onPress={() => onPress(routeName)}>
//       <Image
//         source={source}
//         style={{ width: size, height: size }}
//         resizeMode="contain"
//       />
//     </TouchableOpacity>
//   );
// };

// const AnimatedTabIcon = ({ source, activeSource, size, onPress, isActive, routeName }) => {
//   const animationRef = useRef(null);

//   const handlePress = () => {
//     try {
//       if (animationRef.current) {
//         animationRef.current.play();
//       }
//       onPress(routeName);
//     } catch (error) {
//       console.error('Error in AnimatedTabIcon handlePress:', error);
//     }
//   };

//   return (
//     <TouchableOpacity onPress={handlePress}>
//       <View style={{ width: size, height: size }}>
//         <LottieView
//           ref={animationRef}
//           source={isActive ? activeSource : source}
//           autoPlay={false}
//           loop={false}
//           style={{ width: '100%', height: '100%' }}
//         />
//       </View>
//     </TouchableOpacity>
//   );
// };

// const MainTabNavigator = () => {
//   const [activeTab, setActiveTab] = useState('Home');
//   const navigation = useNavigation();

//   const handleTabPress = (routeName) => {
//     try {
//       setActiveTab(routeName);
//       navigation.navigate(routeName);
//     } catch (error) {
//       logError(error, { component: 'MainTabNavigator', method: 'handleTabPress' });
//     }
//   };

//   return (
//     <Tab.Navigator
//       screenOptions={({ route }) => ({
//         headerShown: false,
//         tabBarIcon: ({ focused, color, size }) => {
//           if (route.name === 'Add') {
//             return (
//               <AnimatedTabIcon
//                 source={require('../../assets/icons/add-icon.json')}
//                 activeSource={require('../../assets/icons/add-icon.json')}
//                 size={size * 4.5}
//                 onPress={handleTabPress}
//                 isActive={activeTab === route.name}
//                 routeName={route.name}
//               />
//             );
//           }

//           let iconSource;
//           try {
//             if (route.name === 'Home') {
//               iconSource = focused
//                 ? require('../../assets/icons/home-bold.png')
//                 : require('../../assets/icons/home.png');
//             } else if (route.name === 'Analytics') {
//               iconSource = focused
//                 ? require('../../assets/icons/analytics-bold.png')
//                 : require('../../assets/icons/analytics.png');
//             } else if (route.name === 'Profile') {
//               iconSource = focused
//                 ? require('../../assets/icons/profile-bold.png')
//                 : require('../../assets/icons/profile.png');
//             }
//           } catch (error) {
//             logError(error, { component: 'MainTabNavigator', method: 'screenOptions' });
//             iconSource = require('../../assets/icons/home.png');
//           }

//           return (
//             <TabIcon
//               source={iconSource}
//               size={size * 0.8}
//               onPress={handleTabPress}
//               routeName={route.name}
//               style={focused ? styles.focusedIcon : styles.defaultIcon}
//             />
//           );
//         },
//         tabBarBackground: () => (
//           <BlurView
//             style={StyleSheet.absoluteFill}
//             blurType=""
//             blurAmount={20}
//           />
//         ),
//         tabBarStyle: {
//           display: route.name === 'Add' ? 'none' : 'flex',
//           borderTopWidth: 0,
//           backgroundColor: 'rgba(255, 255, 255, 0.8)',
//           height: 80,
//           paddingBottom: Platform.OS === 'ios' ? 20 : 0,
//         },
//         tabBarActiveTintColor: '#000000',
//         tabBarInactiveTintColor: '#8E8E93',
//         tabBarLabelStyle: {
//           fontWeight: '850',
//         },
//       })}
//     >
//       <Tab.Screen name="Home" component={HomeScreen} />
//       <Tab.Screen name="Analytics" component={AnalyticsScreen} />
//       <Tab.Screen name="Profile" component={ProfileScreen} />
//       <Tab.Screen
//         name="Add"
//         component={AddScreen}
//         options={{
//           tabBarStyle: { display: 'none' },
//           tabBarIcon: ({ size }) => (
//             <View style={styles.addButtonContainer}>
//               <AnimatedTabIcon
//                 source={require('../../assets/icons/add-icon.json')}
//                 activeSource={require('../../assets/icons/add-icon.json')}
//                 size={size * 4.5}
//                 onPress={handleTabPress}
//                 isActive={activeTab === 'Add'}
//                 routeName="Add"
//               />
//             </View>
//           ),
//           tabBarLabel: () => null,
//         }}
//       />
//     </Tab.Navigator>
//   );
// };

// const styles = StyleSheet.create({
//   addButtonContainer: {
//     position: 'absolute',
//     top: -30,
//     alignSelf: 'center',
//     justifyContent: 'center',
//     alignItems: 'center',
//     backgroundColor: 'white',
//     borderRadius: 35,
//     height: 70,
//     width: 70,
//     shadowColor: "#000",
//     shadowOffset: {
//       width: 0,
//       height: 2,
//     },
//     shadowOpacity: 0.25,
//     shadowRadius: 3.84,
//     elevation: 5,
//   },
//   defaultIcon: {
//     color: '#8E8E93',
//     shadowColor: 'transparent',
//     transform: [{ scale: 1 }],
//   },
//   focusedIcon: {
//     color: '#007AFF',
//     shadowColor: '#007AFF',
//     shadowOffset: { width: 0, height: 2 },
//     shadowOpacity: 0.5,
//     shadowRadius: 3,
//     transform: [{ scale: 1.1 }],
//   },
// });

// export default MainTabNavigator;







import React, { useRef, useState } from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { TouchableOpacity, View, StyleSheet, Platform, Image } from 'react-native';
import { BlurView } from '@react-native-community/blur';
import LottieView from 'lottie-react-native';
import { useNavigation } from '@react-navigation/native';

// Import your screen components here
import HomeScreen from '../screens/HomeScreen';
import AnalyticsScreen from '../screens/AnalyticsScreen';
import ProfileScreen from '../screens/ProfileScreen';
import AddScreen from '../screens/CameraScreen';

const Tab = createBottomTabNavigator();

const logError = (error, errorInfo) => {
  console.error('Error:', error);
  console.error('Error Info:', errorInfo);
};

const TabIcon = ({ source, size, onPress, routeName }) => {
  return (
    <TouchableOpacity onPress={() => onPress(routeName)}>
      <Image
        source={source}
        style={{ width: size, height: size }}
        resizeMode="contain"
      />
    </TouchableOpacity>
  );
};

const AnimatedTabIcon = ({ source, activeSource, size, onPress, isActive, routeName }) => {
  const animationRef = useRef(null);

  const handlePress = () => {
    try {
      if (animationRef.current) {
        animationRef.current.play();
      }
      onPress(routeName);
    } catch (error) {
      console.error('Error in AnimatedTabIcon handlePress:', error);
    }
  };

  return (
    <TouchableOpacity onPress={handlePress}>
      <View style={{ width: size, height: size }}>
        <LottieView
          ref={animationRef}
          source={isActive ? activeSource : source}
          autoPlay={false}
          loop={false}
          style={{ width: '100%', height: '100%' }}
        />
      </View>
    </TouchableOpacity>
  );
};

const MainTabNavigator = () => {
  const [activeTab, setActiveTab] = useState('Home');
  const navigation = useNavigation();

  const handleTabPress = (routeName) => {
    try {
      setActiveTab(routeName);
      navigation.navigate(routeName);
    } catch (error) {
      logError(error, { component: 'MainTabNavigator', method: 'handleTabPress' });
    }
  };

  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarIcon: ({ focused, color, size }) => {
          if (route.name === 'Add') {
            return (
              <AnimatedTabIcon
                source={require('../../assets/icons/add-icon.json')}
                activeSource={require('../../assets/icons/add-icon.json')}
                size={size * 4.5}
                onPress={handleTabPress}
                isActive={activeTab === route.name}
                routeName={route.name}
              />
            );
          }

          let iconSource;
          try {
            if (route.name === 'Home') {
              iconSource = focused
                ? require('../../assets/icons/home-bold.png')
                : require('../../assets/icons/home.png');
            } else if (route.name === 'Analytics') {
              iconSource = focused
                ? require('../../assets/icons/analytics-bold.png')
                : require('../../assets/icons/analytics.png');
            } else if (route.name === 'Profile') {
              iconSource = focused
                ? require('../../assets/icons/profile-bold.png')
                : require('../../assets/icons/profile.png');
            }
          } catch (error) {
            logError(error, { component: 'MainTabNavigator', method: 'screenOptions' });
            iconSource = require('../../assets/icons/home.png');
          }

          return (
            <TabIcon
              source={iconSource}
              size={size * 0.8}
              onPress={handleTabPress}
              routeName={route.name}
              style={focused ? styles.focusedIcon : styles.defaultIcon}
            />
          );
        },
        tabBarBackground: () => (
          <View style={styles.tabBarBackground}>
            <BlurView
              style={StyleSheet.absoluteFill}
              blurType={Platform.OS === 'ios' ? 'light' : 'light'}
              blurAmount={100}
              opacity={100}
              reducedTransparencyFallbackColor="white"
            />
          </View>
        ),
        tabBarStyle: {
          position: 'absolute',
          display: route.name === 'Add' ? 'none' : 'flex',
          borderTopWidth: 0,
          height: 80,
          paddingBottom: Platform.OS === 'ios' ? 20 : 0,
          backgroundColor: 'transparent',
          elevation: 0,
          borderTopColor: 'transparent',
        },
        tabBarActiveTintColor: '#000000',
        tabBarInactiveTintColor: '#8E8E93',
        tabBarLabelStyle: {
          fontWeight: '850',
        },
      })}
    >
      <Tab.Screen name="Home" component={HomeScreen} />
      <Tab.Screen name="Analytics" component={AnalyticsScreen} />
      <Tab.Screen name="Profile" component={ProfileScreen} />
      <Tab.Screen
        name="Add"
        component={AddScreen}
        options={{
          tabBarStyle: { display: 'none' },
          tabBarIcon: ({ size }) => (
            <View style={styles.addButtonContainer}>
              <AnimatedTabIcon
                source={require('../../assets/icons/add-icon.json')}
                activeSource={require('../../assets/icons/add-icon.json')}
                size={size * 4.5}
                onPress={handleTabPress}
                isActive={activeTab === 'Add'}
                routeName="Add"
              />
            </View>
          ),
          tabBarLabel: () => null,
        }}
      />
    </Tab.Navigator>
  );
};

const styles = StyleSheet.create({
  tabBarBackground: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(236, 236, 236, 0.7)',
    // borderTopLeftRadius: 20,
    // borderTopRightRadius: 20,
    overflow: 'hidden',
    // backgroundColor: '#EEEEEE',
  },
  addButtonContainer: {
    position: 'absolute',
    top: -30,
    alignSelf: 'center',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'white',
    borderRadius: 35,
    height: 70,
    width: 70,
    shadowColor: "#000",
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  defaultIcon: {
    color: '#8E8E93',
    shadowColor: 'transparent',
    transform: [{ scale: 1 }],
  },
  focusedIcon: {
    color: '#007AFF',
    shadowColor: '#007AFF',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.5,
    shadowRadius: 3,
    transform: [{ scale: 1.1 }],
  },
});

export default MainTabNavigator;


















// import React, { useRef, useState } from 'react';
// import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
// import { TouchableOpacity, View, StyleSheet, Platform } from 'react-native';
// import { BlurView } from '@react-native-community/blur';
// import LottieView from 'lottie-react-native';
// import { useNavigation } from '@react-navigation/native';
// import { SFSymbol } from 'react-native-sfsymbols';
// import theme from '../styles/theme';

// // Import your screen components here
// import HomeScreen from '../screens/HomeScreen';
// import AnalyticsScreen from '../screens/AnalyticsScreen';
// import ProfileScreen from '../screens/ProfileScreen';
// import AddScreen from '../screens/CameraScreen';

// const Tab = createBottomTabNavigator();

// const logError = (error, errorInfo) => {
//   console.error('Error:', error);
//   console.error('Error Info:', errorInfo);
// };

// const AnimatedTabIcon = ({ source, activeSource, size, onPress, isActive, routeName }) => {
//   const animationRef = useRef(null);

//   const handlePress = () => {
//     try {
//       if (animationRef.current) {
//         animationRef.current.play();
//       }
//       onPress(routeName);
//     } catch (error) {
//       console.error('Error in AnimatedTabIcon handlePress:', error);
//     }
//   };

//   return (
//     <TouchableOpacity onPress={handlePress}>
//       <View style={{ width: size, height: size }}>
//         <LottieView
//           ref={animationRef}
//           source={isActive ? activeSource : source}
//           autoPlay={false}
//           loop={false}
//           style={{ width: '100%', height: '100%' }}
//         />
//       </View>
//     </TouchableOpacity>
//   );
// };

// const MainTabNavigator = () => {
//   const [activeTab, setActiveTab] = useState('Home');
//   const navigation = useNavigation();

//   const handleTabPress = (routeName) => {
//     try {
//       setActiveTab(routeName);
//       navigation.navigate(routeName);
//     } catch (error) {
//       logError(error, { component: 'MainTabNavigator', method: 'handleTabPress' });
//     }
//   };

//   return (
//     <Tab.Navigator
//       screenOptions={({ route }) => ({
//         headerShown: false,
//         tabBarIcon: ({ focused, color, size }) => {
//           let iconSource;
//           let activeIconSource;

//           try {
//             if (route.name === 'Home') {
//               iconSource = require('../../assets/icons/home.png');
//               activeIconSource = require('../../assets/icons/home-bold.png');
//             } else if (route.name === 'Analytics') {
//               iconSource = require('../../assets/icons/home.png');
//               activeIconSource = require('../../assets/icons/home-bold.png');
//             } else if (route.name === 'Profile') {
//               iconSource = require('../../assets/icons/home.png');
//               activeIconSource = require('../../assets/icons/home-bold.png');
//             } else if (route.name === 'Add') {
//               iconSource = require('../../assets/icons/add-icon.json');
//               activeIconSource = iconSource; // Same icon for Add screen
//             }

//             if (route.name === 'Add') {
//               return (
//                 <AnimatedTabIcon
//                   source={require('../../assets/icons/add-icon.json')}
//                   activeSource={require('../../assets/icons/add-icon.json')}
//                   size={size * 4.5} // Keeping original multiplier as it matches your needs
//                   onPress={handleTabPress}
//                   isActive={activeTab === 'Add'}
//                   routeName="Add"
//                 />
//               );
//             }

//             return (
//               <SFSymbol 
//                 name={symbolName} 
//                 size={size * 1.0} // Keeping original multiplier
//                 color={focused ? theme.colors.primary.dark : theme.colors.text.secondary.light}
//                 style={focused ? styles.focusedIcon : styles.defaultIcon}
//                 weight="light" // Options: 'ultralight', 'thin', 'light', 'regular', 'medium', 'semibold', 'bold', 'heavy', 'black'
//               />
//             );
//           } catch (error) {
//             logError(error, { component: 'MainTabNavigator', method: 'screenOptions' });
//             return null;
//           }
//         },
//         tabBarBackground: () => (
//           <BlurView
//             style={StyleSheet.absoluteFill}
//             blurType="light"
//             blurAmount={900}
//           />
//         ),
//         tabBarStyle: {
//           display: route.name === 'Add' ? 'none' : 'flex',
//           borderTopWidth: 0,
//           backgroundColor: theme.colors.background.frostedGlass,
//           height: theme.layout.buttonHeight + (Platform.OS === 'ios' ? theme.spacing.xl : 0), // 80px equivalent
//           paddingBottom: Platform.OS === 'ios' ? theme.spacing.xl : 0, // 20px equivalent
//         },
//         tabBarActiveTintColor: theme.colors.primary.dark,
//         tabBarInactiveTintColor: theme.colors.text.secondary.light,
//         tabBarLabelStyle: {
//           fontSize: theme.typography.button2.fontSize * 0.7, // Reduce label size

//         },
//       })}
//     >
//       <Tab.Screen name="Home" component={HomeScreen} />
//       <Tab.Screen name="Analytics" component={AnalyticsScreen} />
//       <Tab.Screen name="Profile" component={ProfileScreen} />
//       <Tab.Screen
//         name="Add"
//         component={AddScreen}
//         options={{
//           tabBarStyle: { display: 'none' },
//           tabBarIcon: ({ size }) => (
//             <View style={styles.addButtonContainer}>
//               <AnimatedTabIcon
//                 source={require('../../assets/icons/add-icon.json')}
//                 activeSource={require('../../assets/icons/add-icon.json')}
//                 size={size * 4.6}
//                 onPress={handleTabPress}
//                 isActive={activeTab === 'Add'}
//                 routeName="Add"
//               />
//             </View>
//           ),
//           tabBarLabel: () => null,
//         }}
//       />
//     </Tab.Navigator>
//   );
// };

// const styles = StyleSheet.create({
//   addButtonContainer: {
//     position: 'absolute',
//     top: -theme.spacing.m, // -30px equivalent
//     alignSelf: 'center',
//     justifyContent: 'center',
//     alignItems: 'center',
//     backgroundColor: theme.colors.background.secondary.light,
//     borderRadius: theme.layout.borderRadius.xxl + theme.layout.borderRadius.xxl, // 35px equivalent
//     // height: theme.layout.camera.controlButtonSize + theme.spacing.xxxl, // 70px equivalent
//     // width: theme.layout.camera.controlButtonSize + theme.spacing.xxxl, // 70px equivalent
//     // ...theme.shadows.medium,
//     borderRadius: theme.layout.camera.controlButtonSize / 2, // Match half of the width/height for a perfect circle
//     height: theme.layout.camera.controlButtonSize, // Match the size of the AnimatedTabIcon
//     width: theme.layout.camera.controlButtonSize, // Match the size of the AnimatedTabIcon
//   },
//   defaultIcon: {
//     color: theme.colors.text.secondary.light,
//     shadowColor: 'transparent',
//     transform: [{ scale: 1 }],
//   },
//   focusedIcon: {
//     color: theme.colors.primary.dark,
//     shadowColor: theme.colors.primary.dark,
//     shadowOffset: theme.shadows.small.shadowOffset,
//     shadowOpacity: theme.shadows.small.shadowOpacity,
//     shadowRadius: theme.shadows.small.shadowRadius,
//     transform: [{ scale: 1.1 }],
//   },
// });

// export default MainTabNavigator;




// import React, { useRef, useState } from 'react';
// import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
// import { TouchableOpacity, View, StyleSheet, Platform } from 'react-native';
// import { BlurView } from '@react-native-community/blur';
// import LottieView from 'lottie-react-native';
// import { useNavigation } from '@react-navigation/native';
// import { SFSymbol } from 'react-native-sfsymbols';

// // Import your screen components here
// import HomeScreen from '../screens/HomeScreen';
// import AnalyticsScreen from '../screens/AnalyticsScreen';
// import ProfileScreen from '../screens/ProfileScreen';
// import AddScreen from '../screens/CameraScreen';

// const Tab = createBottomTabNavigator();

// const logError = (error, errorInfo) => {
//   console.error('Error:', error);
//   console.error('Error Info:', errorInfo);
// };

// // Only used for Add button now
// const AnimatedTabIcon = ({ source, activeSource, size, onPress, isActive, routeName }) => {
//   const animationRef = useRef(null);

//   const handlePress = () => {
//     try {
//       if (animationRef.current) {
//         animationRef.current.play();
//       }
//       onPress(routeName);
//     } catch (error) {
//       console.error('Error in AnimatedTabIcon handlePress:', error);
//     }
//   };

//   return (
//     <TouchableOpacity onPress={handlePress}>
//       <View style={{ width: size, height: size }}>
//         <LottieView
//           ref={animationRef}
//           source={isActive ? activeSource : source}
//           autoPlay={false}
//           loop={false}
//           style={{ width: '100%', height: '100%' }}
//         />
//       </View>
//     </TouchableOpacity>
//   );
// };

// const MainTabNavigator = () => {
//   const [activeTab, setActiveTab] = useState('Home');
//   const navigation = useNavigation();

//   const handleTabPress = (routeName) => {
//     try {
//       setActiveTab(routeName);
//       navigation.navigate(routeName);
//     } catch (error) {
//       logError(error, { component: 'MainTabNavigator', method: 'handleTabPress' });
//     }
//   };

//   return (
//     <Tab.Navigator
//       screenOptions={({ route }) => ({
//         headerShown: false,
//         tabBarIcon: ({ focused, color, size }) => {
//           try {
//             if (route.name === 'Add') {
//               return (
//                 <AnimatedTabIcon
//                   source={require('../../assets/icons/add-icon.json')}
//                   activeSource={require('../../assets/icons/add-icon.json')}
//                   size={size * 4.5}
//                   onPress={handleTabPress}
//                   isActive={activeTab === 'Add'}
//                   routeName="Add"
//                 />
//               );
//             }

//             // SF Symbols configuration for other tabs
//             let symbolName;
//             if (route.name === 'Home') {
//               symbolName = focused ? 'house.fill' : 'house';
//             } else if (route.name === 'Analytics') {
//               symbolName = focused ? 'chart.bar.fill' : 'chart.bar';
//             } else if (route.name === 'Profile') {
//               symbolName = focused ? 'person.fill' : 'person';
//             }

//             return (
//               <SFSymbol 
//                 name={symbolName} 
//                 size={size * 1.2}
//                 color={focused ? '#007AFF' : '#8E8E93'}
//                 style={focused ? styles.focusedIcon : styles.defaultIcon}
//               />
//             );
//           } catch (error) {
//             logError(error, { component: 'MainTabNavigator', method: 'screenOptions' });
//             return null;
//           }
//         },
//         tabBarBackground: () => (
//           <BlurView
//             style={StyleSheet.absoluteFill}
//             blurType="light"
//             blurAmount={900}
//           />
//         ),
//         tabBarStyle: {
//           display: route.name === 'Add' ? 'none' : 'flex',
//           borderTopWidth: 0,
//           backgroundColor: 'rgba(255, 255, 255, 0.8)',
//           height: 80,
//           paddingBottom: Platform.OS === 'ios' ? 20 : 0,
//         },
//         tabBarActiveTintColor: '#007AFF',
//         tabBarInactiveTintColor: '#8E8E93',
//         tabBarLabelStyle: {
//           fontWeight: '850',
//         },
//       })}
//     >
//       <Tab.Screen name="Home" component={HomeScreen} />
//       <Tab.Screen name="Analytics" component={AnalyticsScreen} />
//       <Tab.Screen name="Profile" component={ProfileScreen} />
//       <Tab.Screen
//         name="Add"
//         component={AddScreen}
//         options={{
//           tabBarStyle: { display: 'none' },
//           tabBarIcon: ({ size }) => (
//             <View style={styles.addButtonContainer}>
//               <AnimatedTabIcon
//                 source={require('../../assets/icons/add-icon.json')}
//                 activeSource={require('../../assets/icons/add-icon.json')}
//                 size={size * 4.5}
//                 onPress={handleTabPress}
//                 isActive={activeTab === 'Add'}
//                 routeName="Add"
//               />
//             </View>
//           ),
//           tabBarLabel: () => null,
//         }}
//       />
//     </Tab.Navigator>
//   );
// };

// const styles = StyleSheet.create({
//   addButtonContainer: {
//     position: 'absolute',
//     top: -30,
//     alignSelf: 'center',
//     justifyContent: 'center',
//     alignItems: 'center',
//     backgroundColor: 'white',
//     borderRadius: 35,
//     height: 70,
//     width: 70,
//     shadowColor: "#000",
//     shadowOffset: {
//       width: 0,
//       height: 2,
//     },
//     shadowOpacity: 0.25,
//     shadowRadius: 3.84,
//     elevation: 5,
//   },
//   defaultIcon: {
//     color: '#8E8E93',
//     shadowColor: 'transparent',
//     transform: [{ scale: 1 }],
//   },
//   focusedIcon: {
//     color: '#007AFF',
//     shadowColor: '#007AFF',
//     shadowOffset: { width: 0, height: 2 },
//     shadowOpacity: 0.5,
//     shadowRadius: 3,
//     transform: [{ scale: 1.1 }],
//   },
// });

// export default MainTabNavigator;







// import React, { useRef, useState,useEffect } from 'react';
// import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
// import { TouchableOpacity, View, StyleSheet, Platform, Animated } from 'react-native';
// import { BlurView } from '@react-native-community/blur';
// import LottieView from 'lottie-react-native';
// import { useNavigation } from '@react-navigation/native';
// // import ErrorBoundary from '../Components/ErrorBoundary';

// // Import your screen components here
// import HomeScreen from '../screens/HomeScreen';
// import AnalyticsScreen from '../screens/AnalyticsScreen';
// import ProfileScreen from '../screens/ProfileScreen';
// import AddScreen from '../screens/CameraScreen';

// const Tab = createBottomTabNavigator();

// // Hypothetical logging service
// const logError = (error, errorInfo) => {
//   console.error('Error:', error);
//   console.error('Error Info:', errorInfo);
//   // In a real app, you'd send this to a logging service
// };

// const AnimatedTabIcon = ({ source, size, onPress, isActive, routeName }) => {
//   const animationRef = useRef(null);

//   useEffect(() => {
//     try {
//       if (!isActive && animationRef.current) {
//         animationRef.current.reset();
//       }
//     } catch (error) {
//       console.error('Error in AnimatedTabIcon useEffect:', error);
//     }
//   }, [isActive]);

//   const handlePress = () => {
//     try {
//       if (animationRef.current) {
//         animationRef.current.play();
//       }
//       onPress(routeName);
//     } catch (error) {
//       console.error('Error in AnimatedTabIcon handlePress:', error);
//     }
//   };

//   return (
//     // <ErrorBoundary onError={(error) => console.error('ErrorBoundary in AnimatedTabIcon:', error)}>
//       <TouchableOpacity onPress={handlePress}>
//         <View style={{ width: size, height: size }}>
//           <LottieView
//             ref={animationRef}
//             source={source}
//             autoPlay={false}
//             loop={false}
//             style={{ width: '100%', height: '100%' }}
//           />
//         </View>
//       </TouchableOpacity>
//     // </ErrorBoundary>
//   );
// };

// const MainTabNavigator = () => {
//   const [activeTab, setActiveTab] = useState('Home');
//   const navigation = useNavigation();

//   const handleTabPress = (routeName) => {
//     try {
//       setActiveTab(routeName);
//       navigation.navigate(routeName);
//     } catch (error) {
//       logError(error, { component: 'MainTabNavigator', method: 'handleTabPress' });
//     }
//   };

//   return (
//     // <ErrorBoundary>
//       <Tab.Navigator
//         screenOptions={({ route }) => ({
//           headerShown: false,
//           tabBarIcon: ({ focused, color, size }) => {
//             let iconSource;

//             try {
//               if (route.name === 'Home') {
//                 iconSource = require('../../assets/icons/home-icon.json');
//               } else if (route.name === 'Analytics') {
//                 iconSource = require('../../assets/icons/home-icon.json');
//               } else if (route.name === 'Profile') {
//                 iconSource = require('../../assets/icons/profile-icon.json');
//               } else if (route.name === 'Add') {
//                 iconSource = require('../../assets/icons/add-icon.json');
//               }
//             } catch (error) {
//               logError(error, { component: 'MainTabNavigator', method: 'screenOptions' });
//               iconSource = require('../../assets/icons/default-icon.json');
//             }

//             return (
//               <AnimatedTabIcon
//                 source={iconSource}
//                 size={size * 2}
//                 onPress={handleTabPress}
//                 isActive={activeTab === route.name}
//                 routeName={route.name}
//                 style={focused ? styles.focusedIcon : styles.defaultIcon} // Apply styles

//               />
//             );
//           },
//           tabBarBackground: () => (
//             <BlurView
//               style={StyleSheet.absoluteFill}
//               blurType="light"
//               blurAmount={900}
//             />
//           ),
//           tabBarStyle: {
//             display: route.name === 'Add' ? 'none' : 'flex',
//             borderTopWidth: 0,
//             backgroundColor: 'rgba(255, 255, 255, 0.8)',
//             height: 80,
//             paddingBottom: Platform.OS === 'ios' ? 20 : 0,
//           },
//           tabBarActiveTintColor: '#000000', // Active tab color (e.g., Blue)
//           tabBarInactiveTintColor: '#8E8E93', // Inactive tab color (e.g., Gray)
//           tabBarLabelStyle: {
//             fontWeight: '850', // Default font weight
//           },
//         })}
//       >
//         <Tab.Screen name="Home" component={HomeScreen} />
//         <Tab.Screen name="Analytics" component={AnalyticsScreen} />
//         <Tab.Screen name="Profile" component={ProfileScreen} />
//         <Tab.Screen
//           name="Add"
//           component={AddScreen}
//           options={{
//             tabBarStyle: { display: 'none' },
//             tabBarIcon: ({ size }) => (
//               <View style={styles.addButtonContainer}>
//                 <AnimatedTabIcon
//                   source={require('../../assets/icons/add-icon.json')}
//                   size={size * 4.5}
//                   onPress={handleTabPress}
//                   isActive={activeTab === 'Add'}
//                   routeName="Add"
//                 />
//               </View>
//             ),
//             tabBarLabel: () => null,
//           }}
//         />
//       </Tab.Navigator>
//     // </ErrorBoundary>
//   );
// };

// const styles = StyleSheet.create({
//   addButtonContainer: {
//     position: 'absolute',
//     top: -30,
//     alignSelf: 'center',
//     justifyContent: 'center',
//     alignItems: 'center',
//     backgroundColor: 'white',
//     borderRadius: 35,
//     height: 70,
//     width: 70,
//     shadowColor: "#000",
//     shadowOffset: {
//       width: 0,
//       height: 2,
//     },
//     shadowOpacity: 0.25,
//     shadowRadius: 3.84,
//     elevation: 5,
//   },
//   defaultIcon: {
//     color: '#8E8E93',
//     shadowColor: 'transparent', // No shadow for inactive
//     transform: [{ scale: 1 }], // Default size
//   },
//   focusedIcon: {
//     color: '#007AFF',
//     shadowColor: '#007AFF', // Shadow matches active color
//     shadowOffset: { width: 0, height: 2 },
//     shadowOpacity: 0.5,
//     shadowRadius: 3,
//     transform: [{ scale: 1.1 }], // Slightly larger size
//   },
// });

// export default MainTabNavigator;





