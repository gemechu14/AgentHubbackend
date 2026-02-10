This is the **AgentHub** frontend, built with [Next.js](https://nextjs.org) App Router, TypeScript, and Tailwind CSS.

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the main dashboard by modifying `app/page.tsx`. The page auto-updates as you edit the file.

## API configuration

All data fetching goes through a small API client in `services/` using a configurable `BASE_API_URL` defined in `lib/config.ts`.

- The default value is the local mock API: `/api/mock`.
- To point the app at a real backend, set:

```bash
export NEXT_PUBLIC_API_BASE_URL="https://api.agenthub.com"
```

No component changes are required; only this environment variable (or the constant in `lib/config.ts`) needs to be updated.

