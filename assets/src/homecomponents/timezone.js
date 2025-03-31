import { format, parse, startOfDay, endOfDay, isToday, isSameDay } from 'date-fns';
import { Text } from 'react-native';
import { memo } from 'react';

// Cache timezone since it won't change during app lifecycle
const TIMEZONE = Intl.DateTimeFormat().resolvedOptions().timeZone;

// Memoize date formatting results
const dateFormatCache = new Map();
const getCacheKey = (date, format) => `${date.getTime()}-${format}`;

export const getLocalTimeZone = () => TIMEZONE;

export const getLocalDate = (date = new Date()) => {
  // Return original date if it's already a Date object to avoid unnecessary object creation
  return date instanceof Date ? date : new Date(date);
};

export const getLocalStartOfDay = (date) => {
  const key = `start-${date.getTime()}`;
  if (dateFormatCache.has(key)) {
    return dateFormatCache.get(key);
  }
  
  const result = startOfDay(getLocalDate(date));
  dateFormatCache.set(key, result);
  return result;
};

export const getLocalEndOfDay = (date) => {
  const key = `end-${date.getTime()}`;
  if (dateFormatCache.has(key)) {
    return dateFormatCache.get(key);
  }
  
  const result = endOfDay(getLocalDate(date));
  dateFormatCache.set(key, result);
  return result;
};

export const formatLocalDate = (date, formatString) => {
  if (!date || !formatString) {
    console.warn('formatLocalDate: Invalid date or format string');
    return '';
  }
  
  const cacheKey = getCacheKey(date, formatString);
  if (dateFormatCache.has(cacheKey)) {
    return dateFormatCache.get(cacheKey);
  }
  
  try {
    const result = format(getLocalDate(date), formatString);
    dateFormatCache.set(cacheKey, result);
    return result;
  } catch (error) {
    console.error('formatLocalDate: Error formatting date:', error);
    return '';
  }
};

// Clear cache when it gets too large
const MAX_CACHE_SIZE = 100;
export const clearDateCache = () => {
  if (dateFormatCache.size > MAX_CACHE_SIZE) {
    dateFormatCache.clear();
  }
};

// Optimized comparison functions that avoid creating unnecessary Date objects
export const isLocalSameDay = (dateLeft, dateRight) => {
  if (!dateLeft || !dateRight) return false;
  
  try {
    return isSameDay(
      dateLeft instanceof Date ? dateLeft : new Date(dateLeft),
      dateRight instanceof Date ? dateRight : new Date(dateRight)
    );
  } catch (error) {
    console.error('isLocalSameDay: Error comparing dates:', error);
    return false;
  }
};

export const isLocalToday = (date) => {
  if (!date) return false;
  
  try {
    return isToday(date instanceof Date ? date : new Date(date));
  } catch (error) {
    console.error('isLocalToday: Error checking if date is today:', error);
    return false;
  }
};

// Memoized date formatter component
export const MemoizedDateText = memo(({ date, formatString, style }) => {
  if (!date || !formatString) {
    return null;
  }

  return (
    <Text style={style}>
      {formatLocalDate(date, formatString)}
    </Text>
  );
});

// Add prop-types for the MemoizedDateText component
MemoizedDateText.displayName = 'MemoizedDateText';