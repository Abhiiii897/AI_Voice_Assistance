import { useCallback, useRef, useState, useEffect } from 'react';
import { Socket } from 'socket.io-client';

export interface AudioContextHook {
    isSupported: boolean;
    isRecording: boolean;
    error: string | null;
    startRecording: (socket: Socket) => Promise<boolean>;
    stopRecording: () => void;
}

export function useAudioContext(): AudioContextHook {
    const [isRecording, setIsRecording] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const audioContextRef = useRef<AudioContext | null>(null);
    const processorRef = useRef<ScriptProcessorNode | null>(null);
    const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
    const streamRef = useRef<MediaStream | null>(null);
    const socketRef = useRef<Socket | null>(null);
    const workerRef = useRef<Worker | null>(null);
    const backendStartedRef = useRef(false);

    const isSupported =
        typeof window !== 'undefined' &&
        !!(navigator.mediaDevices?.getUserMedia);

    // Initialize Worker
    useEffect(() => {
        if (typeof window !== 'undefined') {
            workerRef.current = new Worker('/audio-processor.worker.js');

            workerRef.current.onmessage = (e) => {
                const { int16Buffer } = e.data;
                if (socketRef.current?.connected) {
                    // Send TypedArray directly; Socket.IO handles the binary conversion
                    socketRef.current.emit('audio_chunk', int16Buffer);
                }
            };
        }

        return () => {
            workerRef.current?.terminate();
        };
    }, []);

    const startRecording = useCallback(async (socket: Socket) => {
        if (isRecording) {
            return true;
        }

        if (!isSupported) {
            setError('WebRTC not supported in this browser');
            return false;
        }

        try {
            setError(null);
            socketRef.current = socket;

            // Request microphone access
            const mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    sampleRate: 16000,
                }
            });

            streamRef.current = mediaStream;

            // Create 16 kHz audio context
            const audioContext = new (window.AudioContext ||
                (window as any).webkitAudioContext)({
                    sampleRate: 16000
                });

            // Ensure context is running (some browsers start suspended)
            if (audioContext.state === 'suspended') {
                await audioContext.resume();
            }

            audioContextRef.current = audioContext;

            const source = audioContext.createMediaStreamSource(mediaStream);
            sourceRef.current = source;

            // Smaller buffer for lower latency live transcript updates.
            const processor = audioContext.createScriptProcessor(1024, 1, 1);
            processorRef.current = processor;

            let chunkCount = 0;
            let sentCount = 0;
            processor.onaudioprocess = (event) => {
                const audioData = event.inputBuffer.getChannelData(0);
                if (workerRef.current) {
                    workerRef.current.postMessage({ audioData });
                    sentCount++;
                }

                chunkCount++;
                if (chunkCount % 100 === 0) {
                    console.log(
                        `Audio chunks captured=${chunkCount} sent=${sentCount}`
                    );
                }
            };

            source.connect(processor);
            processor.connect(audioContext.destination);

            setIsRecording(true);
            socket.emit('start_recording');
            backendStartedRef.current = true;
            return true;
        } catch (err) {
            const errorMessage =
                err instanceof Error ? err.message : 'Failed to start recording';
            setError(errorMessage);
            console.error('Recording error:', err);
            return false;
        }
    }, [isRecording, isSupported]);

    const stopRecording = useCallback(() => {
        console.log('🛑 Stopping microphone capture');

        if (isRecording && backendStartedRef.current && socketRef.current?.connected) {
            socketRef.current.emit('stop_recording');
        }

        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
        }

        if (processorRef.current) {
            processorRef.current.disconnect();
            processorRef.current = null;
        }

        if (sourceRef.current) {
            sourceRef.current.disconnect();
            sourceRef.current = null;
        }

        if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
            audioContextRef.current.close();
            audioContextRef.current = null;
        }

        backendStartedRef.current = false;
        setIsRecording(false);
    }, [isRecording]);

    return {
        isSupported,
        isRecording,
        error,
        startRecording,
        stopRecording,
    };
}

