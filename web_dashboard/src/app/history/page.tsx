"use client";

import { useEffect, useState } from "react";
import { Clock, CheckCircle2, XCircle, Loader2, RefreshCw, ChevronRight } from "lucide-react";
import { useRouter } from "next/navigation";

interface PipelineHistory {
  run_id: string;
  pipeline_id: string;
  start_time: string;
  end_time: string | null;
  items_scraped: number;
  items_passed_llm: number;
  drafts_generated: number;
  status: string;
}

export default function HistoryPage() {
  const router = useRouter();
  const [history, setHistory] = useState<PipelineHistory[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/history");
      const json = await res.json();
      if (json.status === "success") {
        setHistory(json.data);
      }
    } catch (error) {
      console.error("Failed to fetch history:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const formatDate = (isoStr: string | null) => {
    if (!isoStr) return "-";
    try {
      const d = new Date(isoStr);
      return d.toLocaleString("zh-CN", { 
        month: "short", day: "numeric", 
        hour: "2-digit", minute: "2-digit", second: "2-digit"
      });
    } catch (e) {
      return isoStr;
    }
  };

  const getDuration = (start: string, end: string | null) => {
    if (!end) return "-";
    try {
      const durationMs = new Date(end).getTime() - new Date(start).getTime();
      const seconds = Math.floor(durationMs / 1000);
      if (seconds < 60) return `${seconds}秒`;
      const mins = Math.floor(seconds / 60);
      const remainingSecs = seconds % 60;
      return `${mins}分${remainingSecs}秒`;
    } catch (e) {
      return "-";
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "SUCCESS":
        return <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800"><CheckCircle2 size={14} /> 成功</span>;
      case "RUNNING":
        return <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"><Loader2 size={14} className="animate-spin" /> 执行中</span>;
      case "FAILED":
      case "ERROR":
        return <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800"><XCircle size={14} /> 失败</span>;
      default:
        return <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">{status}</span>;
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Clock className="text-blue-500" size={32} />
            管线执行历史
          </h1>
          <p className="text-gray-500 mt-2">监控数据采抓取与大模型过滤漏斗 (Pipeline Funnel Observability)</p>
        </div>
        
        <button 
          onClick={fetchHistory}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg shadow-sm hover:bg-gray-50 text-gray-700 transition"
        >
          <RefreshCw size={18} className={loading ? "animate-spin" : ""} />
          刷新数据
        </button>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-100 text-sm font-medium text-gray-500 uppercase tracking-wider">
                <th className="p-4 pl-6">执行时间</th>
                <th className="p-4">管线 ID</th>
                <th className="p-4 text-center">状态</th>
                <th className="p-4 text-center" title="原来抓取数量">原始抓取</th>
                <th className="p-4 text-center" title="通过 LLM 过滤的数量">LLM 筛选</th>
                <th className="p-4 text-center" title="最终生成的投递/草稿数">生成产物</th>
                <th className="p-4 text-right">耗时</th>
                <th className="p-4 text-right pr-6 w-10">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 text-sm">
              {loading && history.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-12 text-center text-gray-400">
                    <Loader2 size={32} className="animate-spin -ml-1 mr-3 inline-block" />
                    加载中...
                  </td>
                </tr>
              ) : history.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-12 text-center text-gray-400">
                    暂无执行记录
                  </td>
                </tr>
              ) : (
                history.map((run) => (
                  <tr 
                    key={run.run_id} 
                    className="hover:bg-blue-50/50 cursor-pointer transition-colors group"
                    onClick={() => router.push(`/history/${run.run_id}`)}
                  >
                    <td className="p-4 pl-6 whitespace-nowrap text-gray-900 font-medium">
                      {formatDate(run.start_time)}
                    </td>
                    <td className="p-4 whitespace-nowrap">
                      <code className="text-xs bg-gray-100 text-gray-800 px-2 py-1 rounded inline-block">
                        {run.pipeline_id}
                      </code>
                    </td>
                    <td className="p-4 text-center whitespace-nowrap">
                      {getStatusBadge(run.status)}
                    </td>
                    <td className="p-4 text-center text-gray-600">
                      {run.items_scraped ?? "-"}
                    </td>
                    <td className="p-4 text-center">
                      <span className="inline-block bg-blue-50 text-blue-700 font-medium px-2.5 py-0.5 rounded-full text-xs">
                        {run.items_passed_llm ?? "-"}
                      </span>
                    </td>
                    <td className="p-4 text-center font-bold text-gray-900">
                      {run.drafts_generated ?? "-"}
                    </td>
                    <td className="p-4 text-right text-gray-500 whitespace-nowrap">
                      {getDuration(run.start_time, run.end_time)}
                    </td>
                    <td className="p-4 text-right pr-6 text-gray-400 group-hover:text-blue-500">
                      <ChevronRight size={18} className="inline" />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
