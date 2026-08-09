type IronSightEmblemProps = {
  className?: string;
  title?: string;
};

/** Compact IronSight monogram: I + S integrated with a precision inspection reticle. */
export function IronSightEmblem({ className, title }: IronSightEmblemProps) {
  return (
    <svg
      className={className}
      viewBox="0 0 32 32"
      width="32"
      height="32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden={title ? undefined : true}
      role={title ? "img" : undefined}
    >
      {title ? <title>{title}</title> : null}

      {/* Outer inspection ring */}
      <circle className="emblem-ring-outer" cx="16" cy="16" r="13.25" stroke="currentColor" strokeWidth="1.15" />

      {/* Inner measurement ring */}
      <circle
        className="emblem-ring-inner"
        cx="16"
        cy="16"
        r="8.75"
        stroke="currentColor"
        strokeWidth="0.7"
        opacity="0.45"
      />

      {/* Crosshair ticks */}
      <path
        className="emblem-crosshair"
        d="M16 2.75v3.1M16 26.15v3.1M2.75 16h3.1M26.15 16h3.1"
        stroke="currentColor"
        strokeWidth="1.15"
        strokeLinecap="square"
      />

      {/* Diagonal precision ticks */}
      <path
        className="emblem-ticks"
        d="M7.2 7.2l1.7 1.7M23.1 7.2l-1.7 1.7M7.2 24.8l1.7-1.7M23.1 24.8l-1.7-1.7"
        stroke="currentColor"
        strokeWidth="0.85"
        opacity="0.55"
      />

      {/* Letter I — vertical instrument stem */}
      <path
        className="emblem-letter-i"
        d="M10.2 9.4h3.1M11.75 9.4v13.2M10.2 22.6h3.1"
        stroke="currentColor"
        strokeWidth="1.55"
        strokeLinecap="square"
        strokeLinejoin="miter"
      />

      {/* Letter S — measurement sweep through the sight */}
      <path
        className="emblem-letter-s"
        d="M21.6 11.05c0-1.35-1.15-2.25-2.7-2.25-1.45 0-2.55.75-2.55 1.95 0 2.85 5.4 2.2 5.4 5.35 0 1.4-1.35 2.45-3.05 2.45-1.85 0-3.05-1.05-3.15-2.55"
        stroke="currentColor"
        strokeWidth="1.55"
        strokeLinecap="square"
        strokeLinejoin="round"
      />

      {/* Center aperture */}
      <circle className="emblem-aperture" cx="16" cy="16" r="1.35" fill="currentColor" opacity="0.9" />
    </svg>
  );
}
