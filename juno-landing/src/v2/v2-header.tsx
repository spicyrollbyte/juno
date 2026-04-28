"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";
import Image from "next/image";
import { gsap } from "@/lib/gsap";

export function V2Header() {
  const headerRef = useRef<HTMLElement>(null);
  const innerRef = useRef<HTMLDivElement>(null);
  const logoRef = useRef<HTMLAnchorElement>(null);
  const aboutRef = useRef<HTMLAnchorElement>(null);
  const joinRef = useRef<HTMLAnchorElement>(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.from(innerRef.current, {
        y: -20, opacity: 0, duration: 0.9, ease: "power3.out", delay: 0.2,
      });

      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: document.body,
          start: "top -60",
          end: "top -220",
          scrub: 1,
        },
      });

      tl.to(innerRef.current, {
        maxWidth: 600, paddingTop: 10, paddingBottom: 10,
        paddingLeft: 24, paddingRight: 24, borderRadius: 999,
        backgroundColor: "rgba(61,79,95,0.28)",
        backdropFilter: "blur(24px)",
        boxShadow: "0 4px 24px rgba(26,42,58,0.14), 0 0 0 1px rgba(61,79,95,0.12)",
        ease: "none",
      }, 0);

      const logoImg = logoRef.current?.querySelector("img");
      if (logoImg) tl.to(logoImg, { width: 108, ease: "none" }, 0);
      tl.to(aboutRef.current, { fontSize: 13, paddingLeft: 10, paddingRight: 10, ease: "none" }, 0);
      tl.to(joinRef.current, { fontSize: 12, paddingLeft: 16, paddingRight: 16, ease: "none" }, 0);
      tl.to(headerRef.current, { paddingTop: 14, ease: "none" }, 0);
    }, headerRef);

    return () => ctx.revert();
  }, []);

  return (
    <header
      ref={headerRef}
      className="fixed top-0 left-0 right-0 z-50 flex justify-center px-10 transition-none"
      style={{ paddingTop: 40 }}
    >
      <div
        ref={innerRef}
        className="flex items-center w-full will-change-transform"
        style={{
          maxWidth: 1100,
          borderRadius: 0,
          backgroundColor: "transparent",
          backdropFilter: "none",
          boxShadow: "none",
          padding: 0,
        }}
      >
        <Link
          ref={logoRef}
          href="/"
          className="flex items-center leading-none"
          aria-label="Juno"
        >
          <Image
            src="/images/juno-logo.png"
            alt="Juno"
            width={154}
            height={73}
            priority
            className="h-auto"
            style={{ width: 150 }}
          />
        </Link>

        <div className="flex-1" />

        <nav className="flex items-center gap-5">
          <Link
            ref={aboutRef}
            href="#"
            className="rounded-full py-1.5 transition-colors hover:bg-[#3AAFD0]/5"
            style={{ fontSize: 15, paddingLeft: 16, paddingRight: 16, color: "#7B8FA3", fontWeight: 500 }}
          >
            About
          </Link>
          <a
            ref={joinRef}
            href="sms:+16283586166"
            className="rounded-full py-2.5 text-white transition-all hover:opacity-90"
            style={{ fontSize: 14, paddingLeft: 28, paddingRight: 28, backgroundColor: "#3AAFD0", fontWeight: 600 }}
          >
            Join the Waitlist
          </a>
        </nav>
      </div>
    </header>
  );
}
