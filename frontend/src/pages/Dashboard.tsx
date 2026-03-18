import { Activity } from "lucide-react";

function Dashboard() {
  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <header className="border-b border-gray-800 px-6 py-4">
        <div className="flex items-center gap-3">
          <Activity className="h-8 w-8 text-blue-500" />
          <h1 className="text-2xl font-bold">Smart NVR</h1>
        </div>
      </header>

      <main className="p-6">
        <div className="mx-auto max-w-7xl">
          <div className="rounded-lg border border-gray-800 bg-gray-900 p-8 text-center">
            <h2 className="mb-2 text-xl font-semibold">
              Smart NVR Dashboard
            </h2>
            <p className="text-gray-400">
              System initializing...
            </p>
          </div>

          <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-3">
            <div className="rounded-lg border border-gray-800 bg-gray-900 p-6">
              <h3 className="mb-1 text-sm font-medium text-gray-400">Cameras</h3>
              <p className="text-3xl font-bold">0</p>
            </div>
            <div className="rounded-lg border border-gray-800 bg-gray-900 p-6">
              <h3 className="mb-1 text-sm font-medium text-gray-400">Events Today</h3>
              <p className="text-3xl font-bold">0</p>
            </div>
            <div className="rounded-lg border border-gray-800 bg-gray-900 p-6">
              <h3 className="mb-1 text-sm font-medium text-gray-400">Alerts</h3>
              <p className="text-3xl font-bold">0</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default Dashboard;
