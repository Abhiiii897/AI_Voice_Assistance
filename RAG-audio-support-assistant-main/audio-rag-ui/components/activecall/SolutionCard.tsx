import type { SolutionCard as SolutionCardType } from '@/types';
import { useState } from 'react';

interface SolutionCardProps {
    card: SolutionCardType;
}

function SolutionCard({ card }: Readonly<SolutionCardProps>) {

    const [isExpanded, setIsExpanded] = useState(false);

    // Category color mapping
    const categoryColors: Record<string, { bg: string; text: string; border: string }> = {
        'Machine Operation': {
            bg: 'bg-purple-500/20',
            text: 'text-purple-300',
            border: 'border-purple-500',
        },
        'Maintenance & Parts': {
            bg: 'bg-yellow-500/20',
            text: 'text-yellow-300',
            border: 'border-yellow-500',
        },
        'Technical Troubleshooting': {
            bg: 'bg-orange-500/20',
            text: 'text-orange-300',
            border: 'border-orange-500',
        },
    };

    const colors = categoryColors[card.category] || categoryColors['Machine Operation'];

    // Determine how many steps to show (max 3, then "X more")
    const visibleSteps = isExpanded ? card.steps : card.steps.slice(0, 3);
    const hiddenStepCount = card.steps.length - visibleSteps.length;

    return (
        <div className="bg-gray-700/50 rounded-lg p-3 border border-gray-600 hover:border-gray-500 transition-colors">
            {/* Header: Title + Confidence */}
            <div className="flex items-start justify-between gap-2 mb-2">
                <h3 className="font-bold text-sm flex-1 text-white">{card.title}</h3>
                <span className="text-xs font-bold text-green-400 flex-shrink-0 whitespace-nowrap">
                    {(card.confidence * 100).toFixed(0)}%
                </span>
            </div>

            {/* Category Badge */}
            <div className={`inline-block text-xs px-2 py-1 rounded border mb-2 ${colors.bg} ${colors.text} ${colors.border}`}>
                {card.category}
            </div>

            {/* Steps List */}
            <ol className="text-xs text-gray-300 space-y-1 mb-3 ml-4">
                {visibleSteps.map((step) => (
                    <li key={step} className="list-decimal text-gray-400">
                        {step}
                    </li>
                ))}
                {hiddenStepCount > 0 && (
                    <button
                        onClick={() => setIsExpanded(!isExpanded)}
                        className="text-blue-400 cursor-pointer hover:text-blue-300 italic font-semibold transition-colors bg-none border-none p-0 text-left"
                    >
                        {isExpanded ? '- Hide steps' : `+ Show ${hiddenStepCount} more steps`}
                    </button>
                )}
            </ol>

            {/* Source Info */}
            <div className="text-xs text-gray-500 border-t border-gray-600 pt-2">
                <div className="font-semibold text-gray-400">Source:</div>
                <div className="text-gray-600 ml-2">
                    {card.source.manual} → {card.source.section} (p. {card.source.page})
                </div>
            </div>
        </div>
    );
}

export default SolutionCard;
