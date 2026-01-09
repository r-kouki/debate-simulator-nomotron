
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Desktop } from '@/components/Desktop';
import { Taskbar } from '@/components/Taskbar';
import { Notifications } from '@/components/Common/Notifications';
import { useKeyboardShortcuts } from '@/hooks';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function AppContent() {
  useKeyboardShortcuts();

  return (
    <div className="w-screen h-screen overflow-hidden flex flex-col">
      <div className="flex-1 relative overflow-hidden">
        <Desktop />
      </div>
      <Taskbar />
      <Notifications />
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}

export default App;
