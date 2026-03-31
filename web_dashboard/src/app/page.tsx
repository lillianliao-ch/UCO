"use client";

import React, { useState, useEffect } from "react";
import { RefreshCw, GitMerge, FileText, Send, EyeOff, Settings2, X, Save, Settings, ExternalLink } from "lucide-react";

export default function PipelinesPage() {
  const [pipelines, setPipelines] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Edit Modal State
  const [editingPipeline, setEditingPipeline] = useState<any | null>(null);

  const fetchPipelines = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/system/pipelines");
      const data = await res.json();
      if (data.status === "success" && data.data && data.data.pipelines) {
        setPipelines(data.data.pipelines);
      } else {
        setPipelines([]);
      }
    } catch (e) {
      console.error(e);
      alert("Failed to connect to Python api_server.py.");
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchPipelines();
  }, []);

  const togglePipeline = async (id: string, currentStatus: boolean) => {
    try {
      setPipelines(prev => prev.map(p => p.id === id ? { ...p, active: !currentStatus } : p));
      const res = await fetch("http://localhost:8000/api/system/pipelines", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id, active: !currentStatus })
      });
      const data = await res.json();
      if (data.status !== "success") {
        alert("写入失败");
        fetchPipelines();
      }
    } catch (e) {
      alert("网络断开");
      fetchPipelines();
    }
  };

  const handleEditSubmit = async () => {
    if (!editingPipeline) return;
    try {
      const res = await fetch(`http://localhost:8000/api/system/pipelines/${editingPipeline.id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(editingPipeline)
      });
      const data = await res.json();
      if (data.status === "success") {
        alert("✅ 管线配置保存成功！");
        setEditingPipeline(null);
        fetchPipelines();
      } else {
        alert("保存失败: " + data.message);
      }
    } catch (e) {
      alert("网络错误无法保存");
    }
  };

  // Mappings for User-Friendly source names
  const SOURCE_MAP: Record<string, { label: string, desc: string }> = {
    // TrendRadar MCP
    "tr_baidu": { label: "📈 百度热点 (TrendRadar)", desc: "追踪国内全网突发与宏观头条" },
    "tr_weibo": { label: "🔥 微博热搜 (TrendRadar)", desc: "追踪全网热议、发酵与突发事件" },
    "tr_zhihu": { label: "🎓 知乎热榜 (TrendRadar)", desc: "深度吃瓜、硬核科技争议与行业知识点" },
    "tr_wallstreetcn-hot": { label: "💵 华尔街见闻 (TrendRadar)", desc: "国内顶级的二级市场、财报与宏观经济风暴圈" },
    "tr_bilibili-hot-search": { label: "📺 B站热搜 (TrendRadar)", desc: "年轻态现象级爆点与数码/AI大UP主动态" },
    "tr_toutiao": { label: "📰 今日头条 (TrendRadar)", desc: "下沉与全民级泛社会焦点事件" },
    
    // Chinese RSS
    "rss_36kr": { label: "💰 36Kr (中国创投情报)", desc: "本土 A/B 轮私募、创业风口首发" },
    "rss_tmtpost": { label: "🚀 钛媒体 (TMTPost商业化)", desc: "AI 变现、国内商战、核心高层人事变动" },
    "rss_jiqizhixin": { label: "🤖 机器之心", desc: "AI 前沿技术、大佬离职与大厂重组" },
    "rss_geekpark": { label: "🛸 极客公园", desc: "国产 AI 消费级产品与创客生态" },
    
    // Global RSS
    "rss_techcrunch": { label: "💸 TechCrunch AI", desc: "硅谷最强风投资本局、A轮初创团队 BD" },
    "rss_wsj": { label: "📰 WSJ 华尔街科技金融", desc: "硅谷巨头大单、M&A与美股大事件" },
    "rss_hackernews": { label: "👨‍💻 HackerNews", desc: "独立极客、技术开源、隐秘大牛离职动态" },
    "rss_producthunt": { label: "💡 ProductHunt", desc: "每日海外独立黑客产品发榜打新" },
    
    // Advanced/Misc
    "live_footprint_source": { label: "🌐 绝密足迹监控 (DuckDuckGo)", desc: "免密全网人物历史足迹动态扫描" }
  };

  const PUB_MAP: Record<string, string> = {
    "xiaohongshu": "小红书矩阵 (自动图文)",
    "wechat_official": "微信公众号 (草稿箱)",
    "telegram_log": "Telegram (您的私人审查群)",
    "feishu_webhook": "飞书工作台 (猎头/交付端点)"
  };

  // Group definitions for UI
  const SOURCE_GROUPS: Record<string, string[]> = {
    "📊 TrendRadar 实况舆情": ["tr_baidu", "tr_weibo", "tr_bilibili-hot-search", "tr_zhihu", "tr_toutiao", "tr_wallstreetcn-hot"],
    "🇨🇳 本土创投与商业媒体": ["rss_36kr", "rss_tmtpost", "rss_jiqizhixin", "rss_geekpark"],
    "🌐 硅谷大厂与极客风投": ["rss_techcrunch", "rss_wsj", "rss_hackernews", "rss_producthunt"],
    "🔒 追踪与审查引擎": ["live_footprint_source"]
  };

  const AVAILABLE_PUBLISHERS = Object.keys(PUB_MAP);

  // Utility to handle array toggling
  const toggleArrayItem = (arrayName: string, item: string) => {
    setEditingPipeline((prev: any) => {
      const currentArray = prev[arrayName] || [];
      const newArray = currentArray.includes(item) 
        ? currentArray.filter((i: string) => i !== item)
        : [...currentArray, item];
      return { ...prev, [arrayName]: newArray };
    });
  };

  return (
    <div className="flex flex-col w-full min-h-screen bg-[#f8f9fa] relative pb-20 font-sans">
      {/* Top Header */}
      <div className="flex justify-between items-center px-6 py-4 border-b border-[#dadce0] sticky top-0 bg-white z-20 shadow-sm">
        <h1 className="text-[20px] font-semibold text-gray-900">管线编排面板 (Orchestration Hub)</h1>
      </div>

      <div className="p-8 w-full max-w-[1240px] mx-auto">
        <div className="flex justify-between items-end mb-8">
          <div>
            <h2 className="text-[24px] font-semibold text-gray-900 leading-tight">调度管线清单</h2>
            <p className="text-gray-500 text-sm mt-1">独立人设、并发抓取。如需配置频道内参数，请点击“精细化配置”。</p>
          </div>
          <button onClick={fetchPipelines} className="flex items-center justify-center gap-1.5 px-4 py-2 border rounded-lg text-sm font-medium transition-all bg-[#0a66c2] border-[#0a66c2] text-white hover:bg-[#004182] shadow-sm">
             刷新底层配置 <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          </button>
        </div>

        {loading ? (
          <div className="w-full py-32 flex flex-col items-center justify-center text-gray-400 gap-4">
             <RefreshCw className="animate-spin text-[#0a66c2]" size={32} />
             <span className="font-medium">正在读取管线架构网络...</span>
          </div>
        ) : (
          <div className="flex flex-col gap-6">
            {pipelines.map(p => (
              <div key={p.id} className={`bg-white border rounded-xl p-5 transition-all relative group ${p.active ? 'border-[#dadce0] shadow-sm' : 'border-[#dadce0] opacity-60 bg-[#f8f9fa]'}`}>
                
                {/* Header row */}
                <div className="flex justify-between items-start mb-6">
                  <div className="flex flex-col gap-1">
                     <h3 className="text-[18px] font-semibold text-gray-900 flex items-center gap-2">
                       {p.name}
                       {!p.active && <span className="text-xs text-gray-500 font-medium bg-gray-100 border border-[#dadce0] px-2 py-0.5 rounded-full">未激活</span>}
                     </h3>
                     <p className="text-gray-500 text-sm">{p.description}</p>
                  </div>
                  
                  <div className="flex items-center gap-3">
                    <button 
                      onClick={() => setEditingPipeline(JSON.parse(JSON.stringify(p)))}
                      className="flex items-center justify-center gap-1.5 px-3 py-1.5 border border-[#dadce0] rounded-lg bg-white text-xs font-medium text-gray-700 hover:bg-[#f1f3f4] hover:text-[#0a66c2] hover:border-[#0a66c2] transition-all"
                    >
                      <Settings2 size={14} />
                      精细化配置
                    </button>

                    <label className="flex items-center gap-2 cursor-pointer group bg-white px-3 py-1.5 rounded-lg border border-[#dadce0] hover:bg-[#f1f3f4] transition-colors">
                      <input 
                        type="checkbox" 
                        checked={p.active} 
                        onChange={() => togglePipeline(p.id, p.active)}
                        className="w-4 h-4 accent-[#0a66c2] cursor-pointer" 
                      />
                      <span className={`text-xs font-medium ${p.active ? 'text-gray-800' : 'text-gray-500'}`}>
                        {p.active ? "开启调度" : "已休眠"}
                      </span>
                    </label>
                  </div>
                </div>

                {/* Pipeline Topography - Grid layout avoids truncation */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pt-4 border-t border-[#dadce0]">
                   
                   {/* Col 1: Input Sources */}
                   <div className="flex flex-col">
                     <div className="flex items-center gap-1.5 text-gray-700 font-medium text-sm mb-3">
                       <GitMerge size={16} className="text-[#0a66c2]"/> 1. 信号采集端点 (Sources)
                     </div>
                     <div className="flex flex-wrap gap-2">
                       {p.source_refs?.length ? p.source_refs.map((src: string) => (
                         <div key={src} className="flex flex-col gap-0.5 bg-white border border-[#dadce0] px-3 py-2 rounded-lg truncate max-w-full group-hover:border-[#c2d7f0]">
                           <span className="text-sm font-medium text-gray-800 truncate">{SOURCE_MAP[src]?.label || src}</span>
                         </div>
                       )) : <span className="text-xs text-gray-400">尚未分配抓取源</span>}
                     </div>
                   </div>

                   {/* Col 2: LLM Prompt Config */}
                   <div className="flex flex-col">
                     <div className="flex items-center gap-1.5 text-gray-700 font-medium text-sm mb-3">
                       <FileText size={16} className="text-[#0a66c2]" /> 2. 模型人格与生成 (Prompt)
                     </div>
                     {p.prompt_template ? (
                        <div 
                          className="flex flex-col justify-center bg-[#f0f7ff] border border-[#c2d7f0] px-3 py-3 rounded-lg w-full hover:bg-[#ddeeff] cursor-pointer transition-colors"
                          onClick={() => window.location.href = `/settings?prompt=${p.prompt_template}`}
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-semibold text-[#0a66c2] font-mono truncate">{p.prompt_template}</span>
                            <ExternalLink size={14} className="text-[#0a66c2]" />
                          </div>
                          <span className="text-[11px] text-[#0a66c2] mt-1 opacity-80">点击跳转至编辑器查阅/修改</span>
                        </div>
                     ) : <span className="text-xs text-gray-400">缺失剧本</span>}
                   </div>

                   {/* Col 3: Output Publishers */}
                   <div className="flex flex-col">
                     <div className="flex items-center gap-1.5 text-gray-700 font-medium text-sm mb-3">
                       <Send size={16} className="text-[#0a66c2]" /> 3. 分发终端 (Publishers)
                     </div>
                     <div className="flex flex-wrap gap-2">
                       {p.publisher_refs?.length ? p.publisher_refs.map((pub: string) => (
                         <div key={pub} className="bg-white border border-[#dadce0] text-sm font-medium text-gray-800 px-3 py-2 rounded-lg truncate max-w-full group-hover:border-[#c2d7f0]">
                           {PUB_MAP[pub] || pub}
                         </div>
                       )) : <span className="text-xs text-gray-400">孤岛状态</span>}
                     </div>
                   </div>
                   
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Editing Modal (LinkedIn Style) */}
      {editingPipeline && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-3xl shadow-[0_4px_12px_rgba(0,0,0,0.15)] flex flex-col max-h-[90vh] overflow-hidden">
             
             {/* Modal Header */}
             <div className="px-6 py-4 border-b border-[#dadce0] flex justify-between items-center bg-white shrink-0">
               <div>
                 <h2 className="text-[18px] font-semibold text-gray-900 leading-tight">配置管线节点</h2>
                 <p className="text-xs text-gray-500 font-mono mt-0.5">{editingPipeline.id}</p>
               </div>
               <button onClick={() => setEditingPipeline(null)} className="text-gray-400 hover:text-gray-700 transition-colors">
                 <X size={20} />
               </button>
             </div>

             {/* Modal Body */}
             <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-8 bg-[#f8f9fa]">
                
                {/* 1. Name & Desc */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 bg-white p-5 rounded-xl border border-[#dadce0]">
                  <div className="flex flex-col gap-2">
                    <label className="text-xs font-semibold text-gray-700 uppercase tracking-wider">管线名称</label>
                    <input 
                      type="text" 
                      value={editingPipeline.name}
                      onChange={e => setEditingPipeline({...editingPipeline, name: e.target.value})}
                      className="border border-[#dadce0] rounded-lg px-3 py-2 text-sm text-gray-900 focus:border-[#0a66c2] focus:ring-1 focus:ring-[#0a66c2] outline-none"
                    />
                  </div>
                  <div className="flex flex-col gap-2">
                    <label className="text-xs font-semibold text-gray-700 uppercase tracking-wider">管线人设载荷 (Prompt File)</label>
                    <input 
                      type="text" 
                      value={editingPipeline.prompt_template}
                      onChange={e => setEditingPipeline({...editingPipeline, prompt_template: e.target.value})}
                      className="border border-[#dadce0] rounded-lg px-3 py-2 font-mono text-sm text-[#0a66c2] focus:border-[#0a66c2] focus:ring-1 focus:ring-[#0a66c2] outline-none"
                    />
                  </div>
                </div>

                {/* 2. Sources Select */}
                <div className="flex flex-col gap-4 bg-white p-5 rounded-xl border border-[#dadce0]">
                   <div className="flex items-center gap-2 text-gray-900 font-semibold text-sm border-b border-[#dadce0] pb-2">
                     1. 请勾选本管线的「数据采集探针」
                   </div>
                   
                   <div className="flex flex-col gap-6 mt-2">
                     {Object.entries(SOURCE_GROUPS).map(([groupName, sources]) => (
                       <div key={groupName} className="flex flex-col gap-3">
                         <div className="text-[12px] font-bold text-gray-400 uppercase tracking-widest pl-1">{groupName}</div>
                         <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                           {sources.map(source => {
                             const isSelected = editingPipeline.source_refs?.includes(source);
                             const { label, desc } = SOURCE_MAP[source] || { label: source, desc: "" };
                             return (
                               <div 
                                 key={source}
                                 onClick={() => toggleArrayItem("source_refs", source)}
                                 className={`p-3 rounded-lg cursor-pointer transition-all border flex flex-col gap-1.5 ${isSelected ? 'bg-[#f0f7ff] border-[#0a66c2]' : 'bg-[#f8f9fa] border-transparent hover:border-[#dadce0] hover:bg-white'}`}
                               >
                                  <span className={`text-sm font-semibold truncate ${isSelected ? 'text-[#0a66c2]' : 'text-gray-700'}`}>
                                    {label}
                                  </span>
                                  <span className="text-[11px] text-gray-500 leading-snug line-clamp-2">{desc}</span>
                               </div>
                             )
                           })}
                         </div>
                       </div>
                     ))}
                   </div>
                </div>

                {/* 3. Publishers Select */}
                <div className="flex flex-col gap-4 bg-white p-5 rounded-xl border border-[#dadce0]">
                   <div className="flex items-center gap-2 text-gray-900 font-semibold text-sm border-b border-[#dadce0] pb-2">
                     2. 请勾选本管线的「全域分发终端」
                   </div>
                   <div className="flex flex-wrap gap-2 mt-2">
                     {AVAILABLE_PUBLISHERS.map(pub => {
                       const isSelected = editingPipeline.publisher_refs?.includes(pub);
                       return (
                         <div 
                           key={pub}
                           onClick={() => toggleArrayItem("publisher_refs", pub)}
                           className={`px-4 py-2 rounded-lg text-sm font-semibold cursor-pointer transition-all border ${isSelected ? 'bg-[#f0f7ff] border-[#0a66c2] text-[#0a66c2]' : 'bg-white border-[#dadce0] text-gray-700 hover:bg-[#f1f3f4]'}`}
                         >
                            {isSelected ? "✅ " : ""}{PUB_MAP[pub] || pub}
                         </div>
                       )
                     })}
                   </div>
                </div>
             </div>

             {/* Modal Footer */}
             <div className="px-6 py-4 border-t border-[#dadce0] flex justify-end gap-3 bg-white shrink-0">
               <button 
                 onClick={() => setEditingPipeline(null)}
                 className="flex items-center justify-center gap-1.5 px-4 py-2 border border-[#dadce0] rounded-lg bg-white text-sm font-medium text-gray-700 hover:bg-[#f1f3f4] transition-all"
               >
                 丢弃更改
               </button>
               <button 
                 onClick={handleEditSubmit}
                 className="flex items-center justify-center gap-1.5 px-4 py-2 border rounded-lg text-sm font-medium transition-all bg-[#0a66c2] border-[#0a66c2] text-white hover:bg-[#004182] shadow-sm"
               >
                 写入底层管线 (YAML)
               </button>
             </div>
          </div>
        </div>
      )}

    </div>
  );
}
