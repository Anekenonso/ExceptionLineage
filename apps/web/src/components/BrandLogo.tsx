import React from "react";

interface BrandLogoProps {
  className?: string;
  size?: number;
}

export function BrandLogo({ className = "h-8 w-8", size = 32 }: BrandLogoProps) {
  return (
    <div
      className={`shrink-0 flex items-center justify-center rounded-lg bg-[#1c2621] text-[#faf6ef] shadow-2xs ${className}`}
      style={{ width: size, height: size }}
      aria-hidden="true"
    >
      <svg
        viewBox="0 0 32 32"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-full p-1"
      >
        {/* Outer classical architectural arch */}
        <path
          d="M8 26V14C8 9.58172 11.5817 6 16 6C20.4183 6 24 9.58172 24 14V26"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeLinecap="round"
        />
        {/* Inner arch with contract lineage curve */}
        <path
          d="M12 26V15C12 12.7909 13.7909 11 16 11C18.2091 11 20 12.7909 20 15V26"
          stroke="currentColor"
          strokeWidth="1.25"
          strokeLinecap="round"
          strokeOpacity="0.75"
        />
        {/* Center verification node with forest accent */}
        <circle cx="16" cy="18" r="2" fill="#5b7f6a" stroke="#dfeae3" strokeWidth="1" />
        {/* Base foundation line */}
        <path
          d="M6 26H26"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeLinecap="round"
        />
      </svg>
    </div>
  );
}
