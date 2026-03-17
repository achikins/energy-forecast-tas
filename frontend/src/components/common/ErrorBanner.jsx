export default function ErrorBanner({ message, onRetry }) {
  return (
    <div className="error-banner">
      <span>⚠ {message}</span>
      {onRetry && (
        <button className="error-retry" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}
