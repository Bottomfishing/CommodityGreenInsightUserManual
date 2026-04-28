<template>
  <div class="globe-panel">
    <div class="globe-head">
      <div class="panel-title-row">
        <span class="panel-tag">GLOBE</span>
        <span class="panel-title">全球节点</span>
        <span class="panel-hint">（鼠标悬停即可获得各地区油价）</span>
      </div>
    </div>
    <div ref="canvasWrapRef" class="globe-canvas-wrap"></div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import * as THREE from "three";

const canvasWrapRef = ref<HTMLDivElement | null>(null);
let renderer: THREE.WebGLRenderer | null = null;
let scene: THREE.Scene | null = null;
let camera: THREE.PerspectiveCamera | null = null;
let globe: THREE.Mesh | null = null;
let atmosphere: THREE.Mesh | null = null;
let markerGroup: THREE.Group | null = null;
let rafId = 0;
let resizeObserver: ResizeObserver | null = null;

const markers = [
  { lat: 40.71, lng: -74.0 }, // 纽约
  { lat: 51.5, lng: -0.12 }, // 伦敦
  { lat: 39.9, lng: 116.4 }, // 北京
  { lat: 31.2, lng: 121.5 }, // 上海
  { lat: 35.68, lng: 139.76 }, // 东京
  { lat: 25.2, lng: 55.27 }, // 迪拜
];

function latLngToVector3(lat: number, lng: number, radius: number) {
  const phi = (90 - lat) * (Math.PI / 180);
  const theta = (lng + 180) * (Math.PI / 180);
  const x = -(radius * Math.sin(phi) * Math.cos(theta));
  const z = radius * Math.sin(phi) * Math.sin(theta);
  const y = radius * Math.cos(phi);
  return new THREE.Vector3(x, y, z);
}

function resizeRenderer() {
  if (!canvasWrapRef.value || !renderer || !camera) return;
  const { clientWidth, clientHeight } = canvasWrapRef.value;
  if (!clientWidth || !clientHeight) return;
  renderer.setSize(clientWidth, clientHeight, false);
  camera.aspect = clientWidth / clientHeight;
  camera.updateProjectionMatrix();
}

function animate() {
  if (!renderer || !scene || !camera || !globe || !atmosphere) return;
  globe.rotation.y += 0.0035;
  atmosphere.rotation.y += 0.0025;
  if (markerGroup) markerGroup.rotation.y += 0.0035;
  renderer.render(scene, camera);
  rafId = window.requestAnimationFrame(animate);
}

onMounted(() => {
  if (!canvasWrapRef.value) return;

  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(42, 1, 0.1, 1000);
  camera.position.set(0, 0, 4.6);

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  canvasWrapRef.value.appendChild(renderer.domElement);

  const ambientLight = new THREE.AmbientLight(0x67e8f9, 0.9);
  const pointLight = new THREE.PointLight(0x60a5fa, 1.2);
  pointLight.position.set(4, 3, 5);
  scene.add(ambientLight, pointLight);

  const globeGeometry = new THREE.SphereGeometry(1.15, 48, 48);
  const globeMaterial = new THREE.MeshStandardMaterial({
    color: 0x0a2244,
    emissive: 0x07152f,
    metalness: 0.3,
    roughness: 0.65,
    wireframe: false,
  });
  globe = new THREE.Mesh(globeGeometry, globeMaterial);
  scene.add(globe);

  const wire = new THREE.LineSegments(
    new THREE.WireframeGeometry(new THREE.SphereGeometry(1.16, 24, 24)),
    new THREE.LineBasicMaterial({ color: 0x22d3ee, transparent: true, opacity: 0.22 }),
  );
  scene.add(wire);

  atmosphere = new THREE.Mesh(
    new THREE.SphereGeometry(1.22, 48, 48),
    new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.12,
    }),
  );
  scene.add(atmosphere);

  markerGroup = new THREE.Group();
  const markerGeometry = new THREE.SphereGeometry(0.03, 12, 12);
  const markerMaterial = new THREE.MeshBasicMaterial({ color: 0xfbbf24 });
  markers.forEach((m) => {
    const point = new THREE.Mesh(markerGeometry, markerMaterial);
    point.position.copy(latLngToVector3(m.lat, m.lng, 1.18));
    markerGroup?.add(point);
  });
  scene.add(markerGroup);

  resizeRenderer();
  resizeObserver = new ResizeObserver(resizeRenderer);
  resizeObserver.observe(canvasWrapRef.value);
  animate();
});

onBeforeUnmount(() => {
  if (rafId) {
    cancelAnimationFrame(rafId);
    rafId = 0;
  }
  resizeObserver?.disconnect();
  resizeObserver = null;
  scene?.clear();
  renderer?.dispose();
  if (renderer?.domElement?.parentElement) {
    renderer.domElement.parentElement.removeChild(renderer.domElement);
  }
  renderer = null;
  scene = null;
  camera = null;
  globe = null;
  atmosphere = null;
  markerGroup = null;
});
</script>

<style scoped>
.globe-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 8px 10px 10px;
}

.globe-head {
  margin-bottom: 4px;
}

.panel-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.panel-hint {
  font-size: 11px;
  color: rgba(148, 163, 184, 0.9);
  letter-spacing: 0.02em;
  white-space: nowrap;
}

.globe-canvas-wrap {
  flex: 1;
  min-height: 180px;
  border: 1px solid rgba(56, 189, 248, 0.18);
  border-radius: 8px;
  background: radial-gradient(circle at 50% 50%, rgba(8, 47, 73, 0.2), rgba(2, 6, 23, 0.2));
  overflow: hidden;
}

.globe-canvas-wrap :deep(canvas) {
  width: 100% !important;
  height: 100% !important;
  display: block;
}
</style>
