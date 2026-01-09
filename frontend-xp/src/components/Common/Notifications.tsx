import React from 'react';
import { useUIStore } from '@/stores';
import { Notification as NotificationType } from '@/types';

export const Notifications: React.FC = () => {
  const { notifications, removeNotification } = useUIStore();

  if (notifications.length === 0) return null;

  return (
    <div className="fixed bottom-[44px] right-4 flex flex-col gap-2 z-[10001]">
      {notifications.map((notification) => (
        <NotificationToast
          key={notification.id}
          notification={notification}
          onClose={() => removeNotification(notification.id)}
        />
      ))}
    </div>
  );
};

interface NotificationToastProps {
  notification: NotificationType;
  onClose: () => void;
}

const NotificationToast: React.FC<NotificationToastProps> = ({ notification, onClose }) => {
  const bgColor = {
    info: 'bg-blue-50 border-blue-300',
    success: 'bg-green-50 border-green-300',
    warning: 'bg-yellow-50 border-yellow-300',
    error: 'bg-red-50 border-red-300',
  }[notification.type];

  const iconMap = {
    info: 'ℹ️',
    success: '✅',
    warning: '⚠️',
    error: '❌',
  };

  return (
    <div
      className={`w-[300px] p-3 rounded border-2 shadow-lg ${bgColor} animate-slide-in`}
      style={{
        animation: 'slideIn 0.3s ease-out',
      }}
    >
      <div className="flex items-start gap-2">
        <span className="text-xl">{notification.icon || iconMap[notification.type]}</span>
        <div className="flex-1 min-w-0">
          <h4 className="font-bold text-sm">{notification.title}</h4>
          <p className="text-xs text-gray-600">{notification.message}</p>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 text-lg leading-none"
        >
          ×
        </button>
      </div>
      <style>{`
        @keyframes slideIn {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
      `}</style>
    </div>
  );
};
