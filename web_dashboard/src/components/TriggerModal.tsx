"use client";

import React, { useState } from "react";
import { Play, Loader2, X, Terminal } from "lucide-react";

export default function TriggerModal() {
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [resultMsg, setResultMsg] = useState("");

  const handleLaunch = async () => {
    setLoading(true);
    setResultMsg("");
    try {
      const res = await fetch("http://localhost:8000/api/system/pipelines/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pipeline_id: "all_active" })
      });
      const data = await res.json();
      if (data.status === "success") {
        setResultMsg(data.message);
      } else {
        setResultMsg("🚨 调度失败: " + data.message);
      }
    } catch (e) {
      setResultMsg("🚨 系统离线，Python API 失联。");
    }
    setLoading(false);
    
    // Auto-close after 3 seconds on success
    setTimeout(() => {
        setIsOpen(false);
        setResultMsg("");
    }, 4000);
  };

  return (
    <>
      <button 
        onClick={() => setIsOpen(true)}
        className="mt-8 bg-[#0a66c2] text-white w-full max-w-[230px] font-bold text-[15px] rounded-lg py-3 hover:bg-[#004182] transition-colors shadow-sm flex justify-center items-center gap-2"
      >
        🚀 手动并发唤醒 (Global Run)
      </button>

      {isOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-[0_12px_32px_rgba(0,0,0,0.2)] w-full max-w-md p-6 relative flex flex-col gap-4 animate-in fade-in zoom-in duration-200">
             
             <div className="flex items-center justify-between border-b border-[#dadce0] pb-3">
               <div className="flex items-center gap-2">
                 <Terminal size={20} className="text-[#0a66c2]"/>
                 <h2 className="text-lg font-bold text-gray-900">执行指令投递中心</h2>
               </div>
               <button onClick={() => setIsOpen(false)} className="text-gray-400 hover:text-gray-900">
                 <X size={20} />
               </button>
             </div>

             <div className="text-gray-600 text-[14px] leading-relaxed">
               您正在尝试向底层系统派发一枚 <strong className="text-red-500">全局热启动</strong> 信号！系统将读取 <code>pipelines.yaml</code> 的最新状态，拉起所有目前处于 [激活态] 的管线并立刻向外界终端（微信/小红书）投递稿件。
             </div>

             {resultMsg && (
                 <div className="bg-gray-100 p-3 rounded-lg border border-[#dadce0] font-mono text-xs text-green-700 break-all leading-normal">
                    {resultMsg}
                 </div>
             )}

             <div className="flex gap-3 justify-end mt-2">
               <button onClick={() => setIsOpen(false)} className="px-4 py-2 border border-[#dadce0] rounded-lg text-sm font-bold text-gray-700 hover:bg-[#f1f3f4]">
                 取消核武发射
               </button>
               <button 
                 onClick={handleLaunch}
                 disabled={loading}
                 className="flex items-center justify-center gap-2 px-5 py-2 rounded-lg text-sm font-bold bg-[#0a66c2] text-white hover:bg-[#004182] disabled:opacity-50"
               >
                 {loading ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} fill="white" />} 
                 {loading ? "引信熔断中..." : "立刻执行主程序"}
               </button>
             </div>
          </div>
        </div>
      )}
    </>
  );
}
