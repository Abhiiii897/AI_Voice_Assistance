'use client';

import { useState } from 'react';
import { ChevronDown } from 'lucide-react';
import type { AgentProfile } from '@/types';

interface AgentProfileBadgeProps {
    readonly profile: AgentProfile;
}

function AgentProfileBadge({ profile }: AgentProfileBadgeProps) {
    const [expanded, setExpanded] = useState(false);

    return (
        <div className="relative">
            {/* Collapsed Badge - Always Visible */}
            <button
                onClick={() => setExpanded(!expanded)}
                className="flex items-center gap-2 hover:bg-gray-800 rounded-full px-2 py-1 transition-colors"
            >
                <img
                    src={profile.profilePicture}
                    alt={profile.name}
                    className="w-8 h-8 rounded-full border border-gray-700"
                />
                <ChevronDown className="w-4 h-4 text-gray-300" />
            </button>

            {/* Expanded Panel - Dropdown */}
            {expanded && (
                <div className="absolute right-0 mt-2 bg-gray-900 rounded-lg shadow-lg p-4 min-w-[280px] z-50 border border-gray-800">
                    {/* Profile Header */}
                    <div className="flex items-center gap-3 mb-4">
                        <img
                            src={profile.profilePicture}
                            alt={profile.name}
                            className="w-12 h-12 rounded-full border border-gray-700"
                        />
                        <div>
                            <h3 className="font-bold text-white">{profile.name}</h3>
                            <p className="text-xs text-gray-400">{profile.department}</p>
                        </div>
                    </div>

                    {/* Divider */}
                    <div className="border-t border-gray-800 my-3" />

                    {/* Details Section */}
                    <div className="space-y-2 text-sm text-gray-300 text-left">
                        <div className="flex items-start gap-2">
                            <span className="text-gray-500 min-w-fit">Email:</span>
                            <span className="text-gray-200 break-all">{profile.email}</span>
                        </div>
                        <div className="flex items-start gap-2">
                            <span className="text-gray-500 min-w-fit">Phone:</span>
                            <span className="text-gray-200">{profile.phone}</span>
                        </div>
                        <div className="flex items-start gap-2">
                            <span className="text-gray-500 min-w-fit">Department:</span>
                            <span className="text-gray-200">{profile.department}</span>
                        </div>
                    </div>

                    {/* Close hint */}
                    <p className="text-xs text-gray-500 mt-4 text-center">
                        Click badge to close
                    </p>
                </div>
            )}
        </div>
    );
}

export default AgentProfileBadge;
