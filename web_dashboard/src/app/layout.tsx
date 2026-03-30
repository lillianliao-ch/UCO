import type { Metadata } from "next";
import "./globals.css";
import React from "react";
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
              { label: "数据源管理", icon: <Database size={24} />, active: true },
              { label: "未读采集", icon: <Bell size={24} />, active: false },
              { label: "私有 Timeline", icon: <LayoutList size={24} />, active: false },
              { label: "审核与发布", icon: <CheckSquare size={24} />, active: false },
              { label: "系统设置", icon: <Settings size={24} />, active: false },
            ].map((item) => (
              <div key={item.label} className={`flex items-center gap-4 w-fit rounded-full px-5 py-3 cursor-pointer transition-colors duration-200 ${item.active ? 'font-bold' : 'hover:bg-[var(--app-hover)]'}`}>
                <div className={item.active ? 'text-black' : 'text-gray-700'}>{item.icon}</div>
                <span className="text-xl tracking-wide">{item.label}</span>
              </div>
            ))}
          </nav>

          <button className="mt-8 bg-[var(--app-blue)] text-white w-full max-w-[230px] font-bold text-lg rounded-full py-4 hover:bg-[var(--app-blue-hover)] transition-colors shadow-md flex justify-center items-center gap-2">
            开始了，采集 <Play size={18} className="fill-white" />
          </button>
          
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
        <main className="flex-1 w-full max-w-[700px] min-h-screen border-r border-[var(--app-border)] bg-white relative">
          {children}
        </main>

        {/* Right Sidebar - System Tools */}
        <aside className="w-[350px] pl-8 py-4 sticky top-0 h-screen overflow-y-auto hidden lg:block bg-white">
          
          <div className="bg-[var(--app-bg)] mb-6 z-10 sticky top-0 border border-transparent">
            <div className="bg-[var(--app-gray-light)] flex items-center gap-3 px-4 py-3 rounded-full border border-[var(--app-border)] focus-within:border-[var(--app-blue)] focus-within:bg-white transition-colors shadow-sm">
              <Search className="text-[var(--app-gray)]" size={18} />
              <input 
                type="text" 
                placeholder="Search Console" 
                className="bg-transparent text-black outline-none w-full placeholder-[var(--app-gray)] text-sm"
              />
            </div>
          </div>
          
          {/* Action Tips Card */}
          <div className="bg-[var(--app-gray-light)] rounded-2xl p-4 mt-2 border border-[var(--app-border)]">
            <div className="flex items-center gap-2 mb-3">
              <Info size={20} className="text-black" />
              <h2 className="text-lg font-bold">操作提示</h2>
            </div>
            <div className="text-[sm] text-[var(--app-gray)] flex flex-col gap-2">
              <p>默认 dry-run，不会真实发布。</p>
              <p>会话失效会触发登录提醒。</p>
            </div>
          </div>

          {/* Module Mapping Preview */}
          <div className="bg-[var(--app-gray-light)] rounded-2xl p-4 mt-4 border border-[var(--app-border)]">
            <div className="flex items-center gap-2 mb-3">
              <LayoutTemplate size={20} className="text-black" />
              <h2 className="text-lg font-bold">模块映射预览</h2>
            </div>
            <div className="flex flex-col gap-4">
              <div>
                <span className="text-[13px] text-[var(--app-gray)] block mb-1">主导航</span>
                <span className="font-bold text-[15px]">Left Rail / Home Nav</span>
              </div>
              <div>
                <span className="text-[13px] text-[var(--app-gray)] block mb-1">主内容区</span>
                <span className="font-bold text-[15px]">Center Timeline Column</span>
              </div>
              <div>
                <span className="text-[13px] text-[var(--app-gray)] block mb-1">辅助栏</span>
                <span className="font-bold text-[15px]">Right Sidebar Cards</span>
              </div>
            </div>
          </div>

          {/* Theme Mode */}
          <div className="bg-[var(--app-gray-light)] rounded-2xl p-4 mt-4 border border-[var(--app-border)]">
            <div className="flex items-center gap-2 mb-3">
              <Palette size={20} className="text-black" />
              <h2 className="text-lg font-bold">主题模式</h2>
            </div>
            <p className="text-[14px] text-[var(--app-gray)] flex items-center gap-2">
               手动模式 - 当前亮色 <span className="w-2 h-2 rounded-full bg-yellow-400 inline-block"></span>
            </p>
          </div>

        </aside>

      </body>
    </html>
  );
}
