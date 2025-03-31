import React, { useState } from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import MainTabNavigator from './MainTabNavigator';
import AddScreen from '../screens/CameraScreen';

const Stack = createStackNavigator();

const RootNavigator = () => {
  const [isTabBarVisible, setIsTabBarVisible] = useState(true);

  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="MainTabs">
        {(props) => <MainTabNavigator {...props} isTabBarVisible={isTabBarVisible} />}
      </Stack.Screen>
      <Stack.Screen 
        name="Add" 
        component={AddScreen} 
        listeners={{
          focus: () => setIsTabBarVisible(false),
          blur: () => setIsTabBarVisible(true),
        }}
      />
    </Stack.Navigator>
  );
};

export default RootNavigator;
