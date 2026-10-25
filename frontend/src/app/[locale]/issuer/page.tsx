import { getTranslations, setRequestLocale } from "next-intl/server";
import PageTitle from "@/components/PageTitle";
import { serverGet } from "@/lib/server-api";
import { fmtDate } from "@/lib/format";

export const dynamic = "force-dynamic";

type Issuer = {
  issuer: string;
  issuer_ka: string;
  website: string;
  chain_id: number;
  chain_name: string;
  contract_address: string | null;
  contract_explorer_url: string;
  owner_address: string | null;
  issuer_addresses: { address: string; valid_from: string; valid_to: string | null }[];
  well_known_url: string;
};

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "issuer" });
  return { title: t("title") };
}

export default async function IssuerPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("issuer");
  const info = await serverGet<Issuer>("/public/issuer");
  const steps = t.raw("steps") as string[];

  const rows: [string, React.ReactNode][] = info
    ? [
        [t("name"), locale === "ka" ? info.issuer_ka : info.issuer],
        [t("website"), <a key="w" href={info.website} className="underline underline-offset-4" rel="noopener">{info.website}</a>],
        [t("network"), info.chain_name],
        [t("chainId"), String(info.chain_id)],
        [t("contract"), info.contract_address ? (
          info.contract_explorer_url
            ? <a key="c" href={info.contract_explorer_url} className="mono underline" rel="noopener">{info.contract_address}</a>
            : <span key="c" className="mono">{info.contract_address}</span>
        ) : t("notDeployed")],
        [t("owner"), <span key="o" className="mono">{info.owner_address ?? "—"}</span>],
        [t("issuers"), (
          <ul key="i" className="space-y-1">
            {info.issuer_addresses.map((a) => (
              <li key={a.address}><span className="mono">{a.address}</span> <span className="text-sm text-muted">· {t("since", { date: fmtDate(a.valid_from) })}</span></li>
            ))}
          </ul>
        )],
        [t("wellKnown"), <a key="k" href="/.well-known/btu-issuer.json" className="mono underline">/.well-known/btu-issuer.json</a>],
      ]
    : [];

  return (
    <>
      <PageTitle title={t("title")} lead={t("lead")} />
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6">
        <div className="frame">
          <dl className="sheet divide-y divide-line px-6">
            {rows.map(([k, v]) => (
              <div key={k} className="grid gap-1 py-4 md:grid-cols-[280px_1fr]">
                <dt className="font-semibold">{k}</dt>
                <dd className="min-w-0 break-words">{v}</dd>
              </div>
            ))}
            {!info && <p className="py-6 text-muted">{t("notDeployed")}</p>}
          </dl>
        </div>

        <section className="mt-14 grid gap-10 lg:grid-cols-2">
          <div>
            <h2 className="font-display text-2xl font-black">{t("stepsTitle")}</h2>
            <ol className="mt-5 space-y-4">
              {steps.map((s, i) => (
                <li key={i} className="flex gap-4">
                  <span className="font-numeric text-3xl leading-none text-orange">{i + 1}</span>
                  <span className="leading-relaxed">{s}</span>
                </li>
              ))}
            </ol>
          </div>
          <div className="h-fit border-2 border-ink p-6">
            <h2 className="font-display text-xl font-black">{t("signatureTitle")}</h2>
            <p className="mt-3 leading-relaxed text-muted">{t("signatureBody")}</p>
            <pre className="mt-5 overflow-x-auto bg-ink p-4 text-xs leading-relaxed text-white">{`sha256sum BTU-AI-2026-00001-v1.pdf

cast call ${info?.contract_address ?? "<contract>"} \\
  "lookupPdf(bytes32)(bytes32,uint32,(bytes32,bytes32,uint64,uint64,address))" \\
  0x<sha256> --rpc-url <rpc>`}</pre>
          </div>
        </section>
      </div>
    </>
  );
}
