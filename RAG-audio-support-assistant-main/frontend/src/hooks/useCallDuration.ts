import { useState, useEffect } from 'react';

/**
 * Hook to track call duration and format it for display
 * Updates every second and returns both raw seconds and formatted string
 *
 * Usage:
 *   const { duration, displayDuration } = useCallDuration(startTime);
 *   // Returns: { duration: 125, displayDuration: "0:02:05" }
 */
function useCallDuration(startTime: number | null) {
  const [duration, setDuration] = useState(0);
  const [displayDuration, setDisplayDuration] = useState('0:00');

  useEffect(() => {
    // If no start time, don't run timer
    if (!startTime) {
      
      setDuration(0);
      setDisplayDuration('0:00');
      return;

    }

    // Update every 1 second
    //setInterval() is what recalls this every second
    const interval = setInterval(() => {
      const elapsed = Math.floor((Date.now() - startTime) / 1000);
      setDuration(elapsed);

      // Format as HH:MM:SS or MM:SS
      const hours = Math.floor(elapsed / 3600);
      const minutes = Math.floor((elapsed % 3600) / 60);
      const seconds = elapsed % 60;

      if (hours > 0) {
        // Format: 1:05:30
        setDisplayDuration(
          `${hours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
        );
      } else {
        // Format: 2:45 (no hours)
        setDisplayDuration(`${minutes}:${String(seconds).padStart(2, '0')}`);
      }
    }, 1000/*-> this is the interval for retrigger */);

    // Cleanup: clear interval when component unmounts or startTime changes
    return () => clearInterval(interval);
  }, [startTime]);

  return { duration, displayDuration };
}

export default useCallDuration;