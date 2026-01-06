import clsx from "clsx";

export type IconName =
  | "debate"
  | "chat"
  | "search"
  | "score"
  | "gear"
  | "help"
  | "info"
  | "trophy"
  | "network"
  | "profile";

const Icon = ({ name, className }: { name: IconName; className?: string }) => {
  const common = {
    className: clsx("pixel-icon", className),
    viewBox: "0 0 32 32",
    role: "img",
    "aria-hidden": true
  } as const;

  switch (name) {
    case "debate":
      return (
        <svg {...common}>
          <rect x="2" y="6" width="12" height="20" fill="#e0e0e0" stroke="#000" />
          <rect x="18" y="6" width="12" height="20" fill="#c0c0ff" stroke="#000" />
          <rect x="6" y="10" width="4" height="2" fill="#000" />
          <rect x="22" y="10" width="4" height="2" fill="#000" />
          <rect x="6" y="16" width="6" height="2" fill="#000" />
          <rect x="20" y="16" width="6" height="2" fill="#000" />
        </svg>
      );
    case "chat":
      return (
        <svg {...common}>
          <rect x="4" y="6" width="22" height="16" fill="#fff" stroke="#000" />
          <polygon points="10,22 12,26 16,22" fill="#fff" stroke="#000" />
          <rect x="8" y="10" width="10" height="2" fill="#000" />
          <rect x="8" y="14" width="14" height="2" fill="#000" />
        </svg>
      );
    case "search":
      return (
        <svg {...common}>
          <circle cx="14" cy="14" r="8" fill="#fff" stroke="#000" />
          <rect x="19" y="19" width="8" height="3" fill="#000" transform="rotate(45 19 19)" />
        </svg>
      );
    case "score":
      return (
        <svg {...common}>
          <rect x="6" y="4" width="20" height="24" fill="#fff" stroke="#000" />
          <rect x="10" y="8" width="12" height="2" fill="#000" />
          <rect x="10" y="12" width="12" height="2" fill="#000" />
          <rect x="10" y="16" width="12" height="2" fill="#000" />
          <rect x="10" y="20" width="8" height="2" fill="#000" />
        </svg>
      );
    case "gear":
      return (
        <svg {...common}>
          <circle cx="16" cy="16" r="6" fill="#c0c0c0" stroke="#000" />
          <circle cx="16" cy="16" r="2" fill="#000" />
          <rect x="15" y="4" width="2" height="6" fill="#000" />
          <rect x="15" y="22" width="2" height="6" fill="#000" />
          <rect x="4" y="15" width="6" height="2" fill="#000" />
          <rect x="22" y="15" width="6" height="2" fill="#000" />
        </svg>
      );
    case "help":
      return (
        <svg {...common}>
          <circle cx="16" cy="16" r="12" fill="#fff" stroke="#000" />
          <path d="M12 12c0-2 2-4 4-4s4 2 4 4c0 2-2 3-3 4-1 1-1 2-1 3" fill="none" stroke="#000" strokeWidth="2" />
          <circle cx="16" cy="24" r="1.5" fill="#000" />
        </svg>
      );
    case "info":
      return (
        <svg {...common}>
          <rect x="6" y="4" width="20" height="24" fill="#fff" stroke="#000" />
          <rect x="15" y="10" width="2" height="10" fill="#000" />
          <rect x="15" y="6" width="2" height="2" fill="#000" />
        </svg>
      );
    case "trophy":
      return (
        <svg {...common}>
          <rect x="10" y="6" width="12" height="10" fill="#ffd000" stroke="#000" />
          <rect x="12" y="16" width="8" height="6" fill="#ffd000" stroke="#000" />
          <rect x="8" y="22" width="16" height="4" fill="#000" />
          <rect x="6" y="6" width="4" height="6" fill="#ffd000" stroke="#000" />
          <rect x="22" y="6" width="4" height="6" fill="#ffd000" stroke="#000" />
        </svg>
      );
    case "network":
      return (
        <svg {...common}>
          <rect x="4" y="8" width="24" height="16" fill="#fff" stroke="#000" />
          <rect x="8" y="12" width="16" height="2" fill="#000" />
          <rect x="8" y="16" width="12" height="2" fill="#000" />
        </svg>
      );
    case "profile":
      return (
        <svg {...common}>
          <circle cx="16" cy="12" r="6" fill="#f2c1a0" stroke="#000" />
          <rect x="8" y="20" width="16" height="8" fill="#0078d7" stroke="#000" />
        </svg>
      );
    default:
      return null;
  }
};

export default Icon;
