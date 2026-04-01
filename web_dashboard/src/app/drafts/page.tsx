"use client";
import React, { useEffect, useState } from "react";
import { Check, Trash2, Edit3, Image as ImageIcon, Send } from "lucide-react";

interface Draft {
  draft_id: string; // from SQLite
  title: string;
  content_md: string;
  poster_path_xhs: string;
  poster_path_wx: string;
  pipeline_id: string;
  generate_time: string;
}

export default function DraftsPage() {
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [editorContent, setEditorContent] = useState("");
  const [editorTitle, setEditorTitle] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [isPublishing, setIsPublishing] = useState(false);

  useEffect(() => {
    fetchDrafts();
  }, []);

  const fetchDrafts = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/drafts");
      const data = await res.json();
      if (data.status === "success") {
        setDrafts(data.data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const selectedDraft = drafts.find(d => d.draft_id === selectedId);

  useEffect(() => {
    if (selectedDraft) {
      setEditorContent(selectedDraft.content_md);
      setEditorTitle(selectedDraft.title);
    }
  }, [selectedId, selectedDraft]);

  const handleSave = async () => {
    if (!selectedId) return;
    setIsSaving(true);
    try {
      await fetch(`http://localhost:8000/api/drafts/${selectedId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: editorTitle, content_md: editorContent })
      });
    } catch (e) {
      console.error(e);
    }
    setIsSaving(false);
  };

  const handlePublish = async () => {
    if (!selectedId) return;
    setIsPublishing(true);
    await handleSave(); // save before publishing
    try {
      const res = await fetch(`http://localhost:8000/api/drafts/${selectedId}/publish`, { method: "POST" });
      const data = await res.json();
      if (data.status === "success") {
        alert("发布成功！");
        fetchDrafts();
        setSelectedId(null);
      } else {
        alert("发布失败: " + data.message);
      }
    } catch (e) {
      console.error(e);
    }
    setIsPublishing(false);
  };

  const handleDiscard = async () => {
    if (!selectedId) return;
    if (!confirm("确定要彻底销毁这篇草稿吗？")) return;
    try {
      await fetch(`http://localhost:8000/api/drafts/${selectedId}/discard`, { method: "POST" });
      fetchDrafts();
      setSelectedId(null);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="flex h-[calc(100vh)] bg-[#f8f9fa] w-full overflow-hidden text-gray-900 font-sans">
      
      {/* Draft Queue Panel */}
      <div className="w-[320px] bg-white border-r border-[#dadce0] flex flex-col h-full shrink-0">
        <div className="px-5 py-4 border-b border-[#dadce0] flex items-center justify-between">
          <h2 className="text-lg font-bold">待审草稿 (Pending)</h2>
          <span className="bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded-full font-medium">{drafts.length}</span>
        </div>
        
        <div className="flex-1 overflow-y-auto">
          {drafts.length === 0 ? (
            <div className="flex flex-col items-center justify-center p-8 text-gray-400 h-64 text-sm">
              <Check size={32} className="mb-2 opacity-50" />
              <p>太棒了，目前没有积压的待审件</p>
            </div>
          ) : (
            <div className="flex flex-col">
              {drafts.map((d) => (
                <div 
                  key={d.draft_id}
                  onClick={() => setSelectedId(d.draft_id)}
                  className={`p-4 border-b border-[#dadce0] cursor-pointer transition-colors ${selectedId === d.draft_id ? 'bg-[#f0f7ff] border-l-4 border-l-[#0a66c2]' : 'hover:bg-[#f1f3f4] border-l-4 border-l-transparent'}`}
                >
                  <h3 className={`text-sm mb-1 line-clamp-2 ${selectedId === d.draft_id ? 'font-bold text-[#0a66c2]' : 'font-semibold text-gray-800'}`}>
                    {d.title}
                  </h3>
                  <div className="flex items-center justify-between text-xs mt-2">
                    <span className="text-gray-500 font-medium bg-gray-100 px-1.5 py-0.5 rounded">{d.pipeline_id}</span>
                    <span className="text-gray-400">{d.generate_time.split(" ")[1]}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Main Workspace */}
      <div className="flex-1 flex flex-col h-full bg-[#f8f9fa]">
        {selectedDraft ? (
          <>
            {/* Split View Container */}
            <div className="flex-1 flex overflow-hidden p-6 gap-6">
              
              {/* Left Editable Markdown Area */}
              <div className="flex-1 flex flex-col bg-white rounded-xl shadow-sm border border-[#dadce0] overflow-hidden">
                <div className="px-4 py-3 border-b border-[#dadce0] flex items-center gap-2 bg-gray-50 shrink-0">
                  <Edit3 size={16} className="text-gray-500" />
                  <span className="text-sm font-semibold text-gray-700">内容精修 (Markdown)</span>
                </div>
                <div className="flex-1 p-4 flex flex-col gap-4 overflow-y-auto">
                  <div className="shrink-0">
                    <label className="block text-xs font-bold text-gray-500 mb-1 uppercase tracking-wider">标题 / Title</label>
                    <input 
                      className="w-full text-lg font-bold border border-gray-200 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500 text-gray-900 placeholder-gray-300"
                      value={editorTitle}
                      onChange={e => setEditorTitle(e.target.value)}
                    />
                  </div>
                  <div className="flex-1 flex flex-col min-h-0">
                    <label className="block text-xs font-bold text-gray-500 mb-1 uppercase tracking-wider">正文 / Body</label>
                    <textarea 
                      className="flex-1 w-full resize-none border border-gray-200 rounded p-2 focus:outline-none focus:ring-1 focus:ring-blue-500 text-gray-800 leading-relaxed font-mono text-sm placeholder-gray-300"
                      value={editorContent}
                      onChange={e => setEditorContent(e.target.value)}
                    />
                  </div>
                </div>
              </div>

              {/* Right Preview Box (Simulating Mobile Phone Feed) */}
              <div className="w-[380px] flex flex-col bg-white rounded-xl shadow-sm border border-[#dadce0] overflow-hidden shrink-0">
                <div className="px-4 py-3 border-b border-[#dadce0] flex items-center gap-2 bg-gray-50 shrink-0">
                  <ImageIcon size={16} className="text-gray-500" />
                  <span className="text-sm font-semibold text-gray-700">发稿预览 (Live Preview)</span>
                </div>
                <div className="flex-1 overflow-y-auto bg-[#f8f9fa] p-4 flex justify-center w-full">
                  <div className="w-[320px] bg-white shadow-[0_2px_8px_rgba(0,0,0,0.06)] rounded-lg overflow-hidden flex flex-col border border-gray-100 pb-4 shrink-0 h-max">
                    <div className="p-3 flex items-center gap-2 border-b border-gray-50">
                      <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold text-xs shrink-0">LL</div>
                      <div className="flex flex-col">
                        <span className="text-sm font-bold text-gray-900 leading-none">Lilian聊AI</span>
                        <span className="text-[10px] text-gray-400">刚刚 · AI 管线引擎</span>
                      </div>
                    </div>
                    
                    {/* Fake text preview block, truncating some text */}
                    <div className="px-3 pt-3">
                      <h4 className="font-bold text-sm mb-1 text-gray-900">{editorTitle}</h4>
                      <div className="text-sm text-gray-700 whitespace-pre-wrap leading-snug line-clamp-6 opacity-90">
                        {editorContent}
                      </div>
                      <span className="text-blue-500 text-xs mt-1 block font-medium cursor-pointer">展开全文</span>
                    </div>

                    {/* Fake Poster Image Block (Visualizer) */}
                    <div className="mt-3 px-3">
                       <div className="w-full h-48 bg-gray-100 rounded flex flex-col items-center justify-center border border-gray-200 overflow-hidden relative">
                         <div className="absolute inset-0 bg-blue-50/50 mix-blend-multiply pointer-events-none"></div>
                         <ImageIcon size={32} className="text-gray-300 mb-2" />
                         <span className="text-xs text-gray-400 font-mono text-center px-4">
                            系统封面占位图<br/>
                            {selectedDraft.poster_path_xhs && "✅ XHS Cover Built"}<br/>
                            {selectedDraft.poster_path_wx && "✅ WX Cover Built"}
                         </span>
                       </div>
                    </div>
                  </div>
                </div>
              </div>

            </div>

            {/* Bottom Action Bar */}
            <div className="bg-white border-t border-[#dadce0] p-4 flex items-center justify-between shrink-0 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.02)] z-10 w-full">
              <div className="flex items-center gap-3 text-sm text-gray-500">
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-yellow-400"></span> 拦截大闸活跃
                </span>
                <span>•</span>
                <span>ID: {selectedId}</span>
              </div>
              
              <div className="flex items-center gap-3">
                <button 
                  onClick={handleDiscard}
                  className="flex items-center justify-center gap-1.5 px-4 py-2 border border-[#dadce0] rounded-lg bg-white text-sm font-medium text-gray-500 hover:bg-red-50 hover:text-red-600 hover:border-red-200 transition-all cursor-pointer"
                >
                  <Trash2 size={16} /> 废弃此稿
                </button>
                <button 
                  onClick={handlePublish}
                  disabled={isPublishing}
                  className="flex items-center justify-center gap-1.5 px-6 py-2 border border-[#c2d7f0] rounded-lg bg-[#f0f7ff] text-sm font-bold text-[#0a66c2] hover:bg-[#ddeeff] transition-all cursor-pointer disabled:opacity-50"
                >
                  <Send size={16} className={isPublishing ? "animate-bounce" : ""} /> 
                  {isPublishing ? '发布中...' : '核准直发 (Approve & Publish)'}
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-gray-400 h-full w-full">
             <InboxIcon size={64} className="mb-4 opacity-20" />
             <h3 className="text-xl font-semibold text-gray-600 mb-2">未选择草稿</h3>
             <p className="text-sm">请从左侧队列中选择需要审核的项目</p>
          </div>
        )}
      </div>

    </div>
  );
}

const InboxIcon = ({ size, className }: any) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <polyline points="22 12 16 12 14 15 10 15 8 12 2 12"></polyline>
    <path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"></path>
  </svg>
);
