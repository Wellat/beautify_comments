import React, { useState } from 'react';
import { MessageSquare, User, Clock, MapPin, ChevronDown, ChevronRight } from 'lucide-react';
import clsx from 'clsx';

const CommentItem = ({ comment, depth = 0 }) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const hasChildren = comment.children && comment.children.length > 0;

  return (
    <div className={clsx("flex flex-col mb-4", depth > 0 && "ml-2 pl-2 border-l-2 border-gray-200")}>
      <div className={clsx(
          "bg-white p-4 rounded-lg shadow-sm border border-gray-100 hover:shadow-md transition-shadow",
          depth > 0 && "bg-gray-50"
      )}>
        {/* Header */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            {comment.author_avatar && !comment.author_avatar.includes('default') ? (
                <img src={comment.author_avatar} alt={comment.author} className="w-6 h-6 rounded-full" />
            ) : (
                <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                  <User size={14} className="text-blue-500" />
                </div>
            )}
            <span className="font-semibold text-gray-800 text-sm">{comment.author}</span>
            {comment.reply_to_user && (
                <span className="text-gray-500 text-xs flex items-center gap-1">
                    <span className="text-gray-400">回复</span>
                    <span className="text-blue-600">@{comment.reply_to_user}</span>
                </span>
            )}
          </div>
          <div className="flex items-center gap-3 text-xs text-gray-400">
             {comment.location && <span className="flex items-center gap-1"><MapPin size={12}/>{comment.location}</span>}
             <span className="flex items-center gap-1"><Clock size={12}/>{comment.time}</span>
          </div>
        </div>

        {/* Content */}
        <div 
          className="text-gray-700 text-sm leading-relaxed break-words prose prose-sm max-w-none"
          dangerouslySetInnerHTML={{ __html: comment.content }}
        />
        
        {/* Footer / Actions */}
        {hasChildren && (
            <button 
                onClick={() => setIsExpanded(!isExpanded)}
                className="mt-2 flex items-center gap-1 text-xs text-blue-500 hover:text-blue-700 font-medium select-none"
            >
                {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                {isExpanded ? '收起回复' : `展开 ${comment.children.length} 条回复`}
            </button>
        )}
      </div>

      {/* Children */}
      {hasChildren && isExpanded && (
        <div className="mt-2">
          {comment.children.map(child => (
            <CommentItem key={child.id} comment={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
};

const CommentTree = ({ comments }) => {
  if (!comments || comments.length === 0) return <div className="text-center text-gray-500 py-10">暂无评论</div>;

  return (
    <div className="space-y-4">
      {comments.map(comment => (
        <CommentItem key={comment.id} comment={comment} />
      ))}
    </div>
  );
};

export default CommentTree;
