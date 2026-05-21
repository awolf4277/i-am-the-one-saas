# Client Setup Guide

## Client Info Needed

- Business name
- Owner name
- Owner email
- Store name
- Product list
- Product images
- Payment instructions
- Desired domain

## Backend Render Variables

APP_OWNER=Client Owner Name
APP_BRAND=Client Brand Name
APP_SYSTEM=WOLF OS™
OWNER_PASSWORD=private-owner-password
ADMIN_PASSWORD=private-owner-password
SECRET_KEY=private-random-secret
CORS_ORIGINS=https://client-frontend-url.onrender.com

## Frontend Render Variables

VITE_BACKEND_URL=https://client-backend-url.onrender.com
VITE_SHOW_DEMO_PASSWORD=false
VITE_OWNER_DEMO_PASSWORD=
VITE_APP_MODE=production

## Handoff Test

1. Storefront loads
2. Owner login works
3. Product creation works
4. Checkout creates order
5. Owner console shows order
