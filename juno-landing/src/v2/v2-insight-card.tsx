interface V2InsightCardProps {
  badge: string;
  badgeColor?: string;
  date: string;
  text: string;
  link?: string;
  dark?: boolean;
}

export function V2InsightCard({ badge, badgeColor, date, text, link, dark }: V2InsightCardProps) {
  return (
    <div
      className="w-[200px] rounded-2xl p-3.5 shadow-xl"
      style={{
        backgroundColor: dark ? "rgba(58,175,208,0.85)" : "rgba(255,255,255,0.93)",
        backdropFilter: "blur(12px)",
        border: dark ? "1px solid rgba(58,175,208,0.3)" : "1px solid rgba(184,197,214,0.2)",
      }}
    >
      <div className="flex items-center gap-2 mb-2">
        <span
          className="text-[9px] px-2 py-0.5 rounded-md font-semibold"
          style={{
            backgroundColor: dark ? "rgba(255,255,255,0.2)" : (badgeColor || "rgba(58,175,208,0.15)"),
            color: dark ? "rgba(255,255,255,0.9)" : "#3AAFD0",
          }}
        >
          {badge}
        </span>
        <span className="text-[9px]" style={{ color: dark ? "rgba(255,255,255,0.5)" : "#B8C5D6" }}>
          {date}
        </span>
      </div>
      <p
        className="text-[12px] leading-snug"
        style={{
          fontFamily: "var(--font-display)",
          color: dark ? "#fff" : "#3D4F5F",
        }}
      >
        {text}
      </p>
      {link && (
        <p className="text-[9px] mt-1.5" style={{ color: dark ? "rgba(255,255,255,0.5)" : "#B8C5D6" }}>
          {link}
        </p>
      )}
    </div>
  );
}
