"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, CheckCircle2, AlertCircle, Loader2, Link as LinkIcon, FileText } from "lucide-react";
import ReactMarkdown from 'react-markdown';

interface ChannelStatus {
  status: "success" | "error" | "draft_saved";
  message?: string;
  notice?: string;
}

interface RunArtifact {
  artifact_id: string;
  run_id: string;
  pipeline_id: string;
  event_url: string;
  title: string;
  markdown_body: string;
  channel_status: Record<string, ChannelStatus>;
  created_at: string;
}

export default function RunDetailPage() {
  const params = useParams();
  const router = useRouter();
  const run_id = params.run_id as string;
  
  const [artifacts, setArtifacts] = useState<RunArtifact[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchArtifacts = async () => {
      setLoading(true);
      try {
        const res = await fetch(`http://localhost:8000/api/history/${run_id}/artifacts`);
        const json = await res.json();
        if (json.status === "success") {
          setArtifacts(json.data);
        } else {
          setError(json.message);
        }
      } catch (err) {
        setError("Failed to fetch artifacts data");
      } finally {
        setLoading(false);
      }
    };
    
    if (run_id) {
      fetchArtifacts();
    }
  }, [run_id]);

  const getChannelBadgeParams = (channel: string, statusObj: ChannelStatus) => {
    switch (statusObj.status) {
      case "success":
        return { color: "bg-green-100 text-green-800 border-green-200", icon: <CheckCircle2 size={12} />, text: "成功已发" };
      case "draft_saved":
        return { color: "bg-yellow-100 text-yellow-800 border-yellow-200", icon: <FileText size={12} />, text: "生成草稿" };
      case "error":
        return { color: "bg-red-100 text-red-800 border-red-200", icon: <AlertCircle size={12} />, text: "发生异常" };
      default:
        return { color: "bg-gray-100 text-gray-800 border-gray-200", icon: null, text: statusObj.status };
    }
  };

  const formatPlatformName = (key: string) => {
    const map: Record<string, string> = {
      telegram: "Telegram",
      wecom: "企业微信",
      feishu: "飞书",
      xiaohongshu: "小红书",
      wechat: "公众号"
    };
    return map[key] || key;
  };

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8">
      <div>
        <button 
          onClick={() => router.back()}
          className="text-gray-500 hover:text-blue-600 flex items-center gap-1.5 mb-4 text-sm font-medium transition"
        >
          <ArrowLeft size={16} /> 返回历史列表
        </button>
        <h1 className="text-2xl font-bold text-gray-900 break-all leading-relaxed">
          执行批次详情
        </h1>
        <p className="text-gray-500 mt-2 font-mono text-sm bg-gray-100 px-3 py-1 rounded inline-block">
          {run_id}
        </p>
      </div>

      {loading ? (
        <div className="flex justify-center items-center py-20">
          <Loader2 size={32} className="animate-spin text-blue-500" />
        </div>
      ) : error ? (
        <div className="bg-red-50 text-red-800 p-4 rounded-xl border border-red-100 flex items-start gap-3">
          <AlertCircle className="mt-0.5" />
          <div>
            <h3 className="font-bold">加载失败</h3>
            <p className="text-sm opacity-90 mt-1">{error}</p>
          </div>
        </div>
      ) : artifacts.length === 0 ? (
        <div className="bg-white border-2 border-dashed border-gray-200 rounded-2xl p-16 text-center text-gray-500">
          <div className="text-4xl mb-4">📭</div>
          <h3 className="text-lg font-medium text-gray-900">本次运行没有生成最终产物</h3>
          <p className="mt-1">抓取的情报可能全部未通过大模型筛选，或已被去重保护拦截。</p>
        </div>
      ) : (
        <div className="space-y-6">
          {artifacts.map((art) => (
            <div key={art.artifact_id} className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
              <div className="p-5 border-b border-gray-100 bg-gray-50 flex flex-col sm:flex-row justify-between gap-4">
                <div>
                  <h2 className="text-xl font-bold text-gray-900 leading-snug">
                    {art.title}
                  </h2>
                  <div className="flex items-center gap-4 mt-2">
                    <span className="text-xs text-gray-500">
                      生成时间: {new Date(art.created_at).toLocaleString('zh-CN')}
                    </span>
                    <a 
                      href={art.event_url} 
                      target="_blank" 
                      rel="noreferrer"
                      className="text-xs text-blue-600 hover:underline flex items-center gap-1 font-medium bg-blue-50 px-2 py-0.5 rounded"
                    >
                      <LinkIcon size={12} /> 源文件地址
                    </a>
                  </div>
                </div>
                
                <div className="flex gap-2 flex-wrap sm:justify-end items-start content-start max-w-xs">
                  {Object.entries(art.channel_status).map(([channel, statusObj]) => {
                    const badge = getChannelBadgeParams(channel, statusObj);
                    const tooltipMsg = statusObj.message || statusObj.notice || "";
                    
                    return (
                      <div 
                        key={channel} 
                        className={`group relative flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-semibold border ${badge.color}`}
                        title={tooltipMsg}
                      >
                        {badge.icon}
                        <span>{formatPlatformName(channel)}</span>
                        
                        {/* Custom Tooltip for errors */}
                        {statusObj.status === "error" && (
                          <div className="absolute top-full lg:-left-1/2 left-0 mt-2 z-10 w-64 p-2 bg-gray-900 text-white text-xs rounded shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all">
                            {tooltipMsg}
                          </div>
                        )}
                      </div>
                    );
                  })}
                  {Object.keys(art.channel_status).length === 0 && (
                    <span className="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded">无渠道分发</span>
                  )}
                </div>
              </div>
              
              <div className="p-6">
                <div className="prose prose-sm prose-blue max-w-none prose-headings:font-bold prose-a:text-blue-600 bg-slate-50/50 p-6 rounded-xl border border-slate-100 font-sans leading-relaxed">
                  <ReactMarkdown>{art.markdown_body}</ReactMarkdown>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
