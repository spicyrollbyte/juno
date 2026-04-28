"use client";

import { useEffect, useRef } from "react";
import Image from "next/image";
import { gsap } from "@/lib/gsap";

export function V2CTA() {
  const sectionRef = useRef<HTMLElement>(null);
  const btnRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      if (btnRef.current) {
        gsap.from(btnRef.current, {
          scale: 0.85,
          opacity: 0,
          y: 18,
          duration: 0.9,
          ease: "back.out(2)",
          scrollTrigger: {
            trigger: btnRef.current,
            start: "top 92%",
            once: true,
          },
        });
      }
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  return (
    <section
      ref={sectionRef}
      className="relative w-full overflow-hidden"
      style={{ backgroundColor: "#F5F6F7" }}
    >
      {/* Combined CTA + landscape image (headline + mascot + wordmark baked in) */}
      <div className="relative w-full">
        <Image
          src="/images/cta-footer.png"
          alt="Your data already knows the answer. Juno."
          width={1509}
          height={1209}
          priority={false}
          sizes="100vw"
          className="w-full h-auto block"
        />

        {/* Top fade so the image blends out of the previous beige section */}
        <div
          className="absolute inset-x-0 top-0 h-24 pointer-events-none"
          style={{
            background:
              "linear-gradient(to bottom, #F5F6F7 0%, rgba(245,246,247,0) 100%)",
          }}
        />

        {/* Bottom fade into the dark footer bar */}
        <div
          className="absolute inset-x-0 bottom-0 h-32 pointer-events-none"
          style={{
            background:
              "linear-gradient(to bottom, rgba(26,42,58,0) 0%, rgba(26,42,58,0.75) 100%)",
          }}
        />

        {/* Text Me button — just below the headline, sized up, Satoshi */}
        <div
          ref={btnRef}
          className="absolute inset-x-0 flex justify-center pointer-events-none"
          style={{ top: "42%" }}
        >
          <a
            href="sms:+16283586166"
            className="pointer-events-auto inline-block rounded-full text-white transition-transform duration-300 ease-out hover:scale-[1.08]"
            style={{
              backgroundColor: "#3AAFD0",
              fontFamily: 'var(--font-sans), "Satoshi", system-ui, sans-serif',
              fontWeight: 600,
              fontSize: "clamp(18px, 2vw, 26px)",
              padding: "16px 40px",
              boxShadow:
                "0 14px 36px rgba(26,42,58,0.38), 0 4px 14px rgba(58,175,208,0.32)",
              letterSpacing: "0.01em",
            }}
          >
            Text Me &rarr;
          </a>
        </div>
      </div>
    </section>
  );
}
