import React, { useState, useEffect } from 'react';

export const SystemTray: React.FC = () => {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    });
  };

  return (
    <div
      className="h-full flex items-center gap-2 px-3 bg-gradient-to-b from-[#0F8AEE] to-[#0A5FC9]
                 border-l-2 border-[#0E3789]"
    >
      {/* Tray icons */}
      <div className="flex items-center gap-1">
        <span className="text-white/80 text-sm cursor-pointer hover:text-white" title="Volume">
          🔊
        </span>
        <span className="text-white/80 text-sm cursor-pointer hover:text-white" title="System Status">
          🟢
        </span>
      </div>
      
      {/* Clock */}
      <div
        className="text-white text-[11px] font-bold cursor-default min-w-[60px] text-center"
        title={formatDate(time)}
      >
        {formatTime(time)}
      </div>
    </div>
  );
};
