import { useEffect, useRef } from "react";
import useDashboardStore from "@/store/useDashboardStore";
import type { TranscriptChunk } from "@/types";

function TranscriptPanel() {

    // Subscribe to the zustand store transcript state
    const transcript = useDashboardStore((state) => state.transcript)

    // Ref to be used to detect when new messages arrive (for auto-scroll)
    const scrollContainerRef = useRef<HTMLDivElement>(null);
    const lastTranscriptLengthRef = useRef(0);

    /**
     * Auto-scroll to bottom when new messages arrive
     * Only scrolls if user is already near bottom (good UX)
     */
    useEffect(() => {
        if (transcript.length > lastTranscriptLengthRef.current && scrollContainerRef.current) {
            lastTranscriptLengthRef.current = transcript.length;

            setTimeout(() => {
                if (scrollContainerRef.current) {
                    scrollContainerRef.current.scrollTo({
                        top: scrollContainerRef.current.scrollHeight,
                        behavior: 'smooth',
                    });
                }
            }, 0);
        }
    }, [transcript]);


    return (
        <div className="flex flex-col h-full text-white">
            {/* Header */}
            <div className="px-4 py-3 border-b border-gray-700 flex-shrink-0">
                <h2 className="font-bold text-sm">Live Transcript</h2>
                <p className="text-xs text-gray-500 mt-1">{transcript.length} messages</p>
            </div>

            {/* Scrollable Transcript Area */}
            <div
                ref={scrollContainerRef}
                className="flex-1 overflow-y-auto px-4 py-4 space-y-3 scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800"
            >
                {transcript.length === 0 ? (
                    <div className="text-gray-500 text-center py-8 text-sm">
                        Waiting for transcript...
                    </div>
                ) : (
                    transcript.map((chunk) => (
                        <TranscriptBubble key={chunk.id} chunk={chunk} />
                    ))
                )}
            </div>
        </div>
    );
}

interface TranscriptBubbleProps {
    chunk: TranscriptChunk;
}

function TranscriptBubble({ chunk }: Readonly<TranscriptBubbleProps>) {
    const isAgent = chunk.speaker === 'agent';
    const formattedTime = new Date(chunk.timestamp).toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
    });

    return (
        <div className={`flex ${isAgent ? 'justify-end' : 'justify-start'}`}>
            <div
                className={`max-w-[80%] rounded-lg px-4 py-2 ${isAgent
                        ? 'bg-blue-600 text-white rounded-br-none'
                        : 'bg-gray-700 text-gray-100 rounded-bl-none'
                    } text-sm ${chunk.isFinal ? '' : 'opacity-60 italic'}`}
            >
                {/* Message Text */}
                <div className="break-words">{chunk.text}</div>

                <div className={`mt-1 flex items-center gap-2 text-[10px] leading-none ${isAgent ? 'text-blue-200/80 justify-end' : 'text-gray-400/85 justify-start'}`}>
                    <span>{formattedTime}</span>
                    {!chunk.isFinal && <span className="opacity-80">typing...</span>}
                </div>
            </div>
        </div>
    );
}

export default TranscriptPanel;
