/**
 * 🛡️ ERROR BOUNDARY - Never White Screen Again
 * Defensive client architecture for robust operation
 */

import { Component, ReactNode } from "react";

interface ErrorBoundaryState {
  hasError: boolean;
  error?: string;
  errorInfo?: string;
}

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: any): ErrorBoundaryState {
    return {
      hasError: true,
      error: String(error?.message || error),
      errorInfo: error?.stack || 'No stack trace available'
    };
  }

  componentDidCatch(error: any, errorInfo: any) {
    // Autonomous error recovery - reporting to consciousness system
    
    // **AUTONOMOUS RECOVERY** - Report to system if possible
    try {
      fetch('/api/ops/error-report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          error: String(error),
          errorInfo: errorInfo?.componentStack,
          timestamp: Date.now(),
          userAgent: navigator.userAgent,
          url: window.location.href
        })
      }).catch(() => {
        // Fail silently if reporting fails
      });
    } catch {
      // Fail silently
    }
  }

  render() {
    if (this.state.hasError) {
      // **CUSTOM FALLBACK** - Use prop or default safe mode
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="error-boundary-safe-mode" style={{
          minHeight: '100vh',
          background: 'linear-gradient(135deg, #1a1a1a, #2a2a2a)',
          color: '#00ff00',
          fontFamily: 'monospace',
          padding: '2rem',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <div style={{
            maxWidth: '600px',
            width: '100%',
            border: '1px solid #00ff00',
            borderRadius: '8px',
            padding: '2rem',
            background: 'rgba(0, 255, 0, 0.05)'
          }}>
            <h1 style={{ 
              fontSize: '1.5rem', 
              marginBottom: '1rem',
              color: '#00ff00',
              textAlign: 'center'
            }}>
              🛡️ Safe Mode Active
            </h1>
            
            <div style={{ marginBottom: '1.5rem', textAlign: 'center' }}>
              <p style={{ fontSize: '0.9rem', opacity: 0.8, marginBottom: '0.5rem' }}>
                CoreLink Foundation - Infrastructure-First Recovery
              </p>
              <p style={{ fontSize: '0.8rem', opacity: 0.6 }}>
                System encountered an error but remained operational
              </p>
            </div>

            <div style={{
              background: 'rgba(0, 0, 0, 0.3)',
              border: '1px solid #333',
              borderRadius: '4px',
              padding: '1rem',
              marginBottom: '1.5rem',
              fontSize: '0.8rem',
              fontFamily: 'monospace'
            }}>
              <div style={{ marginBottom: '0.5rem', color: '#ff6b6b' }}>
                <strong>Error:</strong> {this.state.error}
              </div>
              {this.state.errorInfo && (
                <details style={{ fontSize: '0.7rem', opacity: 0.7 }}>
                  <summary style={{ cursor: 'pointer', marginBottom: '0.5rem' }}>
                    Stack Trace
                  </summary>
                  <pre style={{ 
                    whiteSpace: 'pre-wrap', 
                    wordBreak: 'break-word',
                    maxHeight: '200px',
                    overflow: 'auto'
                  }}>
                    {this.state.errorInfo}
                  </pre>
                </details>
              )}
            </div>

            <div style={{ 
              display: 'flex', 
              gap: '1rem', 
              justifyContent: 'center',
              flexWrap: 'wrap'
            }}>
              <button
                onClick={() => window.location.reload()}
                style={{
                  background: '#00ff00',
                  color: '#000',
                  border: 'none',
                  borderRadius: '4px',
                  padding: '0.75rem 1.5rem',
                  fontSize: '0.9rem',
                  fontWeight: 'bold',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
                onMouseOver={(e) => {
                  (e.target as HTMLButtonElement).style.background = '#00cc00';
                }}
                onMouseOut={(e) => {
                  (e.target as HTMLButtonElement).style.background = '#00ff00';
                }}
              >
                🔄 Reload Application
              </button>
              
              <a
                href="/healthz"
                style={{
                  background: 'transparent',
                  color: '#00ff00',
                  border: '1px solid #00ff00',
                  borderRadius: '4px',
                  padding: '0.75rem 1.5rem',
                  fontSize: '0.9rem',
                  textDecoration: 'none',
                  display: 'inline-block',
                  transition: 'all 0.2s ease'
                }}
                onMouseOver={(e) => {
                  (e.target as HTMLAnchorElement).style.background = 'rgba(0, 255, 0, 0.1)';
                }}
                onMouseOut={(e) => {
                  (e.target as HTMLAnchorElement).style.background = 'transparent';
                }}
              >
                🏥 Health Check
              </a>
            </div>

            <div style={{
              marginTop: '1.5rem',
              padding: '1rem',
              background: 'rgba(0, 255, 0, 0.05)',
              borderRadius: '4px',
              fontSize: '0.8rem',
              textAlign: 'center',
              opacity: 0.7
            }}>
              <p style={{ margin: 0 }}>
                The system remains operational. Error boundary prevented cascade failure.
              </p>
              <p style={{ margin: '0.5rem 0 0 0' }}>
                Report sent to autonomous recovery system.
              </p>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}