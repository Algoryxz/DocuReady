import { DocuReadyBridge } from "../shared/types";

export {};

declare global {
  interface Window {
    docureadyDesktop: DocuReadyBridge;
  }
}
