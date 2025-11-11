# Web Platform

## Overview
This directory contains web-specific build configurations and deployment guides.

## Prerequisites
- Node.js 18.0+
- npm 9.0+ or Yarn 1.22+
- Modern web browser (Chrome, Firefox, Safari, Edge)

## Getting Started
1. Install dependencies:
   ```bash
   npm install
   # or
   yarn install
   ```
2. Start development server:
   ```bash
   npm run dev
   # or
   yarn dev
   ```

## Building for Production
```bash
npm run build
# or
yarn build
```

## Testing
```bash
npm test
# or
yarn test
```

## Deployment
- Static hosting (Vercel, Netlify, GitHub Pages)
- Containerized (Dfile)
- Serverless (AWS Lambda, Cloudflare Workers)

## Platform Notes
- Progressive Web App (PWA) support
- Responsive design
- Service Worker for offline capabilities
- Environment-based configuration

## Browser Support
- Chrome (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- Edge (latest 2 versions)
- Mobile browsers (Chrome for Android, Safari on iOS)

## Performance
- Code splitting
- Lazy loading
- Asset optimization
- Bundle analysis

## Security
- CSP headers
- Security headers
- XSS protection
- CSRF tokens

## Troubleshooting
- Clear browser cache
- Check console for errors
- Verify environment variables
- Check network requests

## License
See main LICENSE file.
