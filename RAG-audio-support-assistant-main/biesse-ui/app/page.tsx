'use client';

import AgentProfileBadge from '@/components/common/AgentProfileBadge';
import { useRouter } from 'next/navigation';
import type { AgentProfile } from '@/types';
import useDashboardStore from '@/store/useDashboardStore';

export default function LandingPage() {
  const router = useRouter();

  // Mock agent data for [POC]
  const mockAgent: AgentProfile = {
    id: 'emp_001',
    name: 'Support Agent',
    profilePicture: 'https://api.dicebear.com/9.x/pixel-art/svg',
    email: 'agent@support.ai',
    phone: '+1-555-0123',
    department: 'Technical Support',
  };

  const mockStats = [
    { label: 'Avg Response Time', value: '320ms' },
    { label: "Today's calls", value: '12' },
    { label: 'Avg Satisfaction', value: '4.8/5' }
  ];

  const mockCallLogs = [
    {
      id: '1',
      customerName: 'Some Company x',
      category: 'Technical Troubleshooting',
      duration: '20 min',
      time: '1 hour ago',
    },
    {
      id: '2',
      customerName: 'Some Company y',
      category: 'Machine Operation',
      duration: '9 min',
      time: '2 hours ago',
    },
  ];

  const handleStartRecording = () => {
    const store = useDashboardStore.getState();
    store.startCall();
    router.push('/call');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-neutral-950 to-neutral-900 text-white">
      {/* Top Bar */}
      <div className="bg-gray-900 border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        {/* Left: Logo/Title */}
        <div className="text-2xl font-bold">Project Alpha</div>

        {/* Right: Agent Profile Badge */}
        <AgentProfileBadge profile={mockAgent} />
      </div>

      {/* Main Content - Centered */}
      <main className="flex flex-col items-center justify-center min-h-[calc(100vh-200px)] p-8">
        <div className="text-center max-w-2xl mb-12">
          <h1 className="text-5xl font-bold mb-4">Real-Time Support Intelligence</h1>
          <p className="text-xl text-gray-300 mb-8">
            POC for real-time technical support intelligence
          </p>

          {/* Stats Grid */}
          <div className="grid grid-cols-3 gap-6 mb-8">
            {mockStats.map((stat) => (
              <div
                key={stat.label}
                className="bg-gray-900/80 rounded-lg p-6 border border-gray-800"
              >
                <p className="text-gray-400 text-sm mb-2">{stat.label}</p>
                <p className="text-3xl font-bold">{stat.value}</p>
              </div>
            ))}
          </div>

          {/* Start Recording Button */}
          <button
            onClick={handleStartRecording}
            className="bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-8 rounded-full transition-colors"
          >
            Start Recording
          </button>
          <p className="text-gray-500 text-sm mt-4">
            POC: Click to start mic capture and navigate to dashboard
          </p>
        </div>
      </main>

      {/* Call Logs Section */}
      <div className="bg-gray-900/80 border-t border-gray-800 px-8 py-6">
        <h2 className="text-xl font-bold mb-4">Recent Call Logs</h2>
        <div className="space-y-2">
          {mockCallLogs.map((log) => (
            <div
              key={log.id}
              className="bg-gray-800/60 rounded-lg p-4 flex items-center justify-between"
            >
              <div className="flex-1 text-left">
                <p className="font-medium">{log.customerName}</p>
                <p className="text-sm text-gray-400">{log.category}</p>
              </div>
              <div className="text-right">
                <p className="text-sm">{log.duration}</p>
                <p className="text-xs text-gray-500">{log.time}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}