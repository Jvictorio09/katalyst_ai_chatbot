import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { VRM, VRMUtils, VRMLoaderPlugin, VRMExpressionPresetName } from '@pixiv/three-vrm';

let renderer: THREE.WebGLRenderer;
let scene: THREE.Scene;
let camera: THREE.PerspectiveCamera;
let clock = new THREE.Clock();

let vrm: VRM | null = null;
let raf = 0;

// idle micro-motion
let headYaw = 0;        // −1..1
let breathePhase = 0;   // radians

function addLights(s: THREE.Scene) {
  const hemi = new THREE.HemisphereLight(0xffffff, 0x334455, 1.0);
  const key  = new THREE.DirectionalLight(0xffffff, 2.0);
  key.position.set(1.2, 1.6, 1.2);
  const fill = new THREE.DirectionalLight(0xffffff, 0.6);
  fill.position.set(-1.2, 1.0, -0.8);
  const rim  = new THREE.DirectionalLight(0xffffff, 1.2);
  rim.position.set(0, 1.6, -1.4);
  s.add(hemi, key, fill, rim, new THREE.AmbientLight(0xffffff, 0.25));
}

export async function initAvatar(canvas: HTMLCanvasElement, vrmURL: string) {
  // renderer
  renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.setSize(canvas.clientWidth, canvas.clientHeight, false);
  renderer.outputColorSpace = THREE.SRGBColorSpace;

  // scene/camera
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(35, canvas.clientWidth / canvas.clientHeight, 0.1, 50);
  camera.position.set(0, 1.45, 2.1);
  addLights(scene);

  // loader with VRM plugin
  const loader = new GLTFLoader();
  loader.register(parser => new VRMLoaderPlugin(parser));

  const gltf = await loader.loadAsync(vrmURL);
  vrm = gltf.userData.vrm as VRM;

  // common optimizations
  VRMUtils.removeUnnecessaryJoints(vrm.scene);
  VRMUtils.removeUnnecessaryVertices(vrm.scene);

  // face the camera
  vrm.scene.rotation.y = Math.PI;

  // nice default look
  vrm.scene.traverse((o: any) => {
    if (o.isMesh) {
      o.castShadow = true;
      o.receiveShadow = true;
    }
  });

  scene.add(vrm.scene);

  // idle blink
  setInterval(() => blink(80), 3200);

  // keep aspect on resize
  const resize = () => {
    const { clientWidth: w, clientHeight: h } = canvas;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  };
  window.addEventListener('resize', resize);
  resize();

  animate();
}

function animate() {
  raf = requestAnimationFrame(animate);
  const dt = clock.getDelta();

  // idle micro-motion
  if (vrm) {
    // subtle head yaw
    headYaw += (Math.random() - 0.5) * 0.002;
    headYaw = THREE.MathUtils.clamp(headYaw, -0.04, 0.04);
    const head = vrm.humanoid?.getBoneNode('head');
    if (head) head.rotation.y = THREE.MathUtils.damp(head.rotation.y, headYaw, 6, dt);

    // breathing (chest scale)
    breathePhase += dt * 1.2;
    const chest = vrm.humanoid?.getBoneNode('chest');
    const s = 1 + Math.sin(breathePhase) * 0.015;
    if (chest) chest.scale.set(1, s, 1);
  }

  if (vrm) vrm.update(dt);
  renderer.render(scene, camera);
}

export function disposeAvatar() {
  cancelAnimationFrame(raf);
  if (vrm) {
    scene.remove(vrm.scene);
    vrm = null;
  }
  renderer?.dispose();
}

function setExpression(name: string, value: number) {
  if (!vrm?.expressionManager) return;
  const v = THREE.MathUtils.clamp(value, 0, 1);
  try { vrm.expressionManager.setValue(name as any, v); } catch {}
}

/** Primary mouth-open control: call 10–60 fps with 0..1 */
export function setMouthOpen(v: number) {
  // Map to common VRM phonemes. Many RPM/VRoid exports include "aa/ih/oh".
  setExpression('aa', v);
  setExpression('ih', v * 0.25);
  setExpression('oh', v * 0.5);
}

/** Blink once; ms = duration fully closed before reopening */
export function blink(ms = 80) {
  setExpression(VRMExpressionPresetName.Blink, 1);
  setTimeout(() => setExpression(VRMExpressionPresetName.Blink, 0), ms);
}

/** Optional: smile on positive sentiment, etc. */
export function setMoodHappy(v: number) {
  setExpression(VRMExpressionPresetName.Happy, v);
}

/** Smooth energy → mouth envelope (attack/decay) if you only have RMS */
let env = 0;
export function onEnergy(e: number) {
  const target = THREE.MathUtils.clamp(e, 0, 1);
  const attack = 0.5, release = 0.08;
  env = target > env ? env + (target - env) * attack : env + (target - env) * release;
  setMouthOpen(env);
}
