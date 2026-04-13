'use client';

import { useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Mic, MicOff, Clock, ArrowLeft } from 'lucide-react';
import { io, Socket } from 'socket.io-client';

import NotesPanel from '@/components/activecall/NotesPanel';
import TranscriptPanel from '@/components/activecall/TranscriptPanel';
import SolutionPanel from '@/components/activecall/SolutionPanel';
import useDashboardStore from '@/store/useDashboardStore';
import { useAudioContext } from '@/lib/useAudioContext';

export default function ActiveCallPage() {
    const router = useRouter();
    const socketRef = useRef<Socket | null>(null);

    // Zustand Store
    const {
        currentSentiment,
        currentCategory,
        startCall,
        stopRecording,
        isRecording,
        callStartTime,
        notes,
        addTranscriptChunk,
        updateSentiment,
        updateCategory,
        addSolutionCards,
        setConnected,
        isConnected,
        callDuration,
        setCallDuration
    } = useDashboardStore();

    // Audio Context Hook
    const { startRecording, stopRecording: stopMic, error: micError } = useAudioContext();

    // Use refs for store actions to keep useEffect dependency array stable
    const addTranscriptChunkRef = useRef(addTranscriptChunk);
    const updateSentimentRef = useRef(updateSentiment);
    const updateCategoryRef = useRef(updateCategory);
    const addSolutionCardsRef = useRef(addSolutionCards);
    const setConnectedRef = useRef(setConnected);
    const hasStartedMicRef = useRef(false);
    const connectErrorCountRef = useRef(0);
    const notesCountRef = useRef(0);

    useEffect(() => {
        addTranscriptChunkRef.current = addTranscriptChunk;
        updateSentimentRef.current = updateSentiment;
        updateCategoryRef.current = updateCategory;
        addSolutionCardsRef.current = addSolutionCards;
        setConnectedRef.current = setConnected;
    });

    // Socket.IO Setup
    useEffect(() => {
        if (socketRef.current) {
            socketRef.current.disconnect();
            socketRef.current = null;
        }

        // Using 127.0.0.1 instead of localhost for Windows stability
        const serverUrl = process.env.NEXT_PUBLIC_WS_URL || 'http://127.0.0.1:5001';

        console.log(`🔌 Connecting to: ${serverUrl}`);

        const socketInstance = io(serverUrl, {
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionAttempts: 10,
            reconnectionDelay: 1000,
        });

        socketInstance.onAny((eventName, ...args) => {
            console.log(`📡 Event: ${eventName}`, args);
        });

        socketInstance.on('connect', () => {
            console.log('✅ Connected to backend');
            connectErrorCountRef.current = 0;
            setConnectedRef.current(true);
            
            // Start backend recording session if we are already in recording state
            if (useDashboardStore.getState().isRecording && hasStartedMicRef.current) {
                console.log('🎙️ Emitting start_recording to backend');
                socketInstance.emit('start_recording');
            }
        });

        socketInstance.on('disconnect', (reason) => {
            console.log('❌ Disconnected from backend:', reason);
            setConnectedRef.current(false);
        });

        socketInstance.on('connect_error', (err) => {
            connectErrorCountRef.current += 1;
            const attempt = connectErrorCountRef.current;
            if (attempt <= 3 || attempt % 5 === 0) {
                console.warn(`Socket connect_error (attempt ${attempt}):`, err?.message || err);
            }
        });

        socketInstance.io.on('reconnect_attempt', (attempt) => {
            console.log(`Reconnecting attempt #${attempt}`);
        });

        socketInstance.io.on('reconnect', (attempt) => {
            console.log(`Reconnected on attempt #${attempt}`);
        });

        socketInstance.io.on('reconnect_error', (err) => {
            console.warn('reconnect_error:', err?.message || err);
        });

        socketInstance.io.on('reconnect_failed', () => {
            console.warn('reconnect_failed: exhausted reconnect attempts');
        });

        // Handle Incoming Events
        socketInstance.on('transcript', (data: any) => {
            console.log('Received transcript:', data);
            if (!data.text) return;

            if (!data.isFinal) {
                useDashboardStore.setState((state) => {
                    const current = state.transcript;
                    const last = current[current.length - 1];
                    if (last && !last.isFinal && last.speaker === 'customer') {
                        const updated = [...current];
                        updated[updated.length - 1] = {
                            ...last,
                            text: data.text,
                            timestamp: data.timestamp || Date.now(),
                        };
                        return { transcript: updated };
                    }
                    return {
                        transcript: [
                            ...current,
                            {
                                id: Date.now().toString(),
                                text: data.text,
                                timestamp: data.timestamp || Date.now(),
                                speaker: 'customer',
                                isFinal: false,
                            },
                        ]
                    };
                });
                return;
            }

            useDashboardStore.setState((state) => {
                const current = state.transcript;
                const last = current[current.length - 1];
                if (last && !last.isFinal && last.speaker === 'customer') {
                    const updated = [...current];
                    updated[updated.length - 1] = {
                        ...last,
                        text: data.text,
                        timestamp: data.timestamp || Date.now(),
                        isFinal: true,
                    };
                    return { transcript: updated };
                }
                return {
                    transcript: [
                        ...current,
                        {
                            id: Date.now().toString(),
                            text: data.text,
                            timestamp: data.timestamp || Date.now(),
                            speaker: 'customer',
                            isFinal: true,
                        },
                    ]
                };
            });
        });

        socketInstance.on('sentiment', (data: any) => {
            console.log('📊 Received sentiment:', data);
            useDashboardStore.getState().updateSentiment({
                sentiment: data.sentiment || 'Neutral',
                confidence: 0.9,
                timestamp: Date.now(),
            });
            useDashboardStore.getState().updateCategory({
                category: data.category || 'Uncategorized',
                confidence: 0.9,
                timestamp: Date.now(),
            });
        });

        socketInstance.on('ai_suggestions', (data: any) => {
            console.log('💡 Received suggestions:', data);
            if (data.suggestions) {
                const refs = Array.isArray(data.references) ? data.references : [];
                const cards = data.suggestions.map((s: any, idx: number) => ({
                    id: `sol-${Date.now()}-${idx}`,
                    title: s.title,
                    category: s.category || 'Technical Troubleshooting',
                    confidence: Math.max(0.4, Math.min(0.99, ((typeof s.relevance === 'number' ? s.relevance : 80) / 100))),
                    steps: [s.description],
                    source: {
                        manual: s?.source?.manual || s?.source?.document || refs[idx]?.document || refs[0]?.document || 'General Manual',
                        section: s?.source?.section || refs[idx]?.section || refs[0]?.section || 'General',
                        page: s?.source?.page || refs[idx]?.page || refs[0]?.page || 1,
                    },
                    timestamp: Date.now(),
                }));
                useDashboardStore.getState().addSolutionCards(cards);
            }
        });

        socketInstance.on('transcription_error', (data: any) => {
            console.warn('Transcription error from backend:', data);
        });

        socketRef.current = socketInstance;

        return () => {
            console.log('🔌 Cleaning up socket connection');
            socketInstance.disconnect();
            if (socketRef.current === socketInstance) {
                socketRef.current = null;
            }
        };
    }, []); // Run only once on mount

    // Handle Recording Lifecycle
    useEffect(() => {
        const socket = socketRef.current;
        if (isConnected && socket && isRecording && callStartTime) {
            console.log('🎙️ Starting audio context recording');
            (async () => {
                const started = await startRecording(socket);
                if (started) {
                    hasStartedMicRef.current = true;
                } else {
                    hasStartedMicRef.current = false;
                    stopRecording();
                }
            })();
        }
    }, [isConnected, isRecording, callStartTime, startRecording, stopRecording]);

    // Timer for duration
    useEffect(() => {
        let interval: NodeJS.Timeout;
        if (isRecording) {
            interval = setInterval(() => {
                const elapsed = Math.floor((Date.now() - (callStartTime || Date.now())) / 1000);
                setCallDuration(elapsed);
            }, 1000);
        }
        return () => clearInterval(interval);
    }, [isRecording, callStartTime, setCallDuration]);

    const handleGoHome = () => {
        if (isRecording) {
            if (hasStartedMicRef.current) {
                stopMic();
            }
            stopRecording();
            hasStartedMicRef.current = false;
        }
        router.push('/');
    };

    const handleToggleMic = async () => {
        if (isRecording) {
            if (hasStartedMicRef.current) {
                stopMic();
            }
            stopRecording();
            hasStartedMicRef.current = false;
        } else if (socketRef.current) {
            const started = await startRecording(socketRef.current);
            if (started) {
                hasStartedMicRef.current = true;
                if (!callStartTime) {
                    startCall();
                } else {
                    useDashboardStore.setState({ isRecording: true });
                }
            } else {
                hasStartedMicRef.current = false;
                stopRecording();
            }
        }
    };

    useEffect(() => {
        const socket = socketRef.current;
        if (!socket || !socket.connected || !isConnected) return;
        if (notes.length < notesCountRef.current) {
            notesCountRef.current = notes.length;
            return;
        }
        if (notes.length <= notesCountRef.current) return;

        const addedCount = notes.length - notesCountRef.current;
        const latestAdded = notes.slice(0, addedCount);
        latestAdded.forEach((note) => {
            socket.emit('note_added', {
                id: note.id,
                text: note.text,
                timestamp: note.timestamp
            });
        });
        notesCountRef.current = notes.length;
    }, [notes, isConnected]);

    const formatDuration = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    };

    // Border & BG Colors based on sentiment
    const sentimentColors: Record<string, string> = {
        Positive: '#10B981',
        Neutral: '#3f3f3f',
        Negative: '#F97316',
        Agitated: '#EF4444',
    };

    const sentimentEmojis: Record<string, string> = {
        Positive: '😊',
        Neutral: '🙂',
        Negative: '😕',
        Agitated: '😤',
    };

    const currentSentStr = currentSentiment?.sentiment || 'Neutral';
    const sentimentColor = sentimentColors[currentSentStr] || sentimentColors.Neutral;
    const sentimentEmoji = sentimentEmojis[currentSentStr] || '😐';

    return (
        <div className="h-screen bg-black text-white overflow-hidden flex flex-col">
            {/* Top Bar */}
            <div
                className="px-6 py-3 flex items-center justify-between transition-all duration-500"
                style={{
                    backgroundColor: `${sentimentColor}40`,
                    borderBottom: `3px solid ${sentimentColor}`,
                }}
            >
                {/* Left Section - Back Button */}
                <div className="flex items-center gap-4">
                    <button
                        onClick={handleGoHome}
                        className="flex items-center gap-2 hover:bg-white/10 px-3 py-1.5 rounded-full transition-colors text-gray-300 hover:text-white"
                    >
                        <ArrowLeft className="w-5 h-5" />
                        <span className="text-sm font-medium">Home</span>
                    </button>
                </div>

                {/* Center Section - Metrics Badges */}
                <div className="flex items-center gap-3">
                    {/* Sentiment Badge */}
                    <div
                        className="px-3 py-1.5 rounded-full text-sm font-medium flex items-center gap-2 shadow-sm"
                        style={{
                            backgroundColor: `${sentimentColor}20`,
                            borderLeft: `3px solid ${sentimentColor}`,
                        }}
                    >
                        <span>{sentimentEmoji}</span>
                        <span>{currentSentStr}</span>
                    </div>

                    {/* Category Badge */}
                    <div className="px-3 py-1.5 rounded-full text-sm font-medium bg-blue-500/20 border-l-2 border-blue-500 shadow-sm">
                        {currentCategory?.category || "NOT CLASSIFIED"}
                    </div>

                    {/* Duration Timer */}
                    <div className="px-3 py-1.5 rounded-full text-sm font-mono bg-green-500/20 border-l-2 border-green-500 shadow-sm flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatDuration(callDuration)}
                    </div>

                    {/* Recording Indicator (Moved to Right/Center) */}
                    {isRecording && (
                        <div className="flex items-center gap-2 bg-red-500/10 border-l-2 border-red-500 rounded-full px-3 py-1.5 animate-in fade-in slide-in-from-left-2 transition-all">
                            <Mic className="w-4 h-4 text-red-500 animate-pulse" />
                            <span className="text-sm font-medium text-red-200">Recording</span>
                        </div>
                    )}
                </div>

                {/* Right Section - Mic Toggle */}
                <div className="flex items-center gap-3">
                    <button
                        onClick={handleToggleMic}
                        className={`flex items-center gap-2 px-4 py-1.5 rounded-full font-medium transition-all transform active:scale-95 shadow-lg ${isRecording
                            ? 'bg-red-600 hover:bg-red-700 text-white'
                            : 'bg-neutral-800 hover:bg-neutral-700 text-gray-300'
                            }`}
                    >
                        {isRecording ? <Mic className="w-4 h-4" /> : <MicOff className="w-4 h-4" />}
                        {isRecording ? 'Mic On' : 'Mic Off'}
                    </button>
                </div>
            </div>

            {/* Mic Error Alert */}
            {micError && (
                <div className="bg-red-500/20 text-red-200 px-4 py-2 text-center text-xs animate-bounce border-b border-red-500">
                    ⚠️ Microphone Error: {micError}
                </div>
            )}

            {/* Three-Panel Grid */}
            <div className="flex-1 grid grid-cols-3 gap-4 p-4 overflow-hidden">
                {/* Left Panel: Notes */}
                <div className="bg-neutral-950 rounded-xl overflow-hidden border border-neutral-800 flex flex-col shadow-2xl">
                    <NotesPanel />
                </div>

                {/* Center Panel: Live Transcript */}
                <div className="bg-neutral-950 rounded-xl overflow-hidden border border-neutral-800 flex flex-col shadow-2xl">
                    <TranscriptPanel />
                </div>

                {/* Right Panel: Solution Cards */}
                <div className="bg-neutral-950 rounded-xl overflow-hidden border border-neutral-800 flex flex-col shadow-2xl">
                    <SolutionPanel />
                </div>
            </div>
        </div>
    );
}


