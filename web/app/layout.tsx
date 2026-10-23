import type { Metadata } from "next";
import { Archivo, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const archivo = Archivo({
  variable: "--font-archivo",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
});

const jetbrains = JetBrains_Mono({
  variable: "--font-jetbrains",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  title: "Drishti — Real-time vigilance, powered by foresight",
  description:
    "Real-time driver drowsiness and distraction monitoring. Ocular state, yawn cadence, head pose and phone use, analysed frame by frame.",
};

const themeScript = `
(function(){
  try {
    var stored = localStorage.getItem('drishti-theme');
    var dark = stored ? stored === 'dark'
      : window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (dark) document.documentElement.classList.add('dark');
  } catch (e) {}
})();
`;

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      {/* Extensions such as Liner can add attributes directly to body before hydration. */}
      <body suppressHydrationWarning className={`${archivo.variable} ${jetbrains.variable} antialiased`}>
        {children}
      </body>
    </html>
  );
}
