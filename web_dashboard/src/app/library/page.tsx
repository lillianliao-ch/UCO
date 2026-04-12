"use client";

import { useEffect, useState } from "react";
import ReactMarkdown from 'react-markdown';
import { RefreshCw, BookOpen, Clock, CalendarDays, ExternalLink, Link as LinkIcon } from "lucide-react";

interface PublishedItem {
  draft_id: string;
  pipeline_id: string;
  title: string;
  markdown_body: string;
  created_at: string;
  poster_path_xhs?: string;
  poster_path_wx?: string;
  video_path?: string;
  status: string;
}

export default function LibraryPage() {
  const [items, setItems] = useState<PublishedItem[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchPublished = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/published");
      const json = await res.json();
      if (json.status === "success") {
        setItems(json.data);
      }
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchPublished();
  }, []);

  // Group by Date
  const groupedItems = items.reduce((acc, item) => {
    const dateTitle = new Date(item.created_at).toLocaleDateString('zh-CN', {
      year: 'numeric', month: 'long', day: 'numeric', weekday: 'long'
    });
    if (!acc[dateTitle]) acc[dateTitle] = [];
    acc[dateTitle].push(item);
    return acc;
  }, {} as Record<string, PublishedItem[]>);

  return (
    <div className="flex flex-col w-full min-h-screen bg-[#f8f9fa] relative pb-20 font-sans">
      <div className="flex justify-between items-center px-6 py-3 border-b border-[#dadce0] sticky top-0 bg-white z-20 shadow-sm">
        <h1 className="text-[18px] font-semibold text-gray-900 flex items-center gap-2">
          <BookOpen className="text-blue-500" size={20} /> 内容金库 (Content Library)
        </h1>
        <button 
          onClick={fetchPublished}
          className="flex items-center justify-center gap-1.5 px-3 py-1.5 border border-[#dadce0] rounded-lg bg-white text-xs font-medium text-gray-700 hover:bg-[#f1f3f4] transition"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          同步金库
        </button>
      </div>

      <div className="p-6 w-full max-w-[1240px] mx-auto flex flex-col gap-8">
        <div>
          <h2 className="text-[20px] font-semibold text-gray-900 leading-tight">已发布全息档案</h2>
          <p className="text-gray-500 text-sm mt-1">这里沉淀了所有通过 UCO 发送至外部节点（小红书、视频号、内部群等）的最终物料成果。按时间轴归档存放。</p>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-32 text-gray-400 gap-4">
            <RefreshCw className="animate-spin" size={32} />
            正在从 SQLite 读取历史金库...
          </div>
        ) : items.length === 0 ? (
          <div className="bg-white border-2 border-dashed border-gray-200 rounded-2xl p-24 text-center">
            <div className="text-5xl mb-4">📭</div>
            <h3 className="text-xl font-bold text-gray-900">暂无成功发布的物料</h3>
            <p className="text-gray-500 mt-2">当您在 "待发草稿箱" 核准或系统全自动投递成功后，档案会自动沉淀至此。</p>
          </div>
        ) : (
          <div className="flex flex-col gap-8">
            {Object.entries(groupedItems).map(([dateLabel, dailyItems]) => (
              <div key={dateLabel} className="flex flex-col gap-4">
                <div className="flex items-center gap-3 sticky top-14 bg-[#f8f9fa] py-2 z-10">
                  <div className="flex items-center gap-2 px-3 py-1 bg-white border border-gray-200 rounded-full shadow-sm">
                    <CalendarDays className="text-blue-500" size={14} />
                    <span className="text-sm font-bold text-gray-800">{dateLabel}</span>
                  </div>
                  <div className="h-px bg-gray-200 flex-1"></div>
                  <span className="text-xs font-medium text-gray-400">{dailyItems.length} 篇存档</span>
                </div>
                
                <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                  {dailyItems.map((item) => (
                    <div key={item.draft_id} className="bg-white border border-[#dadce0] rounded-xl overflow-hidden hover:shadow-lg transition-all flex flex-col h-full group">
                      
                      {/* Media Display Area (Top) */}
                      {(item.video_path || item.poster_path_xhs || item.poster_path_wx) ? (
                        <div className="w-full bg-black relative aspect-[3/4] overflow-hidden border-b border-gray-100 flex-shrink-0">
                          {item.video_path ? (
                            <div className="w-full h-full relative object-cover">
                              <video 
                                src={`http://localhost:8000${item.video_path}`} 
                                className="w-full h-full object-cover"
                                controls
                                preload="metadata"
                              ></video>
                              <div className="absolute top-2 right-2 bg-red-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded backdrop-blur bg-opacity-90">VIDEO</div>
                            </div>
                          ) : (
                            <img 
                              src={`http://localhost:8000${item.poster_path_xhs || item.poster_path_wx}`} 
                              alt="Poster" 
                              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                            />
                          )}
                        </div>
                      ) : (
                        <div className="w-full h-3 bg-gradient-to-r from-blue-500 to-cyan-500 shrink-0"></div>
                      )}
                      
                      {/* Text Content (Bottom) */}
                      <div className="p-5 flex flex-col flex-1">
                        <div className="flex items-start justify-between mb-2">
                           <h3 className="font-bold text-base text-gray-900 leading-tight line-clamp-2">
                             {item.title}
                           </h3>
                        </div>
                        
                        <div className="flex items-center gap-1.5 text-[11px] text-gray-500 mb-3 font-mono bg-gray-50 border border-gray-100 px-2 py-1 rounded w-fit">
                           <Clock size={11} /> {new Date(item.created_at).toLocaleTimeString('zh-CN')}
                           <span className="mx-1 text-gray-300">|</span>
                           {item.pipeline_id}
                        </div>
                        
                        <div className="prose prose-sm prose-blue max-w-none text-xs text-gray-600 line-clamp-6 opacity-80 mb-4 flex-1">
                           <ReactMarkdown>{item.markdown_body}</ReactMarkdown>
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
