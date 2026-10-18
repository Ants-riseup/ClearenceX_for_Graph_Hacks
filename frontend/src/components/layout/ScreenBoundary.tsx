import { Component, type ReactNode } from 'react';

export class ScreenBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };

  static getDerivedStateFromError() { return { failed: true }; }

  render() {
    if (this.state.failed) return <section role="alert" className="max-w-xl mx-auto p-8 space-y-4">
      <h1 className="text-2xl font-bold">This screen could not load</h1>
      <p>The application may have been updated. Refresh to load the current version. Your saved dossiers remain available.</p>
      <button onClick={() => window.location.reload()} className="bg-primary text-white rounded-lg px-4 py-3">Refresh application</button>
    </section>;
    return this.props.children;
  }
}
