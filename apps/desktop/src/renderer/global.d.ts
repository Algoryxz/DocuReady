export {};

declare global {
  interface Window {
    docureadyDesktop: {
      readonly platform: string;
      getVersion(): string;
    };
  }
}
