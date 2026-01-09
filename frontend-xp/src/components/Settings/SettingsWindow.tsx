import React, { useState } from 'react';
import { useSettingsStore, useWindowStore } from '@/stores';

interface SettingsWindowProps {
  windowId: string;
  componentProps?: Record<string, unknown>;
}

type TabId = 'appearance' | 'debate' | 'window' | 'advanced';

const tabs: { id: TabId; label: string; icon: string }[] = [
  { id: 'appearance', label: 'Appearance', icon: '🎨' },
  { id: 'debate', label: 'Debate', icon: '💬' },
  { id: 'window', label: 'Window', icon: '🪟' },
  { id: 'advanced', label: 'Advanced', icon: '⚙️' },
];

export const SettingsWindow: React.FC<SettingsWindowProps> = ({ windowId }) => {
  const { settings, updateSettings, resetSettings } = useSettingsStore();
  const { closeWindow } = useWindowStore();
  const [activeTab, setActiveTab] = useState<TabId>('appearance');

  const handleSave = () => {
    closeWindow(windowId);
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'appearance':
        return (
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <label className="font-bold text-sm">Wallpaper:</label>
              <div className="flex gap-2">
                {['bliss', 'azul'].map((wp) => (
                  <button
                    key={wp}
                    onClick={() => updateSettings({ wallpaper: wp, theme: wp as 'bliss' | 'azul' })}
                    className={`w-20 h-14 rounded border-2 ${
                      settings.wallpaper === wp ? 'border-[#316AC5]' : 'border-gray-300'
                    }`}
                    style={{
                      background:
                        wp === 'bliss'
                          ? 'linear-gradient(180deg, #245EDC 0%, #3A7BD5 50%, #7EC87E 75%, #5AAB5A 100%)'
                          : 'linear-gradient(180deg, #003087 0%, #0054E3 50%, #0078D7 100%)',
                    }}
                    title={wp.charAt(0).toUpperCase() + wp.slice(1)}
                  />
                ))}
              </div>
            </div>
          </div>
        );

      case 'debate':
        return (
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-4">
              <label className="font-bold text-sm">Default Rounds:</label>
              <select
                className="xp-select"
                value={settings.defaultRounds}
                onChange={(e) => updateSettings({ defaultRounds: parseInt(e.target.value) })}
              >
                {[1, 2, 3, 4, 5].map((n) => (
                  <option key={n} value={n}>
                    {n}
                  </option>
                ))}
              </select>
            </div>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                className="xp-checkbox"
                checked={settings.useInternet}
                onChange={(e) => updateSettings({ useInternet: e.target.checked })}
              />
              <span className="text-sm">Enable internet research by default</span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                className="xp-checkbox"
                checked={settings.recommendGuests}
                onChange={(e) => updateSettings({ recommendGuests: e.target.checked })}
              />
              <span className="text-sm">Recommend guest experts by default</span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                className="xp-checkbox"
                checked={settings.autoSaveResults}
                onChange={(e) => updateSettings({ autoSaveResults: e.target.checked })}
              />
              <span className="text-sm">Auto-save debate results</span>
            </label>
          </div>
        );

      case 'window':
        return (
          <div className="flex flex-col gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                className="xp-checkbox"
                checked={settings.windowAnimation}
                onChange={(e) => updateSettings({ windowAnimation: e.target.checked })}
              />
              <span className="text-sm">Enable window animations</span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                className="xp-checkbox"
                checked={settings.soundEffects}
                onChange={(e) => updateSettings({ soundEffects: e.target.checked })}
              />
              <span className="text-sm">Enable sound effects</span>
            </label>
          </div>
        );

      case 'advanced':
        return (
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <label className="font-bold text-sm">API Endpoint:</label>
              <input
                type="text"
                className="xp-input w-full"
                value={settings.apiEndpoint}
                onChange={(e) => updateSettings({ apiEndpoint: e.target.value })}
              />
            </div>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                className="xp-checkbox"
                checked={settings.debugMode}
                onChange={(e) => updateSettings({ debugMode: e.target.checked })}
              />
              <span className="text-sm">Enable debug mode</span>
            </label>

            <div className="pt-4 border-t border-gray-300">
              <button
                className="xp-button px-4"
                onClick={() => {
                  if (window.confirm('Reset all settings to defaults?')) {
                    resetSettings();
                  }
                }}
              >
                Reset All Settings
              </button>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="p-4 h-full flex flex-col gap-4">
      {/* Tabs */}
      <div className="flex border-b border-gray-300">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 text-sm flex items-center gap-1 border border-b-0 rounded-t
                        ${
                          activeTab === tab.id
                            ? 'bg-white border-gray-300 -mb-px'
                            : 'bg-xp-gray-dark border-transparent hover:bg-xp-gray-light'
                        }`}
          >
            <span>{tab.icon}</span>
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto">{renderTabContent()}</div>

      {/* Actions */}
      <div className="flex justify-end gap-2 pt-2 border-t border-gray-300">
        <button className="xp-button px-6" onClick={handleSave}>
          OK
        </button>
        <button className="xp-button px-6" onClick={() => closeWindow(windowId)}>
          Cancel
        </button>
      </div>
    </div>
  );
};
