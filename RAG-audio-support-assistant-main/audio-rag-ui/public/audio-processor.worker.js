/**
 * Audio Processor Worker
 * Converts Float32Array to Int16 PCM in a separate thread.
 */

self.onmessage = function(e) {
    const { audioData } = e.data;
    const int16Buffer = floatToInt16(audioData);
    
    // Send back the buffer (transferable)
    self.postMessage({ int16Buffer }, [int16Buffer.buffer]);
};

function floatToInt16(float32Array) {
    const int16Array = new Int16Array(float32Array.length);
    for (let i = 0; i < float32Array.length; i++) {
        const value = Math.max(-1, Math.min(1, float32Array[i]));
        int16Array[i] = value < 0 ? value * 0x8000 : value * 0x7FFF;
    }
    return int16Array;
}
