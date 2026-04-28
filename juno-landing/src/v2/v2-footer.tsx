import Image from "next/image";
import Link from "next/link";

const productLinks = ["Features", "Integrations", "Pricing", "Changelog"];
const companyLinks = ["About", "Blog", "Careers", "Contact"];
const legalLinks = ["Privacy", "Terms", "Security"];
const socialLinks = ["Twitter", "Instagram", "LinkedIn"];

export function V2Footer() {
  return (
    <footer className="relative overflow-hidden">
      {/* Footer content bar */}
      <div style={{ backgroundColor: "#1A2A3A", color: "rgba(255,255,255,0.78)" }}>
        <div className="mx-auto max-w-[1100px] px-6 py-16 md:py-20">
          <div className="grid gap-12 md:grid-cols-5">
            {/* Brand column */}
            <div className="md:col-span-2">
              <Image
                src="/images/juno-logo-white.svg"
                alt="Juno"
                width={238}
                height={113}
                className="w-[128px] h-auto"
              />

              <p
                className="mt-5 max-w-[320px] leading-relaxed"
                style={{
                  color: "rgba(255,255,255,0.6)",
                  fontSize: 15,
                }}
              >
                Your personal context engine. Every app, every moment, one
                clear picture — shaped however makes sense to you.
              </p>

              <a
                href="sms:+16283586166"
                className="inline-block mt-7 px-6 py-3 rounded-full font-semibold transition-all duration-300 hover:scale-[1.03] active:scale-[0.97]"
                style={{
                  backgroundColor: "#ffffff",
                  color: "#1A2A3A",
                  fontSize: 14,
                }}
              >
                Join the waitlist &rarr;
              </a>
            </div>

            {/* Link groups */}
            <FooterColumn heading="Product" links={productLinks} />
            <FooterColumn heading="Company" links={companyLinks} />
            <FooterColumn heading="Legal" links={legalLinks} />
          </div>

          {/* Bottom bar */}
          <div
            className="mt-14 pt-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4"
            style={{ borderTop: "1px solid rgba(255,255,255,0.1)" }}
          >
            <p style={{ color: "rgba(255,255,255,0.45)", fontSize: 13 }}>
              &copy; 2026 Juno Labs, Inc. All rights reserved.
            </p>
            <div className="flex items-center gap-6">
              {socialLinks.map((s) => (
                <Link
                  key={s}
                  href="#"
                  className="transition-colors duration-300 hover:text-white"
                  style={{ color: "rgba(255,255,255,0.55)", fontSize: 13 }}
                >
                  {s}
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}

function FooterColumn({ heading, links }: { heading: string; links: string[] }) {
  return (
    <div className="flex flex-col gap-3">
      <span
        className="uppercase"
        style={{
          color: "rgba(255,255,255,0.5)",
          fontSize: 12,
          fontWeight: 600,
          letterSpacing: "0.18em",
        }}
      >
        {heading}
      </span>
      {links.map((l) => (
        <Link
          key={l}
          href="#"
          className="transition-colors duration-300 hover:text-white"
          style={{ color: "rgba(255,255,255,0.72)", fontSize: 14 }}
        >
          {l}
        </Link>
      ))}
    </div>
  );
}
