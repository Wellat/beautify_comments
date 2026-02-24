import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, Loader2, AlertCircle, RefreshCw, FileText, Menu } from 'lucide-react';
import CommentTree from './components/CommentTree';

// Helper to extract ID from input (URL or ID)
const extractId = (input) => {
  const match = input.match(/question\/(\d+)/);
  if (match) return match[1];
  if (/^\d+$/.test(input)) return input;
  return null;
};

function App() {
  const [inputId, setInputId] = useState('');
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Fetch history on mount
  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const res = await axios.get('http://localhost:8080/api/history');
      setHistory(res.data);
    } catch (err) {
      console.error("Failed to fetch history", err);
    }
  };

  const fetchArticle = async (id, forceUpdate = false) => {
    if (!id) return;
    
    setLoading(true);
    setError(null);
    // Don't clear data immediately if updating, so user still sees old content while loading?
    // Actually, maybe better to show loading state clearly.
    if (!forceUpdate) setData(null);

    try {
      const response = await axios.get(`http://localhost:8080/api/parse`, {
        params: { 
          article_id: id,
          force_update: forceUpdate
        }
      });
      setData(response.data);
      // Refresh history to include new item or update title
      fetchHistory();
    } catch (err) {
      setError(err.response?.data?.detail || err.message || '发生未知错误');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const id = extractId(inputId);
    if (id) {
      fetchArticle(id, false);
    } else {
      setError("请输入有效的文章ID或链接");
    }
  };

  return (
    <div className="flex h-screen bg-gray-50 text-gray-900 font-sans overflow-hidden">
      {/* Sidebar */}
      <aside 
        className={`${sidebarOpen ? 'w-80' : 'w-0'} bg-white border-r border-gray-200 transition-all duration-300 flex flex-col overflow-hidden`}
      >
        <div className="p-4 border-b border-gray-100 flex items-center justify-between bg-gray-50">
          <h2 className="font-bold text-gray-700 flex items-center gap-2">
            <FileText size={18} />
            历史记录
          </h2>
          <span className="text-xs text-gray-400 bg-gray-200 px-2 py-0.5 rounded-full">{history.length}</span>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          {history.length === 0 ? (
            <div className="text-center py-10 text-gray-400 text-sm">暂无历史记录</div>
          ) : (
            <ul className="space-y-1">
              {history.map((item) => (
                <li key={item.id}>
                  <button
                    onClick={() => fetchArticle(item.id, false)}
                    className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition-colors hover:bg-blue-50 group ${data?.id === item.id ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-600'}`}
                  >
                    <div className="truncate">
                      <span className="font-mono text-xs text-gray-400 mr-2">[{item.id}]</span>
                      {item.title}
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="bg-white shadow-sm z-10 px-4 py-3 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-4 flex-1">
            <button 
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 hover:bg-gray-100 rounded-lg text-gray-500 transition-colors"
            >
              <Menu size={20} />
            </button>
            
            <h1 className="text-lg font-bold text-blue-600 tracking-tight hidden md:block">集思录评论盖楼</h1>

            <form onSubmit={handleSubmit} className="flex-1 max-w-lg ml-4 flex gap-2">
              <div className="relative flex-1">
                <input
                  type="text"
                  value={inputId}
                  onChange={(e) => setInputId(e.target.value)}
                  placeholder="输入文章ID (如 517247)"
                  className="w-full pl-9 pr-4 py-1.5 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm transition-all"
                />
                <Search className="absolute left-2.5 top-2 text-gray-400" size={16} />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-1.5 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors font-medium whitespace-nowrap"
              >
                {loading && !data ? '加载中...' : '查看'}
              </button>
            </form>
          </div>
        </header>

        {/* Scrollable Content Area */}
        <main className="flex-1 overflow-y-auto p-4 md:p-8 scroll-smooth">
          <div className="max-w-4xl mx-auto">
            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6 flex items-center gap-2 animate-fade-in">
                <AlertCircle size={20} />
                <span>{error}</span>
              </div>
            )}

            {/* Welcome / Empty State */}
            {!data && !loading && !error && (
              <div className="text-center py-32 text-gray-400">
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Search className="text-gray-300" size={32} />
                </div>
                <p className="text-lg font-medium text-gray-500">输入文章ID或选择左侧历史记录</p>
                <p className="text-sm mt-2 text-gray-400">例如: 517247</p>
              </div>
            )}

            {/* Loading State (Initial) */}
            {loading && !data && (
               <div className="flex flex-col items-center justify-center py-32 text-blue-600">
                 <Loader2 className="animate-spin mb-4" size={40} />
                 <p className="text-sm font-medium">正在获取数据...</p>
               </div>
            )}

            {/* Article Content */}
            {data && (
              <div className="space-y-8 animate-fade-in pb-20">
                <article className="bg-white p-6 md:p-10 rounded-xl shadow-sm border border-gray-100 relative group">
                  {/* Update Button */}
                  <div className="absolute top-6 right-6">
                    <button
                      onClick={() => fetchArticle(data.id, true)}
                      disabled={loading}
                      className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-gray-500 bg-gray-50 hover:bg-blue-50 hover:text-blue-600 rounded-md border border-gray-200 transition-all disabled:opacity-50"
                      title="如果不走缓存，强制从服务器拉取最新内容"
                    >
                      <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
                      {loading ? '更新中...' : '强制更新'}
                    </button>
                  </div>

                  <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-4 pr-24 leading-tight">{data.title}</h1>
                  
                  <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500 mb-8 border-b border-gray-100 pb-4">
                    <span className="font-medium text-blue-600 bg-blue-50 px-2 py-0.5 rounded">{data.author}</span>
                    <span className="flex items-center gap-1">
                      {data.publish_time}
                    </span>
                    <span className="font-mono text-xs text-gray-300">ID: {data.id}</span>
                  </div>
                  
                  <div 
                    className="prose prose-lg max-w-none text-gray-800 leading-relaxed"
                    dangerouslySetInnerHTML={{ __html: data.content }}
                  />
                </article>

                {/* Comments Section */}
                <section>
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                      评论区 
                      <span className="text-sm font-normal text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
                        {data.comments.length}
                      </span>
                    </h2>
                  </div>
                  <CommentTree comments={data.comments} />
                </section>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
