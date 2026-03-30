"use client";

import React, { useState, useEffect, Suspense } from "react";
import { Save, FileText, ArrowLeft, Loader2 } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

function SettingsEditor() {
  const searchParams = useSearchParams();
  const defaultPrompt = searchParams.get('prompt') || "xhs_style_a_lilian.md";
  
  const [activePrompt, setActivePrompt] = useState(defaultPrompt);
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const fetchPrompt = async (filename: string) => {
    setLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/api/system/prompts/${filename}`);
      const data = await res.json();
      if (data.status === "success") {
        setContent(data.content);
      } else {
        setContent("Failed to load prompt. Extracted file may be missing.");
      }
    } catch (e) {
      setContent("Network Error. Ensure python api_server.py is running.");
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchPrompt(activePrompt);
  }, [activePrompt]);

  const savePrompt = async () => {
    setSaving(true);
    try {
      const res = await fetch(`http://localhost:8000/api/system/prompts/${activePrompt}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: content })
      });
      const data = await res.json();
      if (data.status === "success") {
        alert("🎉" + data.message + "\n下一次抓取将采用全新的人设配置！");
      } else {
        alert("Failed to save: " + data.message);
      }
    } catch (e) {
      alert("Network Error");
    }
    setSaving(false);
  };

  const promptsList = [
    { filename: "xhs_style_a_lilian.md", label: "小红书生成人设 (Lilian聊AI)" },
    { filename: "org_chart_analysis.md", label: "AI 技术高管架构分析" },
    { filename: "solopreneur_insight.md", label: "一人公司模式洞察" },
    { filename: "finance_hardcore_report.md", label: "硬核金融分析" },
    { filename: "filter_priority.md", label: "全局热点新闻挑选标准评判" }
  ];

  return (
    <div className="flex flex-col w-full min-h-screen bg-[#f8f9fa] relative pb-20 overflow-hidden">
      
      {/* Top Header */}
      <div className="flex justify-between items-center px-6 py-4 border-b border-[#dadce0] sticky top-0 bg-white z-20">
        <div className="flex items-center gap-4">
          <Link href="/">
             <ArrowLeft size={20} className="text-gray-500 hover:text-[#0a66c2] cursor-pointer transition-colors" />
          </Link>
          <h1 className="text-[20px] font-bold text-gray-900 tracking-tight">人设大脑调音台 (Prompt Editor)</h1>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden h-[calc(100vh-68px)]">
        {/* Left Sidebar for Prompts */}
        <div className="w-[280px] border-r border-[#dadce0] bg-white flex flex-col p-4 gap-2 shrink-0 h-full overflow-y-auto">
          <h3 className="text-[11px] font-bold text-gray-500 mb-2 uppercase tracking-wider">System Templates</h3>
          
          {promptsList.map((p) => (
             <div 
               key={p.filename}
               onClick={() => setActivePrompt(p.filename)}
               className={`flex items-start gap-3 p-3 rounded-lg cursor-pointer transition-all border ${activePrompt === p.filename ? "bg-[#f0f7ff] border-[#c2d7f0] shadow-sm" : "border-transparent hover:bg-[#f1f3f4]"}`}
             >
               <FileText size={18} className={activePrompt === p.filename ? "text-[#0a66c2] mt-0.5" : "text-gray-400 mt-0.5"} />
               <div className="flex flex-col">
                 <span className={`text-sm font-medium ${activePrompt === p.filename ? "text-[#0a66c2]" : "text-gray-700"}`}>{p.label}</span>
                 <span className="text-[11px] text-gray-400 font-mono mt-0.5 pr-2 truncate">{p.filename}</span>
               </div>
             </div>
          ))}
        </div>

        {/* Main Editor */}
        <div className="flex-1 flex flex-col bg-white">
           <div className="h-14 border-b border-[#dadce0] flex items-center justify-between px-6 shrink-0 bg-[#f8f9fa] sticky top-0">
              <div className="flex items-center gap-2">
                 <span className="text-xs font-mono text-gray-600 bg-white border border-[#dadce0] px-3 py-1 rounded-md shadow-sm">~/{activePrompt}</span>
              </div>
              <button 
                onClick={savePrompt}
                disabled={saving || loading}
                className="flex items-center justify-center gap-1.5 px-4 py-1.5 rounded-lg text-sm font-medium transition-all bg-[#0a66c2] text-white hover:bg-[#004182] disabled:opacity-50 shadow-sm"
              >
                {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />} 
                {saving ? "正在写入..." : "保存覆写"}
              </button>
           </div>
           
           <div className="flex-1 p-6 relative bg-white">
              {loading && <div className="absolute inset-0 bg-white/80 z-10 flex items-center justify-center"><Loader2 className="animate-spin text-[#0a66c2]" size={32} /></div>}
              <textarea 
                value={content}
                onChange={(e) => setContent(e.target.value)}
                className="w-full h-full p-6 border border-[#dadce0] rounded-xl focus:outline-none focus:ring-1 focus:ring-[#0a66c2] focus:border-[#0a66c2] font-mono text-[14px] leading-relaxed resize-none bg-white text-gray-800"
                spellCheck={false}
              />
           </div>
        </div>
      </div>
    </div>
  );
}

export default function SettingsPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <SettingsEditor />
    </Suspense>
  );
}
