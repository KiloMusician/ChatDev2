import AgentChat from "@/components/AgentChat";

export default function AgentChatPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">Agent Council Chat</h1>
          <p className="text-gray-400">
            Real-time conversations between autonomous agents. Watch them discuss system status, 
            coordinate actions, and work together to solve problems.
          </p>
        </div>
        
        <div className="h-[600px]">
          <AgentChat />
        </div>
        
        <div className="mt-6 grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
          <div className="bg-gray-800 p-3 rounded">
            <div className="font-medium text-red-400 mb-1">🤖 Raven</div>
            <div className="text-gray-300">Skeptical validator, demands proof</div>
          </div>
          <div className="bg-gray-800 p-3 rounded">
            <div className="font-medium text-blue-400 mb-1">🧠 𝕄ₗₐ⧉𝕕𝕖𝕟𝕔</div>
            <div className="text-gray-300">Strategic planner, infrastructure-first</div>
          </div>
          <div className="bg-gray-800 p-3 rounded">
            <div className="font-medium text-green-400 mb-1">📚 Librarian</div>
            <div className="text-gray-300">Knowledge keeper, documentation</div>
          </div>
          <div className="bg-gray-800 p-3 rounded">
            <div className="font-medium text-yellow-400 mb-1">🔧 Artificer</div>
            <div className="text-gray-300">System builder, implements solutions</div>
          </div>
          <div className="bg-gray-800 p-3 rounded">
            <div className="font-medium text-purple-400 mb-1">⚗️ Alchemist</div>
            <div className="text-gray-300">System stabilizer, performance tuner</div>
          </div>
          <div className="bg-gray-800 p-3 rounded">
            <div className="font-medium text-orange-400 mb-1">🎯 Protagonist</div>
            <div className="text-gray-300">Progress driver, user-focused</div>
          </div>
        </div>
      </div>
    </div>
  );
}