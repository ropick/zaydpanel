# NusaHost - Shared Hosting Website

## Task Summary
Built a complete shared hosting business landing page website called "NusaHost" using Next.js 16, TypeScript, Tailwind CSS 4, and shadcn/ui components.

## Features Implemented

### Sections
1. **Navbar** - Responsive with mobile hamburger menu (Sheet), logo, navigation links, and CTA button
2. **Hero Section** - Animated gradient background, promotional badge, headline, dual CTA buttons, trust badges
3. **Stats Section** - 4 stat counters (2,500+ websites, 99.9% uptime, 1,800+ customers, 24/7 support)
4. **Features Section** - 8 feature cards with icons (Server, Security, LiteSpeed, Uptime, Server Location, Support, Backup, SSL)
5. **Pricing Section** - 3 packages (Starter Rp29.9K, Business Rp69.9K, Premium Rp149.9K) with feature lists and order modal
6. **FAQ Section** - 7 accordion items covering common hosting questions
7. **Contact Section** - WhatsApp, Email, Server Location, Payment Methods info cards + contact form
8. **Footer** - Brand info, 3 link columns (Layanan, Perusahaan, Legal), social media icons

### Backend
- Prisma schema with HostingOrder and ContactMessage models
- POST /api/order - Creates hosting orders with Zod validation
- POST /api/contact - Creates contact messages with Zod validation
- SQLite database for data persistence

### Design
- Dark theme with emerald/teal accent colors
- Framer Motion animations (fade-up, stagger, scroll-triggered)
- Fully responsive (mobile-first design)
- Professional hosting company aesthetic

## Tech Stack
- Next.js 16 (App Router), TypeScript, Tailwind CSS 4, shadcn/ui, Framer Motion, Prisma (SQLite), Zod
