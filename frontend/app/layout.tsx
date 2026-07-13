import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "No-Code Data Intelligence",
  description: "Transformer vos données en décisions",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;600&family=Roboto:wght@300;400;500&family=Roboto+Mono&display=swap"
          rel="stylesheet"
        />
      </head>
      <body suppressHydrationWarning style={{ background: "#131314", color: "#e3e3e3", fontFamily: "'Roboto', sans-serif" }}>
        {children}
      </body>
    </html>
  );
}