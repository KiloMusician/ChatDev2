// Mobile/Desktop Device Detection & Responsive Utils
// Zero-token implementation for viewport and pointer detection

export interface DeviceInfo {
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  hasTouch: boolean;
  viewportWidth: number;
  viewportHeight: number;
  pixelRatio: number;
}

export function detectDevice(): DeviceInfo {
  const width = window.innerWidth;
  const height = window.innerHeight;
  
  return {
    isMobile: width <= 768,
    isTablet: width > 768 && width <= 1024,
    isDesktop: width > 1024,
    hasTouch: 'ontouchstart' in window,
    viewportWidth: width,
    viewportHeight: height,
    pixelRatio: window.devicePixelRatio || 1,
  };
}

export function setCSSVariables(device: DeviceInfo) {
  const root = document.documentElement;
  root.style.setProperty('--viewport-width', `${device.viewportWidth}px`);
  root.style.setProperty('--viewport-height', `${device.viewportHeight}px`);
  root.style.setProperty('--is-mobile', device.isMobile ? '1' : '0');
  root.style.setProperty('--is-touch', device.hasTouch ? '1' : '0');
}

export function initDeviceDetection() {
  const updateDevice = () => {
    const device = detectDevice();
    setCSSVariables(device);
    return device;
  };
  
  // Initial detection
  updateDevice();
  
  // Update on resize
  window.addEventListener('resize', updateDevice);
  
  return updateDevice;
}