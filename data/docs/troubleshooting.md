# Troubleshooting

## App not loading / blank screen
1. Hard refresh the page (clear cache) or try an incognito window.
2. Disable browser extensions that block scripts or third-party cookies.
3. Confirm you are on a supported browser: latest Chrome, Firefox, Safari, or Edge.

## Login loops
- Clear site cookies for our domain, then sign in again.
- If using SSO, verify your IdP clock skew is under 5 minutes.

## Slow performance
- Check network latency and VPN; try a wired connection.
- Large exports run as background jobs; watch the Notifications panel for completion.
