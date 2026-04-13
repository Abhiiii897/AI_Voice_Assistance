import { useRef, useEffect } from 'react';
import useDashboardStore from '@/store/useDashboardStore';
import SolutionCard from './SolutionCard';

function SolutionPanel() {
    // Subscribe to solutions from Zustand
    const solutionCards = useDashboardStore((state) => state.solutionCards);

    // Ref to be used to scroll to top when new solutions arrive
    const scrollContainerRef = useRef<HTMLDivElement>(null);
    const lastCountRef = useRef(solutionCards.length);

    /**
     * Auto-scroll to top when new solutions are added
     * New solutions are prepended to array (appear at top)
     */
    useEffect(() => {
        if (solutionCards.length > lastCountRef.current && scrollContainerRef.current) {
            lastCountRef.current = solutionCards.length;

            setTimeout(() => {
                if (scrollContainerRef.current) {
                    scrollContainerRef.current.scrollTo({
                        top: 0,
                        behavior: 'smooth',
                    });
                }
            }, 0);
        }
    }, [solutionCards]);

    return (
        <div className="flex flex-col h-full text-white">
            {/* Header */}
            <div className="px-4 py-3 border-b border-gray-700 flex-shrink-0">
                <h2 className="font-bold text-sm">Solution Cards</h2>
                <p className="text-xs text-gray-500 mt-1">{solutionCards.length} results</p>
            </div>

            {/* Scrollable Solutions Area */}
            <div
                ref={scrollContainerRef}
                className="flex-1 overflow-y-auto px-4 py-4 space-y-3 scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800"
            >
                {solutionCards.length === 0 ? (
                    <div className="text-gray-500 text-center py-8 text-sm">
                        Awaiting analysis...
                    </div>
                ) : (
                    solutionCards.map((card) => (
                        <SolutionCard key={card.id} card={card} />
                    ))
                )}
            </div>
        </div>
    );
}

export default SolutionPanel;
