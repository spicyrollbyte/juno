"use client";

import { useEffect, useRef } from "react";
import Image from "next/image";
import { gsap } from "@/lib/gsap";

const integrations = [
  { name: "Slack", icon: "/icons/slack.svg" },
  { name: "Gmail", icon: "/icons/gmail.svg" },
  { name: "Notion", icon: "/icons/notion.svg" },
  { name: "Figma", icon: "/icons/figma.svg" },
  { name: "GitHub", icon: "/icons/github.svg" },
  { name: "Zoom", icon: "/icons/zoom.svg" },
  { name: "Chrome", icon: "/icons/chrome.svg" },
  { name: "Outlook", icon: "/icons/outlook.svg" },
  { name: "Dropbox", icon: "/icons/dropbox.svg" },
  { name: "Instagram", icon: "/icons/instagram.svg" },
  { name: "LinkedIn", icon: "/icons/linkedin.svg" },
  { name: "Apple", icon: "/icons/apple.svg" },
  { name: "Safari", icon: "/icons/safari.svg" },
  { name: "Asana", icon: "/icons/asana.svg" },
  { name: "Obsidian", icon: "/icons/obsidian.svg" },
  { name: "Messenger", icon: "/icons/messenger.svg" },
  { name: "Arc", icon: "/icons/arc.svg" },
  { name: "Bluesky", icon: "/icons/bluesky.svg" },
];

const row1 = integrations.slice(0, 6);
const row2 = integrations.slice(6, 12);
const row3 = integrations.slice(12, 18);

function IconTile({ app }: { app: (typeof integrations)[0] }) {
  return (
    <div
      className="w-[110px] h-[110px] rounded-[22px] overflow-hidden shrink-0 p-[16px] pointer-events-none"
      style={{
        backgroundColor: "rgba(255,255,255,0.7)",
        border: "1px solid rgba(184,197,214,0.25)",
        boxShadow: "0 6px 18px rgba(58,175,208,0.06)",
      }}
    >
      <Image
        src={app.icon}
        alt={app.name}
        width={110}
        height={110}
        className="w-full h-full object-contain"
      />
    </div>
  );
}

export function V2Integrations() {
  const sectionRef = useRef<HTMLElement>(null);
  const headingRef = useRef<HTMLHeadingElement>(null);
  const subtextRef = useRef<HTMLParagraphElement>(null);
  const row1Ref = useRef<HTMLDivElement>(null);
  const row2Ref = useRef<HTMLDivElement>(null);
  const row3Ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      if (headingRef.current) {
        gsap.from(headingRef.current, {
          y: 40,
          opacity: 0,
          duration: 1,
          ease: "power3.out",
          scrollTrigger: {
            trigger: sectionRef.current,
            start: "top 75%",
            toggleActions: "play none none reverse",
          },
        });
      }

      if (subtextRef.current) {
        gsap.from(subtextRef.current, {
          y: 30,
          opacity: 0,
          duration: 0.8,
          ease: "power3.out",
          delay: 0.15,
          scrollTrigger: {
            trigger: sectionRef.current,
            start: "top 75%",
            toggleActions: "play none none reverse",
          },
        });
      }

      // Row 1: fast right
      if (row1Ref.current) {
        gsap.to(row1Ref.current, {
          x: 800,
          ease: "power1.out",
          scrollTrigger: {
            trigger: sectionRef.current,
            start: "top bottom",
            end: "bottom top",
            scrub: 0.3,
          },
        });
      }

      // Row 2: fast left
      if (row2Ref.current) {
        gsap.to(row2Ref.current, {
          x: -900,
          ease: "power1.out",
          scrollTrigger: {
            trigger: sectionRef.current,
            start: "top bottom",
            end: "bottom top",
            scrub: 0.5,
          },
        });
      }

      // Row 3: laggy right
      if (row3Ref.current) {
        gsap.to(row3Ref.current, {
          x: 700,
          ease: "power1.out",
          scrollTrigger: {
            trigger: sectionRef.current,
            start: "top bottom",
            end: "bottom top",
            scrub: 0.8,
          },
        });
      }
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  const r1 = [...row1, ...row1, ...row1, ...row1];
  const r2 = [...row2, ...row2, ...row2, ...row2];
  const r3 = [...row3, ...row3, ...row3, ...row3];

  return (
    <section
      ref={sectionRef}
      className="relative py-28 overflow-hidden"
      style={{ backgroundColor: "#F5F6F7" }}
    >
      <div className="mx-auto max-w-[1214px] px-6 mb-16">
        <h2
          ref={headingRef}
          className="text-center"
          style={{
            fontFamily: "var(--font-display)",
            fontSize: "clamp(32px, 4vw, 44px)",
            color: "#3AAFD0",
          }}
        >
          Connect the tools you already live in.
        </h2>
        <p
          ref={subtextRef}
          className="text-center mt-3"
          style={{
            color: "#7B8FA3",
            fontSize: "clamp(16px, 1.6vw, 19px)",
          }}
        >
          Juno syncs with the apps that shape your day — seamlessly,
          silently, always up to date.
        </p>
      </div>

      {/* Three parallax rows */}
      <div className="relative flex flex-col gap-[36px]">
        <div className="flex overflow-visible">
          <div
            ref={row1Ref}
            className="flex gap-[48px] shrink-0 will-change-transform"
            style={{ marginLeft: -300 }}
          >
            {r1.map((app, i) => (
              <IconTile key={`r1-${app.name}-${i}`} app={app} />
            ))}
          </div>
        </div>

        <div className="flex overflow-visible">
          <div
            ref={row2Ref}
            className="flex gap-[48px] shrink-0 will-change-transform"
            style={{ marginLeft: 200 }}
          >
            {r2.map((app, i) => (
              <IconTile key={`r2-${app.name}-${i}`} app={app} />
            ))}
          </div>
        </div>

        <div className="flex overflow-visible">
          <div
            ref={row3Ref}
            className="flex gap-[48px] shrink-0 will-change-transform"
            style={{ marginLeft: -150 }}
          >
            {r3.map((app, i) => (
              <IconTile key={`r3-${app.name}-${i}`} app={app} />
            ))}
          </div>
        </div>

        {/* Beige fade overlays to match v2 theme */}
        <div
          className="absolute inset-0 pointer-events-none z-10"
          style={{
            background:
              "linear-gradient(90deg, #F5F6F7 0%, rgba(245,246,247,0) 10%, rgba(245,246,247,0) 90%, #F5F6F7 100%)",
          }}
        />
      </div>
    </section>
  );
}
