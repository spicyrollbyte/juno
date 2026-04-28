"use client";

import { useEffect, useRef } from "react";
import { gsap, ScrollTrigger } from "@/lib/gsap";
import Image from "next/image";
import { DepthParallax, type ImageSet } from "./depth-parallax";

const HERO_IMAGE: ImageSet = {
  image: "/images/forest-lake.png",
  depth: "/images/depth-forest.png",
  width: 1512,
  height: 916,
  pixelArt: false,
};

export function V2Hero() {
  const sectionRef = useRef<HTMLElement>(null);
  const heroTextRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<HTMLDivElement>(null);
  const imageZoomRef = useRef<HTMLDivElement>(null);
  const overlayRef = useRef<HTMLDivElement>(null);
  const particleContainerRef = useRef<HTMLDivElement>(null);
  const particleRef = useRef<HTMLHeadingElement>(null);
  const particleActive = useRef(false);
  const sceneReady = useRef(false);
  const depthActive = useRef(false);
  const card1Ref = useRef<HTMLDivElement>(null);
  const card2Ref = useRef<HTMLDivElement>(null);
  const card3Ref = useRef<HTMLDivElement>(null);
  const cursorTarget = useRef({ x: 0, y: 0 });
  const cursorSmoothed = useRef({ x: 0, y: 0 });

  useEffect(() => {
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const startW = Math.min(1372, vw * 0.92);
    const startH = startW * (83 / 263);

    gsap.set(imageRef.current, {
      width: startW, height: startH, left: "50%", bottom: "3%",
      xPercent: -50, borderRadius: 28,
    });
    gsap.set(overlayRef.current, { opacity: 0 });
    gsap.set(particleContainerRef.current, { opacity: 0 });

    // Set initial card rotations via GSAP (not inline transform) so scroll timeline can reverse them
    gsap.set(card1Ref.current, { rotation: -6 });
    gsap.set(card2Ref.current, { rotation: -3 });
    gsap.set(card3Ref.current, { rotation: 5 });

    const ctx = gsap.context(() => {
      // --- Load animations ---
      const h1 = heroTextRef.current?.querySelector("h1");
      const subtitle = heroTextRef.current?.querySelector(".v2-subtitle");
      const btn = heroTextRef.current?.querySelector(".v2-cta-btn");

      if (h1) gsap.from(h1, { y: 70, opacity: 0, duration: 1.4, ease: "power4.out", delay: 0.15 });
      if (subtitle) gsap.from(subtitle, { y: 35, opacity: 0, duration: 1.1, ease: "power3.out", delay: 0.5 });
      if (btn) gsap.from(btn, { y: 20, opacity: 0, scale: 0.92, duration: 0.9, ease: "back.out(1.5)", delay: 0.8 });

      // Cards: load animation only (no float — it conflicts with scroll timeline)
      [card1Ref, card2Ref, card3Ref].forEach((ref, i) => {
        if (ref.current) {
          gsap.from(ref.current, {
            y: 70, opacity: 0, scale: 0.85,
            duration: 1, ease: "power3.out", delay: 0.6 + i * 0.15,
          });
        }
      });

      // --- Particle text setup ---
      const particleEl = particleRef.current;
      let chars: NodeListOf<Element> | null = null;
      if (particleEl) {
        const text = particleEl.textContent || "";
        particleEl.innerHTML = text.split("").map((char) => {
          if (char === " ") return '<span class="particle-char inline-block">&nbsp;</span>';
          return `<span class="particle-char inline-block" style="will-change:transform,filter">${char}</span>`;
        }).join("");
        chars = particleEl.querySelectorAll(".particle-char");
        gsap.set(chars, {
          x: () => gsap.utils.random(-70, 70),
          y: () => gsap.utils.random(-45, 45),
          scale: () => gsap.utils.random(0.5, 1.5),
          opacity: 0, filter: "blur(10px)",
        });
      }

      // --- Pinned scroll timeline (shorter, less distortion) ---
      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: sectionRef.current,
          start: "top top",
          end: "+=1200",
          pin: true,
          scrub: 0.5,
          anticipatePin: 1,
          onUpdate: (self) => {
            depthActive.current = self.progress > 0.12;
            sceneReady.current = self.progress > 0.12;
            particleActive.current = self.progress > 0.55;
          },
        },
      });

      // Hero text out (0 → 0.08)
      tl.to(heroTextRef.current, { y: -160, opacity: 0, duration: 0.08, ease: "none" }, 0);

      // Cards curve away — fromTo so GSAP knows both ends (fixes scroll-back glitch)
      const cardExits = [
        { from: { x: 0, y: 0, rotation: -6, scale: 1, opacity: 1 }, to: { x: -220, y: -180, rotation: -25, scale: 0.4, opacity: 0 } },
        { from: { x: 0, y: 0, rotation: -3, scale: 1, opacity: 1 }, to: { x: -180, y: 120, rotation: 18, scale: 0.35, opacity: 0 } },
        { from: { x: 0, y: 0, rotation: 5, scale: 1, opacity: 1 }, to: { x: 240, y: -150, rotation: -22, scale: 0.4, opacity: 0 } },
      ];
      [card1Ref, card2Ref, card3Ref].forEach((ref, i) => {
        if (ref.current) {
          tl.fromTo(ref.current, cardExits[i].from, {
            ...cardExits[i].to, duration: 0.12, ease: "power2.in",
          }, 0);
        }
      });

      // Image expands (0 → 0.15) — no scale bump; avoids extra warping
      tl.to(imageRef.current, {
        width: vw + 40, height: vh + 30, bottom: 0, borderRadius: 0,
        duration: 0.15, ease: "none",
      }, 0);

      // Vignette (0.15 → 0.22)
      tl.to(overlayRef.current, { opacity: 1, duration: 0.07, ease: "none" }, 0.15);

      // Text appears (0.22 → 0.55)
      tl.to(particleContainerRef.current, { opacity: 1, duration: 0.02, ease: "none" }, 0.22);
      if (chars && chars.length > 0) {
        tl.to(chars, {
          x: 0, y: 0, scale: 1, opacity: 1, filter: "blur(0px)",
          duration: 0.26, stagger: { amount: 0.16, from: "random" }, ease: "power2.out",
        }, 0.24);
      }

      // Body copy fades in behind the headline
      const heroBody = particleContainerRef.current?.querySelector(".v2-hero-body");
      if (heroBody) {
        tl.fromTo(heroBody,
          { opacity: 0, y: 20 },
          { opacity: 1, y: 0, duration: 0.18, ease: "power2.out" },
          0.42);
      }

      // Force timeline to 1.0 so remaining scroll = hold
      tl.set({}, {}, 1.0);
    }, sectionRef);

    // --- Mouse parallax (only when fullscreen) ---
    const onMouseMove = (e: MouseEvent) => {
      cursorTarget.current.x = (e.clientX / vw) * 2 - 1;
      cursorTarget.current.y = -(e.clientY / vh) * 2 + 1;
    };
    window.addEventListener("mousemove", onMouseMove);

    let rafId: number;
    const animateParallax = () => {
      const s = cursorSmoothed.current;
      s.x += (cursorTarget.current.x - s.x) * 0.035;
      s.y += (cursorTarget.current.y - s.y) * 0.035;

      if (sceneReady.current && imageZoomRef.current) {
        imageZoomRef.current.style.transform = `translate(${-s.x * 5}px, ${s.y * 3}px)`;
      }
      if (particleActive.current && particleContainerRef.current) {
        particleContainerRef.current.style.transform =
          `perspective(1200px) rotateX(${-s.y * 2}deg) rotateY(${s.x * 3}deg) translate(${s.x * 10}px, ${-s.y * 6}px)`;
      }
      rafId = requestAnimationFrame(animateParallax);
    };
    rafId = requestAnimationFrame(animateParallax);

    return () => {
      ctx.revert();
      window.removeEventListener("mousemove", onMouseMove);
      cancelAnimationFrame(rafId);
    };
  }, []);

  return (
    <section ref={sectionRef} className="relative h-screen overflow-hidden">
      {/* Hero text */}
      <div ref={heroTextRef}
        className="absolute inset-0 flex flex-col items-center pt-[13vh] z-20 px-6 pointer-events-none">
        <h1 className="text-center leading-[1.12] max-w-[720px]"
          style={{ fontFamily: "var(--font-display)", fontSize: "clamp(42px, 6vw, 68px)", color: "#3D4F5F" }}>
          Your world, with a little<br />more{" "}
          <em style={{
            fontFamily: '"Silver Garden", "PP Mondwest", "Didot", "Bodoni 72", Georgia, serif',
            color: "#4A6FA4",
            fontSize: "1.05em",
            fontStyle: "italic",
            fontWeight: 700,
            lineHeight: 1,
            display: "inline-block",
            verticalAlign: "baseline",
          }}>woven</em>{" "}in.
        </h1>
        <p className="v2-subtitle text-center mt-5 max-w-[560px]"
          style={{ color: "#7B8FA3", fontSize: "clamp(14px, 1.55vw, 17px)", lineHeight: 1.55 }}>
          Businesses have thrived on data-driven decisions for decades.
          <br className="hidden md:block" />
          Your life deserves the same quiet intelligence.
        </p>
        <a href="sms:+16283586166"
          className="v2-cta-btn mt-7 inline-block px-8 py-3 rounded-full text-[14px] font-medium tracking-wide text-white transition-all duration-300 hover:scale-[1.05] active:scale-[0.97] pointer-events-auto"
          style={{ backgroundColor: "#3AAFD0", boxShadow: "0 4px 20px rgba(58,175,208,0.2)" }}>
          Request access
        </a>
      </div>

      {/* Image with depth parallax */}
      <div ref={imageRef} className="absolute overflow-hidden will-change-transform z-10"
        style={{ transformOrigin: "center 78%" }}>
        <div ref={imageZoomRef} className="w-full h-full will-change-transform">
          <DepthParallax className="w-full h-full" activeRef={depthActive} imageSet={HERO_IMAGE} />
        </div>
      </div>

      {/* Vignette */}
      <div ref={overlayRef} className="absolute inset-0 pointer-events-none"
        style={{ background: "radial-gradient(ellipse at 50% 45%, rgba(26,42,58,0.08) 0%, rgba(10,18,28,0.5) 100%)", zIndex: 15 }} />

      {/* Fullscreen text — particle headline + supporting body copy in a soft card */}
      <div ref={particleContainerRef}
        className="absolute inset-0 flex items-center justify-center px-6 pointer-events-none will-change-transform"
        style={{ zIndex: 25, perspective: "1200px", transformStyle: "preserve-3d" }}>
        <div
          className="max-w-[640px] w-full rounded-[20px] px-8 md:px-12 py-8 md:py-10 text-center"
          style={{
            backgroundColor: "rgba(26,42,58,0.42)",
            backdropFilter: "blur(14px)",
            border: "1px solid rgba(255,255,255,0.1)",
            boxShadow: "0 24px 60px rgba(10,18,28,0.25)",
            transformStyle: "preserve-3d",
          }}>
          <h2 ref={particleRef}
            className="text-white cursor-default"
            style={{ fontFamily: "var(--font-display)", fontSize: "clamp(28px, 4vw, 44px)", lineHeight: 1.2,
              transformStyle: "preserve-3d" }}>
            What can Juno do for you?
          </h2>
          <p
            className="v2-hero-body mt-4 mx-auto"
            style={{
              color: "rgba(255,255,255,0.86)",
              fontSize: "clamp(14px, 1.35vw, 17px)",
              lineHeight: 1.55,
              maxWidth: 520,
            }}>
            Juno lets you drop interactions anywhere — on your calendar,
            your docs, your whole desktop. And underneath it all, a living
            map of everything you&rsquo;re working on, shaped however makes
            sense to you.
          </p>
        </div>
      </div>

      {/* Left card — Study */}
      <div ref={card1Ref}
        className="absolute z-30 will-change-transform hidden md:block"
        style={{ left: "4%", top: "26%" }}>
        <HeroStudyCard />
      </div>

      {/* Right card — Wellness */}
      <div ref={card2Ref}
        className="absolute z-30 will-change-transform hidden md:block"
        style={{ right: "4%", top: "30%" }}>
        <HeroWellnessCard />
      </div>

      {/* Kept mounted so existing scroll timeline (card3Ref) doesn't null-deref */}
      <div ref={card3Ref} className="absolute hidden" aria-hidden="true" />
    </section>
  );
}

function HeroCardShell({ children }: { children: React.ReactNode }) {
  return (
    <div
      className="relative w-[230px] rounded-[16px]"
      style={{
        backgroundColor: "#FAFBFC",
        border: "1px solid rgba(58,175,208,0.14)",
        boxShadow: "0 18px 36px rgba(58,175,208,0.18), 0 4px 10px rgba(26,42,58,0.08)",
        padding: "16px 16px 14px",
      }}>
      {children}
    </div>
  );
}

function HeroStudyCard() {
  return (
    <div className="relative">
      <HeroCardShell>
        <div className="flex items-center justify-between">
          <span className="inline-flex items-center gap-1.5 rounded-full px-2 py-1"
            style={{ backgroundColor: "rgba(58,175,208,0.09)", color: "#5E7388", fontSize: 10, fontWeight: 500 }}>
            <span className="inline-flex items-center justify-center rounded-[4px]"
              style={{ width: 14, height: 14, backgroundColor: "#3AAFD0", color: "#fff", fontSize: 9, fontWeight: 700 }}>
              T
            </span>
            Study
          </span>
          <span style={{ color: "#AFBCCD", fontSize: 10 }}>2/05/22</span>
        </div>
        <p className="mt-2.5"
          style={{ color: "#3D4F5F", fontFamily: "var(--font-display)", fontSize: 14.5, lineHeight: 1.3 }}>
          Your notes are word-for-word copies of the lecture slides. Try rephrasing in your own words before Thursday&rsquo;s exam.
        </p>
        <p className="mt-2.5" style={{ color: "#9AA9BB", fontSize: 10 }}>
          Read more suggestions →
        </p>
      </HeroCardShell>
      {/* Mascot peeking from the card's bottom-right */}
      <div aria-hidden="true" className="absolute"
        style={{ right: -14, bottom: -14, transform: "rotate(12deg)" }}>
        <Image src="/images/juno-mascot.png" alt="" width={52} height={52}
          className="block pointer-events-none" />
      </div>
    </div>
  );
}

function HeroWellnessCard() {
  return (
    <div className="relative">
      {/* Mascot peeking from the card's left */}
      <div aria-hidden="true" className="absolute"
        style={{ left: -34, bottom: 18, transform: "rotate(-10deg)", zIndex: 0 }}>
        <Image src="/images/juno-mascot.png" alt="" width={64} height={64}
          className="block pointer-events-none" />
      </div>
      <HeroCardShell>
        <div className="flex items-center justify-between">
          <span className="inline-block rounded-full px-2 py-1"
            style={{ backgroundColor: "rgba(58,175,208,0.09)", color: "#5E7388", fontSize: 10, fontWeight: 500 }}>
            Wellness
          </span>
          <span style={{ color: "#AFBCCD", fontSize: 10 }}>4/12/30</span>
        </div>
        <p className="mt-2.5"
          style={{ color: "#3D4F5F", fontFamily: "var(--font-display)", fontSize: 14.5, lineHeight: 1.3 }}>
          Sleep is down 40 min this week. I cleared Tuesday morning and queued a playlist.
        </p>
        <p className="mt-2.5" style={{ color: "#9AA9BB", fontSize: 10 }}>
          See the full report →
        </p>
      </HeroCardShell>
    </div>
  );
}

