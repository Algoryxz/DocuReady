export {};

declare global {
  interface Window {
    docureadyDesktop: {
      readonly platform: string;
      readonly version: string;
    };
  }
}
