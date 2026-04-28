"use client";

import { useEffect } from "react";
import { ScrollTrigger } from "@/lib/gsap";
import { SmoothScroll } from "@/components/smooth-scroll";
import { V2Header } from "./v2-header";
import { V2Hero } from "./v2-hero";
import { V2Features } from "./v2-features";
import { V2Integrations } from "./v2-integrations";
import { V2CTA } from "./v2-cta";
import { V2Footer } from "./v2-footer";

export function V2Page() {
  useEffect(() => {
    // Apply beige theme
    document.body.style.backgroundColor = "#F5F6F7";
    document.body.style.color = "#3D4F5F";

    const raf = requestAnimationFrame(() => {
      ScrollTrigger.refresh();
    });

    return () => {
      cancelAnimationFrame(raf);
      document.body.style.backgroundColor = "";
      document.body.style.color = "";
    };
  }, []);

  return (
    <>
      <SmoothScroll />
      <V2Header />
      <main className="flex-1">
        <V2Hero />
        <V2Features />
        <V2Integrations />
        <V2CTA />
      </main>
      <V2Footer />
    </>
  );
}
