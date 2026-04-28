"use client";

import { useEffect, useRef, useCallback } from "react";

const VERT = `
  attribute vec2 position;
  varying vec2 vUv;
  void main() {
    vUv = position * 0.5 + 0.5;
    gl_Position = vec4(position, 0.0, 1.0);
  }
`;

const FRAG = `
  precision highp float;
  uniform sampler2D uImage;
  uniform sampler2D uDepth;
  uniform sampler2D uImageNext;
  uniform sampler2D uDepthNext;
  uniform vec2 uMouse;
  uniform float uIntensity;
  uniform float uBlend;
  uniform vec2 uResolution;
  uniform vec2 uImageSize;
  uniform vec2 uImageSizeNext;
  uniform float uCoverY;
  varying vec2 vUv;

  vec2 coverUV(vec2 uv, vec2 res, vec2 imgSize) {
    float canvasAspect = res.x / res.y;
    float imageAspect  = imgSize.x / imgSize.y;
    vec2 c = uv;
    if (canvasAspect > imageAspect) {
      float s = canvasAspect / imageAspect;
      c.y = (uv.y - uCoverY) / s + uCoverY;
    } else {
      float s = imageAspect / canvasAspect;
      c.x = (uv.x - 0.5) / s + 0.5;
    }
    return clamp(c, 0.0, 1.0);
  }

  vec4 sampleWithDepth(sampler2D img, sampler2D dep, vec2 uv, vec2 res, vec2 imgSize) {
    vec2 cUv = coverUV(uv, res, imgSize);
    float depthRaw = texture2D(dep, cUv).r;
    float depth = pow(depthRaw, 0.6);
    float factor = (1.0 - depth) * uIntensity;
    vec2 offset = uMouse * factor;
    vec2 displaced = clamp(cUv + offset, 0.0, 1.0);
    return texture2D(img, displaced);
  }

  void main() {
    vec4 current = sampleWithDepth(uImage, uDepth, vUv, uResolution, uImageSize);
    if (uBlend > 0.001) {
      vec4 next = sampleWithDepth(uImageNext, uDepthNext, vUv, uResolution, uImageSizeNext);
      gl_FragColor = mix(current, next, uBlend);
    } else {
      gl_FragColor = current;
    }
  }
`;

export interface ImageSet {
  image: string;
  depth: string;
  width: number;
  height: number;
  pixelArt?: boolean;
}

interface Props {
  className?: string;
  style?: React.CSSProperties;
  activeRef?: React.RefObject<boolean>;
  imageSet: ImageSet;
}

export function DepthParallax({ className, style, activeRef, imageSet }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const mouseTarget = useRef({ x: 0, y: 0 });
  const mouseSmooth = useRef({ x: 0, y: 0 });
  const glRef = useRef<WebGLRenderingContext | null>(null);
  const textures = useRef<{
    img: WebGLTexture | null;
    dep: WebGLTexture | null;
    imgNext: WebGLTexture | null;
    depNext: WebGLTexture | null;
  }>({ img: null, dep: null, imgNext: null, depNext: null });
  const uniformsRef = useRef<Record<string, WebGLUniformLocation | null>>({});
  const blendRef = useRef(0);
  const blendTarget = useRef(0);
  const currentSetRef = useRef<ImageSet | null>(null);
  const imgSizeRef = useRef({ w: 1200, h: 800 });
  const imgSizeNextRef = useRef({ w: 1200, h: 800 });
  const readyRef = useRef(false);
  // Track last canvas size to avoid unnecessary resize (the black flash fix)
  const lastSizeRef = useRef({ w: 0, h: 0 });

  const loadTex = useCallback(
    (gl: WebGLRenderingContext, src: string, unit: number, nearest: boolean
    ): Promise<{ tex: WebGLTexture; w: number; h: number }> => {
      return new Promise((resolve) => {
        const img = new Image();
        img.onload = () => {
          const tex = gl.createTexture()!;
          gl.activeTexture(gl.TEXTURE0 + unit);
          gl.bindTexture(gl.TEXTURE_2D, tex);
          gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
          const filter = nearest ? gl.NEAREST : gl.LINEAR;
          gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, filter);
          gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, filter);
          gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
          gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
          resolve({ tex, w: img.naturalWidth, h: img.naturalHeight });
        };
        img.src = src;
      });
    }, []
  );

  // Hot-swap textures on imageSet change
  useEffect(() => {
    const gl = glRef.current;
    if (!gl || !readyRef.current) return;
    if (currentSetRef.current === imageSet) return;

    if (!currentSetRef.current) {
      currentSetRef.current = imageSet;
      Promise.all([
        loadTex(gl, imageSet.image, 0, imageSet.pixelArt !== false),
        loadTex(gl, imageSet.depth, 1, false),
      ]).then(([img, dep]) => {
        textures.current.img = img.tex;
        textures.current.dep = dep.tex;
        imgSizeRef.current = { w: imageSet.width, h: imageSet.height };
      });
      return;
    }

    currentSetRef.current = imageSet;
    blendTarget.current = 1;
    Promise.all([
      loadTex(gl, imageSet.image, 2, imageSet.pixelArt !== false),
      loadTex(gl, imageSet.depth, 3, false),
    ]).then(([img, dep]) => {
      textures.current.imgNext = img.tex;
      textures.current.depNext = dep.tex;
      imgSizeNextRef.current = { w: imageSet.width, h: imageSet.height };
    });
  }, [imageSet, loadTex]);

  // Init WebGL once
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const gl = canvas.getContext("webgl", {
      alpha: false, antialias: false, premultipliedAlpha: false,
      preserveDrawingBuffer: true, // prevents black flash on resize
    });
    if (!gl) return;
    glRef.current = gl;

    const vs = gl.createShader(gl.VERTEX_SHADER)!;
    gl.shaderSource(vs, VERT);
    gl.compileShader(vs);
    const fs = gl.createShader(gl.FRAGMENT_SHADER)!;
    gl.shaderSource(fs, FRAG);
    gl.compileShader(fs);
    const prog = gl.createProgram()!;
    gl.attachShader(prog, vs);
    gl.attachShader(prog, fs);
    gl.linkProgram(prog);
    gl.useProgram(prog);

    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
    const posLoc = gl.getAttribLocation(prog, "position");
    gl.enableVertexAttribArray(posLoc);
    gl.vertexAttribPointer(posLoc, 2, gl.FLOAT, false, 0, 0);

    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, 1);

    const u = (name: string) => gl.getUniformLocation(prog, name);
    uniformsRef.current = {
      uMouse: u("uMouse"), uIntensity: u("uIntensity"), uBlend: u("uBlend"),
      uImage: u("uImage"), uDepth: u("uDepth"),
      uImageNext: u("uImageNext"), uDepthNext: u("uDepthNext"),
      uResolution: u("uResolution"), uImageSize: u("uImageSize"),
      uImageSizeNext: u("uImageSizeNext"), uCoverY: u("uCoverY"),
    };

    // Load initial textures
    readyRef.current = true;
    const set = imageSet;
    currentSetRef.current = set;
    Promise.all([
      loadTex(gl, set.image, 0, set.pixelArt !== false),
      loadTex(gl, set.depth, 1, false),
    ]).then(([img, dep]) => {
      textures.current.img = img.tex;
      textures.current.dep = dep.tex;
      imgSizeRef.current = { w: set.width, h: set.height };
    });

    // Mouse
    const onMouse = (e: MouseEvent) => {
      mouseTarget.current.x = (e.clientX / window.innerWidth) * 2 - 1;
      mouseTarget.current.y = -((e.clientY / window.innerHeight) * 2 - 1);
    };
    window.addEventListener("mousemove", onMouse);

    // Render loop — resize is done HERE, same frame as draw (no black gap)
    let raf: number;
    let currentIntensity = 0;

    const render = () => {
      // --- Resize check (inline, not in a separate observer callback) ---
      const dpr = Math.min(window.devicePixelRatio, 2);
      const rect = canvas.getBoundingClientRect();
      const targetW = Math.round(rect.width * dpr);
      const targetH = Math.round(rect.height * dpr);

      if (targetW !== lastSizeRef.current.w || targetH !== lastSizeRef.current.h) {
        if (targetW > 0 && targetH > 0) {
          canvas.width = targetW;
          canvas.height = targetH;
          gl.viewport(0, 0, targetW, targetH);
          lastSizeRef.current = { w: targetW, h: targetH };
        }
      }

      // Smooth cursor
      mouseSmooth.current.x += (mouseTarget.current.x - mouseSmooth.current.x) * 0.03;
      mouseSmooth.current.y += (mouseTarget.current.y - mouseSmooth.current.y) * 0.03;

      // Smooth intensity ramp
      const targetIntensity = (activeRef?.current ?? true) ? 0.035 : 0;
      currentIntensity += (targetIntensity - currentIntensity) * 0.04;

      // Blend lerp for crossfade
      blendRef.current += (blendTarget.current - blendRef.current) * 0.045;

      // Promote next→current when blend is done
      if (blendRef.current > 0.98 && blendTarget.current === 1) {
        if (textures.current.img) gl.deleteTexture(textures.current.img);
        if (textures.current.dep) gl.deleteTexture(textures.current.dep);
        textures.current.img = textures.current.imgNext;
        textures.current.dep = textures.current.depNext;
        textures.current.imgNext = null;
        textures.current.depNext = null;
        imgSizeRef.current = { ...imgSizeNextRef.current };
        blendRef.current = 0;
        blendTarget.current = 0;
      }

      // --- Only draw when textures are loaded (prevents black frame) ---
      const t = textures.current;
      if (t.img && t.dep && targetW > 0 && targetH > 0) {
        gl.useProgram(prog);

        gl.activeTexture(gl.TEXTURE0);
        gl.bindTexture(gl.TEXTURE_2D, t.img);
        gl.uniform1i(uniformsRef.current.uImage, 0);

        gl.activeTexture(gl.TEXTURE1);
        gl.bindTexture(gl.TEXTURE_2D, t.dep);
        gl.uniform1i(uniformsRef.current.uDepth, 1);

        if (t.imgNext && t.depNext) {
          gl.activeTexture(gl.TEXTURE2);
          gl.bindTexture(gl.TEXTURE_2D, t.imgNext);
          gl.uniform1i(uniformsRef.current.uImageNext, 2);
          gl.activeTexture(gl.TEXTURE3);
          gl.bindTexture(gl.TEXTURE_2D, t.depNext);
          gl.uniform1i(uniformsRef.current.uDepthNext, 3);
        }

        gl.uniform2f(uniformsRef.current.uMouse!, mouseSmooth.current.x, mouseSmooth.current.y);
        gl.uniform1f(uniformsRef.current.uIntensity!, currentIntensity);
        gl.uniform1f(uniformsRef.current.uBlend!, blendRef.current);
        gl.uniform2f(uniformsRef.current.uResolution!, targetW, targetH);
        gl.uniform2f(uniformsRef.current.uImageSize!, imgSizeRef.current.w, imgSizeRef.current.h);
        gl.uniform2f(uniformsRef.current.uImageSizeNext!, imgSizeNextRef.current.w, imgSizeNextRef.current.h);
        gl.uniform1f(uniformsRef.current.uCoverY!, 0.52);

        gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      }

      raf = requestAnimationFrame(render);
    };
    raf = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("mousemove", onMouse);
      const tx = textures.current;
      if (tx.img) gl.deleteTexture(tx.img);
      if (tx.dep) gl.deleteTexture(tx.dep);
      if (tx.imgNext) gl.deleteTexture(tx.imgNext);
      if (tx.depNext) gl.deleteTexture(tx.depNext);
      gl.deleteBuffer(buf);
      gl.deleteProgram(prog);
      gl.deleteShader(vs);
      gl.deleteShader(fs);
      readyRef.current = false;
      glRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className={className}
      style={{ ...style, imageRendering: "auto" }}
    />
  );
}
