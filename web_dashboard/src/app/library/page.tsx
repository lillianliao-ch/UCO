"use client";

import { useEffect, useState } from "react";
import ReactMarkdown from 'react-markdown';
import { RefreshCw, BookOpen, Clock, CalendarDays, ExternalLink, Filter, ChevronDown, ChevronUp } from "lucide-react";

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

const CHANNEL_LABELS: Record<string, { label: string; dot: string }> = {
  telegram: { label: "Telegram", dot: "bg-sky-400" },
  xiaohongshu: { label: "小红书", dot: "bg-red-400" },
  wechat: { label: "微信公众号", dot: "bg-green-500" },
  wecom: { label: "企业微信", dot: "bg-blue-500" },
  feishu: { label: "飞书", dot: "bg-indigo-500" },
  video_draft: { label: "短视频", dot: "bg-purple-500" },
};

const PIPELINE_LABELS: Record<string, { label: string; accent: string }> = {
  ai_news_daily: { label: "AI 宏观行情与产品观察", accent: "#0a66c2" },
  ai_tech_trends_monitor: { label: "AI 技术动态速报", accent: "#7c3aed" },
  ai_news_video_daily: { label: "AI 短视频日报", accent: "#e11d48" },
  solopreneur_patterns: { label: "独立创客洞察", accent: "#059669" },
};

export default function LibraryPage() {
  const [items, setItems] = useState<LibraryItem[]>([]);
  const [allPipelines, setAllPipelines] = useState<string[]>([]);
  const [activePipeline, setActivePipeline] = useState<string>("__all__");
  const [loading, setLoading] = useState(true);
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

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

  useEffect(() => { fetchLibrary(); }, []);

  const toggleExpand = (id: string) => {
    setExpandedIds(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const filteredItems = activePipeline === "__all__"
    ? items
    : items.filter(item => item.pipeline_id === activePipeline);

  const groupedItems = filteredItems.reduce((acc, item) => {
    const dateTitle = new Date(item.created_at).toLocaleDateString('zh-CN', {
      year: 'numeric', month: 'long', day: 'numeric', weekday: 'long'
    });
    if (!acc[dateTitle]) acc[dateTitle] = [];
    acc[dateTitle].push(item);
    return acc;
  }, {} as Record<string, LibraryItem[]>);

  const getPipelineLabel = (pid: string) => PIPELINE_LABELS[pid]?.label || pid;
  const getPipelineAccent = (pid: string) => PIPELINE_LABELS[pid]?.accent || "#6b7280";

  // Decide if body is "long" (needs expand/collapse)
  const isLong = (body: string) => body.length > 600;

  return (
    <div className="flex flex-col w-full min-h-screen bg-[#f8f9fa] relative pb-20 font-sans">
      {/* Sticky Header */}
      <div className="flex justify-between items-center px-6 py-3 border-b border-[#dadce0] sticky top-0 bg-white z-20 shadow-sm">
        <h1 className="text-[18px] font-semibold text-gray-900 flex items-center gap-2">
          <BookOpen className="text-[#0a66c2]" size={20} /> 内容金库
        </h1>
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-400">{filteredItems.length} 篇物料</span>
          <button
            onClick={fetchLibrary}
            className="flex items-center gap-1.5 px-3 py-1.5 border border-[#dadce0] rounded-lg bg-white text-xs font-medium text-gray-600 hover:bg-[#f1f3f4] transition"
          >
            <RefreshCw size={13} className={loading ? "animate-spin" : ""} /> 刷新
          </button>
        </div>
      </div>

      {/* Reading Pane */}
      <div className="w-full max-w-[780px] mx-auto px-4 py-6 flex flex-col gap-6">

        {/* Pipeline Filter Chips */}
        <div className="flex flex-wrap gap-2 items-center">
          <Filter size={13} className="text-gray-400" />
          <button
            onClick={() => setActivePipeline("__all__")}
            className={`px-3 py-1 rounded-full text-[12px] font-medium border transition-all ${
              activePipeline === "__all__"
                ? "bg-gray-800 text-white border-gray-800"
                : "bg-white text-gray-500 border-[#dadce0] hover:border-gray-400"
            }`}
          >全部</button>
          {allPipelines.map(pid => (
            <button
              key={pid}
              onClick={() => setActivePipeline(pid)}
              className={`px-3 py-1 rounded-full text-[12px] font-medium border transition-all ${
                activePipeline === pid
                  ? "text-white border-transparent"
                  : "bg-white text-gray-500 border-[#dadce0] hover:border-gray-400"
              }`}
              style={activePipeline === pid ? { backgroundColor: getPipelineAccent(pid), borderColor: getPipelineAccent(pid) } : {}}
            >
              {getPipelineLabel(pid)}
            </button>
          ))}
        </div>

        {/* Content Stream */}
        {loading ? (
          <div className="flex flex-col items-center py-32 text-gray-400 gap-3">
            <RefreshCw className="animate-spin" size={28} />
            <span className="text-sm">加载中...</span>
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="bg-white border border-dashed border-gray-300 rounded-xl p-16 text-center">
            <div className="text-4xl mb-3">📭</div>
            <p className="text-gray-500 text-sm">暂无内容</p>
          </div>
        ) : (
          <div className="flex flex-col gap-10">
            {Object.entries(groupedItems).map(([dateLabel, dailyItems]) => (
              <div key={dateLabel}>
                {/* Date Header */}
                <div className="flex items-center gap-3 mb-5">
                  <CalendarDays className="text-gray-400" size={15} />
                  <span className="text-[13px] font-bold text-gray-700">{dateLabel}</span>
                  <div className="h-px bg-gray-200 flex-1"></div>
                  <span className="text-[11px] text-gray-400">{dailyItems.length} 篇</span>
                </div>

                {/* Articles */}
                <div className="flex flex-col gap-6">
                  {dailyItems.map((item) => {
                    const expanded = expandedIds.has(item.id);
                    const needsCollapse = isLong(item.markdown_body);
                    const accent = getPipelineAccent(item.pipeline_id);

                    return (
                      <article key={item.id} className="bg-white rounded-xl border border-[#e5e7eb] overflow-hidden hover:border-[#c5c9d0] transition-colors">
                        {/* Thin accent bar */}
                        <div className="h-[3px]" style={{ backgroundColor: accent }}></div>

                        <div className="px-6 pt-5 pb-5">
                          {/* Meta line */}
                          <div className="flex items-center gap-2 flex-wrap mb-3">
                            <span
                              className="text-[11px] font-semibold px-2 py-0.5 rounded text-white"
                              style={{ backgroundColor: accent }}
                            >
                              {getPipelineLabel(item.pipeline_id)}
                            </span>
                            <span className="text-[11px] text-gray-400 font-mono flex items-center gap-1">
                              <Clock size={10} />
                              {new Date(item.created_at).toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                            </span>
                            {item.event_url && (
                              <a href={item.event_url} target="_blank" rel="noreferrer" className="text-[11px] text-blue-500 hover:underline flex items-center gap-0.5 ml-auto">
                                <ExternalLink size={10} /> 原文链接
                              </a>
                            )}
                          </div>

                          {/* Title */}
                          <h2 className="text-[17px] font-bold text-gray-900 leading-relaxed mb-4">
                            {item.title}
                          </h2>

                          {/* Media (inline, if available) */}
                          {item.video_path && (
                            <div className="mb-4 rounded-lg overflow-hidden border border-gray-200 bg-black">
                              <video
                                src={`http://localhost:8000${item.video_path}`}
                                className="w-full max-h-[400px]"
                                controls
                                preload="metadata"
                              ></video>
                            </div>
                          )}
                          {!item.video_path && (item.poster_path_xhs || item.poster_path_wx) && (
                            <div className="mb-4 rounded-lg overflow-hidden border border-gray-200">
                              <img
                                src={`http://localhost:8000${item.poster_path_xhs || item.poster_path_wx}`}
                                alt=""
                                className="w-full max-h-[360px] object-contain bg-gray-50"
                              />
                            </div>
                          )}

                          {/* Markdown Body — full readable article */}
                          <div
                            className={`prose prose-sm prose-gray max-w-none
                              prose-headings:text-gray-800 prose-headings:font-bold prose-headings:mt-4 prose-headings:mb-2
                              prose-p:text-[14px] prose-p:leading-[1.85] prose-p:text-gray-700 prose-p:my-2
                              prose-li:text-[14px] prose-li:text-gray-700 prose-li:leading-[1.8]
                              prose-strong:text-gray-900
                              prose-a:text-blue-600 prose-a:no-underline hover:prose-a:underline
                              prose-code:text-[13px] prose-code:bg-gray-100 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-rose-600
                              prose-blockquote:border-l-[3px] prose-blockquote:border-gray-300 prose-blockquote:text-gray-500 prose-blockquote:italic
                              ${!expanded && needsCollapse ? 'max-h-[280px] overflow-hidden relative' : ''}`}
                          >
                            <ReactMarkdown>{item.markdown_body}</ReactMarkdown>
                            {/* Fade overlay when collapsed */}
                            {!expanded && needsCollapse && (
                              <div className="absolute bottom-0 left-0 right-0 h-20 bg-gradient-to-t from-white to-transparent pointer-events-none"></div>
                            )}
                          </div>

                          {/* Expand / Collapse toggle */}
                          {needsCollapse && (
                            <button
                              onClick={() => toggleExpand(item.id)}
                              className="flex items-center gap-1 mt-2 text-[12px] font-medium text-blue-600 hover:text-blue-800 transition-colors"
                            >
                              {expanded ? <><ChevronUp size={14} /> 收起</> : <><ChevronDown size={14} /> 展开全文</>}
                            </button>
                          )}

                          {/* Channel delivery footer */}
                          <div className="flex items-center gap-3 mt-4 pt-3 border-t border-gray-100">
                            <span className="text-[11px] text-gray-400">已分发至</span>
                            <div className="flex flex-wrap gap-2">
                              {item.channels.map(ch => {
                                const info = CHANNEL_LABELS[ch] || { label: ch, dot: "bg-gray-400" };
                                return (
                                  <span key={ch} className="flex items-center gap-1.5 text-[11px] text-gray-600 font-medium">
                                    <span className={`w-[6px] h-[6px] rounded-full ${info.dot}`}></span>
                                    {info.label}
                                  </span>
                                );
                              })}
                              {item.channels.length === 0 && (
                                <span className="text-[11px] text-gray-300">—</span>
                              )}
                            </div>
                          </div>
                        </div>
                      </article>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
