import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
// import SpinningGlobe from "../components/SpinningGlobe";


const inter = Inter({ subsets: ["latin"] });

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-midjourney_navy text-white flex flex-col min-h-screen`}>
      <header className="bg-midjourney_navy w-full flex-shrink-0" style={{ height: '40px' }}>
          <div className="w-full h-full">&nbsp;</div>
      </header>
      <main>{children}</main>
      </body>
    </html>
  );
}