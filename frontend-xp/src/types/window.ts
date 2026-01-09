export interface Position {
  x: number;
  y: number;
}

export interface Size {
  width: number;
  height: number;
}

export type WindowComponent =
  | 'debate-creator'
  | 'debate-viewer'
  | 'results-viewer'
  | 'history'
  | 'settings'
  | 'about'
  | 'my-computer';

export interface WindowState {
  id: string;
  title: string;
  icon: string;
  component: WindowComponent;
  componentProps?: Record<string, unknown>;
  position: Position;
  size: Size;
  minSize?: Size;
  maxSize?: Size;
  zIndex: number;
  isMaximized: boolean;
  isMinimized: boolean;
  isFocused: boolean;
  resizable?: boolean;
}

export interface WindowConfig {
  id?: string;
  title: string;
  icon: string;
  component: WindowComponent;
  componentProps?: Record<string, unknown>;
  initialPosition?: Position;
  initialSize?: Size;
  minSize?: Size;
  maxSize?: Size;
  resizable?: boolean;
}
