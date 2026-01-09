import React from 'react';
import { useWindowStore } from '@/stores';
import { Window } from '@/components/Window';
import { DebateCreatorWindow } from '@/components/DebateCreator/DebateCreatorWindow';
import { DebateViewerWindow } from '@/components/DebateViewer/DebateViewerWindow';
import { ResultsViewerWindow } from '@/components/ResultsViewer/ResultsViewerWindow';
import { HistoryWindow } from '@/components/History/HistoryWindow';
import { SettingsWindow } from '@/components/Settings/SettingsWindow';
import { AboutWindow } from '@/components/About/AboutWindow';
import { MyComputerWindow } from '@/components/MyComputer/MyComputerWindow';

const windowComponents: Record<string, React.ComponentType<{ windowId: string; componentProps?: Record<string, unknown> }>> = {
  'debate-creator': DebateCreatorWindow,
  'debate-viewer': DebateViewerWindow,
  'results-viewer': ResultsViewerWindow,
  'history': HistoryWindow,
  'settings': SettingsWindow,
  'about': AboutWindow,
  'my-computer': MyComputerWindow,
};

export const WindowManager: React.FC = () => {
  const windows = useWindowStore((state) => state.windows);

  return (
    <>
      {windows.map((window) => {
        const WindowContent = windowComponents[window.component];
        
        if (!WindowContent) {
          console.warn(`Unknown window component: ${window.component}`);
          return null;
        }

        return (
          <Window key={window.id} window={window}>
            <WindowContent windowId={window.id} componentProps={window.componentProps} />
          </Window>
        );
      })}
    </>
  );
};
