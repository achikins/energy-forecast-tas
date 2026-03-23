/**
 * WakeBanner — explains the Render free-tier cold start delay.
 * Only visible after 3s of loading; disappears once data arrives.
 */

export default function WakeBanner() {
  return (
    <div className="wake-banner">
      <div className="wake-banner-spinner" />
      <div>
        <div className="wake-banner-title">Waking up the server…</div>
        <div className="wake-banner-body">
          The API is hosted on Render's free tier, which spins down after inactivity.
          First load takes up to 60 seconds — hang tight.
        </div>
      </div>
    </div>
  );
}
