const FILES = { FOCUSED: "/stamps/focused.svg", APPLIED: "/stamps/applied.svg", ADVANCED: "/stamps/advanced.svg" } as const;
const SIZES = { FOCUSED: "h-20", APPLIED: "h-14", ADVANCED: "h-20" } as const;

export type StampType = keyof typeof FILES;

export default function Stamp({ type, className = "", alt = "" }: { type: StampType; className?: string; alt?: string }) {
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={FILES[type]} alt={alt} className={`${SIZES[type]} w-auto ${className}`} />
  );
}
