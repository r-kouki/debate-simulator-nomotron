export * from './window';
export * from './debate';
export * from './settings';

export interface ContextMenuItem {
  id: string;
  label: string;
  icon?: string;
  disabled?: boolean;
  separator?: boolean;
  onClick?: () => void;
  submenu?: ContextMenuItem[];
}

export interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  duration?: number;
  icon?: string;
}

export interface DesktopIcon {
  id: string;
  label: string;
  icon: string;
  position: { row: number; col: number };
  onClick?: () => void;
  onDoubleClick?: () => void;
}
