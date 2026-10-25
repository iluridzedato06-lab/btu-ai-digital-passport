export default function PageTitle({ title, lead, eyebrow }: { title: string; lead?: string; eyebrow?: string }) {
  return (
    <div className="border-b border-line bg-fog">
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 md:py-16">
        {eyebrow && <p className="mb-3 text-xs font-bold uppercase tracking-[0.2em] text-magenta">{eyebrow}</p>}
        <h1 className="font-display text-3xl font-black tracking-tight md:text-5xl">{title}</h1>
        {lead && <p className="mt-4 max-w-3xl text-lg text-muted">{lead}</p>}
      </div>
    </div>
  );
}
