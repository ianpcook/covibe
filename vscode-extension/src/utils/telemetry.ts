import * as vscode from 'vscode';

export class ActivationTelemetry {
  private extensionId: string;
  private extensionVersion: string;

  constructor(context: vscode.ExtensionContext) {
    const packageJson = context.extension.packageJSON;
    this.extensionId = packageJson.name;
    this.extensionVersion = packageJson.version;
  }

  async reportActivation(): Promise<void> {
    // Only report if telemetry is enabled
    if (!vscode.env.isTelemetryEnabled) {
      return;
    }

    // For MVP, we'll just log activation
    // In production, this would send to telemetry service
    console.log(`Extension activated: ${this.extensionId} v${this.extensionVersion}`);
    console.log(`VS Code version: ${vscode.version}`);
    console.log(`Platform: ${process.platform}`);
  }

  reportCommand(command: string, properties?: Record<string, string>): void {
    if (!vscode.env.isTelemetryEnabled) {
      return;
    }

    console.log(`Command executed: ${command}`, properties);
  }

  reportError(error: Error, context?: string): void {
    console.error(`Error in ${context || 'unknown context'}:`, error);
  }
}