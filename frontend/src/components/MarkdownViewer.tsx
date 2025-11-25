import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MarkdownViewerProps {
    content: string;
}

export default function MarkdownViewer({ content }: MarkdownViewerProps) {
    return (
        <div className="prose prose-lg prose-indigo max-w-none prose-headings:font-bold prose-h1:text-3xl prose-h2:text-2xl prose-p:text-gray-700 prose-code:text-indigo-600 break-words">
            <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                    // 코드 블록 처리
                    code({ node, inline, className, children, ...props }: any) {
                        const match = /language-(\w+)/.exec(className || '');
                        const language = match ? match[1] : '';
                        
                        if (inline) {
                            return (
                                <code className="px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-700 text-sm font-mono" {...props}>
                                    {children}
                                </code>
                            );
                        }
                        
                        return (
                            <div className="relative my-6">
                                {language && (
                                    <div className="absolute top-3 right-3 px-2.5 py-1 text-xs font-semibold text-gray-300 bg-gray-900/80 rounded-md border border-gray-700 z-10">
                                        {language}
                                    </div>
                                )}
                                <pre className="bg-gray-900 text-gray-100 p-5 rounded-lg overflow-x-auto border border-gray-700 shadow-lg">
                                    <code className={`text-sm font-mono leading-relaxed ${className || ''}`} {...props}>
                                        {children}
                                    </code>
                                </pre>
                            </div>
                        );
                    },
                    // 문단 처리 - word-break 추가
                    p({ children, ...props }: any) {
                        return (
                            <p className="break-words whitespace-pre-wrap" {...props}>
                                {children}
                            </p>
                        );
                    },
                }}
            >
                {content}
            </ReactMarkdown>
        </div>
    );
}
