import { useEffect, useRef } from "react";
import useDashboardStore from "../../hooks/useDashboardStore";
import type { TranscriptChunk } from "../../types";

function TranscriptPanel() {

    //subsribe to the zustand store transcript state
    const transcript = useDashboardStore((state) => state.transcript)

    // Ref to be used to detect when new messages arrive (for auto-scroll)
    const scrollContainerRef = useRef<HTMLDivElement>(null);
    const lastTranscriptLengthRef = useRef(0); //a ref variable because it needs to survive rerenders

    /**
     * Auto-scroll to bottom when new messages arrive
     * Only scrolls if user is already near bottom (good UX)
     */
    useEffect(() => {
        //if transcript length increase
        if (transcript.length > lastTranscriptLengthRef.current && scrollContainerRef.current) {
        // New message arrived
        lastTranscriptLengthRef.current = transcript.length; //reset length

        // Small delay to ensure DOM is updated
        setTimeout(() => {
            if (scrollContainerRef.current) {
            scrollContainerRef.current.scrollTo({ //scrolls to top
                top: scrollContainerRef.current.scrollHeight,
                behavior: 'smooth',
            });
            }
        }, 0);
        }
    }, [transcript]/*-> trigger for the useEffect()*/);


    return (
        <div className="flex flex-col h-full">
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

    /**
     * Individual transcript bubble component
     * Displays message with speaker, timestamp, and style
     */
    interface TranscriptBubbleProps {
    chunk: TranscriptChunk; // TranscriptChunk type active, will break if apeaker tags aren't agent|customer
    }

    function TranscriptBubble({ chunk }: Readonly<TranscriptBubbleProps>) {
    const isAgent = chunk.speaker === 'agent';

    return (
        <div className={`flex ${isAgent ? 'justify-end' : 'justify-start'}`}>
        <div //inner contents in tile
            className={`max-w-[80%] rounded-lg px-4 py-2 ${ //chat bubble
            isAgent
                ? 'bg-blue-600 text-white rounded-br-none' //agent: blue right justified
                : 'bg-gray-700 text-gray-100 rounded-bl-none' //customer grey right justified
            } text-sm ${chunk.isFinal ? '' : 'opacity-60 italic'}`} //partial trascripts (NOT final) will be dim and italic
        >
            {/* Message Text */}
            <div className="break-words">{chunk.text}</div>

            {/* Timestamp */}
            <div className={`text-xs mt-1 ${isAgent ? 'text-blue-200' : 'text-gray-400'}`}>
            {new Date(chunk.timestamp).toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
            })}
            </div>

            {/* Interim indicator */}
            {!chunk.isFinal && <div className="text-xs mt-1 opacity-75">typing...</div>}
        </div>
        </div>
    );
    }

    export default TranscriptPanel;
