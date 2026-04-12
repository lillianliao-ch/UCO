"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, CheckCircle2, AlertCircle, Loader2, Link as LinkIcon, FileText, Activity as ActivityIcon, ArrowRight } from "lucide-react";
import ReactMarkdown from 'react-markdown';

interface RunSourceMetric {
  id: number;
  source_name: string;
  status: "SUCCESS" | "ERROR" | "TIMEOUT";
  items_fetched: number;
  items_selected: number;
  error_msg: string | null;
}

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
  const [metrics, setMetrics] = useState<RunSourceMetric[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [resArt, resMet] = await Promise.all([
           fetch(`http://localhost:8000/api/history/${run_id}/artifacts`),
           fetch(`http://localhost:8000/api/history/${run_id}/metrics`)
        ]);
        const jsonArt = await resArt.json();
        const jsonMet = await resMet.json();
        
        if (jsonArt.status === "success") setArtifacts(jsonArt.data);
        else setError(jsonArt.message);

        if (jsonMet.status === "success") setMetrics(jsonMet.data);
      } catch (err) {
        setError("Failed to fetch run data");
      } finally {
        setLoading(false);
      }
    };
    
    if (run_id) {
      fetchData();
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
        </div>
      ) : (
        <div className="space-y-8">
          
          {/* Funnel Metrics Dashboard */}
          {metrics.length > 0 && (
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-200">
              <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                <ActivityIcon size={18} className="text-blue-500" /> 情报探针漏斗 (Observability Funnel)
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                {metrics.map(m => (
                  <div key={m.id} className="border border-gray-200 rounded-lg p-3.5 bg-gray-50 flex flex-col relative overflow-hidden transition-all hover:border-blue-300">
                    {/* Visual success bar */}
                    {m.items_fetched > 0 && m.status !== "ERROR" && (
                       <div className="absolute top-0 left-0 h-1 bg-gray-200 w-full opacity-60">
                         <div className="h-full bg-blue-500 rounded-r" style={{ width: `${Math.min(100, (m.items_selected / m.items_fetched) * 100)}%` }}></div>
                       </div>
                    )}
                    
                    <div className="flex justify-between items-start mb-2 pt-1 gap-2">
                      <span className="font-bold text-sm text-gray-800 break-all leading-tight">{m.source_name}</span>
                      <div className="shrink-0">
                        {m.status === "ERROR" ? (
                          <span className="bg-red-100 text-red-700 text-[10px] px-1.5 py-0.5 rounded font-bold">ERROR</span>
                        ) : m.items_selected > 0 ? (
                          <span className="bg-green-100 text-green-700 text-[10px] px-1.5 py-0.5 rounded font-bold border border-green-200">HIT</span>
                        ) : (
                          <span className="bg-gray-200 text-gray-500 text-[10px] px-1.5 py-0.5 rounded font-bold border border-gray-300">PASS</span>
                        )}
                      </div>
                    </div>
                    
                    {m.status === "ERROR" ? (
                      <div className="text-[11px] text-red-600 line-clamp-2 mt-auto pt-2 border-t border-gray-200/60" title={m.error_msg || ""}>
                         🚨 {m.error_msg}
                      </div>
                    ) : (
                      <div className="flex items-center text-[11px] text-gray-500 justify-between mt-auto pt-2 border-t border-gray-200/60">
                        <span className="flex items-center gap-1">收集: <strong className="text-gray-900 border-b border-gray-300 pb-px">{m.items_fetched}</strong></span>
                        <ArrowRight size={12} className="text-gray-300" />
                        <span className="flex items-center gap-1">选中: <strong className={m.items_selected > 0 ? "text-blue-600 font-bold bg-blue-50 px-1 rounded" : "text-gray-400"}>{m.items_selected}</strong></span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {artifacts.length === 0 ? (
            <div className="bg-white border-2 border-dashed border-gray-200 rounded-2xl p-16 text-center text-gray-500">
              <div className="text-4xl mb-4">📭</div>
              <h3 className="text-lg font-medium text-gray-900">本次运行没有生成最终产物</h3>
              <p className="mt-1">所有情报均未通过大模型“含金量”筛选，或触发生效去重机制。</p>
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
