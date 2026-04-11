import type { Metadata } from "next";
import "./globals.css";
import React from "react";
import Link from "next/link";
import { Database, Bell, LayoutList, CheckSquare, Settings, Play, Search, Info, LayoutTemplate, Palette } from "lucide-react";

export const metadata: Metadata = {
  title: "Media Query Console",
  description: "Data Source Management Console",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-[var(--app-bg)] text-[var(--app-text)] min-h-screen antialiased flex justify-center font-sans tracking-tight">
        
        {/* Left Sidebar - Navigation */}
        <header className="w-[280px] h-screen sticky top-0 flex flex-col items-start px-4 py-4 border-r border-[var(--app-border)]">
          
          <div className="w-12 h-12 flex flex-shrink-0 items-center justify-center rounded-full hover:bg-[var(--app-hover)] cursor-pointer mb-6 transition-colors">
            {/* Logo placeholder - using an X-like shape as in the screenshot */}
            <svg viewBox="0 0 24 24" aria-hidden="true" className="w-8 h-8 fill-black">
              <g><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.008 5.96H5.078z"></path></g>
            </svg>
          </div>

          <nav className="flex flex-col w-full gap-2 relative">
            {[
              { label: "管线管理", icon: <Database size={24} />, href: "/" },
              { label: "执行历史", icon: <LayoutList size={24} />, href: "/history" },
              { label: "未读采集", icon: <Bell size={24} />, href: "#" },
              { label: "审核与发布", icon: <CheckSquare size={24} />, href: "/drafts" },
              { label: "系统设置", icon: <Settings size={24} />, href: "/settings" },
            ].map((item) => (
              <Link href={item.href} key={item.label} className={`flex items-center gap-4 w-fit rounded-full px-5 py-3 cursor-pointer transition-colors duration-200 hover:bg-[var(--app-hover)]`}>
                <div className="text-gray-700">{item.icon}</div>
                <span className="text-xl tracking-wide">{item.label}</span>
              </Link>
            ))}
          </nav>

          {/* Profile Section */}
          <div className="mt-auto mb-4 flex items-center gap-3 hover:bg-[var(--app-hover)] p-3 rounded-full cursor-pointer w-[250px] transition-colors">
            <div className="w-10 h-10 bg-[var(--app-blue)] rounded-full flex items-center justify-center text-white font-bold flex-shrink-0">
              MQ
            </div>
            <div className="flex flex-col overflow-hidden">
              <span className="font-bold text-[15px] truncate">Media Query</span>
              <span className="text-[var(--app-gray)] text-[15px] truncate">@console</span>
            </div>
            <div className="ml-auto text-xl text-[var(--app-gray)]">...</div>
          </div>
        </header>

        {/* Main Content Area (Data Source Management) */}
        <main className="flex-1 w-full min-h-screen bg-white relative">
          {children}
        </main>

        {/* Right Sidebar - System Tools (Removed per PM architecture plan) */}

      </body>
    </html>
  );
}
