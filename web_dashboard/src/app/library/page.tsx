"use client";

import { useEffect, useState } from "react";
import ReactMarkdown from 'react-markdown';
import { RefreshCw, BookOpen, Clock, CalendarDays, ExternalLink, Filter, Send, MessageSquare, Video } from "lucide-react";

interface LibraryItem {
  id: string;
  source: string;
  pipeline_id: string;
  title: string;
  markdown_body: string;
  event_url?: string;
  channels: string[];
  channel_status: Record<string, any>;
  created_at: string;
  poster_path_xhs?: string;
  poster_path_wx?: string;
  video_path?: string;
}

const CHANNEL_LABELS: Record<string, { label: string; color: string; icon: string }> = {
  telegram: { label: "Telegram", color: "bg-sky-100 text-sky-700 border-sky-200", icon: "📲" },
  xiaohongshu: { label: "小红书", color: "bg-red-50 text-red-600 border-red-200", icon: "📕" },
  wechat: { label: "微信公众号", color: "bg-green-50 text-green-700 border-green-200", icon: "💬" },
  wecom: { label: "企业微信", color: "bg-blue-50 text-blue-700 border-blue-200", icon: "🏢" },
  feishu: { label: "飞书", color: "bg-indigo-50 text-indigo-700 border-indigo-200", icon: "🪶" },
  video_draft: { label: "短视频", color: "bg-purple-50 text-purple-700 border-purple-200", icon: "🎬" },
};

const PIPELINE_LABELS: Record<string, { label: string; color: string }> = {
  ai_news_daily: { label: "📰 AI 宏观行情与产品观察", color: "from-blue-500 to-cyan-500" },
  ai_tech_trends_monitor: { label: "🔬 AI 技术动态速报", color: "from-violet-500 to-purple-500" },
  ai_news_video_daily: { label: "🎬 AI 短视频日报", color: "from-rose-500 to-orange-500" },
};

export default function LibraryPage() {
  const [items, setItems] = useState<LibraryItem[]>([]);
  const [allPipelines, setAllPipelines] = useState<string[]>([]);
  const [activePipeline, setActivePipeline] = useState<string>("__all__");
  const [loading, setLoading] = useState(true);

  const fetchLibrary = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/library");
      const json = await res.json();
      if (json.status === "success") {
        setItems(json.data);
        setAllPipelines(json.pipelines || []);
      }
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchLibrary();
  }, []);

  // Filter by active pipeline
  const filteredItems = activePipeline === "__all__"
    ? items
    : items.filter(item => item.pipeline_id === activePipeline);

  // Group by Date
  const groupedItems = filteredItems.reduce((acc, item) => {
    const dateTitle = new Date(item.created_at).toLocaleDateString('zh-CN', {
      year: 'numeric', month: 'long', day: 'numeric', weekday: 'long'
    });
    if (!acc[dateTitle]) acc[dateTitle] = [];
    acc[dateTitle].push(item);
    return acc;
  }, {} as Record<string, LibraryItem[]>);

  const getPipelineLabel = (pid: string) => PIPELINE_LABELS[pid]?.label || pid;
  const getPipelineGradient = (pid: string) => PIPELINE_LABELS[pid]?.color || "from-gray-400 to-gray-500";

  return (
    <div className="flex flex-col w-full min-h-screen bg-[#f8f9fa] relative pb-20 font-sans">
      {/* Header */}
      <div className="flex justify-between items-center px-6 py-3 border-b border-[#dadce0] sticky top-0 bg-white z-20 shadow-sm">
        <h1 className="text-[18px] font-semibold text-gray-900 flex items-center gap-2">
          <BookOpen className="text-blue-500" size={20} /> 内容金库 (Content Library)
        </h1>
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-500 font-medium">{filteredItems.length} 篇物料</span>
          <button
            onClick={fetchLibrary}
            className="flex items-center justify-center gap-1.5 px-3 py-1.5 border border-[#dadce0] rounded-lg bg-white text-xs font-medium text-gray-700 hover:bg-[#f1f3f4] transition"
          >
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
            同步金库
          </button>
        </div>
      </div>

      <div className="p-6 w-full max-w-[1240px] mx-auto flex flex-col gap-6">
        {/* Description + Pipeline Filter Bar */}
        <div>
          <h2 className="text-[20px] font-semibold text-gray-900 leading-tight">全量物料档案</h2>
          <p className="text-gray-500 text-sm mt-1">所有通过 UCO 生成并分发至外部节点的成品内容（Telegram 速报、小红书图文、飞书战报、短视频等），按管线归类沉淀。</p>
        </div>

        {/* Pipeline Tabs */}
        <div className="flex flex-wrap gap-2 items-center">
          <Filter size={14} className="text-gray-400 mr-1" />
          <button
            onClick={() => setActivePipeline("__all__")}
            className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-all ${
              activePipeline === "__all__"
                ? "bg-gray-900 text-white border-gray-900"
                : "bg-white text-gray-600 border-[#dadce0] hover:bg-gray-50"
            }`}
          >
            全部管线
          </button>
          {allPipelines.map(pid => (
            <button
              key={pid}
              onClick={() => setActivePipeline(pid)}
              className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-all ${
                activePipeline === pid
                  ? "bg-[#0a66c2] text-white border-[#0a66c2]"
                  : "bg-white text-gray-600 border-[#dadce0] hover:bg-blue-50 hover:border-blue-300"
              }`}
            >
              {getPipelineLabel(pid)}
            </button>
          ))}
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-32 text-gray-400 gap-4">
            <RefreshCw className="animate-spin" size={32} />
            正在从 SQLite 读取历史金库...
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="bg-white border-2 border-dashed border-gray-200 rounded-2xl p-24 text-center">
            <div className="text-5xl mb-4">📭</div>
            <h3 className="text-xl font-bold text-gray-900">暂无内容</h3>
            <p className="text-gray-500 mt-2">当管线执行并成功分发内容后，档案会自动沉淀至此。</p>
          </div>
        ) : (
          <div className="flex flex-col gap-8">
            {Object.entries(groupedItems).map(([dateLabel, dailyItems]) => (
              <div key={dateLabel} className="flex flex-col gap-4">
                {/* Date Separator */}
                <div className="flex items-center gap-3 sticky top-14 bg-[#f8f9fa] py-2 z-10">
                  <div className="flex items-center gap-2 px-3 py-1 bg-white border border-gray-200 rounded-full shadow-sm">
                    <CalendarDays className="text-blue-500" size={14} />
                    <span className="text-sm font-bold text-gray-800">{dateLabel}</span>
                  </div>
                  <div className="h-px bg-gray-200 flex-1"></div>
                  <span className="text-xs font-medium text-gray-400">{dailyItems.length} 篇</span>
                </div>

                {/* Cards */}
                <div className="flex flex-col gap-4">
                  {dailyItems.map((item) => (
                    <div key={item.id} className="bg-white border border-[#dadce0] rounded-xl overflow-hidden hover:shadow-md transition-all group">
                      {/* Pipeline gradient bar */}
                      <div className={`h-1 bg-gradient-to-r ${getPipelineGradient(item.pipeline_id)}`}></div>

                      <div className="p-5 flex gap-5">
                        {/* Media thumbnail (left, if exists) */}
                        {(item.video_path || item.poster_path_xhs || item.poster_path_wx) && (
                          <div className="w-28 h-28 flex-shrink-0 rounded-lg overflow-hidden bg-gray-100 border border-gray-200 relative">
                            {item.video_path ? (
                              <>
                                <video
                                  src={`http://localhost:8000${item.video_path}`}
                                  className="w-full h-full object-cover"
                                  preload="metadata"
                                ></video>
                                <div className="absolute bottom-1 right-1 bg-red-500 text-white text-[9px] font-bold px-1 py-0.5 rounded">VIDEO</div>
                              </>
                            ) : (
                              <img
                                src={`http://localhost:8000${item.poster_path_xhs || item.poster_path_wx}`}
                                alt=""
                                className="w-full h-full object-cover"
                              />
                            )}
                          </div>
                        )}

                        {/* Text body (right) */}
                        <div className="flex-1 min-w-0 flex flex-col">
                          {/* Top: Title + Pipeline badge */}
                          <div className="flex items-start justify-between gap-3 mb-2">
                            <h3 className="font-bold text-[15px] text-gray-900 leading-snug line-clamp-2">
                              {item.title}
                            </h3>
                          </div>

                          {/* Meta row */}
                          <div className="flex items-center gap-2 flex-wrap mb-2.5">
                            <span className="text-[11px] text-gray-500 font-mono bg-gray-50 border border-gray-100 px-2 py-0.5 rounded flex items-center gap-1">
                              <Clock size={10} /> {new Date(item.created_at).toLocaleTimeString('zh-CN')}
                            </span>
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full text-white bg-gradient-to-r ${getPipelineGradient(item.pipeline_id)}`}>
                              {getPipelineLabel(item.pipeline_id)}
                            </span>
                            {item.event_url && (
                              <a href={item.event_url} target="_blank" rel="noreferrer" className="text-[11px] text-blue-600 hover:underline flex items-center gap-0.5">
                                <ExternalLink size={10} /> 原文
                              </a>
                            )}
                          </div>

                          {/* Content preview */}
                          <div className="prose prose-sm prose-blue max-w-none text-xs text-gray-600 line-clamp-3 opacity-80 mb-3">
                            <ReactMarkdown>{item.markdown_body}</ReactMarkdown>
                          </div>

                          {/* Channel delivery badges (bottom) */}
                          <div className="flex flex-wrap gap-1.5 mt-auto">
                            {item.channels.map(ch => {
                              const info = CHANNEL_LABELS[ch] || { label: ch, color: "bg-gray-100 text-gray-600 border-gray-200", icon: "📡" };
                              return (
                                <span key={ch} className={`text-[10px] font-semibold px-2 py-0.5 rounded border ${info.color}`}>
                                  {info.icon} {info.label}
                                </span>
                              );
                            })}
                            {item.channels.length === 0 && (
                              <span className="text-[10px] text-gray-400 bg-gray-50 px-2 py-0.5 rounded border border-gray-100">无分发记录</span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
