import { Component } from 'react';
import { AlertTriangle } from 'lucide-react';

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  render() {
    if (!this.state.hasError) return this.props.children;

    return (
      <div className="error-boundary glass-panel">
        <AlertTriangle size={20} className="text-accent-amber" />
        <div>
          <div className="font-bold">{this.props.label || 'This panel failed to load.'}</div>
          <p className="text-sm text-muted m-0">Refresh the page or switch tabs while the latest data catches up.</p>
        </div>
      </div>
    );
  }
}
