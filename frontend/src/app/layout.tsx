import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = { title: 'Commander | Euro-Afro Elite', description: 'Private placement intelligence and concierge operations.' };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
