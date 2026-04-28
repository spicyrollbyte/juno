"use client";

import { useEffect, useRef } from "react";
import Image from "next/image";
import { gsap } from "@/lib/gsap";

// A clean + cute scattered arrangement of the four widget shots.
// Each widget has its own position, rotation, and float phase.
// Triangular constellation: large anchors top-left,
// medium overlaps mid-right, small tucks in bottom-left.
const WIDGETS = [
  {
    src: "/images/widget-large.png",
    w: 346, h: 344,
    alt: "Juno is thinking of you — daily insight",
    style: {
      width: 300,
      top: 4,
      left: 8,
      rotate: -3.5,
      z: 2,
    },
  },
  {
    src: "/images/widget-medium.png",
    w: 392, h: 181,
    alt: "Juno is reminiscing",
    style: {
      width: 330,
      top: 254,
      left: 148,
      rotate: 4.5,
      z: 3,
    },
  },
  {
    src: "/images/widget-small-a.png",
    w: 173, h: 173,
    alt: "Juno is cooking",
    style: {
      width: 166,
      top: 300,
      left: 14,
      rotate: -6,
      z: 1,
    },
  },
];

export function V2Features() {
  const sectionRef = useRef<HTMLElement>(null);
  const copyRef = useRef<HTMLDivElement>(null);
  const stackRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      const parts = copyRef.current?.querySelectorAll(".v2-rise");
      parts?.forEach((el, i) => {
        gsap.from(el, {
          y: 40, opacity: 0, duration: 1, ease: "power3.out", delay: i * 0.08,
          scrollTrigger: {
            trigger: copyRef.current,
            start: "top 78%",
            toggleActions: "play none none reverse",
          },
        });
      });

      const widgets = stackRef.current?.querySelectorAll(".v2-widget");
      widgets?.forEach((el, i) => {
        // Entrance
        gsap.from(el, {
          y: 50, opacity: 0, scale: 0.9,
          duration: 0.9, ease: "power3.out", delay: i * 0.1,
          scrollTrigger: {
            trigger: stackRef.current,
            start: "top 80%",
            toggleActions: "play none none reverse",
          },
        });
        // Gentle floating at rest (different phase per widget)
        gsap.to(el, {
          y: "+=6",
          duration: 3 + i * 0.4,
          ease: "sine.inOut",
          yoyo: true,
          repeat: -1,
          delay: i * 0.3,
        });
      });
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  return (
    <section
      ref={sectionRef}
      className="relative py-28 md:py-36 px-6"
      style={{ backgroundColor: "#F5F6F7" }}
    >
      <div className="mx-auto max-w-[1100px] grid md:grid-cols-2 gap-14 md:gap-20 items-center">
        {/* Left: clean scattered widget arrangement */}
        <div className="order-2 md:order-1 flex justify-center md:justify-start">
          <div
            ref={stackRef}
            className="relative"
            style={{ width: 500, height: 470 }}
          >
            {/* Soft halo */}
            <div
              aria-hidden="true"
              className="absolute inset-0 rounded-[48px] pointer-events-none"
              style={{
                background:
                  "radial-gradient(60% 48% at 50% 50%, rgba(58,175,208,0.08) 0%, rgba(58,175,208,0) 72%)",
              }}
            />

            {WIDGETS.map((w) => (
              <div
                key={w.src}
                className="v2-widget absolute will-change-transform"
                style={{
                  top: w.style.top,
                  left: w.style.left,
                  width: w.style.width,
                  zIndex: w.style.z,
                  transform: `rotate(${w.style.rotate}deg)`,
                  transition:
                    "transform 420ms cubic-bezier(0.22,1,0.36,1), filter 300ms ease",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = `rotate(0deg) translateY(-6px) scale(1.04)`;
                  e.currentTarget.style.zIndex = "40";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = `rotate(${w.style.rotate}deg)`;
                  e.currentTarget.style.zIndex = String(w.style.z);
                }}
              >
                <Image
                  src={w.src}
                  alt={w.alt}
                  width={w.w}
                  height={w.h}
                  priority={false}
                  className="w-full h-auto drop-shadow-[0_18px_36px_rgba(58,175,208,0.18)]"
                  style={{ borderRadius: 16, display: "block" }}
                />
              </div>
            ))}
          </div>
        </div>

        {/* Right: body copy */}
        <div ref={copyRef} className="order-1 md:order-2">
          <h2
            className="v2-rise leading-[1.12]"
            style={{
              fontFamily: "var(--font-display)",
              fontSize: "clamp(30px, 3.6vw, 42px)",
              color: "#3AAFD0",
            }}
          >
            Most students are sitting on years of data they&rsquo;ve never
            been able to use.
          </h2>
          <h3
            className="v2-rise mt-4"
            style={{
              color: "#3D568E",
              fontFamily: '"PP Mondwest", Georgia, serif',
              fontSize: "75.144px",
              fontStyle: "normal",
              fontWeight: 400,
              lineHeight: "73.986px",
            }}
          >
            That changes now.
          </h3>

          <p
            className="v2-rise mt-8 leading-relaxed"
            style={{
              color: "#5E7388",
              fontSize: "clamp(14px, 1.35vw, 16px)",
              maxWidth: 420,
            }}
          >
            Your apps don&rsquo;t talk to each other, but Juno connects
            them. It builds a picture of you that grows over time and acts
            on your behalf — not just when you ask, but before you know
            you need it.
          </p>

          <p
            className="v2-rise mt-5 leading-relaxed"
            style={{
              color: "#7B8FA3",
              fontSize: "clamp(14px, 1.35vw, 16px)",
              maxWidth: 420,
            }}
          >
            In a future where context is everything, your data is your
            edge. Juno makes sure you&rsquo;re building it.
          </p>
        </div>
      </div>
    </section>
  );
}
