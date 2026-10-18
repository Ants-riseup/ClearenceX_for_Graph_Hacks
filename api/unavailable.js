// Replace the /api rewrite with the verified backend origin once provisioned.
// Until then, never return the SPA document as a successful API response.
export default function handler(_request, response) {
  response.setHeader('Cache-Control', 'no-store');
  response.setHeader('Retry-After', '300');
  response.status(503).json({
    detail: 'The hosted workspace is being configured. Sign-in and shipment processing will be available when the backend is connected.',
  });
}
