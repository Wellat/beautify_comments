import React, { useState } from 'react';
import axios from 'axios';
import { Search, Loader2, AlertCircle } from 'lucide-react';
import CommentTree from './components/CommentTree';

function App() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!url) return;
    
    setLoading(true);
    setError(null);
    setData(null);

    try {
      // Use local backend URL
      const response = await axios.get(`http://localhost:8000/api/parse`, {
        params: { url }
      });
      setData(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || '发生未知错误');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 font-sans">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold text-blue-600 tracking-tight">集思录评论盖楼</h1>
          <form onSubmit={handleSubmit} className="flex-1 max-w-lg ml-8 flex gap-2">
            <div className="relative flex-1">
              <input
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="输入集思录文章链接 (https://www.jisilu.cn/question/...)"
                className="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              />
              <Search className="absolute left-3 top-2.5 text-gray-400" size={18} />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium flex items-center gap-2"
            >
              {loading && <Loader2 className="animate-spin" size={18} />}
              {loading ? '抓取中...' : '开始盖楼'}
            </button>
          </form>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6 flex items-center gap-2">
            <AlertCircle size={20} />
            <span>{error}</span>
          </div>
        )}

        {/* Welcome / Empty State */}
        {!data && !loading && !error && (
          <div className="text-center py-20 text-gray-400">
            <p className="text-lg">请输入集思录文章链接以开始阅读</p>
            <p className="text-sm mt-2">例如: https://www.jisilu.cn/question/517247</p>
          </div>
        )}

        {/* Article Content */}
        {data && (
          <div className="space-y-8">
            <article className="bg-white p-8 rounded-xl shadow-sm border border-gray-100">
              <h1 className="text-3xl font-bold text-gray-900 mb-4">{data.title}</h1>
              <div className="flex items-center gap-4 text-sm text-gray-500 mb-8 border-b border-gray-100 pb-4">
                <span className="font-medium text-gray-700">{data.author}</span>
                <span>{data.publish_time}</span>
              </div>
              <div 
                className="prose prose-lg max-w-none text-gray-800 leading-relaxed"
                dangerouslySetInnerHTML={{ __html: data.content }}
              />
            </article>

            {/* Comments Section */}
            <section>
              <h2 className="text-xl font-bold text-gray-800 mb-6 flex items-center gap-2">
                评论区 
                <span className="text-sm font-normal text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
                  {data.comments.length} (顶层)
                </span>
              </h2>
              <CommentTree comments={data.comments} />
            </section>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
