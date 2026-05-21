import React from "react";

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback ?? (
        <section className="terminal-card error-panel" style={{ margin: 18 }}>
          <p className="eyebrow">Render Error</p>
          <h2>A component crashed</h2>
          <p>{this.state.error?.message ?? "Unknown error"}</p>
        </section>
      );
    }
    return this.props.children;
  }
}
