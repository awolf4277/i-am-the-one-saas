# Security Policy

This repository contains proprietary software owned by Andrew Wolverton.

Do not commit:
- Admin passwords
- Owner passwords
- Secret keys
- API keys
- Render secrets
- Database dumps with real customer data
- Private client setup notes

Production rules:
- Keep the GitHub repository private or access-controlled.
- Store secrets only in Render environment variables.
- Do not expose owner/admin passwords in frontend code.
- Disable production source maps.
- Keep backend logic server-side.
- Use controlled demo access for owner/admin views.

Contact:
awolf4277@gmail.com
